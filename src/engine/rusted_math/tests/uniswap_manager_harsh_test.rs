use rusted_soul_dex::smart_router::v2::manager::uniswap::clmm::swap_dynamic::{
    swap_manager as clmm_swap_manager,
    DynamicUniClmmResult,
};
use rusted_soul_dex::smart_router::v2::manager::uniswap::amm::swap_dynamic::{
    swap_manager as amm_swap_manager,
    DynamicUniAmmResult,
};
use rusted_soul_dex::smart_router::manager_errors::SoulManagerError;
use rusted_soul_dex::math::uniswap::clmm::{
    calculate_swap,
    sqrt_price_from_tick_index,
    get_lower_tick, get_upper_tick,
};
use rusted_soul_dex::math::u256::U256;
use rusted_soul_dex::math::u512::U512;
use rusted_soul_dex::math::errors::SoulMathError;
use rusted_soul_dex::dex::uniswap::{Slot0, TickData, UniswapAmm, UniswapClmm};

use r2d2_redis::RedisConnectionManager;
use r2d2::Pool;
use r2d2_redis::redis::Commands;
use std::collections::HashMap;
use std::hash::Hash;
use serde::Deserialize;

pub const MIN_SQRT_RATIO: U512 = U512 { items: [4295128739, 0, 0, 0, 0, 0, 0, 0] };
pub const MAX_SQRT_RATIO: U512 = U512 { items: [6743328256752651558, 17280870778742802505, 4294805859, 0, 0, 0, 0, 0] };

pub fn u128_to_u512(x: u128) -> U512 {
    U512::from_u128(x)
}

/// V3-style fee: ceil(amount_in * fee_rate / (1e6 - fee_rate))
pub fn expected_fee_from_amount_in(amount_in: u128, fee_rate: u32) -> u128 {
    if amount_in == 0 || fee_rate == 0 {
        return 0;
    }
    let num = U256::new(0, amount_in).mul(&U256::new(0, fee_rate as u128)).unwrap();
    let denom = U256::new(0, 1_000_000u128 - fee_rate as u128);
    let (q, r) = num.div(&denom).unwrap();
    let mut result = q.try_into_u128().unwrap();
    if !r.is_zero() {
        result += 1;
    }
    result
}

/// Builds a synthetic UniswapClmm pool at a given tick with given liquidity.
/// Populates every spacing multiple in tick_range with liquidity_net=0,
/// then applies overrides from net_at.
pub fn synthetic_clmm(
    initial_tick: i32,
    liquidity: u128,
    tick_spacing: i32,
    tick_range: (i32, i32),
    net_at: &[(i32, i128)],
) -> UniswapClmm {
    let sqrt = sqrt_price_from_tick_index(initial_tick).unwrap();
    let slot0 = Slot0 {
        sqrt_price_x96: sqrt,
        tick_current: initial_tick,
        liquidity: u128_to_u512(liquidity),
    };

    let mut tick_map: HashMap<i32, TickData> = HashMap::new();
    let (lo, hi) = tick_range;
    let mut t = (lo / tick_spacing) * tick_spacing;
    if t < lo {
        t += tick_spacing;
    }
    while t <= hi {
        tick_map.insert(t, TickData { liquidity_net: 0, liquidity_gross: 0 });
        t += tick_spacing;
    }

    for (tick, net) in net_at {
        tick_map
            .entry(*tick)
            .and_modify(|e| e.liquidity_net = *net)
            .or_insert(TickData { liquidity_net: *net, liquidity_gross: 0 });
    }

    UniswapClmm { slot0, tick: tick_map }
}

pub fn synthetic_amm(reserve0: u128, reserve1: u128) -> UniswapAmm {
    UniswapAmm { reserve0, reserve1 }
}

