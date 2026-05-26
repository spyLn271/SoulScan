use rusted_soul_dex::math::uniswap::clmm::{
    calculate_swap, SwapStepResult, FEE_RATE_MUL_VALUE,
    sqrt_price_from_tick_index, get_amount_x, get_amount_y,
};
use rusted_soul_dex::math::u512::U512;
use rusted_soul_dex::math::u256::U256;
use rusted_soul_dex::math::errors::SoulMathError;
use rusted_soul_dex::dex::uniswap::{Slot0, TickData};

use r2d2_redis::RedisConnectionManager;
use r2d2::Pool;
use r2d2_redis::redis::Commands;

use std::collections::HashMap;
use std::hash::Hash;
use serde::Deserialize;

pub const MIN_SQRT_RATIO: U512 = U512 { items: [4295128739, 0, 0, 0, 0, 0, 0, 0] };
pub const MAX_SQRT_RATIO: U512 = U512 { items: [6743328256752651558, 17280870778742802505, 4294805859, 0, 0, 0, 0, 0] };
pub const MIN_TICK: i32 = -887272;
pub const MAX_TICK: i32 = 887272;


pub fn u128_to_u512(x: u128) -> U512 {
    U512::new(0, 0, 0, x)
}

pub fn baseline_sqrt_price() -> U512 {
    sqrt_price_from_tick_index(0).unwrap()
}

pub fn baseline_liquidity() -> U512 {
    u128_to_u512(1_000_000_000_000_000_000u128) // 1e18
}

/// V3-style fee: ceil(amount_in * fee_rate / (1e6 - fee_rate))
pub fn expected_fee_from_amount_in(amount_in: u128, fee_rate: u32) -> u128 {
    if amount_in == 0 || fee_rate == 0 {
        return 0;
    }
    let num = U256::new(0, amount_in).mul(&U256::new(0, fee_rate as u128)).unwrap();
    let denom = U256::new(0, FEE_RATE_MUL_VALUE - fee_rate as u128);
    let (q, r) = num.div(&denom).unwrap();
    let mut result = q.try_into_u128().unwrap();
    if !r.is_zero() {
        result += 1;
    }
    result
}

/// Per-cell conservation: re-derive amount_in and amount_out from (sqrt_price, next, L),
/// then assert relationship based on which branch of calculate_swap produced the result.
pub fn assert_conservation(
    sqrt_price: &U512,
    liquidity: &U512,
    result: &SwapStepResult,
    x_to_y: bool,
    exact_in: bool,
    ctx: &str,
) {
    let (back_in, back_out) = if x_to_y {
        (
            get_amount_x(sqrt_price, &result.next_sqrt_price, liquidity, true).unwrap(),
            get_amount_y(sqrt_price, &result.next_sqrt_price, liquidity, false).unwrap(),
        )
    } else {
        (
            get_amount_y(sqrt_price, &result.next_sqrt_price, liquidity, true).unwrap(),
            get_amount_x(sqrt_price, &result.next_sqrt_price, liquidity, false).unwrap(),
        )
    };

    if result.is_max {
        assert_eq!(result.amount_in, back_in, "{ctx}: is_max amount_in vs back-derived");
        assert_eq!(result.amount_out, back_out, "{ctx}: is_max amount_out vs back-derived");
    } else if exact_in {
        // amount_in is calc_amount (not back-derived); back-derived must not exceed it
        assert!(back_in <= result.amount_in,
            "{ctx}: partial exact_in: back-derived input ({back_in}) > amount_in ({})", result.amount_in);
        assert_eq!(result.amount_out, back_out, "{ctx}: partial exact_in: amount_out vs back-derived");
    } else {
        // partial exact_out: amount_in is back-derived; amount_out = requested delta.
        // Price overshoots due to V3-style round-up, so back-derived output >= reported amount_out.
        assert_eq!(result.amount_in, back_in, "{ctx}: partial exact_out: amount_in vs back-derived");
        assert!(back_out >= result.amount_out,
            "{ctx}: partial exact_out: back-derived output ({back_out}) < amount_out ({}) — price didn't move enough",
            result.amount_out);
    }
}

