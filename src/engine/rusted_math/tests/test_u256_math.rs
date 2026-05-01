use rusted_soul_dex::math::u256::{U256, mul_q64x64};

fn u(a: u64, b: u64, c: u64, d: u64) -> U256 {
    U256 { items: [a, b, c, d] }
}

fn build_q64(integer: u64, fraction: u64) -> u128 {
    ((integer as u128) << 64) | (fraction as u128)
}

// ═══════════════════════════════════════════════════════════════
// mul_q64x64
// ═══════════════════════════════════════════════════════════════

mod mul_q64x64 {
    use super::*;

    #[test]
    fn test_mul_pure_integers() {
        let v = build_q64(5, 0);
        let n = build_q64(4, 0);
        let result = mul_q64x64(v, n);
        assert_eq!(result.items[0], 0x0);
        assert_eq!(result.items[1], 0x0);
        assert_eq!(result.items[2], 0x14);
        assert_eq!(result.items[3], 0x0);
    }

    #[test]
    fn test_mul_pure_fractions() {
        let v = build_q64(0, 0x8000000000000000);
        let n = build_q64(0, 0x8000000000000000);
        let result = mul_q64x64(v, n);
        assert_eq!(result.items[0], 0x0);
        assert_eq!(result.items[1], 0x4000000000000000);
        assert_eq!(result.items[2], 0x0);
        assert_eq!(result.items[3], 0x0);
    }

    #[test]
    fn test_mul_mixed_numbers() {
        let v = build_q64(2, 0x8000000000000000);
        let n = build_q64(3, 0x8000000000000000);
        let result = mul_q64x64(v, n);
        assert_eq!(result.items[0], 0x0);
        assert_eq!(result.items[1], 0xC000000000000000);
        assert_eq!(result.items[2], 0x8);
        assert_eq!(result.items[3], 0x0);
    }

    #[test]
    fn test_mul_overflow_carries() {
        let v = build_q64(1, 0xC000000000000000);
        let n = build_q64(1, 0xC000000000000000);
        let result = mul_q64x64(v, n);
        assert_eq!(result.items[0], 0x0);
        assert_eq!(result.items[1], 0x1000000000000000);
        assert_eq!(result.items[2], 0x3);
        assert_eq!(result.items[3], 0x0);
    }

    #[test]
    fn test_mul_complex_decimals() {
        let v = build_q64(3, 0x2000000000000000);
        let n = build_q64(5, 0xA000000000000000);
        let result = mul_q64x64(v, n);
        assert_eq!(result.items[0], 0x0);
        assert_eq!(result.items[1], 0x9400000000000000);
        assert_eq!(result.items[2], 0x11);
        assert_eq!(result.items[3], 0x0);
    }

    #[test]
    fn test_mul_max_integers() {
        let v = build_q64(0xFFFFFFFFFFFFFFFF, 0);
        let n = build_q64(0xFFFFFFFFFFFFFFFF, 0);
        let result = mul_q64x64(v, n);
        assert_eq!(result.items[0], 0x0);
        assert_eq!(result.items[1], 0x0);
        assert_eq!(result.items[2], 0x1);
        assert_eq!(result.items[3], 0xFFFFFFFFFFFFFFFE);
    }

    #[test]
    fn test_mul_max_fractions() {
        let v = build_q64(0, 0xFFFFFFFFFFFFFFFF);
        let n = build_q64(0, 0xFFFFFFFFFFFFFFFF);
        let result = mul_q64x64(v, n);
        assert_eq!(result.items[0], 0x1);
        assert_eq!(result.items[1], 0xFFFFFFFFFFFFFFFE);
        assert_eq!(result.items[2], 0x0);
        assert_eq!(result.items[3], 0x0);
    }

    #[test]
    fn test_mul_extreme_crossover() {
        let v = build_q64(1, 0xFFFFFFFFFFFFFFFF);
        let n = build_q64(1, 0xFFFFFFFFFFFFFFFF);
        let result = mul_q64x64(v, n);
        assert_eq!(result.items[0], 0x1);
        assert_eq!(result.items[1], 0xFFFFFFFFFFFFFFFC);
        assert_eq!(result.items[2], 0x3);
        assert_eq!(result.items[3], 0x0);
    }
}

// ═══════════════════════════════════════════════════════════════
// cmp (eq, gt, gte, lt, lte)
// ═══════════════════════════════════════════════════════════════

mod cmp {
    use super::*;

    // ── eq ───────────────────────────────────────────────────────

    #[test]
    fn test_eq_zeros() {
        assert!(u(0,0,0,0).eq(&u(0,0,0,0)));
    }

    #[test]
    fn test_eq_same_values() {
        assert!(u(1, 2, 3, 4).eq(&u(1, 2, 3, 4)));
    }

    #[test]
    fn test_eq_differ_lsw() {
        assert!(!u(1, 0, 0, 0).eq(&u(2, 0, 0, 0)));
    }

    #[test]
    fn test_eq_differ_msw() {
        assert!(!u(0, 0, 0, 1).eq(&u(0, 0, 0, 2)));
    }

    #[test]
    fn test_eq_max() {
        let max = u(u64::MAX, u64::MAX, u64::MAX, u64::MAX);
        assert!(max.eq(&max));
    }

    // ── gt ───────────────────────────────────────────────────────

    #[test]
    fn test_gt_equal_is_false() {
        assert!(!u(5, 5, 5, 5).gt(&u(5, 5, 5, 5)));
    }

    #[test]
    fn test_gt_msw_decides() {
        assert!(u(0, 0, 0, 2).gt(&u(u64::MAX, u64::MAX, u64::MAX, 1)));
    }

    #[test]
    fn test_gt_lsw_decides() {
        assert!(u(2, 0, 0, 0).gt(&u(1, 0, 0, 0)));
    }

    #[test]
    fn test_gt_middle_word_decides() {
        assert!(u(0, 0, 5, 0).gt(&u(0, 0, 4, 0)));
    }

    #[test]
    fn test_gt_zero_not_gt_zero() {
        assert!(!u(0,0,0,0).gt(&u(0,0,0,0)));
    }

    // ── gte ──────────────────────────────────────────────────────

    #[test]
    fn test_gte_equal() {
        assert!(u(1, 2, 3, 4).gte(&u(1, 2, 3, 4)));
    }

    #[test]
    fn test_gte_greater() {
        assert!(u(0, 0, 0, 1).gte(&u(u64::MAX, 0, 0, 0)));
    }

    #[test]
    fn test_gte_less_is_false() {
        assert!(!u(0, 0, 0, 0).gte(&u(0, 0, 0, 1)));
    }

    // ── lt ───────────────────────────────────────────────────────

    #[test]
    fn test_lt_smaller() {
        assert!(u(1, 0, 0, 0).lt(&u(2, 0, 0, 0)));
    }

    #[test]
    fn test_lt_equal_is_false() {
        assert!(!u(5, 5, 5, 5).lt(&u(5, 5, 5, 5)));
    }

    #[test]
    fn test_lt_msw_decides() {
        assert!(u(u64::MAX, u64::MAX, u64::MAX, 0).lt(&u(0, 0, 0, 1)));
    }

    // ── lte ──────────────────────────────────────────────────────

    #[test]
    fn test_lte_equal() {
        assert!(u(1, 2, 3, 4).lte(&u(1, 2, 3, 4)));
    }

    #[test]
    fn test_lte_less() {
        assert!(u(0, 0, 0, 0).lte(&u(0, 0, 0, 1)));
    }

    #[test]
    fn test_lte_greater_is_false() {
        assert!(!u(0, 0, 0, 1).lte(&u(0, 0, 0, 0)));
    }

    // ── cross-checks ────────────────────────────────────────────

    #[test]
    fn test_gt_and_lt_are_opposites() {
        let a = u(100, 0, 0, 0);
        let b = u(200, 0, 0, 0);
        assert!(a.lt(&b));
        assert!(b.gt(&a));
        assert!(!a.gt(&b));
        assert!(!b.lt(&a));
    }

    #[test]
    fn test_eq_implies_gte_and_lte() {
        let a = u(42, 42, 42, 42);
        assert!(a.eq(&a));
        assert!(a.gte(&a));
        assert!(a.lte(&a));
        assert!(!a.gt(&a));
        assert!(!a.lt(&a));
    }
}

// ═══════════════════════════════════════════════════════════════
// add
// ═══════════════════════════════════════════════════════════════

mod add {
    use super::*;

    // ── basic ───────────────────────────────────────────────────

    #[test]
    fn test_add_zeros() {
        let r = u(0,0,0,0).add(&u(0,0,0,0)).unwrap();
        assert_eq!(r.items, [0, 0, 0, 0]);
    }

    #[test]
    fn test_add_one_plus_one() {
        let r = u(1,0,0,0).add(&u(1,0,0,0)).unwrap();
        assert_eq!(r.items, [2, 0, 0, 0]);
    }

    #[test]
    fn test_add_identity() {
        let a = u(42, 99, 7, 3);
        let r = a.add(&u(0,0,0,0)).unwrap();
        assert_eq!(r.items, a.items);
    }

    // ── carry propagation ───────────────────────────────────────

    #[test]
    fn test_add_carry_lsw_to_word1() {
        let r = u(u64::MAX, 0, 0, 0).add(&u(1, 0, 0, 0)).unwrap();
        assert_eq!(r.items, [0, 1, 0, 0]);
    }

    #[test]
    fn test_add_carry_word1_to_word2() {
        let r = u(0, u64::MAX, 0, 0).add(&u(0, 1, 0, 0)).unwrap();
        assert_eq!(r.items, [0, 0, 1, 0]);
    }

    #[test]
    fn test_add_carry_word2_to_word3() {
        let r = u(0, 0, u64::MAX, 0).add(&u(0, 0, 1, 0)).unwrap();
        assert_eq!(r.items, [0, 0, 0, 1]);
    }