/// Hand-driven equivalent of swap_manager. Should produce bit-identical output.
/// Used to catch any regression in the manager's loop logic.
pub fn manual_drive_clmm(
    x_to_y: bool,
    amount_specified_is_in: bool,
    delta_amount: u128,
    fee_rate: u32,
    tick_spacing: i32,
    uni_pool: &UniswapClmm,
) -> Result<DynamicUniClmmResult, SoulManagerError> {
    let mut total_amount_in: u128 = 0;
    let mut total_amount_out: u128 = 0;
    let mut total_fee_amount: u128 = 0;

    let slot0 = uni_pool.slot0;
    let mut liquidity = slot0.liquidity;
    let mut current_sqrt = slot0.sqrt_price_x96;
    let tick_current = slot0.tick_current;

    let mut boundary_tick = if x_to_y {
        get_lower_tick(tick_current, tick_spacing)
    } else {
        get_upper_tick(tick_current, tick_spacing)
    };

    let mut amount_remaining: i128 = delta_amount
        .try_into()
        .map_err(|_| SoulManagerError::AmountOverflow)?;

    while amount_remaining > 0 {
        let step = calculate_swap(
            current_sqrt,
            boundary_tick,
            liquidity,
            amount_remaining as u128,
            fee_rate,
            x_to_y,
            amount_specified_is_in,
        )?;

        current_sqrt = step.next_sqrt_price;
        total_fee_amount += step.fee_amount;
        total_amount_in += step.amount_in + step.fee_amount;
        total_amount_out += step.amount_out;

        if amount_specified_is_in {
            amount_remaining -= (step.amount_in + step.fee_amount) as i128;
        } else {
            amount_remaining -= step.amount_out as i128;
        }

        if step.is_max {
            let td = uni_pool.tick.get(&boundary_tick);
            match td {
                None => return Err(SoulManagerError::RunOutOfLiquidity),
                Some(td) => {
                    let net = td.liquidity_net;
                    if x_to_y {
                        boundary_tick -= tick_spacing;
                        liquidity = apply_delta(liquidity, -net)?;
                    } else {
                        boundary_tick += tick_spacing;
                        liquidity = apply_delta(liquidity, net)?;
                    }
                }
            }
        }
    }

    Ok(DynamicUniClmmResult {
        total_amount_in,
        total_amount_out,
        total_fee_amount,
        new_liquidity: liquidity,
        new_sqrt_price_x96: current_sqrt,
    })
}

fn apply_delta(liquidity: U512, delta: i128) -> Result<U512, SoulManagerError> {
    if delta == 0 {
        Ok(liquidity)
    } else if delta > 0 {
        liquidity.add(&u128_to_u512(delta as u128)).map_err(SoulManagerError::MathError)
    } else {
        liquidity.sub(&u128_to_u512(delta.unsigned_abs())).map_err(SoulManagerError::MathError)
    }
}

/// Maps V3 fee tier to tick_spacing (standard table).
pub fn tick_spacing_for_fee(fee_rate: u32) -> i32 {
    match fee_rate {
        100 => 1,
        500 => 10,
        3000 => 60,
        10000 => 200,
        _ => 60,
    }
}

/// Infers tick_spacing as min consecutive difference among tick keys.
/// Works when the upstream populates every spacing multiple (per user's setup).
pub fn infer_tick_spacing(tick_map: &HashMap<i32, TickData>) -> Option<i32> {
    if tick_map.len() < 2 {
        return None;
    }
    let mut keys: Vec<i32> = tick_map.keys().copied().collect();
    keys.sort();
    keys.windows(2).map(|w| w[1] - w[0]).min().filter(|&d| d > 0)
}

// ------------------------- Redis loader -------------------------

#[derive(Deserialize, Debug)]
#[serde(bound(deserialize = "K: Deserialize<'de> + Eq + Hash, V: Deserialize<'de>"))]
struct PoolFormat<K, V> {
    pub pool_state: HashMap<K, V>,
    pub ts: u64,
}

pub fn redis_pool() -> Pool<RedisConnectionManager> {
    let mgr = RedisConnectionManager::new("redis://127.0.0.1:6379/0").expect("redis manager");
    Pool::builder().max_size(10).build(mgr).expect("redis pool (is SSH tunnel up?)")
}

pub fn load_v3_slots(pool: &Pool<RedisConnectionManager>) -> HashMap<String, Slot0> {
    let mut con = pool.get().expect("redis conn");
    let raw: String = con.hget("snapshot:state:eth:uniswap:v3", "slot").expect("hget slot");
    let pf: PoolFormat<String, Slot0> = serde_json::from_str(&raw).expect("parse slot0");
    pf.pool_state
}

pub fn load_v3_ticks(pool: &Pool<RedisConnectionManager>) -> HashMap<String, HashMap<i32, TickData>> {
    let mut con = pool.get().expect("redis conn");
    let raw: String = con.hget("snapshot:state:eth:uniswap:v3", "ticks").expect("hget ticks");
    let pf: PoolFormat<String, HashMap<i32, TickData>> = serde_json::from_str(&raw).expect("parse ticks");
    pf.pool_state
}

pub fn load_v2_pools(pool: &Pool<RedisConnectionManager>) -> HashMap<String, UniswapAmm> {
    let mut con = pool.get().expect("redis conn");
    let raw: String = con.get("snapshot:state:eth:uniswap:v2").expect("get v2");
    let pf: PoolFormat<String, UniswapAmm> = serde_json::from_str(&raw).expect("parse v2");
    pf.pool_state
}