/// Sanity invariants that must hold for any Ok result.
pub fn assert_basic_invariants(
    sqrt_price: &U512,
    boundary_tick: i32,
    result: &SwapStepResult,
    x_to_y: bool,
    ctx: &str,
) {
    // direction
    if x_to_y {
        assert!(result.next_sqrt_price.lte(sqrt_price),
            "{ctx}: x_to_y but next_sqrt_price > sqrt_price");
    } else {
        assert!(result.next_sqrt_price.gte(sqrt_price),
            "{ctx}: y_to_x but next_sqrt_price < sqrt_price");
    }

    // range
    assert!(MIN_SQRT_RATIO.lte(&result.next_sqrt_price),
        "{ctx}: next_sqrt_price < MIN_SQRT_RATIO");
    assert!(result.next_sqrt_price.lt(&MAX_SQRT_RATIO),
        "{ctx}: next_sqrt_price >= MAX_SQRT_RATIO");

    // boundary equivalence
    let boundary_sqrt = sqrt_price_from_tick_index(boundary_tick).unwrap();
    if result.is_max {
        assert!(result.next_sqrt_price.eq(&boundary_sqrt),
            "{ctx}: is_max but next != boundary_sqrt");
    } else {
        assert!(!result.next_sqrt_price.eq(&boundary_sqrt),
            "{ctx}: !is_max but next == boundary_sqrt");
    }
}


// ------------------------- Redis loader -------------------------

#[derive(Deserialize, Debug)]
#[serde(bound(deserialize = "K: Deserialize<'de> + Eq + Hash, V: Deserialize<'de>"))]
struct PoolFormat<K, V> {
    pub pool_state: HashMap<K, V>,
    pub ts: u64,
}

pub fn redis_pool() -> Pool<RedisConnectionManager> {
    let manager = RedisConnectionManager::new("redis://127.0.0.1:6379/0")
        .expect("redis manager init");
    Pool::builder()
        .max_size(10)
        .build(manager)
        .expect("redis pool build (is SSH tunnel up on 127.0.0.1:6379?)")
}

pub fn load_v3_slots(pool: &Pool<RedisConnectionManager>) -> HashMap<String, Slot0> {
    let mut con = pool.get().expect("redis get conn");
    let raw: String = con.hget("snapshot:state:eth:uniswap:v3", "slot")
        .expect("redis hget slot");
    let pf: PoolFormat<String, Slot0> = serde_json::from_str(&raw)
        .expect("parse slot0 JSON");
    pf.pool_state
}

pub fn load_v3_ticks(
    pool: &Pool<RedisConnectionManager>,
) -> HashMap<String, HashMap<i32, TickData>> {
    let mut con = pool.get().expect("redis get conn");
    let raw: String = con.hget("snapshot:state:eth:uniswap:v3", "ticks")
        .expect("redis hget ticks");
    let pf: PoolFormat<String, HashMap<i32, TickData>> = serde_json::from_str(&raw)
        .expect("parse ticks JSON");
    pf.pool_state
}

pub fn nearest_initialized_below(ticks: &HashMap<i32, TickData>, from: i32) -> Option<i32> {
    ticks.keys().filter(|k| **k < from).max().copied()
}

pub fn nearest_initialized_above(ticks: &HashMap<i32, TickData>, from: i32) -> Option<i32> {
    ticks.keys().filter(|k| **k > from).min().copied()
}


// ------------------------- mod eight_cell_matrix -------------------------

mod eight_cell_matrix {
    use super::*;

    #[test]
    fn x_to_y_exact_in_partial() {
        let sqrt = baseline_sqrt_price();
        let liquidity = baseline_liquidity();
        let fee_rate = 3000u32;
        let boundary_tick = -60_000;
        let delta_amount = 1_000_000u128;

        let result = calculate_swap(sqrt, boundary_tick, liquidity, delta_amount, fee_rate, true, true)
            .expect("swap ok");

        assert!(!result.is_max, "expected partial step");
        assert_basic_invariants(&sqrt, boundary_tick, &result, true, "x_to_y_exact_in_partial");
        // exact_in partial fee equation: amount_in + fee_amount == delta_amount
        assert_eq!(result.amount_in + result.fee_amount, delta_amount, "fee+in=delta");
        assert_conservation(&sqrt, &liquidity, &result, true, true, "x_to_y_exact_in_partial");
    }