    #[test]
    fn test_add_carry_chain_all_words() {
        let r = u(u64::MAX, u64::MAX, u64::MAX, 0).add(&u(1, 0, 0, 0)).unwrap();
        assert_eq!(r.items, [0, 0, 0, 1]);
    }

    #[test]
    fn test_add_carry_chain_from_both_max() {
        let r = u(u64::MAX, 0, 0, 0).add(&u(u64::MAX, 0, 0, 0)).unwrap();
        assert_eq!(r.items, [u64::MAX - 1, 1, 0, 0]);
    }

    #[test]
    fn test_add_all_words_max_plus_all_words_max_except_msw() {
        let r = u(u64::MAX, u64::MAX, u64::MAX, 0)
            .add(&u(u64::MAX, u64::MAX, u64::MAX, 0)).unwrap();
        assert_eq!(r.items, [u64::MAX - 1, u64::MAX, u64::MAX, 1]);
    }

    // ── multi-word values ───────────────────────────────────────

    #[test]
    fn test_add_multi_word() {
        let r = u(10, 20, 30, 40).add(&u(1, 2, 3, 4)).unwrap();
        assert_eq!(r.items, [11, 22, 33, 44]);
    }

    #[test]
    fn test_add_commutative() {
        let a = u(0xAAAA, 0xBBBB, 0xCCCC, 0xDDDD);
        let b = u(0x1111, 0x2222, 0x3333, 0x4444);
        let ab = a.add(&b).unwrap();
        let ba = b.add(&a).unwrap();
        assert_eq!(ab.items, ba.items);
    }

    // ── boundary ────────────────────────────────────────────────

    #[test]
    fn test_add_max_plus_zero() {
        let max = u(u64::MAX, u64::MAX, u64::MAX, u64::MAX);
        let r = max.add(&u(0,0,0,0)).unwrap();
        assert_eq!(r.items, max.items);
    }

    #[test]
    fn test_add_half_max_plus_half_max() {
        let half = u(u64::MAX, u64::MAX, u64::MAX, u64::MAX >> 1);
        let r = half.add(&half).unwrap();
        assert_eq!(r.items, [u64::MAX - 1, u64::MAX, u64::MAX, u64::MAX]);
    }

    // ── overflow ────────────────────────────────────────────────

    #[test]
    fn test_add_overflow_max_plus_one() {
        let max = u(u64::MAX, u64::MAX, u64::MAX, u64::MAX);
        assert!(max.add(&u(1, 0, 0, 0)).is_err());
    }

    #[test]
    fn test_add_overflow_max_plus_max() {
        let max = u(u64::MAX, u64::MAX, u64::MAX, u64::MAX);
        assert!(max.add(&max).is_err());
    }

    #[test]
    fn test_add_overflow_msw_only() {
        assert!(u(0, 0, 0, u64::MAX).add(&u(0, 0, 0, 1)).is_err());
    }

    #[test]
    fn test_add_overflow_carry_into_msw() {
        assert!(u(0, 0, u64::MAX, u64::MAX).add(&u(0, 0, 1, 0)).is_err());
    }
}

// ═══════════════════════════════════════════════════════════════
// sub
// ═══════════════════════════════════════════════════════════════

mod sub {
    use super::*;

    // ── basic ───────────────────────────────────────────────────

    #[test]
    fn test_sub_zeros() {
        let r = u(0,0,0,0).sub(&u(0,0,0,0)).unwrap();
        assert_eq!(r.items, [0, 0, 0, 0]);
    }

    #[test]
    fn test_sub_self() {
        let a = u(42, 99, 7, 3);
        let r = a.sub(&a).unwrap();
        assert_eq!(r.items, [0, 0, 0, 0]);
    }

    #[test]
    fn test_sub_zero_identity() {
        let a = u(42, 99, 7, 3);
        let r = a.sub(&u(0,0,0,0)).unwrap();
        assert_eq!(r.items, a.items);
    }

    // ── borrow propagation ──────────────────────────────────────

    #[test]
    fn test_sub_borrow_from_word1() {
        let r = u(0, 1, 0, 0).sub(&u(1, 0, 0, 0)).unwrap();
        assert_eq!(r.items, [u64::MAX, 0, 0, 0]);
    }

    #[test]
    fn test_sub_borrow_from_word2() {
        let r = u(0, 0, 1, 0).sub(&u(1, 0, 0, 0)).unwrap();
        assert_eq!(r.items, [u64::MAX, u64::MAX, 0, 0]);
    }

    #[test]
    fn test_sub_borrow_from_word3() {
        let r = u(0, 0, 0, 1).sub(&u(1, 0, 0, 0)).unwrap();
        assert_eq!(r.items, [u64::MAX, u64::MAX, u64::MAX, 0]);
    }

    #[test]
    fn test_sub_borrow_chain_all_words() {
        let r = u(0, 0, 0, 2).sub(&u(1, 0, 0, 0)).unwrap();
        assert_eq!(r.items, [u64::MAX, u64::MAX, u64::MAX, 1]);
    }

    #[test]
    fn test_sub_borrow_when_word_is_zero() {
        let r = u(0, 0, 1, 0).sub(&u(u64::MAX, 0, 0, 0)).unwrap();
        assert_eq!(r.items, [1, u64::MAX, 0, 0]);
    }

    // ── max values ──────────────────────────────────────────────

    #[test]
    fn test_sub_max_minus_max() {
        let max = u(u64::MAX, u64::MAX, u64::MAX, u64::MAX);
        let r = max.sub(&max).unwrap();
        assert_eq!(r.items, [0, 0, 0, 0]);
    }

    #[test]
    fn test_sub_max_minus_one() {
        let max = u(u64::MAX, u64::MAX, u64::MAX, u64::MAX);
        let r = max.sub(&u(1, 0, 0, 0)).unwrap();
        assert_eq!(r.items, [u64::MAX - 1, u64::MAX, u64::MAX, u64::MAX]);
    }

    #[test]
    fn test_sub_max_minus_half() {
        let max = u(u64::MAX, u64::MAX, u64::MAX, u64::MAX);
        let half = u(u64::MAX, u64::MAX, u64::MAX, u64::MAX >> 1);
        let r = max.sub(&half).unwrap();
        assert_eq!(r.items, [0, 0, 0, 0x8000000000000000]);
    }

    // ── add/sub roundtrip ───────────────────────────────────────

    #[test]
    fn test_add_then_sub_roundtrip() {
        let a = u(0xDEAD, 0xBEEF, 0xCAFE, 0);
        let b = u(0x1111, 0x2222, 0x3333, 0);
        let sum = a.add(&b).unwrap();
        let r = sum.sub(&b).unwrap();
        assert_eq!(r.items, a.items);
    }

    #[test]
    fn test_add_then_sub_roundtrip_with_carries() {
        let a = u(u64::MAX, u64::MAX, 0, 0);
        let b = u(u64::MAX, 0, 0, 0);
        let sum = a.add(&b).unwrap();
        let r = sum.sub(&b).unwrap();
        assert_eq!(r.items, a.items);
    }

    // ── underflow errors ────────────────────────────────────────

    #[test]
    fn test_sub_underflow_simple() {
        assert!(u(0,0,0,0).sub(&u(1,0,0,0)).is_err());
    }

    #[test]
    fn test_sub_underflow_by_one() {
        assert!(u(5,0,0,0).sub(&u(6,0,0,0)).is_err());
    }

    #[test]
    fn test_sub_underflow_msw_decides() {
        assert!(u(u64::MAX, u64::MAX, u64::MAX, 0).sub(&u(0, 0, 0, 1)).is_err());
    }

    #[test]
    fn test_sub_no_underflow_at_boundary() {
        let a = u(0, 0, 0, 1);
        assert!(a.sub(&a).is_ok());
    }
}

// ═══════════════════════════════════════════════════════════════
// mul
// ═══════════════════════════════════════════════════════════════

mod mul {
    use super::*;

    // ── zeros and identity ──────────────────────────────────────

    #[test]
    fn test_mul_zero_times_zero() {
        let r = u(0,0,0,0).mul(&u(0,0,0,0)).unwrap();
        assert_eq!(r.items, [0, 0, 0, 0]);
    }

    #[test]
    fn test_mul_max_times_zero() {
        let r = u(u64::MAX, u64::MAX, u64::MAX, u64::MAX).mul(&u(0,0,0,0)).unwrap();
        assert_eq!(r.items, [0, 0, 0, 0]);
    }

    #[test]
    fn test_mul_zero_times_max() {
        let r = u(0,0,0,0).mul(&u(u64::MAX, u64::MAX, u64::MAX, u64::MAX)).unwrap();
        assert_eq!(r.items, [0, 0, 0, 0]);
    }

    #[test]
    fn test_mul_by_one() {
        let a = u(0xDEAD, 0xBEEF, 0xCAFE, 0);
        let r = a.mul(&u(1, 0, 0, 0)).unwrap();
        assert_eq!(r.items, a.items);
    }

    #[test]
    fn test_mul_max_by_one() {
        let max = u(u64::MAX, u64::MAX, u64::MAX, u64::MAX);
        let r = max.mul(&u(1, 0, 0, 0)).unwrap();
        assert_eq!(r.items, max.items);
    }

    // ── small numbers ───────────────────────────────────────────

    #[test]
    fn test_mul_3_times_7() {
        let r = u(3, 0, 0, 0).mul(&u(7, 0, 0, 0)).unwrap();
        assert_eq!(r.items, [21, 0, 0, 0]);
    }

    #[test]
    fn test_mul_1000_times_1000() {
        let r = u(1000, 0, 0, 0).mul(&u(1000, 0, 0, 0)).unwrap();
        assert_eq!(r.items, [1_000_000, 0, 0, 0]);
    }

    #[test]
    fn test_mul_commutative() {
        let a = u(0xAAAA, 0xBBBB, 0, 0);
        let b = u(0x1111, 0x2222, 0, 0);
        assert_eq!(a.mul(&b).unwrap().items, b.mul(&a).unwrap().items);
    }

    // ── single word carry ───────────────────────────────────────