// ====================== CLMM manager tests ======================

mod clmm_no_crossing {
    use super::*;

    #[test]
    fn x_to_y_small_swap_matches_single_step() {
        // Initial tick 30 (between -60 and 0), boundary will be at 0.
        // Use a small enough delta that we don't reach tick 0.
        let pool = synthetic_clmm(
            30,
            1_000_000_000_000_000_000u128,
            60,
            (-600, 600),
            &[],
        );
        let delta = 1_000u128;
        let fee_rate = 3000u32;

        let result = clmm_swap_manager(true, true, delta, fee_rate, 60, &pool).expect("swap ok");

        // No tick crossing -> liquidity unchanged.
        assert!(result.new_liquidity.eq(&pool.slot0.liquidity), "liquidity should be unchanged");
        // Price should have moved down (x_to_y).
        assert!(result.new_sqrt_price_x96.lt(&pool.slot0.sqrt_price_x96), "price didn't fall");
        // No boundary hit, so we should have consumed exactly delta as gross input.
        assert_eq!(result.total_amount_in, delta, "gross in should equal delta for partial exact_in");
    }

    #[test]
    fn y_to_x_small_swap_matches_single_step() {
        let pool = synthetic_clmm(
            -30,
            1_000_000_000_000_000_000u128,
            60,
            (-600, 600),
            &[],
        );
        let delta = 1_000u128;
        let result = clmm_swap_manager(false, true, delta, 3000, 60, &pool).expect("swap ok");

        assert!(result.new_liquidity.eq(&pool.slot0.liquidity));
        assert!(result.new_sqrt_price_x96.gt(&pool.slot0.sqrt_price_x96), "price didn't rise");
        assert_eq!(result.total_amount_in, delta);
    }
}


mod clmm_crossing {
    use super::*;

    // For L=1e18, the X (or Y) needed per 60-tick crossing is ~3e15.
    // delta=1e16 crosses roughly 3 ticks — enough to verify the liquidity_net change
    // at the targeted tick, without exhausting our synthetic tick range.

    #[test]
    fn x_to_y_subtracts_positive_liquidity_net() {
        // Start at tick 30, x_to_y → first boundary at 0.
        // Set liquidity_net at -60 to +1e17 (so crossing it going down should SUBTRACT it).
        let pool = synthetic_clmm(
            30,
            1_000_000_000_000_000_000u128, // 1e18
            60,
            (-600, 600),
            &[(-60, 100_000_000_000_000_000i128)], // +1e17 at -60
        );
        let delta = 10_000_000_000_000_000u128; // 1e16

        let result = clmm_swap_manager(true, true, delta, 3000, 60, &pool).expect("ok");

        // After tick -60: liquidity = 1e18 - 1e17 = 9e17.
        let expected_liquidity = u128_to_u512(900_000_000_000_000_000u128);

        let sqrt_at_minus_60 = sqrt_price_from_tick_index(-60).unwrap();
        assert!(
            result.new_sqrt_price_x96.lt(&sqrt_at_minus_60),
            "swap should have crossed tick -60"
        );
        assert!(
            result.new_liquidity.eq(&expected_liquidity),
            "after crossing positive liquidity_net=+1e17 going x_to_y, liquidity should subtract"
        );
    }

    #[test]
    fn x_to_y_adds_negative_liquidity_net() {
        let pool = synthetic_clmm(
            30,
            1_000_000_000_000_000_000u128,
            60,
            (-600, 600),
            &[(-60, -100_000_000_000_000_000i128)],
        );
        let delta = 10_000_000_000_000_000u128;

        let result = clmm_swap_manager(true, true, delta, 3000, 60, &pool).expect("ok");

        // After crossing tick -60: liquidity = 1e18 - (-1e17) = 1.1e18.
        let expected = u128_to_u512(1_100_000_000_000_000_000u128);
        assert!(result.new_liquidity.eq(&expected), "negative net should add to liquidity in x_to_y");
    }

    #[test]
    fn y_to_x_adds_positive_liquidity_net() {
        let pool = synthetic_clmm(
            -30,
            1_000_000_000_000_000_000u128,
            60,
            (-600, 600),
            &[(60, 100_000_000_000_000_000i128)],
        );
        let delta = 10_000_000_000_000_000u128;

        let result = clmm_swap_manager(false, true, delta, 3000, 60, &pool).expect("ok");

        let expected = u128_to_u512(1_100_000_000_000_000_000u128);
        assert!(result.new_liquidity.eq(&expected), "positive net should add to liquidity in y_to_x");
    }

