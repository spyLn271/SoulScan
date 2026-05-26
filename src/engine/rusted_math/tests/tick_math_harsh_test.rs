use rusted_soul_dex::math::uniswap::clmm::{sqrt_price_from_tick_index, tick_index_from_sqrt_price};
use rusted_soul_dex::math::u512::U512;
use rusted_soul_dex::math::errors::SoulMathError;

pub const MIN_TICK: i32 = -887272;
pub const MAX_TICK: i32 = 887272;
pub const MIN_SQRT_RATIO: U512 = U512 { items: [4295128739, 0, 0, 0, 0, 0, 0, 0] };
pub const MAX_SQRT_RATIO: U512 = U512 { items: [6743328256752651558, 17280870778742802505, 4294805859, 0, 0, 0, 0, 0] };

pub const SLOT0_JSON: &str = include_str!("/Users/sln/PycharmProjects/Live-Like-Quasar/slot0.json");

pub fn u512_from_u64(n: u64) -> U512 {
    U512 { items: [n, 0, 0, 0, 0, 0, 0, 0] }
}

pub fn parse_binary_to_u512(s: &str) -> U512 {
    let mut result = U512 { items: [0; 8] };
    let one = U512 { items: [1, 0, 0, 0, 0, 0, 0, 0] };
    for c in s.chars() {
        result = result.shift_left(1);
        if c == '1' {
            result = result.wrapping_add(&one);
        }
    }
    result
}

pub fn parse_decimal_to_u512(s: &str) -> U512 {
    let mut result = U512 { items: [0; 8] };
    let ten = u512_from_u64(10);
    for c in s.chars() {
        let d = c.to_digit(10).expect("decimal digit") as u64;
        result = result.wrapping_mul(&ten).wrapping_add(&u512_from_u64(d));
    }
    result
}


mod sqrt_price_at_tick_known_values {
    use super::*;

    #[test]
    fn tick_zero_is_two_to_96() {
        let expected = parse_decimal_to_u512("79228162514264337593543950336");
        assert!(sqrt_price_from_tick_index(0).unwrap().eq(&expected));
    }

    #[test]
    fn tick_one_matches_published_value() {
        let expected = parse_decimal_to_u512("79232123823359799118286999568");
        assert!(sqrt_price_from_tick_index(1).unwrap().eq(&expected));
    }

    #[test]
    fn tick_minus_one_matches_published_value() {
        let expected = parse_decimal_to_u512("79224201403219477170569942574");
        assert!(sqrt_price_from_tick_index(-1).unwrap().eq(&expected));
    }

    #[test]
    fn tick_min_is_min_sqrt_ratio() {
        assert!(sqrt_price_from_tick_index(MIN_TICK).unwrap().eq(&MIN_SQRT_RATIO));
    }

    #[test]
    fn tick_max_is_max_sqrt_ratio() {
        assert!(sqrt_price_from_tick_index(MAX_TICK).unwrap().eq(&MAX_SQRT_RATIO));
    }
}


mod sqrt_price_at_tick_boundaries {
    use super::*;

    #[test]
    fn rejects_above_max_tick() {
        for t in [MAX_TICK + 1, MAX_TICK + 100, i32::MAX] {
            assert!(matches!(
                sqrt_price_from_tick_index(t),
                Err(SoulMathError::TickIsNotInRange)
            ), "expected TickIsNotInRange at tick {t}");
        }
    }

    #[test]
    fn rejects_below_min_tick() {
        for t in [MIN_TICK - 1, MIN_TICK - 100, i32::MIN] {
            assert!(matches!(
                sqrt_price_from_tick_index(t),
                Err(SoulMathError::TickIsNotInRange)
            ), "expected TickIsNotInRange at tick {t}");
        }
    }

    #[test]
    fn accepts_exact_boundaries() {
        assert!(sqrt_price_from_tick_index(MIN_TICK).is_ok());
        assert!(sqrt_price_from_tick_index(MAX_TICK).is_ok());
        assert!(sqrt_price_from_tick_index(MIN_TICK + 1).is_ok());
        assert!(sqrt_price_from_tick_index(MAX_TICK - 1).is_ok());
        assert!(sqrt_price_from_tick_index(0).is_ok());
    }
}


mod sqrt_price_at_tick_monotonicity {
    use super::*;

    #[test]
    fn strictly_increasing_around_zero() {
        for t in -100..100 {
            let p = sqrt_price_from_tick_index(t).unwrap();
            let p_next = sqrt_price_from_tick_index(t + 1).unwrap();
            assert!(p.lt(&p_next), "sqrt_price({t}) >= sqrt_price({})", t + 1);
        }
    }