    #[test]
    fn x_to_y_exact_in_hit_boundary() {
        let sqrt = baseline_sqrt_price();
        let liquidity = baseline_liquidity();
        let fee_rate = 3000u32;
        let boundary_tick = -10;
        let delta_amount = 1_000_000_000_000_000_000u128; // 1e18

        let result = calculate_swap(sqrt, boundary_tick, liquidity, delta_amount, fee_rate, true, true)
            .expect("swap ok");

        assert!(result.is_max, "expected hit boundary");
        assert_basic_invariants(&sqrt, boundary_tick, &result, true, "x_to_y_exact_in_hit_boundary");
        // exact_in hit_boundary fee equation: fee = ceil(amount_in * fee / (1e6 - fee))
        assert_eq!(result.fee_amount, expected_fee_from_amount_in(result.amount_in, fee_rate),
            "fee equation hit boundary");
        // Consumed input + fee should be <= delta_amount
        assert!(result.amount_in + result.fee_amount <= delta_amount,
            "in+fee should not exceed delta");
        assert_conservation(&sqrt, &liquidity, &result, true, true, "x_to_y_exact_in_hit_boundary");
    }

    #[test]
    fn x_to_y_exact_out_partial() {
        let sqrt = baseline_sqrt_price();
        let liquidity = baseline_liquidity();
        let fee_rate = 3000u32;
        let boundary_tick = -60_000;
        let delta_amount = 1_000_000u128; // small Y output

        let result = calculate_swap(sqrt, boundary_tick, liquidity, delta_amount, fee_rate, true, false)
            .expect("swap ok");

        assert!(!result.is_max, "expected partial step");
        assert_basic_invariants(&sqrt, boundary_tick, &result, true, "x_to_y_exact_out_partial");
        assert_eq!(result.amount_out, delta_amount, "exact_out: amount_out == requested");
        // fee equation: fee = ceil(amount_in * fee / (1e6 - fee))
        assert_eq!(result.fee_amount, expected_fee_from_amount_in(result.amount_in, fee_rate),
            "fee equation exact_out partial");
        assert_conservation(&sqrt, &liquidity, &result, true, false, "x_to_y_exact_out_partial");
    }

    #[test]
    fn x_to_y_exact_out_hit_boundary() {
        let sqrt = baseline_sqrt_price();
        let liquidity = baseline_liquidity();
        let fee_rate = 3000u32;
        let boundary_tick = -10;
        let delta_amount = 100_000_000_000_000_000u128; // 1e17, large Y request

        let result = calculate_swap(sqrt, boundary_tick, liquidity, delta_amount, fee_rate, true, false)
            .expect("swap ok");

        assert!(result.is_max, "expected hit boundary");
        assert_basic_invariants(&sqrt, boundary_tick, &result, true, "x_to_y_exact_out_hit_boundary");
        assert_eq!(result.fee_amount, expected_fee_from_amount_in(result.amount_in, fee_rate),
            "fee equation exact_out hit boundary");
        assert_conservation(&sqrt, &liquidity, &result, true, false, "x_to_y_exact_out_hit_boundary");
    }

    #[test]
    fn y_to_x_exact_in_partial() {
        let sqrt = baseline_sqrt_price();
        let liquidity = baseline_liquidity();
        let fee_rate = 3000u32;
        let boundary_tick = 60_000;
        let delta_amount = 1_000_000u128;

        let result = calculate_swap(sqrt, boundary_tick, liquidity, delta_amount, fee_rate, false, true)
            .expect("swap ok");

        assert!(!result.is_max, "expected partial step");
        assert_basic_invariants(&sqrt, boundary_tick, &result, false, "y_to_x_exact_in_partial");
        assert_eq!(result.amount_in + result.fee_amount, delta_amount, "fee+in=delta");
        assert_conservation(&sqrt, &liquidity, &result, false, true, "y_to_x_exact_in_partial");
    }