    #[test]
    fn test_mul_max_word_times_2() {
        let r = u(u64::MAX, 0, 0, 0).mul(&u(2, 0, 0, 0)).unwrap();
        assert_eq!(r.items, [u64::MAX - 1, 1, 0, 0]);
    }

    #[test]
    fn test_mul_max_word_times_max_word() {
        let r = u(u64::MAX, 0, 0, 0).mul(&u(u64::MAX, 0, 0, 0)).unwrap();
        assert_eq!(r.items, [1, u64::MAX - 1, 0, 0]);
    }

    // ── multi-word operands ─────────────────────────────────────

    #[test]
    fn test_mul_two_word_times_single() {
        let r = u(1, 1, 0, 0).mul(&u(3, 0, 0, 0)).unwrap();
        assert_eq!(r.items, [3, 3, 0, 0]);
    }

    #[test]
    fn test_mul_two_word_times_two_word() {
        let r = u(1, 1, 0, 0).mul(&u(1, 1, 0, 0)).unwrap();
        assert_eq!(r.items, [1, 2, 1, 0]);
    }

    #[test]
    fn test_mul_2_64_times_2_64() {
        let r = u(0, 1, 0, 0).mul(&u(0, 1, 0, 0)).unwrap();
        assert_eq!(r.items, [0, 0, 1, 0]);
    }

    #[test]
    fn test_mul_2_128_times_2() {
        let r = u(0, 0, 1, 0).mul(&u(2, 0, 0, 0)).unwrap();
        assert_eq!(r.items, [0, 0, 2, 0]);
    }

    // ── heavy carry propagation ─────────────────────────────────

    #[test]
    fn test_mul_u128_max_times_max_word() {
        // (2^128-1) * (2^64-1) = 2^192 - 2^128 - 2^64 + 1
        let r = u(u64::MAX, u64::MAX, 0, 0).mul(&u(u64::MAX, 0, 0, 0)).unwrap();
        assert_eq!(r.items, [1, u64::MAX, u64::MAX - 1, 0]);
    }

    #[test]
    fn test_mul_u128_max_squared() {
        // (2^128-1)^2 = 2^256 - 2^129 + 1
        let r = u(u64::MAX, u64::MAX, 0, 0).mul(&u(u64::MAX, u64::MAX, 0, 0)).unwrap();
        assert_eq!(r.items, [1, 0, u64::MAX - 1, u64::MAX]);
    }

    #[test]
    fn test_mul_three_words_times_single_max() {
        // (2^192-1) * (2^64-1) = 2^256 - 2^192 - 2^64 + 1
        let r = u(u64::MAX, u64::MAX, u64::MAX, 0).mul(&u(u64::MAX, 0, 0, 0)).unwrap();
        assert_eq!(r.items, [1, u64::MAX, u64::MAX, u64::MAX - 1]);
    }

    #[test]
    fn test_mul_three_words_times_2() {
        // 2 * (2^192 - 1) = 2^193 - 2
        let r = u(u64::MAX, u64::MAX, u64::MAX, 0).mul(&u(2, 0, 0, 0)).unwrap();
        assert_eq!(r.items, [u64::MAX - 1, u64::MAX, u64::MAX, 1]);
    }

    // ── multiply by power of 2 matches shift ────────────────────

    #[test]
    fn test_mul_by_2_equals_shift_left_1() {
        let a = u(0xDEAD, 0xBEEF, 0xCAFE, 0);
        let mul_result = a.mul(&u(2, 0, 0, 0)).unwrap();
        let shift_result = a.shift_left(1);
        assert_eq!(mul_result.items, shift_result.items);
    }

    #[test]
    fn test_mul_by_4_equals_shift_left_2() {
        let a = u(0xDEAD, 0xBEEF, 0xCAFE, 0);
        let mul_result = a.mul(&u(4, 0, 0, 0)).unwrap();
        let shift_result = a.shift_left(2);
        assert_eq!(mul_result.items, shift_result.items);
    }

    #[test]
    fn test_mul_by_2_64_equals_shift_word_left() {
        let a = u(42, 99, 7, 0);
        let mul_result = a.mul(&u(0, 1, 0, 0)).unwrap();
        let shift_result = a.shift_left(64);
        assert_eq!(mul_result.items, shift_result.items);
    }

    // ── distributivity: a*(b+c) == a*b + a*c ────────────────────

    #[test]
    fn test_mul_distributive() {
        let a = u(u64::MAX, 0, 0, 0);
        let b = u(100, 0, 0, 0);
        let c = u(200, 0, 0, 0);
        let bc = b.add(&c).unwrap();
        let left = a.mul(&bc).unwrap();
        let right = a.mul(&b).unwrap().add(&a.mul(&c).unwrap()).unwrap();
        assert_eq!(left.items, right.items);
    }

    // ── associativity: (a*b)*c == a*(b*c) ───────────────────────

    #[test]
    fn test_mul_associative() {
        let a = u(1000, 0, 0, 0);
        let b = u(2000, 0, 0, 0);
        let c = u(3000, 0, 0, 0);
        let left = a.mul(&b).unwrap().mul(&c).unwrap();
        let right = a.mul(&b.mul(&c).unwrap()).unwrap();
        assert_eq!(left.items, right.items);
    }

    // ── overflow cases ──────────────────────────────────────────

    #[test]
    fn test_mul_overflow_2_192_times_2_64() {
        assert!(u(0, 0, 0, 1).mul(&u(0, 1, 0, 0)).is_err());
    }

    #[test]
    fn test_mul_overflow_2_128_times_2_128() {
        assert!(u(0, 0, 1, 0).mul(&u(0, 0, 1, 0)).is_err());
    }

    #[test]
    fn test_mul_overflow_max_times_2() {
        let max = u(u64::MAX, u64::MAX, u64::MAX, u64::MAX);
        assert!(max.mul(&u(2, 0, 0, 0)).is_err());
    }

    #[test]
    fn test_mul_overflow_max_times_max() {
        let max = u(u64::MAX, u64::MAX, u64::MAX, u64::MAX);
        assert!(max.mul(&max).is_err());
    }

    #[test]
    fn test_mul_overflow_msw_times_anything() {
        assert!(u(0, 0, 0, 2).mul(&u(0, 0, 0, 1)).is_err());
    }

    #[test]
    fn test_mul_overflow_from_carry_propagation() {
        assert!(u(u64::MAX, u64::MAX, u64::MAX, u64::MAX).mul(&u(1, 1, 0, 0)).is_err());
    }

    // ── verify against mul_q64x64 ──────────────────────────────

    #[test]
    fn test_mul_matches_mul_q64x64() {
        let v: u128 = 5 << 64;
        let n: u128 = 4 << 64;
        let expected = mul_q64x64(v, n);

        let a = U256::new(0, v);
        let b = U256::new(0, n);
        let r = a.mul(&b).unwrap();

        assert_eq!(r.items, [0, 0, 20, 0]);
        assert_eq!(r.items, expected.items);
    }
}

// ═══════════════════════════════════════════════════════════════
// div
// ═══════════════════════════════════════════════════════════════

mod div {
    use super::*;

    /// Helper: assert q * divisor + remainder == dividend, remainder < divisor
    fn assert_div_invariant(dividend: &U256, divisor: &U256) {
        let (q, r) = dividend.div(divisor).unwrap();
        // remainder < divisor
        assert!(
            r.lt(divisor) || r.is_zero(),
            "remainder must be < divisor\n  dividend:  {:?}\n  divisor:   {:?}\n  quotient:  {:?}\n  remainder: {:?}",
            dividend.items, divisor.items, q.items, r.items
        );
        // q * divisor + r == dividend
        let reconstructed = q.mul(divisor).unwrap().add(&r).unwrap();
        assert!(
            reconstructed.eq(dividend),
            "q * divisor + r != dividend\n  dividend:      {:?}\n  divisor:       {:?}\n  quotient:      {:?}\n  remainder:     {:?}\n  reconstructed: {:?}",
            dividend.items, divisor.items, q.items, r.items, reconstructed.items
        );
    }

    // ── divide by zero ──────────────────────────────────────────

    #[test]
    fn test_div_by_zero() {
        assert!(u(1, 0, 0, 0).div(&u(0, 0, 0, 0)).is_err());
    }

    #[test]
    fn test_div_zero_by_zero() {
        assert!(u(0, 0, 0, 0).div(&u(0, 0, 0, 0)).is_err());
    }

    // ── zero dividend ───────────────────────────────────────────

    #[test]
    fn test_div_zero_by_one() {
        let (q, r) = u(0, 0, 0, 0).div(&u(1, 0, 0, 0)).unwrap();
        assert_eq!(q.items, [0, 0, 0, 0]);
        assert_eq!(r.items, [0, 0, 0, 0]);
    }

    #[test]
    fn test_div_zero_by_max() {
        let max = u(u64::MAX, u64::MAX, u64::MAX, u64::MAX);
        let (q, r) = u(0, 0, 0, 0).div(&max).unwrap();
        assert_eq!(q.items, [0, 0, 0, 0]);
        assert_eq!(r.items, [0, 0, 0, 0]);
    }

    // ── identity: x / 1 == x ────────────────────────────────────

    #[test]
    fn test_div_by_one_small() {
        let a = u(42, 0, 0, 0);
        let (q, r) = a.div(&u(1, 0, 0, 0)).unwrap();
        assert_eq!(q.items, a.items);
        assert_eq!(r.items, [0, 0, 0, 0]);
    }

    #[test]
    fn test_div_by_one_multi_word() {
        let a = u(0xDEAD, 0xBEEF, 0xCAFE, 0xBABE);
        let (q, r) = a.div(&u(1, 0, 0, 0)).unwrap();
        assert_eq!(q.items, a.items);
        assert_eq!(r.items, [0, 0, 0, 0]);
    }

    #[test]
    fn test_div_max_by_one() {
        let max = u(u64::MAX, u64::MAX, u64::MAX, u64::MAX);
        let (q, r) = max.div(&u(1, 0, 0, 0)).unwrap();
        assert_eq!(q.items, max.items);
        assert_eq!(r.items, [0, 0, 0, 0]);
    }