    #[test]
    fn y_to_x_subtracts_negative_liquidity_net() {
        let pool = synthetic_clmm(
            -30,
            1_000_000_000_000_000_000u128,
            60,
            (-600, 600),
            &[(60, -100_000_000_000_000_000i128)],
        );
        let delta = 10_000_000_000_000_000u128;

        let result = clmm_swap_manager(false, true, delta, 3000, 60, &pool).expect("ok");

        let expected = u128_to_u512(900_000_000_000_000_000u128);
        assert!(result.new_liquidity.eq(&expected), "negative net should subtract in y_to_x");
    }

    #[test]
    fn boundary_at_current_tick_still_applies_liquidity_net() {
        // tick_current=0 exactly on a spacing multiple. First boundary = 0 (current).
        // First iter is no-op but still crosses tick 0, applying its liquidity_net.
        let pool = synthetic_clmm(
            0,
            1_000_000_000_000_000_000u128,
            60,
            (-600, 600),
            &[(0, 50_000_000_000_000_000i128)], // 5e16 at the current tick
        );

        let result = clmm_swap_manager(true, true, 1_000_000u128, 3000, 60, &pool).expect("ok");

        // After crossing tick 0 (immediately, since boundary == current):
        // liquidity = 1e18 - 5e16 = 9.5e17.
        // Then small swap continues with this liquidity (final liquidity stays 9.5e17).
        let expected = u128_to_u512(950_000_000_000_000_000u128);
        assert!(
            result.new_liquidity.eq(&expected),
            "boundary at current_tick should still cross and apply liquidity_net"
        );
        // Should have small price movement.
        assert!(result.new_sqrt_price_x96.lt(&pool.slot0.sqrt_price_x96));
    }
}


mod clmm_manual_drive {
    use super::*;

    fn assert_result_eq(a: &DynamicUniClmmResult, b: &DynamicUniClmmResult, ctx: &str) {
        assert_eq!(a.total_amount_in, b.total_amount_in, "{ctx}: total_amount_in mismatch");
        assert_eq!(a.total_amount_out, b.total_amount_out, "{ctx}: total_amount_out mismatch");
        assert_eq!(a.total_fee_amount, b.total_fee_amount, "{ctx}: total_fee_amount mismatch");
        assert!(a.new_liquidity.eq(&b.new_liquidity), "{ctx}: new_liquidity mismatch");
        assert!(a.new_sqrt_price_x96.eq(&b.new_sqrt_price_x96), "{ctx}: new_sqrt_price mismatch");
    }

    #[test]
    fn matches_swap_manager_synthetic() {
        let pools = vec![
            ("small", synthetic_clmm(0, 1_000_000_000_000_000_000u128, 60, (-600, 600), &[(60, 1_000_000_000_000_000i128), (-60, -1_000_000_000_000_000i128)])),
            ("mid", synthetic_clmm(30, 100_000_000_000_000_000_000u128, 60, (-1200, 1200), &[(120, -5_000_000_000_000_000_000i128), (-120, 5_000_000_000_000_000_000i128)])),
            ("large", synthetic_clmm(-15, 1_000_000_000_000_000_000_000u128, 60, (-300, 300), &[])),
        ];

        for (name, pool) in &pools {
            for x_to_y in [true, false] {
                for exact_in in [true, false] {
                    for &delta in &[1_000u128, 1_000_000u128, 1_000_000_000u128, 100_000_000_000_000u128] {
                        for &fee_rate in &[0u32, 500, 3000] {
                            let m = clmm_swap_manager(x_to_y, exact_in, delta, fee_rate, 60, pool);
                            let h = manual_drive_clmm(x_to_y, exact_in, delta, fee_rate, 60, pool);
                            let ctx = format!("{name} x={x_to_y} in={exact_in} delta={delta} fee={fee_rate}");

                            match (m, h) {
                                (Ok(mr), Ok(hr)) => assert_result_eq(&mr, &hr, &ctx),
                                (Err(_), Err(_)) => {} // both errored — that's consistent
                                (Ok(mr), Err(e)) => panic!("{ctx}: manager Ok({mr:?}) but hand Err({e:?})"),
                                (Err(e), Ok(hr)) => panic!("{ctx}: manager Err({e:?}) but hand Ok({hr:?})"),
                            }
                        }
                    }
                }
            }
        }
    }