    #[test]
    fn strictly_increasing_at_min_boundary() {
        for t in MIN_TICK..MIN_TICK + 50 {
            let p = sqrt_price_from_tick_index(t).unwrap();
            let p_next = sqrt_price_from_tick_index(t + 1).unwrap();
            assert!(p.lt(&p_next), "monotonicity violated at tick {t} near MIN");
        }
    }

    #[test]
    fn strictly_increasing_at_max_boundary() {
        for t in MAX_TICK - 50..MAX_TICK {
            let p = sqrt_price_from_tick_index(t).unwrap();
            let p_next = sqrt_price_from_tick_index(t + 1).unwrap();
            assert!(p.lt(&p_next), "monotonicity violated at tick {t} near MAX");
        }
    }

    #[test]
    fn strictly_increasing_sampled_across_range() {
        let mut prev = sqrt_price_from_tick_index(MIN_TICK).unwrap();
        for t in (MIN_TICK + 10000..MAX_TICK).step_by(10000) {
            let cur = sqrt_price_from_tick_index(t).unwrap();
            assert!(prev.lt(&cur), "monotonicity violated at tick {t}");
            prev = cur;
        }
    }
}


mod sqrt_price_at_powers_of_two {
    use super::*;

    #[test]
    fn each_positive_power_of_two_succeeds() {
        for k in 0..20u32 {
            let t = 1i32 << k;
            if t > MAX_TICK { break; }
            sqrt_price_from_tick_index(t).expect("positive power of 2 must succeed");
        }
    }

    #[test]
    fn each_negative_power_of_two_succeeds() {
        for k in 0..20u32 {
            let t = -(1i32 << k);
            if t < MIN_TICK { break; }
            sqrt_price_from_tick_index(t).expect("negative power of 2 must succeed");
        }
    }

    #[test]
    fn powers_of_two_round_trip() {
        for k in 0..20u32 {
            let t = 1i32 << k;
            if t >= MAX_TICK { break; }
            let sp_pos = sqrt_price_from_tick_index(t).unwrap();
            let sp_neg = sqrt_price_from_tick_index(-t).unwrap();
            assert_eq!(tick_index_from_sqrt_price(&sp_pos).unwrap(), t, "+2^{k} = {t} failed");
            assert_eq!(tick_index_from_sqrt_price(&sp_neg).unwrap(), -t, "-2^{k} = {} failed", -t);
        }
    }
}


mod tick_at_sqrt_price_known_values {
    use super::*;

    #[test]
    fn min_sqrt_ratio_returns_min_tick() {
        assert_eq!(tick_index_from_sqrt_price(&MIN_SQRT_RATIO).unwrap(), MIN_TICK);
    }

    #[test]
    fn two_to_96_returns_zero() {
        let two_to_96 = parse_decimal_to_u512("79228162514264337593543950336");
        assert_eq!(tick_index_from_sqrt_price(&two_to_96).unwrap(), 0);
    }

    #[test]
    fn sqrt_at_tick_1_returns_1() {
        let sp = parse_decimal_to_u512("79232123823359799118286999568");
        assert_eq!(tick_index_from_sqrt_price(&sp).unwrap(), 1);
    }

    #[test]
    fn sqrt_at_tick_minus_1_returns_minus_1() {
        let sp = parse_decimal_to_u512("79224201403219477170569942574");
        assert_eq!(tick_index_from_sqrt_price(&sp).unwrap(), -1);
    }
}


mod tick_at_sqrt_price_boundaries {
    use super::*;

    #[test]
    fn rejects_max_sqrt_ratio_exactly() {
        // V3 uses sqrtPriceX96 < MAX_SQRT_RATIO (strict). MAX_SQRT_RATIO itself is excluded.
        assert!(matches!(
            tick_index_from_sqrt_price(&MAX_SQRT_RATIO),
            Err(SoulMathError::PriceIsNotInRange)
        ));
    }

    #[test]
    fn accepts_max_sqrt_ratio_minus_one() {
        let one_below = MAX_SQRT_RATIO.wrapping_sub(&u512_from_u64(1));
        let tick = tick_index_from_sqrt_price(&one_below).unwrap();
        assert_eq!(tick, MAX_TICK - 1);
    }

    #[test]
    fn accepts_min_sqrt_ratio_inclusive() {
        // V3 uses sqrtPriceX96 >= MIN_SQRT_RATIO (inclusive). MIN_SQRT_RATIO is accepted.
        assert!(tick_index_from_sqrt_price(&MIN_SQRT_RATIO).is_ok());
    }