    // ── self-division: x / x == 1 ──────────────────────────────

    #[test]
    fn test_div_self_small() {
        let a = u(7, 0, 0, 0);
        let (q, r) = a.div(&a).unwrap();
        assert_eq!(q.items, [1, 0, 0, 0]);
        assert_eq!(r.items, [0, 0, 0, 0]);
    }

    #[test]
    fn test_div_self_multi_word() {
        let a = u(0xDEAD, 0xBEEF, 0xCAFE, 0xBABE);
        let (q, r) = a.div(&a).unwrap();
        assert_eq!(q.items, [1, 0, 0, 0]);
        assert_eq!(r.items, [0, 0, 0, 0]);
    }

    #[test]
    fn test_div_self_max() {
        let max = u(u64::MAX, u64::MAX, u64::MAX, u64::MAX);
        let (q, r) = max.div(&max).unwrap();
        assert_eq!(q.items, [1, 0, 0, 0]);
        assert_eq!(r.items, [0, 0, 0, 0]);
    }

    // ── dividend < divisor → quotient=0, remainder=dividend ────

    #[test]
    fn test_div_smaller_than_divisor() {
        let (q, r) = u(5, 0, 0, 0).div(&u(10, 0, 0, 0)).unwrap();
        assert_eq!(q.items, [0, 0, 0, 0]);
        assert_eq!(r.items, [5, 0, 0, 0]);
    }

    #[test]
    fn test_div_one_less_than_divisor() {
        let a = u(u64::MAX, u64::MAX, u64::MAX, 0);
        let b = u(0, 0, 0, 1);
        let (q, r) = a.div(&b).unwrap();
        assert_eq!(q.items, [0, 0, 0, 0]);
        assert_eq!(r.items, a.items);
    }

    // ── simple single-word divisions ────────────────────────────

    #[test]
    fn test_div_21_by_7() {
        let (q, r) = u(21, 0, 0, 0).div(&u(7, 0, 0, 0)).unwrap();
        assert_eq!(q.items, [3, 0, 0, 0]);
        assert_eq!(r.items, [0, 0, 0, 0]);
    }

    #[test]
    fn test_div_22_by_7() {
        let (q, r) = u(22, 0, 0, 0).div(&u(7, 0, 0, 0)).unwrap();
        assert_eq!(q.items, [3, 0, 0, 0]);
        assert_eq!(r.items, [1, 0, 0, 0]);
    }

    #[test]
    fn test_div_1000000_by_1000() {
        let (q, r) = u(1_000_000, 0, 0, 0).div(&u(1000, 0, 0, 0)).unwrap();
        assert_eq!(q.items, [1000, 0, 0, 0]);
        assert_eq!(r.items, [0, 0, 0, 0]);
    }

    #[test]
    fn test_div_max_word_by_2() {
        // (2^64-1) / 2 = 2^63 - 1 remainder 1
        let (q, r) = u(u64::MAX, 0, 0, 0).div(&u(2, 0, 0, 0)).unwrap();
        assert_eq!(q.items, [u64::MAX >> 1, 0, 0, 0]);
        assert_eq!(r.items, [1, 0, 0, 0]);
    }

    #[test]
    fn test_div_max_word_by_max_word() {
        let (q, r) = u(u64::MAX, 0, 0, 0).div(&u(u64::MAX, 0, 0, 0)).unwrap();
        assert_eq!(q.items, [1, 0, 0, 0]);
        assert_eq!(r.items, [0, 0, 0, 0]);
    }

    // ── powers of two (shift equivalence) ───────────────────────

    #[test]
    fn test_div_by_2_equals_shift_right_1() {
        let a = u(0xDEADBEEF, 0xCAFEBABE, 0x12345678, 0x9ABCDEF0);
        let (q, _) = a.div(&u(2, 0, 0, 0)).unwrap();
        let shifted = a.shift_right(1);
        assert_eq!(q.items, shifted.items);
    }

    #[test]
    fn test_div_by_4_equals_shift_right_2() {
        let a = u(0xDEADBEEF, 0xCAFEBABE, 0x12345678, 0x9ABCDEF0);
        let (q, _) = a.div(&u(4, 0, 0, 0)).unwrap();
        let shifted = a.shift_right(2);
        assert_eq!(q.items, shifted.items);
    }

    #[test]
    fn test_div_by_2_64() {
        // dividing by 2^64 = shifting right by 64
        let a = u(0xAAAA, 0xBBBB, 0xCCCC, 0xDDDD);
        let (q, r) = a.div(&u(0, 1, 0, 0)).unwrap();
        assert_eq!(q.items, [0xBBBB, 0xCCCC, 0xDDDD, 0]);
        assert_eq!(r.items, [0xAAAA, 0, 0, 0]);
    }

    #[test]
    fn test_div_by_2_128() {
        let a = u(0xAAAA, 0xBBBB, 0xCCCC, 0xDDDD);
        let (q, r) = a.div(&u(0, 0, 1, 0)).unwrap();
        assert_eq!(q.items, [0xCCCC, 0xDDDD, 0, 0]);
        assert_eq!(r.items, [0xAAAA, 0xBBBB, 0, 0]);
    }

    #[test]
    fn test_div_by_2_192() {
        let a = u(0xAAAA, 0xBBBB, 0xCCCC, 0xDDDD);
        let (q, r) = a.div(&u(0, 0, 0, 1)).unwrap();
        assert_eq!(q.items, [0xDDDD, 0, 0, 0]);
        assert_eq!(r.items, [0xAAAA, 0xBBBB, 0xCCCC, 0]);
    }

    // ── multi-word dividend, single-word divisor ────────────────

    #[test]
    fn test_div_u128_max_by_max_word() {
        // (2^128-1) / (2^64-1) = 2^64 + 1, remainder 0
        let (q, r) = u(u64::MAX, u64::MAX, 0, 0).div(&u(u64::MAX, 0, 0, 0)).unwrap();
        assert_eq!(q.items, [1, 1, 0, 0]);
        assert_eq!(r.items, [0, 0, 0, 0]);
    }

    #[test]
    fn test_div_u192_minus_1_by_max_word() {
        // (2^192-1) / (2^64-1) = 2^128 + 2^64 + 1
        let a = u(u64::MAX, u64::MAX, u64::MAX, 0);
        let (q, r) = a.div(&u(u64::MAX, 0, 0, 0)).unwrap();
        assert_eq!(q.items, [1, 1, 1, 0]);
        assert_eq!(r.items, [0, 0, 0, 0]);
    }

    #[test]
    fn test_div_u256_max_by_max_word() {
        // (2^256-1) / (2^64-1) = 2^192 + 2^128 + 2^64 + 1
        let max = u(u64::MAX, u64::MAX, u64::MAX, u64::MAX);
        let (q, r) = max.div(&u(u64::MAX, 0, 0, 0)).unwrap();
        assert_eq!(q.items, [1, 1, 1, 1]);
        assert_eq!(r.items, [0, 0, 0, 0]);
    }

    #[test]
    fn test_div_u256_max_by_2() {
        // (2^256-1) / 2 = 2^255 - 1 remainder 1
        let max = u(u64::MAX, u64::MAX, u64::MAX, u64::MAX);
        let (q, r) = max.div(&u(2, 0, 0, 0)).unwrap();
        assert_eq!(q.items, [u64::MAX, u64::MAX, u64::MAX, u64::MAX >> 1]);
        assert_eq!(r.items, [1, 0, 0, 0]);
    }

    #[test]
    fn test_div_u256_max_by_3() {
        // just verify the invariant
        let max = u(u64::MAX, u64::MAX, u64::MAX, u64::MAX);
        assert_div_invariant(&max, &u(3, 0, 0, 0));
    }

    // ── multi-word dividend, multi-word divisor ─────────────────

    #[test]
    fn test_div_u128_max_by_u128_max() {
        let a = u(u64::MAX, u64::MAX, 0, 0);
        let (q, r) = a.div(&a).unwrap();
        assert_eq!(q.items, [1, 0, 0, 0]);
        assert_eq!(r.items, [0, 0, 0, 0]);
    }

    #[test]
    fn test_div_u256_max_by_u128_max() {
        // (2^256-1) / (2^128-1) = 2^128 + 1, remainder 0
        // because (2^128+1)(2^128-1) = 2^256-1
        let max = u(u64::MAX, u64::MAX, u64::MAX, u64::MAX);
        let d = u(u64::MAX, u64::MAX, 0, 0);
        let (q, r) = max.div(&d).unwrap();
        assert_eq!(q.items, [1, 0, 1, 0]);
        assert_eq!(r.items, [0, 0, 0, 0]);
    }

    #[test]
    fn test_div_two_word_by_two_word_with_remainder() {
        // (2^128) / (2^64 + 1) = 2^64 - 1, remainder 1
        // because (2^64+1)(2^64-1) = 2^128 - 1, so 2^128 = (2^64+1)(2^64-1) + 1
        let a = u(0, 0, 1, 0);
        let d = u(1, 1, 0, 0); // 2^64 + 1
        let (q, r) = a.div(&d).unwrap();
        assert_eq!(q.items, [u64::MAX, 0, 0, 0]);
        assert_eq!(r.items, [1, 0, 0, 0]);
    }

    #[test]
    fn test_div_three_word_by_two_word() {
        // (2^192 - 1) / (2^128 - 1)
        // = 2^64 + 1 remainder 2^64
        // because (2^128-1)(2^64+1) = 2^192 + 2^128 - 2^64 - 1
        //   and 2^192 - 1 - (2^192 + 2^128 - 2^64 - 1) = -2^128 + 2^64
        // hmm let me just verify invariant
        let a = u(u64::MAX, u64::MAX, u64::MAX, 0);
        let d = u(u64::MAX, u64::MAX, 0, 0);
        assert_div_invariant(&a, &d);
    }