    #[test]
    fn matches_swap_manager_real_pools() {
        let pool = redis_pool();
        let slots = load_v3_slots(&pool);
        let ticks = load_v3_ticks(&pool);

        let mut tested: usize = 0;
        for (addr, slot0) in slots.iter().take(30) {
            if slot0.liquidity.is_zero() {
                continue;
            }
            let pool_ticks = match ticks.get(addr) {
                Some(t) => t,
                None => continue,
            };
            let tick_spacing = match infer_tick_spacing(pool_ticks) {
                Some(s) => s,
                None => continue,
            };

            let uni_pool = UniswapClmm {
                slot0: *slot0,
                tick: pool_ticks.clone(),
            };

            for x_to_y in [true, false] {
                for &delta in &[1_000u128, 1_000_000_000u128] {
                    let m = clmm_swap_manager(x_to_y, true, delta, 3000, tick_spacing, &uni_pool);
                    let h = manual_drive_clmm(x_to_y, true, delta, 3000, tick_spacing, &uni_pool);

                    match (m, h) {
                        (Ok(mr), Ok(hr)) => assert_result_eq(&mr, &hr, &format!("{addr} x={x_to_y} delta={delta}")),
                        (Err(_), Err(_)) => {}
                        (m_res, h_res) => panic!("{addr}: manager vs hand Ok/Err mismatch: {m_res:?} vs {h_res:?}"),
                    }
                }
            }
            tested += 1;
        }
        assert!(tested > 0, "no real V3 pools were exercised");
        println!("manual_drive: tested {tested} real V3 pools");
    }
}


mod clmm_real_pools_sweep {
    use super::*;

    #[test]
    fn invariants_across_pools() {
        let pool = redis_pool();
        let slots = load_v3_slots(&pool);
        let ticks = load_v3_ticks(&pool);

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
            let tick_spacing = match infer_tick_spacing(pool_ticks) {
                Some(s) => s,
                None => continue,
            };

            let uni_pool = UniswapClmm {
                slot0: *slot0,
                tick: pool_ticks.clone(),
            };

            for x_to_y in [true, false] {
                for &delta in &[1_000u128, 1_000_000u128, 1_000_000_000u128] {
                    for &exact_in in &[true, false] {
                        let r = clmm_swap_manager(x_to_y, exact_in, delta, 3000, tick_spacing, &uni_pool);
                        match r {
                            Ok(result) => {
                                ok_count += 1;
                                if let Err(msg) = check_invariants(&uni_pool, &result, x_to_y, exact_in, delta) {
                                    failures.push(format!("{addr} x_to_y={x_to_y} delta={delta} exact_in={exact_in}: {msg}"));
                                }
                            }
                            Err(_) => err_count += 1,
                        }
                    }
                }
            }
        }

        println!("clmm sweep: ok={ok_count}, err={err_count}, failures={}", failures.len());
        if !failures.is_empty() {
            let preview = failures.iter().take(20).cloned().collect::<Vec<_>>().join("\n");
            panic!("{} invariant failures:\n{}", failures.len(), preview);
        }
    }

    fn check_invariants(
        pool: &UniswapClmm,
        r: &DynamicUniClmmResult,
        x_to_y: bool,
        exact_in: bool,
        delta: u128,
    ) -> Result<(), String> {
        // direction
        if x_to_y && !r.new_sqrt_price_x96.lte(&pool.slot0.sqrt_price_x96) {
            return Err("x_to_y but new > old sqrt".into());
        }
        if !x_to_y && !r.new_sqrt_price_x96.gte(&pool.slot0.sqrt_price_x96) {
            return Err("y_to_x but new < old sqrt".into());
        }
        // range
        if !MIN_SQRT_RATIO.lte(&r.new_sqrt_price_x96) {
            return Err("new < MIN_SQRT_RATIO".into());
        }
        if !r.new_sqrt_price_x96.lt(&MAX_SQRT_RATIO) {
            return Err("new >= MAX_SQRT_RATIO".into());
        }
        // aggregation bounds
        if exact_in && r.total_amount_in > delta {
            return Err(format!("exact_in: total_in {} > delta {}", r.total_amount_in, delta));
        }
        if !exact_in && r.total_amount_out < delta {
            return Err(format!("exact_out: total_out {} < delta {}", r.total_amount_out, delta));
        }
        // fee proportionality (exact_in only — gross = net * 1e6 / (1e6 - fee))
        if exact_in {
            let net_in = r.total_amount_in.checked_sub(r.total_fee_amount)
                .ok_or_else(|| format!("fee {} > total_in {}", r.total_fee_amount, r.total_amount_in))?;
            // gross ≈ net * 1e6 / (1e6 - fee_rate). Allow small per-step rounding (a few hundred wei tolerance for thousands of steps).
            let fee_rate = 3000u128;
            let expected_gross_lo = net_in * 1_000_000 / (1_000_000 - fee_rate);
            let expected_gross_hi = expected_gross_lo + r.total_amount_in / 1_000 + 10;
            if r.total_amount_in < net_in || r.total_amount_in > expected_gross_hi {
                return Err(format!(
                    "fee proportion off: total_in={}, net_in={}, expected_gross in [{}, {}]",
                    r.total_amount_in, net_in, expected_gross_lo, expected_gross_hi
                ));
            }
        }
        Ok(())
    }
}