    #[test]
    fn y_to_x_exact_in_hit_boundary() {
        let sqrt = baseline_sqrt_price();
        let liquidity = baseline_liquidity();
        let fee_rate = 3000u32;
        let boundary_tick = 10;
        let delta_amount = 1_000_000_000_000_000_000u128; // 1e18

        let result = calculate_swap(sqrt, boundary_tick, liquidity, delta_amount, fee_rate, false, true)
            .expect("swap ok");

        assert!(result.is_max, "expected hit boundary");
        assert_basic_invariants(&sqrt, boundary_tick, &result, false, "y_to_x_exact_in_hit_boundary");
        assert_eq!(result.fee_amount, expected_fee_from_amount_in(result.amount_in, fee_rate),
            "fee equation hit boundary");
        assert!(result.amount_in + result.fee_amount <= delta_amount, "in+fee should not exceed delta");
        assert_conservation(&sqrt, &liquidity, &result, false, true, "y_to_x_exact_in_hit_boundary");
    }

    #[test]
    fn y_to_x_exact_out_partial() {
        let sqrt = baseline_sqrt_price();
        let liquidity = baseline_liquidity();
        let fee_rate = 3000u32;
        let boundary_tick = 60_000;
        let delta_amount = 1_000_000u128; // small X output

        let result = calculate_swap(sqrt, boundary_tick, liquidity, delta_amount, fee_rate, false, false)
            .expect("swap ok");

        assert!(!result.is_max, "expected partial step");
        assert_basic_invariants(&sqrt, boundary_tick, &result, false, "y_to_x_exact_out_partial");
        assert_eq!(result.amount_out, delta_amount, "exact_out: amount_out == requested");
        assert_eq!(result.fee_amount, expected_fee_from_amount_in(result.amount_in, fee_rate),
            "fee equation exact_out partial");
        assert_conservation(&sqrt, &liquidity, &result, false, false, "y_to_x_exact_out_partial");
    }

    #[test]
    fn y_to_x_exact_out_hit_boundary() {
        let sqrt = baseline_sqrt_price();
        let liquidity = baseline_liquidity();
        let fee_rate = 3000u32;
        let boundary_tick = 10;
        let delta_amount = 100_000_000_000_000_000u128; // 1e17

        let result = calculate_swap(sqrt, boundary_tick, liquidity, delta_amount, fee_rate, false, false)
            .expect("swap ok");

        assert!(result.is_max, "expected hit boundary");
        assert_basic_invariants(&sqrt, boundary_tick, &result, false, "y_to_x_exact_out_hit_boundary");
        assert_eq!(result.fee_amount, expected_fee_from_amount_in(result.amount_in, fee_rate),
            "fee equation exact_out hit boundary");
        assert_conservation(&sqrt, &liquidity, &result, false, false, "y_to_x_exact_out_hit_boundary");
    }
}


// ------------------------- mod fee_equations -------------------------

mod fee_equations {
    use super::*;

    #[test]
    fn exact_in_partial_conservation_synthetic() {
        let sqrt = baseline_sqrt_price();
        let liquidity = baseline_liquidity();
        let boundary_tick = -60_000;
        for fee_rate in [0u32, 100, 500, 3000, 10000] {
            for delta in [1_000u128, 1_000_000, 1_000_000_000] {
                let r = calculate_swap(sqrt, boundary_tick, liquidity, delta, fee_rate, true, true)
                    .expect("ok");
                assert!(!r.is_max);
                assert_eq!(r.amount_in + r.fee_amount, delta,
                    "fee_rate={fee_rate}, delta={delta}: in+fee != delta");
            }
        }
    }

    #[test]
    fn exact_in_hit_boundary_fee_equation_synthetic() {
        let sqrt = baseline_sqrt_price();
        let liquidity = baseline_liquidity();
        let boundary_tick = -100;
        let big_delta = 1_000_000_000_000_000_000u128;
        for fee_rate in [100u32, 500, 3000, 10000] {
            let r = calculate_swap(sqrt, boundary_tick, liquidity, big_delta, fee_rate, true, true)
                .expect("ok");
            assert!(r.is_max, "fee_rate={fee_rate}: expected hit boundary");
            assert_eq!(r.fee_amount, expected_fee_from_amount_in(r.amount_in, fee_rate),
                "fee_rate={fee_rate}: fee equation");
        }
    }