    #[test]
    fn test_div_four_word_by_three_word() {
        let a = u(u64::MAX, u64::MAX, u64::MAX, u64::MAX);
        let d = u(u64::MAX, u64::MAX, u64::MAX, 0);
        // quotient should be 2^64 + 1, remainder = 2^128
        // verify: (2^192-1)(2^64+1) = 2^256 + 2^192 - 2^64 - 1
        // that overflows, so quotient must be just 2^64
        // verify via invariant
        assert_div_invariant(&a, &d);
    }

    #[test]
    fn test_div_four_word_by_four_word() {
        let a = u(u64::MAX, u64::MAX, u64::MAX, u64::MAX);
        let d = u(0, 0, 0, u64::MAX);
        let (q, r) = a.div(&d).unwrap();
        // (2^256-1) / (u64::MAX * 2^192) = floor(2^256-1 / (2^256-2^192)) = 1
        // remainder = 2^256-1 - (2^256-2^192) = 2^192-1
        assert_eq!(q.items, [1, 0, 0, 0]);
        assert_eq!(r.items, [u64::MAX, u64::MAX, u64::MAX, 0]);
    }

    // ── normalization edge cases ────────────────────────────────
    // These test divisors whose MSB is already set (shift_amount=0)
    // and divisors that need maximum normalization shift (shift_amount=63)

    #[test]
    fn test_div_no_normalization_needed() {
        // divisor top word has MSB set → shift_amount = 0
        let a = u(u64::MAX, u64::MAX, u64::MAX, u64::MAX);
        let d = u(0, 0, 0, 0x8000000000000000);
        let (q, r) = a.div(&d).unwrap();
        assert_eq!(q.items, [1, 0, 0, 0]);
        // remainder = max - 0x8000..0 * 2^192 = 2^255 - 1
        assert_eq!(r.items, [u64::MAX, u64::MAX, u64::MAX, u64::MAX >> 1]);
    }

    #[test]
    fn test_div_max_normalization_shift() {
        // divisor top word = 1 → leading_zeros = 63
        let a = u(u64::MAX, u64::MAX, u64::MAX, u64::MAX);
        let d = u(0, 0, 0, 1); // 2^192
        assert_div_invariant(&a, &d);
    }

    #[test]
    fn test_div_single_word_max_normalization() {
        // divisor = 1 → leading_zeros = 63
        let a = u(u64::MAX, u64::MAX, 0, 0);
        assert_div_invariant(&a, &u(1, 0, 0, 0));
    }

    #[test]
    fn test_div_divisor_just_above_half_word() {
        // divisor top word = 0x8000000000000001 → shift_amount = 0
        let d = u(0x8000000000000001, 0, 0, 0);
        let a = u(u64::MAX, u64::MAX, 0, 0);
        assert_div_invariant(&a, &d);
    }

    #[test]
    fn test_div_divisor_just_below_half_word() {
        // divisor top word = 0x7FFFFFFFFFFFFFFF → shift_amount = 1
        let d = u(0x7FFFFFFFFFFFFFFF, 0, 0, 0);
        let a = u(u64::MAX, u64::MAX, 0, 0);
        assert_div_invariant(&a, &d);
    }

    // ── q_guess overestimate & correction stress tests ─────────
    //
    // Knuth Algorithm D guarantees q̂ ≤ q + 2 when the divisor is
    // normalized (MSB of top word = 1).  The correction loop
    // (`'q_correlation: for j in 0..3`) decrements q_guess until
    // the mul_sub no longer critically underflows.
    //
    // q̂ overestimate is maximized when:
    //  - The divisor top word (mini_divisor) is SMALL (close to 2^63)
    //    → makes the trial division hi_lo(..) / mini_divisor larger
    //  - The divisor lower words are LARGE (close to MAX)
    //    → the ignored portion d0*q is huge, making q̂ overshoot
    //
    // Below we construct dividends via  dividend = q_true * divisor + remainder
    // so the TRUE quotient is known exactly, then analytically verify that
    // q̂ = q_true + 1  (single correction) or  q̂ = q_true + 2  (double).

    // ── single correction: q̂ = q + 1 ───────────────────────────

    #[test]
    fn test_div_single_correction_two_word_divisor() {
        // divisor = [MAX, 0x8000000000000000]  (n=2, shift=0)
        // mini_divisor = 0x8000000000000000
        //
        // q_true = MAX-1.   dividend = (MAX-1) * divisor
        //   word0 = ((MAX-1)*MAX).lo() = 2
        //   word1 = ((MAX-1)*MAX).hi() + ((MAX-1)*0x8..0).lo() = (MAX-2) + 0 = MAX-2
        //   word2 = ((MAX-1)*0x8..0).hi() = 0x7FFFFFFFFFFFFFFF
        //
        // q̂ = hi_lo(0x7FFFFFFFFFFFFFFF, MAX-2) / 0x8000000000000000
        //    = (2^127 - 2^64 + 2^64 - 2 - 1) / 2^63
        //    = (2^127 - 3) / 2^63  =  MAX     (since 2^63*MAX = 2^127-2^63 < 2^127-3)
        //
        // q̂ = MAX,  q_true = MAX-1  →  exactly 1 correction
        let d = u(u64::MAX, 0x8000000000000000, 0, 0);
        let q_true = u(u64::MAX - 1, 0, 0, 0);
        let dividend = q_true.mul(&d).unwrap();
        let (q, r) = dividend.div(&d).unwrap();
        assert_eq!(q.items, q_true.items);
        assert_eq!(r.items, [0, 0, 0, 0]);
    }

    #[test]
    fn test_div_single_correction_two_word_with_remainder() {
        // Same divisor, q_true = MAX-1, remainder = [MAX-1, 0, 0, 0]
        // q̂ is still MAX → 1 correction
        let d = u(u64::MAX, 0x8000000000000000, 0, 0);
        let q_true = u(u64::MAX - 1, 0, 0, 0);
        let rem = u(u64::MAX - 1, 0, 0, 0);
        let dividend = q_true.mul(&d).unwrap().add(&rem).unwrap();
        let (q, r) = dividend.div(&d).unwrap();
        assert_eq!(q.items, q_true.items);
        assert_eq!(r.items, rem.items);
    }

    #[test]
    fn test_div_single_correction_three_word_divisor() {
        // divisor = [MAX, MAX, 0x8000000000000000, 0]  (n=3, shift=0)
        // q_true = MAX-1, remainder = 0
        //
        // q̂ at i=0 overshoots by 1, corrected once
        let d = u(u64::MAX, u64::MAX, 0x8000000000000000, 0);
        let q_true = u(u64::MAX - 1, 0, 0, 0);
        let dividend = q_true.mul(&d).unwrap();
        let (q, r) = dividend.div(&d).unwrap();
        assert_eq!(q.items, q_true.items);
        assert_eq!(r.items, [0, 0, 0, 0]);
    }

    // ── double correction: q̂ = q + 2  (maximum overshoot) ──────

    #[test]
    fn test_div_double_correction_two_word_divisor() {
        // divisor = [MAX, 0x8000000000000000]  (n=2, shift=0)
        // mini_divisor = 0x8000000000000000
        //
        // q_true = MAX-2.   dividend = (MAX-2) * divisor + (MAX-1)
        //   word0 = 1     (3 + MAX-1 overflows, carry to word1)
        //   word1 = 0x7FFFFFFFFFFFFFFD
        //   word2 = 0x7FFFFFFFFFFFFFFF
        //
        // q̂ = hi_lo(0x7FFFFFFFFFFFFFFF, 0x7FFFFFFFFFFFFFFD) / 0x8000000000000000
        //    = (2^127 - 3) / 2^63  =  MAX
        //
        // q̂ = MAX,  q_true = MAX-2  →  exactly 2 corrections!
        // The loop runs j=0 (q=MAX → underflow), j=1 (q=MAX-1 → underflow),
        // j=2 (q=MAX-2 → success).
        let d = u(u64::MAX, 0x8000000000000000, 0, 0);
        let q_true = u(u64::MAX - 2, 0, 0, 0);
        let rem = u(u64::MAX - 1, 0, 0, 0);
        let dividend = q_true.mul(&d).unwrap().add(&rem).unwrap();
        let (q, r) = dividend.div(&d).unwrap();
        assert_eq!(q.items, q_true.items);
        assert_eq!(r.items, rem.items);
    }

    #[test]
    fn test_div_double_correction_two_word_zero_remainder() {
        // Same divisor, q_true = MAX-2, remainder = 0
        let d = u(u64::MAX, 0x8000000000000000, 0, 0);
        let q_true = u(u64::MAX - 2, 0, 0, 0);
        let dividend = q_true.mul(&d).unwrap();
        let (q, r) = dividend.div(&d).unwrap();
        assert_eq!(q.items, q_true.items);
        assert_eq!(r.items, [0, 0, 0, 0]);
    }

    #[test]
    fn test_div_double_correction_three_word_divisor() {
        // divisor = [MAX, MAX, 0x8000000000000000, 0]  (n=3, shift=0)
        // q_true = MAX-2, remainder = 0
        //
        // The trial division ignores both lower words [MAX, MAX],
        // causing a 2-overshoot. Both j=0 and j=1 trigger critical
        // underflow; j=2 succeeds.
        let d = u(u64::MAX, u64::MAX, 0x8000000000000000, 0);
        let q_true = u(u64::MAX - 2, 0, 0, 0);
        let dividend = q_true.mul(&d).unwrap();
        let (q, r) = dividend.div(&d).unwrap();
        assert_eq!(q.items, q_true.items);
        assert_eq!(r.items, [0, 0, 0, 0]);
    }

    #[test]
    fn test_div_double_correction_three_word_with_remainder() {
        let d = u(u64::MAX, u64::MAX, 0x8000000000000000, 0);
        let q_true = u(u64::MAX - 2, 0, 0, 0);
        let rem = u(u64::MAX - 1, u64::MAX - 1, 0, 0);
        let dividend = q_true.mul(&d).unwrap().add(&rem).unwrap();
        let (q, r) = dividend.div(&d).unwrap();
        assert_eq!(q.items, q_true.items);
        assert_eq!(r.items, rem.items);
    }