mod clmm_edge_cases {
    use super::*;

    #[test]
    fn delta_zero_no_movement() {
        let pool = synthetic_clmm(30, 1_000_000_000_000_000_000u128, 60, (-600, 600), &[]);
        let result = clmm_swap_manager(true, true, 0u128, 3000, 60, &pool).expect("ok");
        assert_eq!(result.total_amount_in, 0);
        assert_eq!(result.total_amount_out, 0);
        assert_eq!(result.total_fee_amount, 0);
        assert!(result.new_liquidity.eq(&pool.slot0.liquidity));
        assert!(result.new_sqrt_price_x96.eq(&pool.slot0.sqrt_price_x96));
    }

    #[test]
    fn empty_tick_map_errors_at_first_crossing() {
        let mut pool = synthetic_clmm(30, 1_000_000_000_000_000_000u128, 60, (-600, 600), &[]);
        pool.tick.clear(); // empty tick map → first boundary lookup returns None.

        // Use a large enough delta to force a boundary crossing attempt.
        let result = clmm_swap_manager(true, true, 1_000_000_000_000_000_000u128, 3000, 60, &pool);
        assert!(
            matches!(result, Err(SoulManagerError::RunOutOfLiquidity)),
            "expected RunOutOfLiquidity on empty tick map, got {result:?}"
        );
    }

    #[test]
    fn fee_zero_preserves_aggregation() {
        // With fee=0, exact_in partial step: total_amount_in == delta exactly.
        let pool = synthetic_clmm(30, 1_000_000_000_000_000_000u128, 60, (-600, 600), &[]);
        let delta = 1_000u128;
        let r = clmm_swap_manager(true, true, delta, 0, 60, &pool).expect("ok");
        assert_eq!(r.total_fee_amount, 0);
        assert_eq!(r.total_amount_in, delta);
    }

    #[test]
    fn liquidity_underflow_at_crossing_errors_cleanly() {
        // initial_tick=0 means first boundary == current_tick, so the FIRST iteration
        // immediately crosses tick 0 (no-op swap math, then liquidity update).
        // x_to_y subtracts liquidity_net at tick 0 (+2e18) from L=1e18 → underflow.
        let pool = synthetic_clmm(
            0,
            1_000_000_000_000_000_000u128,
            60,
            (-600, 600),
            &[(0, 2_000_000_000_000_000_000i128)],
        );
        let result = clmm_swap_manager(true, true, 1_000u128, 3000, 60, &pool);
        assert!(
            matches!(
                result,
                Err(SoulManagerError::MathError(SoulMathError::SubUnderflow))
            ),
            "expected SubUnderflow, got {result:?}"
        );
    }

    #[test]
    fn huge_amount_consumes_all_or_errors() {
        // delta=u128::MAX. Either traverses many ticks until empty map / MIN_TICK error,
        // or completes (unlikely with this magnitude). Just verify no panic.
        let pool = synthetic_clmm(30, 1_000_000_000_000_000_000u128, 60, (-600, 600), &[]);
        let _ = clmm_swap_manager(true, true, u128::MAX, 3000, 60, &pool);
    }
}


// ====================== AMM manager tests ======================

mod amm_four_cells {
    use super::*;
    use rusted_soul_dex::math::uniswap::amm::calculate_swap as amm_calculate_swap;