    #[test]
    fn exact_out_fee_equation_synthetic() {
        let sqrt = baseline_sqrt_price();
        let liquidity = baseline_liquidity();
        // both partial and hit_boundary cells use the same fee formula
        for (boundary_tick, delta, expected_max) in [
            (-60_000i32, 1_000u128, false),
            (-60_000, 1_000_000_000, false),
            (-100, 100_000_000_000_000_000, true), // 1e17 hits boundary
        ] {
            for fee_rate in [100u32, 500, 3000, 10000] {
                let r = calculate_swap(sqrt, boundary_tick, liquidity, delta, fee_rate, true, false)
                    .expect("ok");
                assert_eq!(r.is_max, expected_max, "is_max mismatch for ({boundary_tick}, {delta})");
                assert_eq!(r.fee_amount, expected_fee_from_amount_in(r.amount_in, fee_rate),
                    "boundary={boundary_tick}, delta={delta}, fee_rate={fee_rate}: fee equation");
            }
        }
    }

    #[test]
    fn fee_zero_yields_zero_fee() {
        let sqrt = baseline_sqrt_price();
        let liquidity = baseline_liquidity();
        // partial exact_in
        let r = calculate_swap(sqrt, -60_000, liquidity, 1_000_000_000u128, 0, true, true)
            .expect("ok");
        assert_eq!(r.fee_amount, 0);
        assert_eq!(r.amount_in, 1_000_000_000u128);
        // hit boundary exact_in
        let r = calculate_swap(sqrt, -100, liquidity, 1_000_000_000_000_000_000u128, 0, true, true)
            .expect("ok");
        assert_eq!(r.fee_amount, 0);
    }

    #[test]
    fn fee_high_still_satisfies_equation() {
        let sqrt = baseline_sqrt_price();
        let liquidity = baseline_liquidity();
        let fee_rate = 999_000u32; // 99.9% fee
        let r = calculate_swap(sqrt, -60_000, liquidity, 1_000_000_000u128, fee_rate, true, true)
            .expect("ok");
        assert!(!r.is_max);
        assert_eq!(r.amount_in + r.fee_amount, 1_000_000_000u128);
        assert!(r.amount_in < r.fee_amount, "high fee: amount_in should be small");
    }
}


// ------------------------- mod invariants_on_real_pools -------------------------

mod invariants_on_real_pools {
    use super::*;

    #[test]
    fn all_pools_swap_sweep() {
        let pool = redis_pool();
        let slots = load_v3_slots(&pool);
        let ticks = load_v3_ticks(&pool);
        println!("Loaded {} V3 pools", slots.len());

        let amounts = [1_000u128, 1_000_000, 1_000_000_000, 1_000_000_000_000];
        let fee_rate = 3000u32;

        let mut ok_count: usize = 0;
        let mut err_count: usize = 0;
        let mut failures: Vec<String> = Vec::new();

        for (addr, slot0) in &slots {
            if slot0.liquidity.is_zero() {
                continue;
            }
            let pool_ticks = match ticks.get(addr) {
                Some(t) => t,
                None => continue,
            };

            for (x_to_y, boundary_opt) in [
                (true, nearest_initialized_below(pool_ticks, slot0.tick_current)),
                (false, nearest_initialized_above(pool_ticks, slot0.tick_current)),
            ] {
                let boundary = match boundary_opt {
                    Some(b) if b >= MIN_TICK && b <= MAX_TICK => b,
                    _ => continue,
                };

                for &amt in amounts.iter() {
                    for exact_in in [true, false] {
                        let ctx = format!("{addr} x_to_y={x_to_y} exact_in={exact_in} amt={amt} bnd={boundary}");
                        match calculate_swap(
                            slot0.sqrt_price_x96,
                            boundary,
                            slot0.liquidity,
                            amt,
                            fee_rate,
                            x_to_y,
                            exact_in,
                        ) {
                            Ok(r) => {
                                ok_count += 1;
                                // Run invariants; collect first failure per swap.
                                if let Err(msg) = check_all_invariants(
                                    &slot0.sqrt_price_x96, &slot0.liquidity,
                                    boundary, amt, fee_rate, x_to_y, exact_in, &r,
                                ) {
                                    failures.push(format!("{ctx}: {msg}"));
                                }
                            }
                            Err(_) => {
                                err_count += 1; // legitimate overflow/underflow at extremes
                            }
                        }
                    }
                }
            }
        }

        println!("ok={ok_count}, err={err_count}, failures={}", failures.len());
        if !failures.is_empty() {
            let preview = failures.iter().take(20).cloned().collect::<Vec<_>>().join("\n");
            panic!("{} swap invariant failures:\n{}", failures.len(), preview);
        }
    }