    #[test]
    fn rejects_below_min_sqrt_ratio() {
        let one_below = MIN_SQRT_RATIO.wrapping_sub(&u512_from_u64(1));
        assert!(matches!(
            tick_index_from_sqrt_price(&one_below),
            Err(SoulMathError::PriceIsNotInRange)
        ));
        assert!(matches!(
            tick_index_from_sqrt_price(&U512 { items: [0; 8] }),
            Err(SoulMathError::PriceIsNotInRange)
        ));
    }

    #[test]
    fn rejects_max_sqrt_ratio_plus_large() {
        let big = MAX_SQRT_RATIO.wrapping_add(&u512_from_u64(1_000_000));
        assert!(matches!(
            tick_index_from_sqrt_price(&big),
            Err(SoulMathError::PriceIsNotInRange)
        ));
    }
}


mod round_trip_tick_first {
    use super::*;

    #[test]
    fn round_trip_at_min_tick() {
        let sp = sqrt_price_from_tick_index(MIN_TICK).unwrap();
        assert_eq!(tick_index_from_sqrt_price(&sp).unwrap(), MIN_TICK);
    }

    #[test]
    fn round_trip_at_max_tick_minus_one() {
        // MAX_TICK can't round-trip because its sqrt = MAX_SQRT_RATIO is excluded by strict <.
        let sp = sqrt_price_from_tick_index(MAX_TICK - 1).unwrap();
        assert_eq!(tick_index_from_sqrt_price(&sp).unwrap(), MAX_TICK - 1);
    }

    #[test]
    fn round_trip_near_min() {
        for t in MIN_TICK..MIN_TICK + 20 {
            let sp = sqrt_price_from_tick_index(t).unwrap();
            assert_eq!(tick_index_from_sqrt_price(&sp).unwrap(), t, "near-MIN round-trip failed at {t}");
        }
    }

    #[test]
    fn round_trip_near_max() {
        for t in (MAX_TICK - 20)..MAX_TICK {
            let sp = sqrt_price_from_tick_index(t).unwrap();
            assert_eq!(tick_index_from_sqrt_price(&sp).unwrap(), t, "near-MAX round-trip failed at {t}");
        }
    }

    #[test]
    fn round_trip_around_zero() {
        for t in -1000..=1000 {
            let sp = sqrt_price_from_tick_index(t).unwrap();
            assert_eq!(tick_index_from_sqrt_price(&sp).unwrap(), t, "round-trip failed at {t}");
        }
    }

    #[test]
    fn round_trip_at_sampled_range() {
        for t in (MIN_TICK..MAX_TICK).step_by(5000) {
            let sp = sqrt_price_from_tick_index(t).unwrap();
            assert_eq!(tick_index_from_sqrt_price(&sp).unwrap(), t, "sampled round-trip failed at {t}");
        }
    }
}


mod round_trip_sqrt_first {
    use super::*;

    #[test]
    fn sqrt_just_below_next_tick_maps_back() {
        for t in [-887271, -100000, -1000, -100, -10, 0, 10, 100, 1000, 100000, 500000, 887270] {
            let sp_next = sqrt_price_from_tick_index(t + 1).unwrap();
            let just_below = sp_next.wrapping_sub(&u512_from_u64(1));
            assert_eq!(
                tick_index_from_sqrt_price(&just_below).unwrap(),
                t,
                "sqrt_price(t+1) - 1 should map to t = {t}"
            );
        }
    }

    #[test]
    fn sqrt_at_tick_boundary_maps_to_tick() {
        for t in [MIN_TICK, -1000, -1, 0, 1, 1000, 100000, 500000, 887271] {
            let sp = sqrt_price_from_tick_index(t).unwrap();
            assert_eq!(tick_index_from_sqrt_price(&sp).unwrap(), t);
        }
    }

    #[test]
    fn tick_interval_invariant_brute_force() {
        for t in (MIN_TICK..MAX_TICK).step_by(10000) {
            let sp_at_t = sqrt_price_from_tick_index(t).unwrap();
            let sp_at_t_plus_1 = sqrt_price_from_tick_index(t + 1).unwrap();

            assert_eq!(tick_index_from_sqrt_price(&sp_at_t).unwrap(), t, "lower bound at {t}");

            let inside = sp_at_t.wrapping_add(&u512_from_u64(1));
            // inside might equal sp_at_t_plus_1 if interval is exactly 1; guard:
            if inside.lt(&sp_at_t_plus_1) {
                assert_eq!(tick_index_from_sqrt_price(&inside).unwrap(), t, "interior at {t}");
            }

            let just_below = sp_at_t_plus_1.wrapping_sub(&u512_from_u64(1));
            // Only check when t+1 < MAX_TICK (so just_below is a valid input).
            if t + 1 < MAX_TICK {
                assert_eq!(tick_index_from_sqrt_price(&just_below).unwrap(), t, "upper bound at {t}");
            }
        }
    }
}