    // ── multi-digit quotient with corrections at each digit ─────

    #[test]
    fn test_div_correction_at_multiple_quotient_digits() {
        // divisor = [MAX, 0x8000000000000000, 0, 0]  (n=2)
        // div_loop_iterations = 3  →  quotient digits at i=2, i=1, i=0
        //
        // Pick a large multi-word quotient so that corrections can
        // fire at different digit positions.
        let d = u(u64::MAX, 0x8000000000000000, 0, 0);
        // q_true has 2 words → the division computes two quotient digits
        // Each digit may independently trigger correction
        let q_true = u(u64::MAX - 2, u64::MAX - 2, 0, 0);
        let rem = u(u64::MAX - 1, 0, 0, 0);
        let dividend = q_true.mul(&d).unwrap().add(&rem).unwrap();
        let (q, r) = dividend.div(&d).unwrap();
        assert_eq!(q.items, q_true.items);
        assert_eq!(r.items, rem.items);
    }

    #[test]
    fn test_div_correction_at_three_quotient_digits() {
        // U256::MAX / [MAX, 0x8000000000000000, 0, 0] produces a 3-digit
        // quotient. Each digit position may trigger q̂ overestimate.
        let d = u(u64::MAX, 0x8000000000000000, 0, 0);
        let a = u(u64::MAX, u64::MAX, u64::MAX, u64::MAX);
        assert_div_invariant(&a, &d);
    }

    // ── sweep: many q_true values against correction-prone divisors ─

    #[test]
    fn test_div_correction_sweep_two_word() {
        // divisor with minimum normalized top word + MAX low word
        // → maximum overestimate for any quotient digit
        let d = u(u64::MAX, 0x8000000000000000, 0, 0);
        // Test q_true values from MAX-3 to MAX (single digit quotients)
        for q_val in [1u64, 2, 3, u64::MAX - 3, u64::MAX - 2, u64::MAX - 1, u64::MAX] {
            let q_true = u(q_val, 0, 0, 0);
            for r_val in [0u64, 1, u64::MAX - 1] {
                let rem = u(r_val, 0, 0, 0);
                let dividend = q_true.mul(&d).unwrap().add(&rem).unwrap();
                let (q, r) = dividend.div(&d).unwrap();
                assert_eq!(q.items, q_true.items,
                    "q mismatch for q_true={}, r_val={}", q_val, r_val);
                assert_eq!(r.items, rem.items,
                    "r mismatch for q_true={}, r_val={}", q_val, r_val);
            }
        }
    }

    #[test]
    fn test_div_correction_sweep_three_word() {
        let d = u(u64::MAX, u64::MAX, 0x8000000000000000, 0);
        for q_val in [1u64, 2, u64::MAX - 2, u64::MAX - 1, u64::MAX] {
            let q_true = u(q_val, 0, 0, 0);
            let dividend = q_true.mul(&d).unwrap();
            let (q, r) = dividend.div(&d).unwrap();
            assert_eq!(q.items, q_true.items, "q mismatch for q_true={}", q_val);
            assert_eq!(r.items, [0, 0, 0, 0]);
        }
    }

    // ── original correction tests (indirect, via invariant) ─────

    #[test]
    fn test_div_forces_q_correction_two_word_divisor() {
        let a = u(0, u64::MAX, u64::MAX, 0);
        let d = u(1, u64::MAX, 0, 0);
        assert_div_invariant(&a, &d);
    }

    #[test]
    fn test_div_forces_q_correction_near_base() {
        let a = u(u64::MAX, u64::MAX - 1, u64::MAX, 0);
        let d = u(2, u64::MAX, 0, 0);
        assert_div_invariant(&a, &d);
    }

    #[test]
    fn test_div_correction_with_three_word_divisor() {
        let a = u(u64::MAX, u64::MAX, u64::MAX, u64::MAX);
        let d = u(1, 0, u64::MAX, 0);
        assert_div_invariant(&a, &d);
    }

    #[test]
    fn test_div_correction_with_low_words_matter() {
        let a = u(u64::MAX, u64::MAX, u64::MAX, u64::MAX >> 1);
        let d = u(u64::MAX, u64::MAX, u64::MAX, 0);
        assert_div_invariant(&a, &d);
    }

    // ── mul then div roundtrip: (a * b) / b == a ────────────────

    #[test]
    fn test_mul_div_roundtrip_small() {
        let a = u(12345, 0, 0, 0);
        let b = u(67890, 0, 0, 0);
        let product = a.mul(&b).unwrap();
        let (q, r) = product.div(&b).unwrap();
        assert_eq!(q.items, a.items);
        assert_eq!(r.items, [0, 0, 0, 0]);
    }

    #[test]
    fn test_mul_div_roundtrip_max_word() {
        let a = u(u64::MAX, 0, 0, 0);
        let b = u(u64::MAX, 0, 0, 0);
        let product = a.mul(&b).unwrap();
        let (q, r) = product.div(&b).unwrap();
        assert_eq!(q.items, a.items);
        assert_eq!(r.items, [0, 0, 0, 0]);
    }

    #[test]
    fn test_mul_div_roundtrip_two_word() {
        let a = u(u64::MAX, u64::MAX, 0, 0);
        let b = u(u64::MAX, 0, 0, 0);
        let product = a.mul(&b).unwrap(); // fits in 3 words
        let (q, r) = product.div(&b).unwrap();
        assert_eq!(q.items, a.items);
        assert_eq!(r.items, [0, 0, 0, 0]);
    }

    #[test]
    fn test_mul_div_roundtrip_two_by_two() {
        let a = u(u64::MAX, u64::MAX, 0, 0); // 2^128-1
        let b = u(u64::MAX, u64::MAX, 0, 0);
        let product = a.mul(&b).unwrap(); // (2^128-1)^2 fits in U256
        let (q, r) = product.div(&b).unwrap();
        assert_eq!(q.items, a.items);
        assert_eq!(r.items, [0, 0, 0, 0]);
    }

    #[test]
    fn test_mul_div_roundtrip_three_word_times_single() {
        let a = u(u64::MAX, u64::MAX, u64::MAX, 0);
        let b = u(u64::MAX, 0, 0, 0);
        let product = a.mul(&b).unwrap();
        let (q, r) = product.div(&b).unwrap();
        assert_eq!(q.items, a.items);
        assert_eq!(r.items, [0, 0, 0, 0]);
    }

    #[test]
    fn test_mul_div_roundtrip_asymmetric() {
        let a = u(0xDEADBEEF, 0xCAFEBABE, 0, 0);
        let b = u(0x12345678, 0x9ABCDEF0, 0, 0);
        let product = a.mul(&b).unwrap();
        let (q, r) = product.div(&b).unwrap();
        assert_eq!(q.items, a.items);
        assert_eq!(r.items, [0, 0, 0, 0]);
    }

    // ── (a * b + c) / b == a remainder c ────────────────────────

    #[test]
    fn test_mul_add_div_roundtrip() {
        let a = u(0xDEAD, 0xBEEF, 0, 0);
        let b = u(0xCAFE, 0xBABE, 0, 0);
        let c = u(0xCAFE, 0xBABD, 0, 0); // c < b
        let product = a.mul(&b).unwrap().add(&c).unwrap();
        let (q, r) = product.div(&b).unwrap();
        assert_eq!(q.items, a.items);
        assert_eq!(r.items, c.items);
    }

    #[test]
    fn test_mul_add_div_remainder_max() {
        // remainder = divisor - 1
        let a = u(1000, 0, 0, 0);
        let b = u(u64::MAX, 0, 0, 0);
        let c = u(u64::MAX - 1, 0, 0, 0); // b - 1
        let product = a.mul(&b).unwrap().add(&c).unwrap();
        let (q, r) = product.div(&b).unwrap();
        assert_eq!(q.items, a.items);
        assert_eq!(r.items, c.items);
    }

    // ── consecutive divisions ───────────────────────────────────

    #[test]
    fn test_div_halving_chain() {
        // repeatedly divide by 2, compare with shift_right
        let mut val = u(u64::MAX, u64::MAX, u64::MAX, u64::MAX >> 1);
        let two = u(2, 0, 0, 0);
        for _ in 0..10 {
            let (q, _) = val.div(&two).unwrap();
            let shifted = val.shift_right(1);
            assert_eq!(q.items, shifted.items);
            val = q;
        }
    }

    // ── specific bit patterns ───────────────────────────────────

    #[test]
    fn test_div_alternating_bits_by_alternating() {
        let a = u(0xAAAAAAAAAAAAAAAA, 0xAAAAAAAAAAAAAAAA, 0xAAAAAAAAAAAAAAAA, 0);
        let d = u(0x5555555555555555, 0x5555555555555555, 0, 0);
        assert_div_invariant(&a, &d);
    }

    #[test]
    fn test_div_all_ones_by_alternating() {
        let a = u(u64::MAX, u64::MAX, u64::MAX, u64::MAX);
        let d = u(0xAAAAAAAAAAAAAAAA, 0xAAAAAAAAAAAAAAAA, 0, 0);
        assert_div_invariant(&a, &d);
    }

    #[test]
    fn test_div_single_high_bit_dividend() {
        // 2^255 / (2^64-1)
        let a = u(0, 0, 0, 0x8000000000000000);
        let d = u(u64::MAX, 0, 0, 0);
        assert_div_invariant(&a, &d);
    }

    // ── adjacent values ─────────────────────────────────────────

    #[test]
    fn test_div_n_plus_1_by_n() {
        // (n+1)/n == 1 remainder 1 for large n
        let n = u(u64::MAX, u64::MAX, u64::MAX, 0);
        let n_plus_1 = n.add(&u(1, 0, 0, 0)).unwrap();
        let (q, r) = n_plus_1.div(&n).unwrap();
        assert_eq!(q.items, [1, 0, 0, 0]);
        assert_eq!(r.items, [1, 0, 0, 0]);
    }