    fn run_case(x_to_y: bool, exact_in: bool) {
        let r0 = 1_000_000_000_000_000_000u128;
        let r1 = 1_000_000_000_000_000_000u128;
        let pool = synthetic_amm(r0, r1);
        let fee = 3000u32;
        let delta = 10_000_000_000u128;

        let m = amm_swap_manager(x_to_y, exact_in, delta, fee, &pool).expect("manager ok");
        let s = amm_calculate_swap(r0, r1, delta, fee, x_to_y, exact_in).expect("calc ok");

        // total_amount_in should equal gross from calculate_swap
        let gross = s.amount_in + s.fee_amount;
        assert_eq!(m.total_amount_in, gross, "total_in should be gross");
        assert_eq!(m.total_amount_out, s.amount_out, "total_out mismatch");
        assert_eq!(m.total_fee_amount, s.fee_amount, "fee mismatch");

        // Reserve updates: input side grows by gross, output side shrinks by amount_out.
        if x_to_y {
            assert_eq!(m.new_x_reserves, r0 + gross, "x_to_y: x reserves should grow by gross");
            assert_eq!(m.new_y_reserves, r1 - s.amount_out, "x_to_y: y reserves should shrink");
        } else {
            assert_eq!(m.new_x_reserves, r0 - s.amount_out, "y_to_x: x reserves should shrink");
            assert_eq!(m.new_y_reserves, r1 + gross, "y_to_x: y reserves should grow by gross");
        }
    }

    #[test]
    fn x_to_y_exact_in() { run_case(true, true); }
    #[test]
    fn x_to_y_exact_out() { run_case(true, false); }
    #[test]
    fn y_to_x_exact_in() { run_case(false, true); }
    #[test]
    fn y_to_x_exact_out() { run_case(false, false); }
}


mod amm_k_invariant {
    use super::*;

    fn k(x: u128, y: u128) -> U256 {
        U256::new(0, x).mul(&U256::new(0, y)).unwrap()
    }

    #[test]
    fn fee_zero_preserves_k_within_rounding() {
        let pool = synthetic_amm(1_000_000_000_000_000_000u128, 1_000_000_000_000_000_000u128);
        let k_old = k(pool.reserve0, pool.reserve1);

        for &delta in &[1_000u128, 1_000_000u128, 1_000_000_000u128, 1_000_000_000_000u128] {
            for x_to_y in [true, false] {
                for exact_in in [true, false] {
                    let m = amm_swap_manager(x_to_y, exact_in, delta, 0, &pool).expect("ok");
                    let k_new = k(m.new_x_reserves, m.new_y_reserves);
                    assert!(
                        k_new.gte(&k_old),
                        "fee=0: k_new should be >= k_old (delta={delta}, x_to_y={x_to_y}, exact_in={exact_in})"
                    );
                }
            }
        }
    }

    #[test]
    fn nonzero_fee_strictly_grows_k() {
        let pool = synthetic_amm(1_000_000_000_000_000_000u128, 1_000_000_000_000_000_000u128);
        let k_old = k(pool.reserve0, pool.reserve1);

        for &fee in &[100u32, 500, 3000, 10000] {
            for &delta in &[10_000_000_000u128, 100_000_000_000u128] {
                for x_to_y in [true, false] {
                    for exact_in in [true, false] {
                        let m = amm_swap_manager(x_to_y, exact_in, delta, fee, &pool).expect("ok");
                        let k_new = k(m.new_x_reserves, m.new_y_reserves);
                        assert!(
                            k_new.gt(&k_old),
                            "fee={fee}: k_new should be strictly > k_old (delta={delta})"
                        );
                    }
                }
            }
        }
    }
}


mod amm_real_pools_sweep {
    use super::*;

    fn k(x: u128, y: u128) -> U256 {
        U256::new(0, x).mul(&U256::new(0, y)).unwrap()
    }

    #[test]
    fn invariants_across_v2_pools() {
        let pool = redis_pool();
        let pools = load_v2_pools(&pool);
        println!("Loaded {} V2 pools", pools.len());

        let mut ok_count: usize = 0;
        let mut err_count: usize = 0;
        let mut failures: Vec<String> = Vec::new();

        for (addr, p) in &pools {
            if p.reserve0 == 0 || p.reserve1 == 0 {
                continue;
            }

            let k_old = k(p.reserve0, p.reserve1);

            for x_to_y in [true, false] {
                for &delta in &[1_000u128, 1_000_000u128, 1_000_000_000u128] {
                    for exact_in in [true, false] {
                        // Skip exact_out deltas larger than the output-side reserve.
                        if !exact_in {
                            let target_reserve = if x_to_y { p.reserve1 } else { p.reserve0 };
                            if delta >= target_reserve {
                                continue;
                            }
                        }
                        let r = amm_swap_manager(x_to_y, exact_in, delta, 3000, p);
                        match r {
                            Ok(m) => {
                                ok_count += 1;
                                let k_new = k(m.new_x_reserves, m.new_y_reserves);
                                if !k_new.gte(&k_old) {
                                    failures.push(format!("{addr} x_to_y={x_to_y} delta={delta} exact_in={exact_in}: k_new < k_old"));
                                }
                                // Direction
                                if x_to_y {
                                    if !(m.new_x_reserves >= p.reserve0 && m.new_y_reserves <= p.reserve1) {
                                        failures.push(format!("{addr}: x_to_y direction wrong"));
                                    }
                                } else {
                                    if !(m.new_y_reserves >= p.reserve1 && m.new_x_reserves <= p.reserve0) {
                                        failures.push(format!("{addr}: y_to_x direction wrong"));
                                    }
                                }
                            }
                            Err(_) => err_count += 1,
                        }
                    }
                }
            }
        }

        println!("v2 sweep: ok={ok_count}, err={err_count}, failures={}", failures.len());
        if !failures.is_empty() {
            let preview = failures.iter().take(20).cloned().collect::<Vec<_>>().join("\n");
            panic!("{} v2 invariant failures:\n{}", failures.len(), preview);
        }
    }
}