    // Returns Ok if all invariants hold, Err(msg) on the first failure.
    fn check_all_invariants(
        sqrt_price: &U512, liquidity: &U512,
        boundary_tick: i32, delta_amount: u128, fee_rate: u32,
        x_to_y: bool, exact_in: bool,
        r: &SwapStepResult,
    ) -> Result<(), String> {
        // direction
        if x_to_y && !r.next_sqrt_price.lte(sqrt_price) {
            return Err(format!("x_to_y but next > current"));
        }
        if !x_to_y && !r.next_sqrt_price.gte(sqrt_price) {
            return Err(format!("y_to_x but next < current"));
        }

        // range
        if !MIN_SQRT_RATIO.lte(&r.next_sqrt_price) {
            return Err(format!("next < MIN_SQRT_RATIO"));
        }
        if !r.next_sqrt_price.lt(&MAX_SQRT_RATIO) {
            return Err(format!("next >= MAX_SQRT_RATIO"));
        }

        // boundary
        let boundary_sqrt = sqrt_price_from_tick_index(boundary_tick).map_err(|e| format!("{e:?}"))?;
        if r.is_max && !r.next_sqrt_price.eq(&boundary_sqrt) {
            return Err(format!("is_max but next != boundary"));
        }
        if !r.is_max && r.next_sqrt_price.eq(&boundary_sqrt) {
            return Err(format!("!is_max but next == boundary"));
        }

        // conservation
        let (back_in, back_out) = if x_to_y {
            (
                get_amount_x(sqrt_price, &r.next_sqrt_price, liquidity, true).map_err(|e| format!("back_in: {e:?}"))?,
                get_amount_y(sqrt_price, &r.next_sqrt_price, liquidity, false).map_err(|e| format!("back_out: {e:?}"))?,
            )
        } else {
            (
                get_amount_y(sqrt_price, &r.next_sqrt_price, liquidity, true).map_err(|e| format!("back_in: {e:?}"))?,
                get_amount_x(sqrt_price, &r.next_sqrt_price, liquidity, false).map_err(|e| format!("back_out: {e:?}"))?,
            )
        };

        if r.is_max {
            if r.amount_in != back_in {
                return Err(format!("is_max amount_in {} != back {}", r.amount_in, back_in));
            }
            if r.amount_out != back_out {
                return Err(format!("is_max amount_out {} != back {}", r.amount_out, back_out));
            }
        } else if exact_in {
            if back_in > r.amount_in {
                return Err(format!("partial exact_in: back_in {} > amount_in {}", back_in, r.amount_in));
            }
            if r.amount_out != back_out {
                return Err(format!("partial exact_in: amount_out {} != back {}", r.amount_out, back_out));
            }
        } else {
            // partial exact_out: amount_in is back-derived; amount_out = requested.
            // Price overshoots due to V3-style round-up, so back_out >= amount_out (no V3 cap).
            if r.amount_in != back_in {
                return Err(format!("partial exact_out: amount_in {} != back {}", r.amount_in, back_in));
            }
            if back_out < r.amount_out {
                return Err(format!("partial exact_out: back_out {} < amount_out {} (price didn't move enough)",
                    back_out, r.amount_out));
            }
        }

        // fee equation
        if r.is_max || !exact_in {
            // gross-up rule
            let expected = expected_fee_from_amount_in(r.amount_in, fee_rate);
            if r.fee_amount != expected {
                return Err(format!("fee equation hit-or-out: fee {} != expected {}", r.fee_amount, expected));
            }
        } else {
            // partial exact_in: amount_in + fee = delta
            if r.amount_in + r.fee_amount != delta_amount {
                return Err(format!("partial exact_in fee: in {} + fee {} != delta {}",
                    r.amount_in, r.fee_amount, delta_amount));
            }
        }

        Ok(())
    }
}