mod precision_invariants {
    use super::*;

    #[test]
    fn sqrt_price_zero_is_two_to_96_exact() {
        // 2^96 stored in U512: low limb 0, second limb = 2^32 = 1 << 32.
        let two_to_96 = U512 { items: [0, 1u64 << 32, 0, 0, 0, 0, 0, 0] };
        assert!(sqrt_price_from_tick_index(0).unwrap().eq(&two_to_96));
    }

    #[test]
    fn tick_zero_round_trip_via_two_to_96() {
        let two_to_96 = U512 { items: [0, 1u64 << 32, 0, 0, 0, 0, 0, 0] };
        assert_eq!(tick_index_from_sqrt_price(&two_to_96).unwrap(), 0);
    }

    #[test]
    fn min_sqrt_ratio_equals_sqrt_at_min_tick() {
        assert!(sqrt_price_from_tick_index(MIN_TICK).unwrap().eq(&MIN_SQRT_RATIO));
    }

    #[test]
    fn max_sqrt_ratio_equals_sqrt_at_max_tick() {
        assert!(sqrt_price_from_tick_index(MAX_TICK).unwrap().eq(&MAX_SQRT_RATIO));
    }
}


mod onchain_ground_truth {
    use super::*;

    #[test]
    fn all_pools_round_trip() {
        let parsed: serde_json::Value = serde_json::from_str(SLOT0_JSON)
            .expect("parse slot0.json");
        let pool_state = parsed["pool_state"].as_object().expect("pool_state object");

        let mut count_ok: usize = 0;
        let mut failures: Vec<String> = Vec::new();

        for (addr, state) in pool_state {
            let sqrt_bin = state["sqrt_price_x96"].as_str().expect("sqrt_price_x96 string");
            let expected_tick = state["tick_current"].as_i64().expect("tick_current i64") as i32;

            let sp = parse_binary_to_u512(sqrt_bin);
            match tick_index_from_sqrt_price(&sp) {
                Ok(t) if t == expected_tick => count_ok += 1,
                Ok(t) => failures.push(format!("{addr}: expected tick {expected_tick}, got {t}")),
                Err(e) => failures.push(format!("{addr}: errored: {e:?}")),
            }
        }

        let total = pool_state.len();
        assert!(
            failures.is_empty(),
            "{}/{} pools matched. Failures:\n{}",
            count_ok,
            total,
            failures.join("\n")
        );
    }

    #[test]
    fn at_least_one_pool_at_min_tick() {
        let parsed: serde_json::Value = serde_json::from_str(SLOT0_JSON).unwrap();
        let pool_state = parsed["pool_state"].as_object().unwrap();
        let at_min: Vec<&serde_json::Value> = pool_state
            .values()
            .filter(|v| v["tick_current"].as_i64().unwrap() == MIN_TICK as i64)
            .collect();
        assert!(!at_min.is_empty(), "Expected at least one pool at MIN_TICK in slot0.json");
        for state in at_min {
            let sp = parse_binary_to_u512(state["sqrt_price_x96"].as_str().unwrap());
            assert_eq!(tick_index_from_sqrt_price(&sp).unwrap(), MIN_TICK);
        }
    }

    #[test]
    fn pools_span_wide_tick_range() {
        // Sanity check on the test corpus itself: we must cover both extreme negative
        // and high positive ticks to claim broad ground-truth coverage.
        let parsed: serde_json::Value = serde_json::from_str(SLOT0_JSON).unwrap();
        let pool_state = parsed["pool_state"].as_object().unwrap();
        let ticks: Vec<i32> = pool_state.values()
            .map(|v| v["tick_current"].as_i64().unwrap() as i32)
            .collect();
        let min = *ticks.iter().min().unwrap();
        let max = *ticks.iter().max().unwrap();
        assert!(min <= -100_000, "expected on-chain corpus to include very negative ticks, got min = {min}");
        assert!(max >= 100_000, "expected on-chain corpus to include high positive ticks, got max = {max}");
    }
}