    #[test]
    fn test_div_2n_minus_1_by_n() {
        // (2n-1)/n == 1 remainder n-1 for large n
        let n = u(u64::MAX, u64::MAX, 0, 0);
        let two_n_minus_1 = n.add(&n).unwrap().sub(&u(1, 0, 0, 0)).unwrap();
        let (q, r) = two_n_minus_1.div(&n).unwrap();
        assert_eq!(q.items, [1, 0, 0, 0]);
        let expected_r = n.sub(&u(1, 0, 0, 0)).unwrap();
        assert_eq!(r.items, expected_r.items);
    }

    // ── large quotient stress ───────────────────────────────────

    #[test]
    fn test_div_u256_max_by_small_primes() {
        let max = u(u64::MAX, u64::MAX, u64::MAX, u64::MAX);
        for p in [3u64, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 97, 127, 251] {
            assert_div_invariant(&max, &u(p, 0, 0, 0));
        }
    }

    #[test]
    fn test_div_u256_max_by_powers_of_two_minus_one() {
        let max = u(u64::MAX, u64::MAX, u64::MAX, u64::MAX);
        for shift in [2u32, 3, 4, 7, 8, 15, 16, 31, 32, 48, 63] {
            let d = u((1u64 << shift) - 1, 0, 0, 0);
            assert_div_invariant(&max, &d);
        }
    }

    #[test]
    fn test_div_large_dividend_by_various_multi_word() {
        let a = u(u64::MAX, u64::MAX, u64::MAX, u64::MAX);
        let divisors = [
            u(1, 1, 0, 0),
            u(u64::MAX, 1, 0, 0),
            u(1, u64::MAX, 0, 0),
            u(u64::MAX, u64::MAX, 1, 0),
            u(1, 0, u64::MAX, 0),
            u(1, 1, 1, 0),
            u(u64::MAX, u64::MAX, u64::MAX, 1),
            u(2, 0, 0, 1),
            u(0x8000000000000000, 0x8000000000000000, 0, 0),
        ];
        for d in divisors {
            assert_div_invariant(&a, &d);
        }
    }

    // ── Knuth's notorious worst-case patterns ───────────────────
    // These are adapted from Knuth TAOCP Vol 2, designed to
    // maximally stress the quotient correction step.

    #[test]
    fn test_div_knuth_d_worst_case_1() {
        // dividend has [MAX, MAX] in top two words of the relevant window,
        // divisor top word = MAX → q̂ = MAX, but low words force correction
        let a = u(0, u64::MAX, u64::MAX, 0);
        let d = u(3, u64::MAX, 0, 0);
        assert_div_invariant(&a, &d);
    }

    #[test]
    fn test_div_knuth_d_worst_case_2() {
        // Two-word divisor: [MAX, MAX-1] → after normalization,
        // the trial quotient should overshoot by exactly 1
        let a = u(u64::MAX - 1, u64::MAX, u64::MAX - 1, 0);
        let d = u(u64::MAX, u64::MAX - 1, 0, 0);
        assert_div_invariant(&a, &d);
    }

    #[test]
    fn test_div_knuth_d_worst_case_3() {
        // Three-word divisor worst case
        let a = u(u64::MAX, u64::MAX, u64::MAX, u64::MAX - 1);
        let d = u(u64::MAX, u64::MAX, u64::MAX, 0);
        assert_div_invariant(&a, &d);
    }

    #[test]
    fn test_div_knuth_d_worst_case_4() {
        // Specifically craft: dividend = [0, 0, MAX, MAX-1, 0] (5 words conceptually)
        // divisor = [1, MAX, 0, 0]
        let a = u(0, 0, u64::MAX, u64::MAX - 1);
        let d = u(1, u64::MAX, 0, 0);
        assert_div_invariant(&a, &d);
    }

    // ── regression-style: specific numeric values ───────────────

    #[test]
    fn test_div_specific_values_1() {
        // 2^192 / (2^64 + 1) via invariant
        let a = u(0, 0, 0, 1);
        let d = u(1, 1, 0, 0);
        assert_div_invariant(&a, &d);
    }

    #[test]
    fn test_div_specific_values_2() {
        // (2^256 - 2) / 2 = 2^255 - 1
        let a = u(u64::MAX - 1, u64::MAX, u64::MAX, u64::MAX);
        let (q, r) = a.div(&u(2, 0, 0, 0)).unwrap();
        assert_eq!(q.items, [u64::MAX, u64::MAX, u64::MAX, u64::MAX >> 1]);
        assert_eq!(r.items, [0, 0, 0, 0]);
    }

    #[test]
    fn test_div_specific_values_3() {
        // (2^128 + 2^64) / (2^64 + 1) = 2^64
        // because (2^64+1) * 2^64 = 2^128 + 2^64
        let a = u(0, 1, 1, 0); // 2^64 + 2^128
        let d = u(1, 1, 0, 0); // 2^64 + 1
        let (q, r) = a.div(&d).unwrap();
        assert_eq!(q.items, [0, 1, 0, 0]); // 2^64
        assert_eq!(r.items, [0, 0, 0, 0]);
    }

    // ── exhaustive small value sweep ────────────────────────────

    #[test]
    fn test_div_sweep_small_dividends_and_divisors() {
        for a_val in 0u64..=50 {
            for d_val in 1u64..=50 {
                let a = u(a_val, 0, 0, 0);
                let d = u(d_val, 0, 0, 0);
                let (q, r) = a.div(&d).unwrap();
                assert_eq!(q.items, [a_val / d_val, 0, 0, 0]);
                assert_eq!(r.items, [a_val % d_val, 0, 0, 0]);
            }
        }
    }

    // ── cross-word boundary stress ──────────────────────────────

    #[test]
    fn test_div_straddles_word_boundary_0_1() {
        // dividend just above 2^64
        let a = u(0, 1, 0, 0); // exactly 2^64
        let d = u(3, 0, 0, 0);
        assert_div_invariant(&a, &d);
    }

    #[test]
    fn test_div_straddles_word_boundary_1_2() {
        let a = u(0, 0, 1, 0); // exactly 2^128
        let d = u(7, 0, 0, 0);
        assert_div_invariant(&a, &d);
    }

    #[test]
    fn test_div_straddles_word_boundary_2_3() {
        let a = u(0, 0, 0, 1); // exactly 2^192
        let d = u(13, 0, 0, 0);
        assert_div_invariant(&a, &d);
    }

    // ── divisor is half the dividend (quotient=2) ───────────────

    #[test]
    fn test_div_exact_double() {
        let d = u(0x1234567890ABCDEF, 0xFEDCBA0987654321, 0, 0);
        let a = d.mul(&u(2, 0, 0, 0)).unwrap();
        let (q, r) = a.div(&d).unwrap();
        assert_eq!(q.items, [2, 0, 0, 0]);
        assert_eq!(r.items, [0, 0, 0, 0]);
    }

    // ── quotient uses all 4 words ───────────────────────────────

    #[test]
    fn test_div_quotient_fills_all_words() {
        // dividend = (2^256-1), divisor = 1 → quotient = 2^256-1
        let max = u(u64::MAX, u64::MAX, u64::MAX, u64::MAX);
        let (q, r) = max.div(&u(1, 0, 0, 0)).unwrap();
        assert_eq!(q.items, max.items);
        assert_eq!(r.items, [0, 0, 0, 0]);
    }

    // ── random-looking hard values ──────────────────────────────

    #[test]
    fn test_div_pseudorandom_batch() {
        // hand-picked values that look random but stress different paths
        let cases: Vec<(U256, U256)> = vec![
            (u(0xA3B5C7D9E1F20346, 0x789ABCDE01234567, 0xFEDCBA9876543210, 0x0123456789ABCDEF),
             u(0xDEADBEEFCAFEBABE, 0x1234567890ABCDEF, 0, 0)),
            (u(u64::MAX, 0, u64::MAX, 0),
             u(0, u64::MAX, 0, 0)),
            (u(1, 0, 0, u64::MAX >> 1),
             u(u64::MAX, u64::MAX, 0, 0)),
            (u(0x8000000000000000, 0x8000000000000000, 0x8000000000000000, 0x8000000000000000),
             u(0x8000000000000001, 0, 0, 0)),
            (u(u64::MAX, u64::MAX, u64::MAX, u64::MAX),
             u(0x123456789ABCDEF0, 0xFEDCBA9876543210, 0xAAAAAAAABBBBBBBB, 0)),
        ];
        for (a, d) in &cases {
            assert_div_invariant(a, d);
        }
    }

    // ── commutativity of mul/div: (a*b)/a == b AND (a*b)/b == a

    #[test]
    fn test_div_mul_commutative_recovery() {
        let a = u(0xFEDCBA9876543210, 0x0123456789ABCDEF, 0, 0);
        let b = u(0xAAAABBBBCCCCDDDD, 0, 0, 0);
        let product = a.mul(&b).unwrap();
        let (q1, r1) = product.div(&a).unwrap();
        assert_eq!(q1.items, b.items);
        assert_eq!(r1.items, [0, 0, 0, 0]);
        let (q2, r2) = product.div(&b).unwrap();
        assert_eq!(q2.items, a.items);
        assert_eq!(r2.items, [0, 0, 0, 0]);
    }

    // ── Euclidean invariant stress: many dividends, one divisor ─

    #[test]
    fn test_div_euclidean_invariant_sweep() {
        let d = u(0xBEEF, 0xCAFE, 0, 0);
        let dividends = [
            u(0, 0, 0, 0),
            u(1, 0, 0, 0),
            u(0xBEEE, 0xCAFE, 0, 0),       // d - 1
            u(0xBEEF, 0xCAFE, 0, 0),       // d
            u(0xBEF0, 0xCAFE, 0, 0),       // d + 1
            u(u64::MAX, u64::MAX, 0, 0),
            u(u64::MAX, u64::MAX, u64::MAX, 0),
            u(u64::MAX, u64::MAX, u64::MAX, u64::MAX),
            u(0, 1, 0, 0),
            u(0, 0, 1, 0),
            u(0, 0, 0, 1),
        ];
        for a in &dividends {
            assert_div_invariant(a, &d);
        }
    }