// ------------------------- mod monotonicity -------------------------

mod monotonicity {
    use super::*;

    #[test]
    fn synthetic_pool_exact_in_monotonic() {
        let sqrt = baseline_sqrt_price();
        let liquidity = baseline_liquidity();
        let boundary_tick = -1_000;
        let fee_rate = 3000u32;

        let mut prev_out: Option<u128> = None;
        let mut prev_is_max = false;
        let mut prev_next: Option<U512> = None;

        for delta in [1_000u128, 10_000, 100_000, 1_000_000, 100_000_000, 10_000_000_000, 1_000_000_000_000, 100_000_000_000_000, 10_000_000_000_000_000, 1_000_000_000_000_000_000u128] {
            let r = calculate_swap(sqrt, boundary_tick, liquidity, delta, fee_rate, true, true)
                .expect("swap ok");

            if let Some(p) = prev_out {
                assert!(r.amount_out >= p,
                    "monotonicity: amount_out decreased from {p} to {} at delta={delta}", r.amount_out);
            }

            if prev_is_max {
                assert!(r.is_max, "once is_max, further bigger inputs should stay is_max (delta={delta})");
                assert_eq!(r.next_sqrt_price.eq(prev_next.as_ref().unwrap()), true,
                    "once is_max, next_sqrt_price should be constant (delta={delta})");
            }

            prev_out = Some(r.amount_out);
            prev_is_max = r.is_max;
            prev_next = Some(r.next_sqrt_price);
        }
    }

    #[test]
    fn real_pool_exact_in_monotonic() {
        let pool = redis_pool();
        let slots = load_v3_slots(&pool);
        let ticks = load_v3_ticks(&pool);

        let mut tested = 0;
        for (addr, slot0) in slots.iter().take(20) {
            if slot0.liquidity.is_zero() { continue; }
            let pool_ticks = match ticks.get(addr) { Some(t) => t, None => continue };
            let boundary = match nearest_initialized_below(pool_ticks, slot0.tick_current) {
                Some(b) => b,
                None => continue,
            };

            let mut prev_out: Option<u128> = None;
            for delta in [1_000u128, 1_000_000, 1_000_000_000, 1_000_000_000_000] {
                match calculate_swap(slot0.sqrt_price_x96, boundary, slot0.liquidity, delta, 3000, true, true) {
                    Ok(r) => {
                        if let Some(p) = prev_out {
                            assert!(r.amount_out >= p,
                                "{addr}: amount_out decreased {p} -> {} at delta={delta}", r.amount_out);
                        }
                        prev_out = Some(r.amount_out);
                    }
                    Err(_) => continue,
                }
            }
            tested += 1;
        }
        assert!(tested > 0, "no real pools sampled");
        println!("monotonicity tested on {tested} pools");
    }
}


// ------------------------- mod round_trip -------------------------

mod round_trip {
    use super::*;

    #[test]
    fn with_fee_zero_recovers_approximately() {
        let sqrt = baseline_sqrt_price();
        let liquidity = baseline_liquidity();
        let boundary_down = -60_000;
        let boundary_up = 60_000;
        let initial_x = 1_000_000_000u128;

        // X -> Y (partial)
        let r1 = calculate_swap(sqrt, boundary_down, liquidity, initial_x, 0, true, true)
            .expect("swap1");
        assert!(!r1.is_max);
        let mid_sqrt = r1.next_sqrt_price;
        let received_y = r1.amount_out;

        // Y -> X (partial), using received_y as input
        let r2 = calculate_swap(mid_sqrt, boundary_up, liquidity, received_y, 0, false, true)
            .expect("swap2");
        assert!(!r2.is_max);
        let recovered_x = r2.amount_out;

        // With zero fee, recovered_x ≈ initial_x (allow small rounding loss <= 2)
        let loss = initial_x.saturating_sub(recovered_x);
        assert!(loss <= 2, "fee=0 round-trip lost {} (>2 units of rounding)", loss);
    }