mod amm_round_trip {
    use super::*;

    #[test]
    fn fee_zero_round_trip_recovers() {
        let pool = synthetic_amm(1_000_000_000_000_000_000u128, 1_000_000_000_000_000_000u128);
        let initial_x = 1_000_000_000u128;

        let r1 = amm_swap_manager(true, true, initial_x, 0, &pool).expect("ok");
        let mid = synthetic_amm(r1.new_x_reserves, r1.new_y_reserves);
        let received_y = r1.total_amount_out;

        let r2 = amm_swap_manager(false, true, received_y, 0, &mid).expect("ok");
        let recovered_x = r2.total_amount_out;

        let loss = initial_x.saturating_sub(recovered_x);
        assert!(loss <= 2, "fee=0 round trip should recover within 2 wei, lost {loss}");
    }

    #[test]
    fn fee_round_trip_costs_value() {
        let pool = synthetic_amm(1_000_000_000_000_000_000u128, 1_000_000_000_000_000_000u128);
        let initial_x = 1_000_000_000u128;
        let fee = 3000u32; // 0.3%

        let r1 = amm_swap_manager(true, true, initial_x, fee, &pool).expect("ok");
        let mid = synthetic_amm(r1.new_x_reserves, r1.new_y_reserves);
        let received_y = r1.total_amount_out;

        let r2 = amm_swap_manager(false, true, received_y, fee, &mid).expect("ok");
        let recovered_x = r2.total_amount_out;

        let loss = initial_x - recovered_x;
        // 0.3% twice ≈ 0.6%; allow a band of 0.4% to 0.8% to account for amplification at small reserves.
        let min_loss = initial_x * 4 / 1000;
        let max_loss = initial_x * 8 / 1000;
        assert!(
            loss >= min_loss && loss <= max_loss,
            "fee=0.3% round-trip loss {loss} not in [{min_loss}, {max_loss}]"
        );
    }
}


mod amm_edge_cases {
    use super::*;

    #[test]
    fn delta_zero_no_swap() {
        let pool = synthetic_amm(1_000_000_000u128, 1_000_000_000u128);
        let m = amm_swap_manager(true, true, 0, 3000, &pool).expect("ok");
        assert_eq!(m.total_amount_in, 0);
        assert_eq!(m.total_amount_out, 0);
        assert_eq!(m.total_fee_amount, 0);
        assert_eq!(m.new_x_reserves, pool.reserve0);
        assert_eq!(m.new_y_reserves, pool.reserve1);
    }

    #[test]
    fn exact_out_delta_equal_reserve_errors() {
        let pool = synthetic_amm(1_000_000_000u128, 1_000_000_000u128);
        // exact_out asking for the entire Y reserve → calculate_swap errors with InsufficientLiquidity.
        let r = amm_swap_manager(true, false, pool.reserve1, 3000, &pool);
        assert!(
            matches!(r, Err(SoulManagerError::MathError(SoulMathError::InsufficientLiquidity))),
            "expected InsufficientLiquidity, got {r:?}"
        );
    }

    #[test]
    fn fee_high_still_works() {
        let pool = synthetic_amm(1_000_000_000_000u128, 1_000_000_000_000u128);
        let m = amm_swap_manager(true, true, 1_000_000u128, 999_000, &pool).expect("ok");
        // amount_in is the net (after 99.9% fee) — should be tiny, fee_amount should dominate.
        assert!(m.total_fee_amount > m.total_amount_in - m.total_fee_amount);
        assert_eq!(m.total_amount_in, 1_000_000u128);
    }
}