    // ── division near overflow boundaries ───────────────────────

    #[test]
    fn test_div_max_minus_1_by_max() {
        let max = u(u64::MAX, u64::MAX, u64::MAX, u64::MAX);
        let max_m1 = max.sub(&u(1, 0, 0, 0)).unwrap();
        let (q, r) = max_m1.div(&max).unwrap();
        assert_eq!(q.items, [0, 0, 0, 0]);
        assert_eq!(r.items, max_m1.items);
    }

    #[test]
    fn test_div_max_by_half_max() {
        let max = u(u64::MAX, u64::MAX, u64::MAX, u64::MAX);
        let half = u(0, 0, 0, 0x8000000000000000);
        assert_div_invariant(&max, &half);
    }

    #[test]
    fn test_div_max_by_max_minus_1() {
        let max = u(u64::MAX, u64::MAX, u64::MAX, u64::MAX);
        let max_m1 = max.sub(&u(1, 0, 0, 0)).unwrap();
        let (q, r) = max.div(&max_m1).unwrap();
        assert_eq!(q.items, [1, 0, 0, 0]);
        assert_eq!(r.items, [1, 0, 0, 0]);
    }

    // ── underflow_borrowing > 1 stress tests ────────────────────
    //
    // These target the mul_sub inner loop in div where
    // `underflow_borrowing = underflow1 + underflow2 + underflow3`
    // accumulates to 2 (its proven maximum).
    //
    // The trigger requires, at some iteration k of the inner loop:
    //   1. Large `borrow` from previous iteration (prev divisor_word * q
    //      had a large hi part, e.g. MAX*MAX → hi = MAX-1)
    //   2. The current dividend word (minuend) is 0 or tiny, so
    //      `minuend.overflowing_sub(borrow)` wraps → underflow1 = true,
    //      diff1 wraps to a tiny value (e.g. 2 when borrow = MAX-1)
    //   3. After subtracting the previous underflow_borrowing (≥1),
    //      the residual is still small
    //   4. The current divisor_word * q has a lo part (subtrahend)
    //      that exceeds that tiny residual → underflow3 = true
    //
    // Net result: underflow_borrowing = 1 + 0 + 1 = 2 for that iteration.

    #[test]
    fn test_div_underflow_borrowing_2_three_word_divisor_a() {
        // divisor = [MAX, MAX-1, MAX, 0]:
        //   - No normalization (top word = MAX, leading_zeros = 0)
        //   - n = 3, div_loop_iterations = 2
        //
        // At i=0 with q_guess ≈ MAX, inner loop k=1:
        //   borrow from k=0: (MAX * MAX).hi() = MAX-1
        //   minuend = dividend[1] = 0
        //   diff1 = 0 - (MAX-1) → wraps to 2, underflow1 = true
        //   diff2 = 2 - 1 (underflow_borrowing from k=0) = 1
        //   subtrahend = ((MAX-1) * MAX).lo() = 2
        //   diff3 = 1 - 2 → wraps, underflow3 = true
        //   ⇒ underflow_borrowing = 2
        let a = u(0, 0, u64::MAX - 1, u64::MAX - 1);
        let d = u(u64::MAX, u64::MAX - 1, u64::MAX, 0);
        assert_div_invariant(&a, &d);
    }

    #[test]
    fn test_div_underflow_borrowing_2_three_word_divisor_b() {
        // divisor = [MAX, 1, MAX, 0]:
        //   - No normalization (top word = MAX)
        //   - n = 3
        //
        // At i=0 with q_guess ≈ MAX, inner loop k=1:
        //   borrow from k=0: (MAX * MAX).hi() = MAX-1
        //   minuend = 0
        //   diff1 = 0 - (MAX-1) → wraps to 2, underflow1 = true
        //   diff2 = 2 - 1 = 1
        //   subtrahend = (1 * MAX).lo() = MAX (huge!)
        //   diff3 = 1 - MAX → wraps, underflow3 = true
        //   ⇒ underflow_borrowing = 2
        //
        // Additionally at k=2:
        //   borrow from k=1: (1 * MAX).hi() = 0
        //   underflow_borrowing entering = 2
        //   minuend = dividend[2]
        //   diff1 = dividend[2] - 0 = dividend[2]
        //   diff2 = dividend[2] - 2  ← must handle underflow_borrowing = 2
        let a = u(0, 0, 0, u64::MAX);
        let d = u(u64::MAX, 1, u64::MAX, 0);
        assert_div_invariant(&a, &d);
    }

    #[test]
    fn test_div_underflow_borrowing_2_two_word_divisor() {
        // divisor = [MAX, 0x8000000000000001, 0, 0]:
        //   - No normalization (top word 0x8000000000000001, leading_zeros = 0)
        //   - n = 2
        //
        // At some iteration with q_guess ≈ MAX, inner loop k=1:
        //   borrow from k=0: (MAX * MAX).hi() = MAX-1
        //   minuend = 0
        //   diff1 = 0 - (MAX-1) → wraps to 2, underflow1 = true
        //   diff2 = 2 - 1 = 1
        //   subtrahend = (0x8000000000000001 * MAX).lo() = 0x7FFFFFFFFFFFFFFF
        //   diff3 = 1 - 0x7FFFFFFFFFFFFFFF → wraps, underflow3 = true
        //   ⇒ underflow_borrowing = 2  (hits the final dividend[i+n] check)
        let a = u(0, 0, u64::MAX - 1, u64::MAX - 1);
        let d = u(u64::MAX, 0x8000000000000001, 0, 0);
        assert_div_invariant(&a, &d);
    }

    #[test]
    fn test_div_underflow_borrowing_2_propagates_to_final_check() {
        // Variant where underflow_borrowing = 2 is the value consumed by
        // the final `clone_dividend[i+n].overflowing_sub(underflow_borrowing)`
        // after the inner loop ends.
        //
        // divisor = [MAX, 1, MAX, 0] with dividend = [0, 0, 1, MAX]
        //   k=1 produces underflow_borrowing = 2
        //   k=2 then processes it, and a new underflow_borrowing value
        //   reaches the final subtraction from dividend[i+3].
        let a = u(0, 0, 1, u64::MAX);
        let d = u(u64::MAX, 1, u64::MAX, 0);
        assert_div_invariant(&a, &d);
    }

    #[test]
    fn test_div_underflow_borrowing_2_with_q_correction() {
        // Combine underflow_borrowing = 2 with q_guess correction.
        // divisor = [MAX, MAX-1, MAX, 0], dividend chosen so the
        // first q_guess attempt overestimates and triggers correction,
        // AND the mul_sub hits underflow_borrowing = 2 in both attempts.
        let a = u(u64::MAX, u64::MAX, u64::MAX - 1, u64::MAX - 1);
        let d = u(u64::MAX, u64::MAX - 1, u64::MAX, 0);
        assert_div_invariant(&a, &d);
    }

    #[test]
    fn test_div_underflow_borrowing_2_all_zero_dividend_words() {
        // All dividend words in the subtraction window are 0,
        // maximizing borrow-chain stress across the entire inner loop.
        // divisor = [MAX-1, MAX, MAX, 0] (n=3, no shift)
        //
        // k=0: product = (MAX-1)*q, moderate borrow
        // k=1: dividend word = 0, large borrow from k=0 → underflow1
        //      subtrahend from MAX*q → can trigger underflow3
        // k=2: receives underflow_borrowing ≥ 1, continues chain
        let a = u(0, 0, 0, u64::MAX - 1);
        let d = u(u64::MAX - 1, u64::MAX, u64::MAX, 0);
        assert_div_invariant(&a, &d);
    }

    #[test]
    fn test_div_underflow_borrowing_2_four_word_divisor() {
        // 4-word divisor with normalization, single quotient digit.
        // Even with q_guess ≤ 1, the mul_sub can accumulate
        // underflow_borrowing = 2 if the borrow chain is long.
        let a = u(u64::MAX, u64::MAX, u64::MAX, u64::MAX);
        let d = u(u64::MAX, 1, u64::MAX, 0x8000000000000000);
        assert_div_invariant(&a, &d);
    }

    #[test]
    fn test_div_underflow_borrowing_2_with_normalization_shift() {
        // divisor = [MAX, MAX-1, 1, 0]:
        //   - top word = 1, leading_zeros = 63 → shift_amount = 63
        //   - After normalization the bit pattern changes dramatically,
        //     but the underflow_borrowing mechanism is still exercised
        //     because the normalized divisor inherits large words.
        let a = u(u64::MAX, u64::MAX, u64::MAX, u64::MAX);
        let d = u(u64::MAX, u64::MAX - 1, 1, 0);
        assert_div_invariant(&a, &d);
    }

    #[test]
    fn test_div_underflow_borrowing_2_sweep() {
        // Sweep multiple dividend values against the known
        // underflow_borrowing=2-triggering divisors.
        let divisors = [
            u(u64::MAX, u64::MAX - 1, u64::MAX, 0),
            u(u64::MAX, 1, u64::MAX, 0),
            u(u64::MAX, 0x8000000000000001, 0, 0),
        ];
        let dividends = [
            u(0, 0, u64::MAX - 1, u64::MAX - 1),
            u(0, 0, 0, u64::MAX),
            u(0, 0, 1, u64::MAX),
            u(1, 0, 0, u64::MAX),
            u(0, 1, u64::MAX - 1, u64::MAX - 1),
            u(u64::MAX, u64::MAX, u64::MAX - 1, u64::MAX - 1),
            u(u64::MAX, u64::MAX, u64::MAX, u64::MAX),
            u(0, 0, u64::MAX, u64::MAX >> 1),
            u(0x8000000000000000, 0, 0, u64::MAX),
        ];
        for d in &divisors {
            for a in &dividends {
                if !a.lt(d) {
                    assert_div_invariant(a, d);
                }
            }
        }
    }
}