    #[test]
    fn with_fee_costs_user_value() {
        let sqrt = baseline_sqrt_price();
        let liquidity = baseline_liquidity();
        let boundary_down = -60_000;
        let boundary_up = 60_000;
        let initial_x = 1_000_000_000u128;
        let fee_rate = 3000u32; // 0.3%

        let r1 = calculate_swap(sqrt, boundary_down, liquidity, initial_x, fee_rate, true, true)
            .expect("swap1");
        let mid_sqrt = r1.next_sqrt_price;
        let received_y = r1.amount_out;

        let r2 = calculate_swap(mid_sqrt, boundary_up, liquidity, received_y, fee_rate, false, true)
            .expect("swap2");
        let recovered_x = r2.amount_out;

        // With 0.3% fee twice, we lose at least ~0.6% of initial
        let loss = initial_x - recovered_x;
        let min_expected_loss = initial_x * 5 / 1000; // 0.5% lower bound (conservative)
        let max_expected_loss = initial_x * 10 / 1000; // 1.0% upper bound
        assert!(loss >= min_expected_loss && loss <= max_expected_loss,
            "fee=0.3% round-trip loss {} not in [{}, {}]",
            loss, min_expected_loss, max_expected_loss);
    }
}


// ------------------------- mod edge_cases -------------------------

mod edge_cases {
    use super::*;

    #[test]
    fn delta_amount_zero_yields_zero_swap() {
        let sqrt = baseline_sqrt_price();
        let liquidity = baseline_liquidity();
        let r = calculate_swap(sqrt, -60_000, liquidity, 0, 3000, true, true).expect("ok");
        assert_eq!(r.amount_in, 0);
        assert_eq!(r.amount_out, 0);
        assert_eq!(r.fee_amount, 0);
    }

    #[test]
    fn boundary_at_current_tick_is_degenerate() {
        let sqrt = baseline_sqrt_price();
        let liquidity = baseline_liquidity();
        // tick 0, boundary also at tick 0
        let r = calculate_swap(sqrt, 0, liquidity, 1_000_000_000u128, 3000, true, true)
            .expect("ok");
        assert!(r.is_max, "boundary==current should be is_max");
        assert_eq!(r.amount_in, 0, "no input consumed");
        assert_eq!(r.amount_out, 0, "no output");
        assert_eq!(r.fee_amount, 0, "no fee");
        assert!(r.next_sqrt_price.eq(&sqrt), "no price movement");
    }

    #[test]
    fn liquidity_zero_yields_no_swap() {
        let sqrt = baseline_sqrt_price();
        let zero_l = U512 { items: [0; 8] };
        let r = calculate_swap(sqrt, -60_000, zero_l, 1_000_000_000u128, 3000, true, true)
            .expect("ok");
        // L=0: target_sqrt = 0, falls below boundary -> hit boundary path with 0 amounts
        assert!(r.is_max);
        assert_eq!(r.amount_in, 0);
        assert_eq!(r.amount_out, 0);
        assert_eq!(r.fee_amount, 0);
    }

    #[test]
    fn boundary_outside_tick_range_errors() {
        let sqrt = baseline_sqrt_price();
        let liquidity = baseline_liquidity();
        let result = calculate_swap(sqrt, MAX_TICK + 1, liquidity, 1_000_000_000u128, 3000, true, true);
        assert!(matches!(result, Err(SoulMathError::TickIsNotInRange)));

        let result = calculate_swap(sqrt, MIN_TICK - 1, liquidity, 1_000_000_000u128, 3000, true, true);
        assert!(matches!(result, Err(SoulMathError::TickIsNotInRange)));
    }

    #[test]
    fn very_large_delta_does_not_panic() {
        let sqrt = baseline_sqrt_price();
        let liquidity = baseline_liquidity();
        // u128::MAX delta — should either hit boundary or error cleanly, no panic
        let _ = calculate_swap(sqrt, -60_000, liquidity, u128::MAX, 3000, true, true);
        // Just verify the call returns (Ok or Err), no panic.
    }

    #[test]
    fn fee_zero_partial_amount_in_equals_delta() {
        let sqrt = baseline_sqrt_price();
        let liquidity = baseline_liquidity();
        let delta = 1_000_000_000u128;
        let r = calculate_swap(sqrt, -60_000, liquidity, delta, 0, true, true).expect("ok");
        assert!(!r.is_max);
        assert_eq!(r.amount_in, delta);
        assert_eq!(r.fee_amount, 0);
    }
}
