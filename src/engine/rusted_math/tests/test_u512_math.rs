use rusted_soul_dex::math::errors::SoulMathError;
use rusted_soul_dex::math::u512::U512;

mod shifting {
    use super::*;

    // ----- shift_left -----

    #[test]
    fn left_shift_by_zero_is_identity() {
        let a = U512::new(0xDEAD, 0xBEEF, 0xCAFE, 0xBABE);
        let b = a.shift_left(0);
        assert!(a.eq(&b));
    }

    #[test]
    fn left_shift_intra_word() {
        // 0xFF << 4 fits in the lowest word — no carry between words.
        let a = U512::new(0, 0, 0, 0xFF).shift_left(4);
        let expected = U512::new(0, 0, 0, 0xFF0);
        assert!(a.eq(&expected));
    }

    #[test]
    fn left_shift_with_inter_word_carry() {
        // u64::MAX in items[0], shift by 4 → top 4 bits must spill into items[1].
        let a = U512::new(0, 0, 0, u64::MAX as u128).shift_left(4);
        let expected = U512::new(0, 0, 0, (u64::MAX as u128) << 4);
        assert!(a.eq(&expected));
    }

    #[test]
    fn left_shift_one_word() {
        // 64 → ll moves into items[1].
        let a = U512::new(0, 0, 0, 1).shift_left(64);
        let expected = U512::new(0, 0, 0, 1u128 << 64);
        assert!(a.eq(&expected));
    }

    #[test]
    fn left_shift_two_words() {
        // 128 → ll lands in lh.
        let a = U512::new(0, 0, 0, 0xABCD).shift_left(128);
        let expected = U512::new(0, 0, 0xABCD, 0);
        assert!(a.eq(&expected));
    }

    #[test]
    fn left_shift_four_words() {
        // 256 → ll lands in hl.
        let a = U512::new(0, 0, 0, 0xABCD).shift_left(256);
        let expected = U512::new(0, 0xABCD, 0, 0);
        assert!(a.eq(&expected));
    }

    #[test]
    fn left_shift_six_words() {
        // 384 → ll lands in hh.
        let a = U512::new(0, 0, 0, 0xABCD).shift_left(384);
        let expected = U512::new(0xABCD, 0, 0, 0);
        assert!(a.eq(&expected));
    }

    #[test]
    fn left_shift_word_plus_partial() {
        // 68 = 64 + 4 → one word shift, then 4-bit intra-word shift with carry.
        let a = U512::new(0, 0, 0, u64::MAX as u128).shift_left(68);
        // After shift: items[1] = 0xFFFF_FFFF_FFFF_FFF0, items[2] = 0xF.
        let expected = U512::new(0, 0, 0xF, (u64::MAX as u128) << 68);
        assert!(a.eq(&expected));
    }

    #[test]
    fn left_shift_max_valid_sets_top_bit() {
        // 511 → value 1 ends up as the MSB of items[7].
        let a = U512::new(0, 0, 0, 1).shift_left(511);
        let expected = U512::new(1u128 << 127, 0, 0, 0);
        assert!(a.eq(&expected));
    }

    #[test]
    fn left_shift_at_boundary_returns_zero() {
        // shift_amount >= 512 short-circuits to zero.
        let a = U512::new(0xDEAD, 0xBEEF, 0xCAFE, 0xBABE).shift_left(512);
        let zero = U512::new(0, 0, 0, 0);
        assert!(a.eq(&zero));
    }

    #[test]
    fn left_shift_far_overflow_returns_zero() {
        let a = U512::new(0xDEAD, 0xBEEF, 0xCAFE, 0xBABE).shift_left(1024);
        let zero = U512::new(0, 0, 0, 0);
        assert!(a.eq(&zero));
    }

    // ----- shift_right -----

    #[test]
    fn right_shift_by_zero_is_identity() {
        let a = U512::new(0xDEAD, 0xBEEF, 0xCAFE, 0xBABE);
        let b = a.shift_right(0);
        assert!(a.eq(&b));
    }

    #[test]
    fn right_shift_intra_word() {
        let a = U512::new(0, 0, 0, 0xFF0).shift_right(4);
        let expected = U512::new(0, 0, 0, 0xFF);
        assert!(a.eq(&expected));
    }

    #[test]
    fn right_shift_with_inter_word_borrow() {
        // 2^64 (items[1] = 1) shifted right by 4 lands at items[0] = 1 << 60.
        let a = U512::new(0, 0, 0, 1u128 << 64).shift_right(4);
        let expected = U512::new(0, 0, 0, 1u128 << 60);
        assert!(a.eq(&expected));
    }

    #[test]
    fn right_shift_one_word() {
        let a = U512::new(0, 0, 0, 1u128 << 64).shift_right(64);
        let expected = U512::new(0, 0, 0, 1);
        assert!(a.eq(&expected));
    }

    #[test]
    fn right_shift_two_words() {
        let a = U512::new(0, 0, 0xABCD, 0).shift_right(128);
        let expected = U512::new(0, 0, 0, 0xABCD);
        assert!(a.eq(&expected));
    }

    #[test]
    fn right_shift_four_words() {
        let a = U512::new(0, 0xABCD, 0, 0).shift_right(256);
        let expected = U512::new(0, 0, 0, 0xABCD);
        assert!(a.eq(&expected));
    }

    #[test]
    fn right_shift_six_words() {
        let a = U512::new(0xABCD, 0, 0, 0).shift_right(384);
        let expected = U512::new(0, 0, 0, 0xABCD);
        assert!(a.eq(&expected));
    }

    #[test]
    fn right_shift_max_valid_lands_in_lsb() {
        // bit 511 → bit 0.
        let a = U512::new(1u128 << 127, 0, 0, 0).shift_right(511);
        let expected = U512::new(0, 0, 0, 1);
        assert!(a.eq(&expected));
    }

    #[test]
    fn right_shift_at_boundary_returns_zero() {
        let a = U512::new(0xDEAD, 0xBEEF, 0xCAFE, 0xBABE).shift_right(512);
        let zero = U512::new(0, 0, 0, 0);
        assert!(a.eq(&zero));
    }

    #[test]
    fn right_shift_far_overflow_returns_zero() {
        let a = U512::new(0xDEAD, 0xBEEF, 0xCAFE, 0xBABE).shift_right(1024);
        let zero = U512::new(0, 0, 0, 0);
        assert!(a.eq(&zero));
    }

    #[test]
    fn left_then_right_roundtrip() {
        // A value that fits in the bottom 32 bits survives a 200-bit round trip.
        let a = U512::new(0, 0, 0, 0xCAFE_BABE);
        let b = a.shift_left(200).shift_right(200);
        assert!(a.eq(&b));
    }

    // ----- edge cases -----

    #[test]
    fn left_shift_by_one_bit() {
        // Smallest non-zero shift; no inter-word interaction.
        let a = U512::new(0, 0, 0, 1).shift_left(1);
        let expected = U512::new(0, 0, 0, 2);
        assert!(a.eq(&expected));
    }

    #[test]
    fn left_shift_by_sixty_three_bits() {
        // Max intra-word shift. Inner formula uses `U64_RESOLUTION - 63 = 1`,
        // so the top bit of items[0] must carry into items[1].
        let a = U512::new(0, 0, 0, u64::MAX as u128).shift_left(63);
        // items[0] = 1<<63, items[1] = u64::MAX >> 1.
        let expected = U512::new(0, 0, 0, (u64::MAX as u128) << 63);
        assert!(a.eq(&expected));
    }

    #[test]
    fn left_shift_by_sixty_five_bits() {
        // Smallest multi-word + partial: 1 word jump, then 1-bit shift.
        let a = U512::new(0, 0, 0, u64::MAX as u128).shift_left(65);
        // items[1] = u64::MAX << 1, items[2] = u64::MAX >> 63 = 1.
        let expected = U512::new(0, 0, 1, (u64::MAX as u128) << 65);
        assert!(a.eq(&expected));
    }

    #[test]
    fn left_shift_drops_bit_511() {
        // Bit 511 shifted left by 1 falls off the top → zero.
        let a = U512::new(1u128 << 127, 0, 0, 0).shift_left(1);
        let zero = U512::new(0, 0, 0, 0);
        assert!(a.eq(&zero));
    }

    #[test]
    fn left_shift_promotes_bit_510_to_511() {
        // The bit just below the top should land at the top.
        let a = U512::new(1u128 << 126, 0, 0, 0).shift_left(1);
        let expected = U512::new(1u128 << 127, 0, 0, 0);
        assert!(a.eq(&expected));
    }

    #[test]
    fn left_shift_all_ones_clears_only_bit_zero() {
        // U512::MAX << 1: carry cascades through all 8 words. Bit 0 becomes 0,
        // every other bit remains 1 (bit 510 fills the vacated 511 slot).
        let max = U512::new(u128::MAX, u128::MAX, u128::MAX, u128::MAX);
        let a = max.shift_left(1);
        let expected = U512::new(u128::MAX, u128::MAX, u128::MAX, u128::MAX ^ 1);
        assert!(a.eq(&expected));
    }

    #[test]
    fn left_shift_drops_word_when_only_top_word_set() {
        // Bit 448 (items[7] bit 0); items[6] is 0 so nothing fills in.
        // Shifting left by 64 moves the bit to position 512 → dropped → zero.
        let a = U512::new(1u128 << 64, 0, 0, 0).shift_left(64);
        let zero = U512::new(0, 0, 0, 0);
        assert!(a.eq(&zero));
    }

    #[test]
    fn left_shift_zero_stays_zero() {
        let zero = U512::new(0, 0, 0, 0);
        assert!(zero.shift_left(1).eq(&zero));
        assert!(zero.shift_left(64).eq(&zero));
        assert!(zero.shift_left(300).eq(&zero));
        assert!(zero.shift_left(511).eq(&zero));
    }

    #[test]
    fn right_shift_by_one_bit() {
        let a = U512::new(0, 0, 0, 2).shift_right(1);
        let expected = U512::new(0, 0, 0, 1);
        assert!(a.eq(&expected));
    }

    #[test]
    fn right_shift_by_sixty_three_bits() {
        // (u64::MAX << 63) >> 63 == u64::MAX. Spans the items[0]/items[1] boundary,
        // exercising `U64_RESOLUTION - 63 = 1` in the right-shift formula.
        let a = U512::new(0, 0, 0, (u64::MAX as u128) << 63).shift_right(63);
        let expected = U512::new(0, 0, 0, u64::MAX as u128);
        assert!(a.eq(&expected));
    }

    #[test]
    fn right_shift_drops_bit_zero() {
        // Bit 0 shifted right by 1 falls off the bottom → zero.
        let a = U512::new(0, 0, 0, 1).shift_right(1);
        let zero = U512::new(0, 0, 0, 0);
        assert!(a.eq(&zero));
    }

    #[test]
    fn right_shift_demotes_bit_511_to_510() {
        let a = U512::new(1u128 << 127, 0, 0, 0).shift_right(1);
        let expected = U512::new(1u128 << 126, 0, 0, 0);
        assert!(a.eq(&expected));
    }

    #[test]
    fn right_shift_all_ones_clears_only_bit_511() {
        // U512::MAX >> 1: only bit 511 becomes 0.
        let max = U512::new(u128::MAX, u128::MAX, u128::MAX, u128::MAX);
        let a = max.shift_right(1);
        let expected = U512::new(u128::MAX >> 1, u128::MAX, u128::MAX, u128::MAX);
        assert!(a.eq(&expected));
    }

    #[test]
    fn right_shift_drops_word_when_bottom_word_set() {
        // u128::MAX in ll (items[0..2]) shifted right by 128 drops both bottom words.
        let a = U512::new(0, 0, 0, u128::MAX).shift_right(128);
        let zero = U512::new(0, 0, 0, 0);
        assert!(a.eq(&zero));
    }

    #[test]
    fn right_shift_zero_stays_zero() {
        let zero = U512::new(0, 0, 0, 0);
        assert!(zero.shift_right(1).eq(&zero));
        assert!(zero.shift_right(64).eq(&zero));
        assert!(zero.shift_right(300).eq(&zero));
        assert!(zero.shift_right(511).eq(&zero));
    }

    #[test]
    fn right_then_left_roundtrip() {
        // A value with zero bottom 200 bits survives a right→left round trip.
        let a = U512::new(0, 0, 0, 0xCAFE_BABE).shift_left(200);
        let b = a.shift_right(200).shift_left(200);
        assert!(a.eq(&b));
    }
}

mod equality {
    use super::*;

    // ----- eq -----

    #[test]
    fn eq_zero_with_zero() {
        let a = U512::new(0, 0, 0, 0);
        let b = U512::new(0, 0, 0, 0);
        assert!(a.eq(&b));
    }

    #[test]
    fn eq_identical_large_values() {
        let a = U512::new(0xDEAD, 0xBEEF, 0xCAFE, 0xBABE);
        let b = U512::new(0xDEAD, 0xBEEF, 0xCAFE, 0xBABE);
        assert!(a.eq(&b));
    }

    #[test]
    fn eq_differs_in_low_word() {
        let a = U512::new(0, 0, 0, 1);
        let b = U512::new(0, 0, 0, 2);
        assert!(!a.eq(&b));
    }

    #[test]
    fn eq_differs_in_top_word() {
        let a = U512::new(1, 0, 0, 0);
        let b = U512::new(2, 0, 0, 0);
        assert!(!a.eq(&b));
    }

    // ----- gt -----

    #[test]
    fn gt_larger_low_word() {
        let a = U512::new(0, 0, 0, 2);
        let b = U512::new(0, 0, 0, 1);
        assert!(a.gt(&b));
    }

    #[test]
    fn gt_equal_returns_false() {
        let a = U512::new(0, 0, 0, 1);
        let b = U512::new(0, 0, 0, 1);
        assert!(!a.gt(&b));
    }

    #[test]
    fn gt_smaller_returns_false() {
        let a = U512::new(0, 0, 0, 1);
        let b = U512::new(0, 0, 0, 2);
        assert!(!a.gt(&b));
    }

    #[test]
    fn gt_top_word_dominates_lower_words() {
        // a is 2^384; b saturates the lower three components but its hh is 0,
        // so the MSW comparison settles it before lower words matter.
        let a = U512::new(1, 0, 0, 0);
        let b = U512::new(0, u128::MAX, u128::MAX, u128::MAX);
        assert!(a.gt(&b));
    }

    #[test]
    fn gt_walks_words_top_down() {
        // Top-down comparison finds a > b at lh before seeing b's huge ll.
        let a = U512::new(5, 5, 5, 0);
        let b = U512::new(5, 5, 4, u128::MAX);
        assert!(a.gt(&b));
    }

    // ----- gte -----

    #[test]
    fn gte_equal_returns_true() {
        let a = U512::new(0xAA, 0xBB, 0xCC, 0xDD);
        let b = U512::new(0xAA, 0xBB, 0xCC, 0xDD);
        assert!(a.gte(&b));
    }

    #[test]
    fn gte_greater_returns_true() {
        let a = U512::new(0, 0, 0, 2);
        let b = U512::new(0, 0, 0, 1);
        assert!(a.gte(&b));
    }

    #[test]
    fn gte_less_returns_false() {
        let a = U512::new(0, 0, 0, 1);
        let b = U512::new(0, 0, 0, 2);
        assert!(!a.gte(&b));
    }

    // ----- lt -----

    #[test]
    fn lt_smaller_returns_true() {
        let a = U512::new(0, 0, 0, 1);
        let b = U512::new(0, 0, 0, 2);
        assert!(a.lt(&b));
    }

    #[test]
    fn lt_equal_returns_false() {
        let a = U512::new(0, 0, 0, 1);
        let b = U512::new(0, 0, 0, 1);
        assert!(!a.lt(&b));
    }

    #[test]
    fn lt_larger_returns_false() {
        let a = U512::new(0, 0, 0, 2);
        let b = U512::new(0, 0, 0, 1);
        assert!(!a.lt(&b));
    }

    #[test]
    fn lt_top_word_dominates_lower_words() {
        // a saturates 3 lower components but loses on hh.
        let a = U512::new(0, u128::MAX, u128::MAX, u128::MAX);
        let b = U512::new(1, 0, 0, 0);
        assert!(a.lt(&b));
    }

    // ----- lte -----

    #[test]
    fn lte_equal_returns_true() {
        let a = U512::new(0xAA, 0xBB, 0xCC, 0xDD);
        let b = U512::new(0xAA, 0xBB, 0xCC, 0xDD);
        assert!(a.lte(&b));
    }

    #[test]
    fn lte_less_returns_true() {
        let a = U512::new(0, 0, 0, 1);
        let b = U512::new(0, 0, 0, 2);
        assert!(a.lte(&b));
    }

    #[test]
    fn lte_greater_returns_false() {
        let a = U512::new(0, 0, 0, 2);
        let b = U512::new(0, 0, 0, 1);
        assert!(!a.lte(&b));
    }

    // ----- edge cases -----

    #[test]
    fn eq_max_with_max() {
        let a = U512::new(u128::MAX, u128::MAX, u128::MAX, u128::MAX);
        let b = U512::new(u128::MAX, u128::MAX, u128::MAX, u128::MAX);
        assert!(a.eq(&b));
    }

    #[test]
    fn eq_differs_only_in_middle_word() {
        // Same hh and lh; only the hl word diverges.
        let a = U512::new(0, 1, 0xFFFF, 0xFFFF);
        let b = U512::new(0, 2, 0xFFFF, 0xFFFF);
        assert!(!a.eq(&b));
    }

    #[test]
    fn eq_differs_by_one_bit_at_bit_zero() {
        let a = U512::new(0, 0, 0, 0);
        let b = U512::new(0, 0, 0, 1);
        assert!(!a.eq(&b));
    }

    #[test]
    fn eq_differs_by_one_bit_at_bit_511() {
        let a = U512::new(0, 0, 0, 0);
        let b = U512::new(1u128 << 127, 0, 0, 0);
        assert!(!a.eq(&b));
    }

    #[test]
    fn gt_max_vs_max_minus_one() {
        let max = U512::new(u128::MAX, u128::MAX, u128::MAX, u128::MAX);
        let max_minus_one = U512::new(u128::MAX, u128::MAX, u128::MAX, u128::MAX ^ 1);
        assert!(max.gt(&max_minus_one));
        assert!(!max_minus_one.gt(&max));
    }

    #[test]
    fn gt_differs_only_in_hl_word() {
        // hh equal; ll, lh equal; difference is in hl. The walk must reach items[4..6]
        // before deciding.
        let a = U512::new(0, 2, u128::MAX, u128::MAX);
        let b = U512::new(0, 1, u128::MAX, u128::MAX);
        assert!(a.gt(&b));
        assert!(b.lt(&a));
    }

    #[test]
    fn gt_lt_are_antisymmetric() {
        // For any unequal pair, exactly one of gt/lt is true in each direction.
        let small = U512::new(0xAA, 0xBB, 0xCC, 0xDD);
        let big = U512::new(0xAA, 0xBB, 0xCC, 0xEE);
        assert!(big.gt(&small));
        assert!(small.lt(&big));
        assert!(!small.gt(&big));
        assert!(!big.lt(&small));
    }

    #[test]
    fn gte_lte_are_antisymmetric() {
        let small = U512::new(0xAA, 0xBB, 0xCC, 0xDD);
        let big = U512::new(0xAA, 0xBB, 0xCC, 0xEE);
        assert!(big.gte(&small));
        assert!(small.lte(&big));
        assert!(!small.gte(&big));
        assert!(!big.lte(&small));
    }

    #[test]
    fn gte_and_lte_both_true_only_when_equal() {
        let a = U512::new(0xAA, 0xBB, 0xCC, 0xDD);
        let b = U512::new(0xAA, 0xBB, 0xCC, 0xDD);
        // Equal values satisfy both directions of the weak comparisons.
        assert!(a.gte(&b) && a.lte(&b));
        assert!(b.gte(&a) && b.lte(&a));
    }

    #[test]
    fn one_bit_difference_at_bit_zero_compares_correctly() {
        let zero = U512::new(0, 0, 0, 0);
        let one = U512::new(0, 0, 0, 1);
        assert!(one.gt(&zero));
        assert!(zero.lt(&one));
        assert!(!zero.gt(&one));
        assert!(!one.lt(&zero));
    }

    #[test]
    fn one_bit_difference_at_bit_511_compares_correctly() {
        let zero = U512::new(0, 0, 0, 0);
        let top = U512::new(1u128 << 127, 0, 0, 0);
        assert!(top.gt(&zero));
        assert!(zero.lt(&top));
        assert!(!zero.gt(&top));
        assert!(!top.lt(&zero));
    }
}

mod addition {
    use super::*;

    // ----- happy path -----

    #[test]
    fn add_zero_plus_zero_is_zero() {
        let z = U512::new(0, 0, 0, 0);
        let r = z.add(&z).unwrap();
        assert!(r.eq(&z));
    }

    #[test]
    fn add_identity_with_zero() {
        let a = U512::new(0xDEAD, 0xBEEF, 0xCAFE, 0xBABE);
        let z = U512::new(0, 0, 0, 0);
        assert!(a.add(&z).unwrap().eq(&a));
        assert!(z.add(&a).unwrap().eq(&a));
    }

    #[test]
    fn add_intra_word_no_carry() {
        let a = U512::new(0, 0, 0, 100);
        let b = U512::new(0, 0, 0, 23);
        let r = a.add(&b).unwrap();
        assert!(r.eq(&U512::new(0, 0, 0, 123)));
    }

    #[test]
    fn add_inter_word_carry_into_items_one() {
        // items[0] = MAX + 1 = 0 with carry into items[1].
        let a = U512::new(0, 0, 0, u64::MAX as u128);
        let b = U512::new(0, 0, 0, 1);
        let r = a.add(&b).unwrap();
        let expected = U512::new(0, 0, 0, 1u128 << 64);
        assert!(r.eq(&expected));
    }

    #[test]
    fn add_carry_cascades_through_four_words() {
        // (2^256 - 1) + 1 = 2^256. Carry runs from items[0] up to items[4].
        let a = U512::new(0, 0, u128::MAX, u128::MAX);
        let b = U512::new(0, 0, 0, 1);
        let r = a.add(&b).unwrap();
        let expected = U512::new(0, 1, 0, 0);
        assert!(r.eq(&expected));
    }

    #[test]
    fn add_carry_cascades_through_seven_words_and_just_fits() {
        // a = U512::MAX with bit 448 cleared; b = 1.
        // Carry propagates through items[0..6] (each MAX→0) and exactly refills
        // bit 448, producing a value with bits 448..511 set. No final overflow.
        let a = U512::new(u128::MAX ^ (1u128 << 64), u128::MAX, u128::MAX, u128::MAX);
        let b = U512::new(0, 0, 0, 1);
        let r = a.add(&b).unwrap();
        let expected = U512::new((u64::MAX as u128) << 64, 0, 0, 0);
        assert!(r.eq(&expected));
    }

    #[test]
    fn add_max_minus_one_plus_one_just_fits() {
        // (U512::MAX with bit 0 cleared) + 1 = U512::MAX. Tests the final
        // word doesn't spuriously emit a carry-out.
        let max = U512::new(u128::MAX, u128::MAX, u128::MAX, u128::MAX);
        let a = U512::new(u128::MAX, u128::MAX, u128::MAX, u128::MAX ^ 1);
        let b = U512::new(0, 0, 0, 1);
        assert!(a.add(&b).unwrap().eq(&max));
    }

    #[test]
    fn add_large_values_without_carry_between_components() {
        // Each u128 component sums independently — no inter-word carry.
        let a = U512::new(0xAAA, 0xBBB, 0xCCC, 0xDDD);
        let b = U512::new(0x111, 0x222, 0x333, 0x444);
        let r = a.add(&b).unwrap();
        let expected = U512::new(0xBBB, 0xDDD, 0xFFF, 0x1221);
        assert!(r.eq(&expected));
    }

    // ----- overflow -----

    #[test]
    fn add_max_plus_one_overflows() {
        // U512::MAX + 1: carry cascades through all 8 words and escapes.
        let max = U512::new(u128::MAX, u128::MAX, u128::MAX, u128::MAX);
        let one = U512::new(0, 0, 0, 1);
        assert!(matches!(max.add(&one), Err(SoulMathError::AddOverflow)));
    }

    #[test]
    fn add_max_plus_max_overflows() {
        let max = U512::new(u128::MAX, u128::MAX, u128::MAX, u128::MAX);
        assert!(matches!(max.add(&max), Err(SoulMathError::AddOverflow)));
    }

    #[test]
    fn add_two_top_bits_overflows() {
        // 2^511 + 2^511 = 2^512 → out of range.
        let top_bit = U512::new(1u128 << 127, 0, 0, 0);
        assert!(matches!(top_bit.add(&top_bit), Err(SoulMathError::AddOverflow)));
    }

    #[test]
    fn add_one_short_of_top_bit_plus_itself_just_fits() {
        // 2^510 + 2^510 = 2^511 — does NOT overflow.
        let a = U512::new(1u128 << 126, 0, 0, 0);
        let r = a.add(&a).unwrap();
        let expected = U512::new(1u128 << 127, 0, 0, 0);
        assert!(r.eq(&expected));
    }

    // ----- properties -----

    #[test]
    fn add_is_commutative() {
        let pairs = [
            (U512::new(0, 0, 0, 5), U512::new(0, 0, 0, 7)),
            (U512::new(0, 0, 0xFF, 0), U512::new(0, 0, 0, 0xFF)),
            (U512::new(0xAAA, 0xBBB, 0xCCC, 0xDDD), U512::new(0x111, 0x222, 0x333, 0x444)),
            (U512::new(u128::MAX >> 1, 0, 0, 0), U512::new(0, 0, 0, u128::MAX >> 1)),
        ];
        for (a, b) in pairs {
            let ab = a.add(&b).unwrap();
            let ba = b.add(&a).unwrap();
            assert!(ab.eq(&ba));
        }
    }

    #[test]
    fn add_is_associative() {
        // (a + b) + c == a + (b + c).
        let a = U512::new(0, 0, 0x1234, 0x5678);
        let b = U512::new(0, 0x9ABC, 0, 0xDEF0);
        let c = U512::new(0xCAFE, 0, 0xBABE, 0);
        let lhs = a.add(&b).unwrap().add(&c).unwrap();
        let rhs = a.add(&b.add(&c).unwrap()).unwrap();
        assert!(lhs.eq(&rhs));
    }

    #[test]
    fn add_then_sub_recovers_original() {
        let a = U512::new(0xDEAD, 0xBEEF, 0xCAFE, 0xBABE);
        let b = U512::new(0x1234, 0x5678, 0x9ABC, 0xDEF0);
        let sum = a.add(&b).unwrap();
        assert!(sum.sub(&b).unwrap().eq(&a));
        assert!(sum.sub(&a).unwrap().eq(&b));
    }
}

mod subtraction {
    use super::*;

    // ----- happy path -----

    #[test]
    fn sub_zero_minus_zero_is_zero() {
        let z = U512::new(0, 0, 0, 0);
        assert!(z.sub(&z).unwrap().eq(&z));
    }

    #[test]
    fn sub_identity_with_zero() {
        let a = U512::new(0xDEAD, 0xBEEF, 0xCAFE, 0xBABE);
        let z = U512::new(0, 0, 0, 0);
        assert!(a.sub(&z).unwrap().eq(&a));
    }

    #[test]
    fn sub_self_minus_self_is_zero() {
        let a = U512::new(0xDEAD, 0xBEEF, 0xCAFE, 0xBABE);
        let z = U512::new(0, 0, 0, 0);
        assert!(a.sub(&a).unwrap().eq(&z));
    }

    #[test]
    fn sub_max_minus_max_is_zero() {
        let max = U512::new(u128::MAX, u128::MAX, u128::MAX, u128::MAX);
        let z = U512::new(0, 0, 0, 0);
        assert!(max.sub(&max).unwrap().eq(&z));
    }

    #[test]
    fn sub_intra_word_no_borrow() {
        let a = U512::new(0, 0, 0, 100);
        let b = U512::new(0, 0, 0, 23);
        assert!(a.sub(&b).unwrap().eq(&U512::new(0, 0, 0, 77)));
    }

    #[test]
    fn sub_inter_word_borrow_from_items_one() {
        // 2^64 - 1 = u64::MAX. Borrows from items[1] into items[0].
        let a = U512::new(0, 0, 0, 1u128 << 64);
        let b = U512::new(0, 0, 0, 1);
        let expected = U512::new(0, 0, 0, u64::MAX as u128);
        assert!(a.sub(&b).unwrap().eq(&expected));
    }

    #[test]
    fn sub_borrow_cascades_through_four_words() {
        // 2^256 - 1 → 256 ones in the lower half. Borrow propagates items[0..4].
        let a = U512::new(0, 1, 0, 0);
        let b = U512::new(0, 0, 0, 1);
        let expected = U512::new(0, 0, u128::MAX, u128::MAX);
        assert!(a.sub(&b).unwrap().eq(&expected));
    }

    #[test]
    fn sub_borrow_cascades_through_all_words() {
        // 2^511 - 1 → bits 0..510 set, bit 511 clear.
        // Borrow runs from items[0] up through items[6]; items[7] absorbs it.
        let a = U512::new(1u128 << 127, 0, 0, 0);
        let b = U512::new(0, 0, 0, 1);
        let expected = U512::new(u128::MAX >> 1, u128::MAX, u128::MAX, u128::MAX);
        assert!(a.sub(&b).unwrap().eq(&expected));
    }

    #[test]
    fn sub_max_minus_one_clears_bit_zero() {
        let max = U512::new(u128::MAX, u128::MAX, u128::MAX, u128::MAX);
        let one = U512::new(0, 0, 0, 1);
        let expected = U512::new(u128::MAX, u128::MAX, u128::MAX, u128::MAX ^ 1);
        assert!(max.sub(&one).unwrap().eq(&expected));
    }

    #[test]
    fn sub_with_borrow_consumed_mid_loop() {
        // a = 2^128, b = 2^128 - 1. Borrow rises through items[0..2] then is consumed
        // by items[2]. result = 1.
        let a = U512::new(0, 0, 1, 0);
        let b = U512::new(0, 0, 0, u128::MAX);
        let expected = U512::new(0, 0, 0, 1);
        assert!(a.sub(&b).unwrap().eq(&expected));
    }

    #[test]
    fn sub_max_minus_max_minus_one_is_one() {
        let max = U512::new(u128::MAX, u128::MAX, u128::MAX, u128::MAX);
        let max_minus_one = U512::new(u128::MAX, u128::MAX, u128::MAX, u128::MAX ^ 1);
        let one = U512::new(0, 0, 0, 1);
        assert!(max.sub(&max_minus_one).unwrap().eq(&one));
    }

    // ----- underflow -----

    #[test]
    fn sub_zero_minus_one_underflows() {
        let z = U512::new(0, 0, 0, 0);
        let one = U512::new(0, 0, 0, 1);
        assert!(matches!(z.sub(&one), Err(SoulMathError::SubUnderflow)));
    }

    #[test]
    fn sub_smaller_minus_bigger_underflows() {
        let a = U512::new(0, 0, 0, 1);
        let b = U512::new(0, 0, 0, 2);
        assert!(matches!(a.sub(&b), Err(SoulMathError::SubUnderflow)));
    }

    #[test]
    fn sub_underflow_only_in_top_word() {
        // Lower 7 words identical; the difference is in items[6] (hh.lo()).
        // The pre-check must walk MSW-down and catch it.
        let a = U512::new(1, u128::MAX, u128::MAX, u128::MAX);
        let b = U512::new(2, u128::MAX, u128::MAX, u128::MAX);
        assert!(matches!(a.sub(&b), Err(SoulMathError::SubUnderflow)));
    }

    #[test]
    fn sub_underflow_one_bit_short() {
        // a = 2^256, b = 2^256 + 1 → underflow by exactly 1.
        let a = U512::new(0, 1, 0, 0);
        let b = U512::new(0, 1, 0, 1);
        assert!(matches!(a.sub(&b), Err(SoulMathError::SubUnderflow)));
    }

    #[test]
    fn sub_underflow_just_below_threshold() {
        // a = 2^256 - 1 (no top half), b = 2^256 (lowest bit of upper half).
        let a = U512::new(0, 0, u128::MAX, u128::MAX);
        let b = U512::new(0, 1, 0, 0);
        assert!(matches!(a.sub(&b), Err(SoulMathError::SubUnderflow)));
    }

    // ----- properties -----

    #[test]
    fn sub_then_add_recovers_original() {
        let a = U512::new(0xDEAD, 0xBEEF, 0xCAFE, 0xBABE);
        let b = U512::new(0x1234, 0x5678, 0x9ABC, 0xDEF0); // a > b
        let diff = a.sub(&b).unwrap();
        assert!(diff.add(&b).unwrap().eq(&a));
    }

    #[test]
    fn sub_is_not_commutative_when_unequal() {
        // a.sub(b) succeeds, b.sub(a) must underflow.
        let a = U512::new(0xDEAD, 0xBEEF, 0xCAFE, 0xBABE);
        let b = U512::new(0x1234, 0x5678, 0x9ABC, 0xDEF0);
        assert!(a.sub(&b).is_ok());
        assert!(matches!(b.sub(&a), Err(SoulMathError::SubUnderflow)));
    }
}

mod multiplication {
    use super::*;

    // ----- happy path -----

    #[test]
    fn mul_zero_times_zero_is_zero() {
        let z = U512::new(0, 0, 0, 0);
        assert!(z.mul(&z).unwrap().eq(&z));
    }

    #[test]
    fn mul_anything_times_zero_is_zero() {
        let a = U512::new(0xDEAD, 0xBEEF, 0xCAFE, 0xBABE);
        let z = U512::new(0, 0, 0, 0);
        assert!(a.mul(&z).unwrap().eq(&z));
        assert!(z.mul(&a).unwrap().eq(&z));
    }

    #[test]
    fn mul_identity_with_one() {
        let a = U512::new(0xDEAD, 0xBEEF, 0xCAFE, 0xBABE);
        let one = U512::new(0, 0, 0, 1);
        assert!(a.mul(&one).unwrap().eq(&a));
        assert!(one.mul(&a).unwrap().eq(&a));
    }

    #[test]
    fn mul_small_intra_word() {
        let a = U512::new(0, 0, 0, 12345);
        let b = U512::new(0, 0, 0, 6789);
        let expected = U512::new(0, 0, 0, 12345u128 * 6789u128);
        assert!(a.mul(&b).unwrap().eq(&expected));
    }

    #[test]
    fn mul_max_u64_squared() {
        // u64::MAX * u64::MAX = 2^128 - 2^65 + 1.
        // Forces a carry into items[1]: result is items[0] = 1, items[1] = MAX - 1.
        let a = U512::new(0, 0, 0, u64::MAX as u128);
        let expected = U512::new(0, 0, 0, (u64::MAX as u128) * (u64::MAX as u128));
        assert!(a.mul(&a).unwrap().eq(&expected));
    }

    #[test]
    fn mul_2_64_times_2_64_is_2_128() {
        // Single-word inputs whose product lives one word higher.
        let a = U512::new(0, 0, 0, 1u128 << 64);
        let expected = U512::new(0, 0, 1, 0);
        assert!(a.mul(&a).unwrap().eq(&expected));
    }

    #[test]
    fn mul_2_128_times_2_128_is_2_256() {
        let a = U512::new(0, 0, 1, 0);
        let expected = U512::new(0, 1, 0, 0);
        assert!(a.mul(&a).unwrap().eq(&expected));
    }

    #[test]
    fn mul_2_256_times_2_255_just_fits() {
        // Boundary: product lands exactly on bit 511 with no carry-out.
        let a = U512::new(0, 1, 0, 0);              // 2^256
        let b = U512::new(0, 0, 1u128 << 127, 0);   // 2^255
        let expected = U512::new(1u128 << 127, 0, 0, 0); // 2^511
        assert!(a.mul(&b).unwrap().eq(&expected));
        // And commutatively.
        assert!(b.mul(&a).unwrap().eq(&expected));
    }

    #[test]
    fn mul_2_256_times_max_below_2_256() {
        // 2^256 * (2^256 - 1) = 2^512 - 2^256. Upper half is all 1s, no carry-out.
        let a = U512::new(0, 1, 0, 0);
        let b = U512::new(0, 0, u128::MAX, u128::MAX);
        let expected = U512::new(u128::MAX, u128::MAX, 0, 0);
        assert!(a.mul(&b).unwrap().eq(&expected));
    }

    #[test]
    fn mul_max_below_2_256_times_two() {
        // (2^256 - 1) * 2 = 2^257 - 2. Carry propagates through four words,
        // finally landing a 1 in items[4].
        let a = U512::new(0, 0, u128::MAX, u128::MAX);
        let two = U512::new(0, 0, 0, 2);
        let expected = U512::new(0, 1, u128::MAX, u128::MAX - 1);
        assert!(a.mul(&two).unwrap().eq(&expected));
    }

    #[test]
    fn mul_by_power_of_two_equals_left_shift() {
        // Cross-check mul against shift_left for several powers of two.
        let a = U512::new(0, 0, 0xCAFE, 0xBABE);
        let pow2_128 = U512::new(0, 0, 1, 0);
        assert!(a.mul(&pow2_128).unwrap().eq(&a.shift_left(128)));

        let b = U512::new(0, 0, 0, 0xDEAD);
        let pow2_64 = U512::new(0, 0, 0, 1u128 << 64);
        assert!(b.mul(&pow2_64).unwrap().eq(&b.shift_left(64)));
    }

    // ----- overflow -----

    #[test]
    fn mul_2_256_times_2_256_overflows() {
        // i=4, j=4 → position = 8 → MulOverflow inside the inner loop.
        let a = U512::new(0, 1, 0, 0);
        assert!(matches!(a.mul(&a), Err(SoulMathError::MulOverflow)));
    }

    #[test]
    fn mul_2_448_times_2_64_overflows() {
        // i=7, j=1 → position = 8 → MulOverflow.
        let a = U512::new(1u128 << 64, 0, 0, 0);
        let b = U512::new(0, 0, 0, 1u128 << 64);
        assert!(matches!(a.mul(&b), Err(SoulMathError::MulOverflow)));
    }

    #[test]
    fn mul_2_511_times_two_overflows_via_carry() {
        // i=7, j=0: position=7 fits; carry of 1 must propagate to position 8 → MulOverflow.
        // Catches off-by-one bugs in the carry-propagation `carry_pos >= NUM_WORDS` check.
        let a = U512::new(1u128 << 127, 0, 0, 0);
        let two = U512::new(0, 0, 0, 2);
        assert!(matches!(a.mul(&two), Err(SoulMathError::MulOverflow)));
    }

    #[test]
    fn mul_max_times_max_overflows() {
        let max = U512::new(u128::MAX, u128::MAX, u128::MAX, u128::MAX);
        assert!(matches!(max.mul(&max), Err(SoulMathError::MulOverflow)));
    }

    #[test]
    fn mul_max_times_two_overflows_via_carry() {
        // Carry propagates through every word and escapes at carry_pos = 8.
        let max = U512::new(u128::MAX, u128::MAX, u128::MAX, u128::MAX);
        let two = U512::new(0, 0, 0, 2);
        assert!(matches!(max.mul(&two), Err(SoulMathError::MulOverflow)));
    }

    #[test]
    fn mul_2_256_times_2_257_overflows() {
        // 2^256 * 2^257 = 2^513. Position 4 + 4 = 8 with carry-out from the product.
        let a = U512::new(0, 1, 0, 0);
        let b = U512::new(0, 2, 0, 0);
        assert!(matches!(a.mul(&b), Err(SoulMathError::MulOverflow)));
    }

    // ----- properties -----

    #[test]
    fn mul_is_commutative() {
        let pairs = [
            (U512::new(0, 0, 0, 5), U512::new(0, 0, 0, 7)),
            (U512::new(0, 0, 0, u64::MAX as u128), U512::new(0, 0, 0, u64::MAX as u128)),
            (U512::new(0, 0, 0xABCD, 0), U512::new(0, 0, 0, 0x1234)),
            (U512::new(0, 1, 0, 0), U512::new(0, 0, 1, 0)),
            (U512::new(0, 0, 0xDEAD, 0xBEEF), U512::new(0, 0, 0xCAFE, 0xBABE)),
        ];
        for (a, b) in pairs {
            assert!(a.mul(&b).unwrap().eq(&b.mul(&a).unwrap()));
        }
    }

    #[test]
    fn mul_distributes_over_add() {
        let a = U512::new(0, 0, 0, 7);
        let b = U512::new(0, 0, 0, 11);
        let c = U512::new(0, 0, 0, 13);
        let lhs = a.mul(&b.add(&c).unwrap()).unwrap();
        let rhs = a.mul(&b).unwrap().add(&a.mul(&c).unwrap()).unwrap();
        assert!(lhs.eq(&rhs));
    }

    #[test]
    fn mul_distributes_over_sub() {
        let a = U512::new(0, 0, 0, 11);
        let b = U512::new(0, 0, 0, 0x100);
        let c = U512::new(0, 0, 0, 0x50);
        let lhs = a.mul(&b.sub(&c).unwrap()).unwrap();
        let rhs = a.mul(&b).unwrap().sub(&a.mul(&c).unwrap()).unwrap();
        assert!(lhs.eq(&rhs));
    }

    #[test]
    fn mul_is_associative() {
        // (a * b) * c == a * (b * c). Values chosen so all intermediates fit.
        let a = U512::new(0, 0, 0, 0x100);
        let b = U512::new(0, 0, 0, 0x200);
        let c = U512::new(0, 0, 0, 0x300);
        let lhs = a.mul(&b).unwrap().mul(&c).unwrap();
        let rhs = a.mul(&b.mul(&c).unwrap()).unwrap();
        assert!(lhs.eq(&rhs));
    }
}


mod division {
    use super::*;

    #[test]
    fn test_div() {
        let a = U512::new(
            0, 0, 0, 2350
        );
        let b = U512::new(
            0, 0, 0, 552249
        );

        let res = b.div(&a);
        println!("{res:?}");
    }

    // ----- happy path -----

    #[test]
    fn div_by_one_returns_dividend_and_zero() {
        let a = U512::new(0xDEAD, 0xBEEF, 0xCAFE, 0xBABE);
        let one = U512::new(0, 0, 0, 1);
        let (q, r) = a.div(&one).unwrap();
        assert!(q.eq(&a));
        assert!(r.is_zero());
    }

    #[test]
    fn div_self_by_self_is_one_remainder_zero() {
        let a = U512::new(0xDEAD, 0xBEEF, 0xCAFE, 0xBABE);
        let (q, r) = a.div(&a).unwrap();
        assert!(q.eq(&U512::new(0, 0, 0, 1)));
        assert!(r.is_zero());
    }

    #[test]
    fn div_zero_by_anything_is_zero() {
        let z = U512::new(0, 0, 0, 0);
        let a = U512::new(0xDEAD, 0xBEEF, 0xCAFE, 0xBABE);
        let (q, r) = z.div(&a).unwrap();
        assert!(q.is_zero());
        assert!(r.is_zero());
    }

    #[test]
    fn div_smaller_by_bigger_is_zero_remainder_self() {
        // Short-circuit branch: dividend < divisor.
        let a = U512::new(0, 0, 0, 5);
        let b = U512::new(0, 0, 0, 100);
        let (q, r) = a.div(&b).unwrap();
        assert!(q.is_zero());
        assert!(r.eq(&a));
    }

    #[test]
    fn div_dividend_one_above_divisor() {
        // (b + 1) / b = 1 rem 1.
        let b = U512::new(0, 0, 0xCAFE, 0xBABE);
        let a = b.add(&U512::new(0, 0, 0, 1)).unwrap();
        let (q, r) = a.div(&b).unwrap();
        assert!(q.eq(&U512::new(0, 0, 0, 1)));
        assert!(r.eq(&U512::new(0, 0, 0, 1)));
    }

    #[test]
    fn div_small_intra_word() {
        // 100 / 7 = 14 rem 2.
        let a = U512::new(0, 0, 0, 100);
        let b = U512::new(0, 0, 0, 7);
        let (q, r) = a.div(&b).unwrap();
        assert!(q.eq(&U512::new(0, 0, 0, 14)));
        assert!(r.eq(&U512::new(0, 0, 0, 2)));
    }

    #[test]
    fn div_5500_by_56_decimal_walkthrough() {
        // The exact example from the Knuth/decimal walkthrough.
        // 5500 / 56 = 98 rem 12.
        let a = U512::new(0, 0, 0, 5500);
        let b = U512::new(0, 0, 0, 56);
        let (q, r) = a.div(&b).unwrap();
        assert!(q.eq(&U512::new(0, 0, 0, 98)));
        assert!(r.eq(&U512::new(0, 0, 0, 12)));
    }

    #[test]
    fn div_2_256_by_2_128_is_2_128() {
        // Exact powers of two: quotient is the difference shifted.
        let a = U512::new(0, 1, 0, 0);
        let b = U512::new(0, 0, 1, 0);
        let (q, r) = a.div(&b).unwrap();
        assert!(q.eq(&b));
        assert!(r.is_zero());
    }

    #[test]
    fn div_max_by_max_is_one() {
        let max = U512::new(u128::MAX, u128::MAX, u128::MAX, u128::MAX);
        let (q, r) = max.div(&max).unwrap();
        assert!(q.eq(&U512::new(0, 0, 0, 1)));
        assert!(r.is_zero());
    }

    #[test]
    fn div_max_by_two() {
        // U512::MAX = 2^512 - 1 (odd). MAX/2 = 2^511 - 1 rem 1.
        let max = U512::new(u128::MAX, u128::MAX, u128::MAX, u128::MAX);
        let two = U512::new(0, 0, 0, 2);
        let (q, r) = max.div(&two).unwrap();
        let expected_q = U512::new(u128::MAX >> 1, u128::MAX, u128::MAX, u128::MAX);
        assert!(q.eq(&expected_q));
        assert!(r.eq(&U512::new(0, 0, 0, 1)));
    }

    #[test]
    fn div_5000_by_28_forces_full_normalization() {
        // Divisor top digit = 2 (low) → leading_zeros(28) = 59, big normalization shift.
        // 5000 / 28 = 178 rem 16.
        let a = U512::new(0, 0, 0, 5000);
        let b = U512::new(0, 0, 0, 28);
        let (q, r) = a.div(&b).unwrap();
        assert!(q.eq(&U512::new(0, 0, 0, 178)));
        assert!(r.eq(&U512::new(0, 0, 0, 16)));
    }

    #[test]
    fn div_multi_word_dividend_by_single_word_divisor() {
        // 2^256 / 7. Quotient ≈ 1.65e76; check via identity q*b + r == a.
        let a = U512::new(0, 1, 0, 0);
        let b = U512::new(0, 0, 0, 7);
        let (q, r) = a.div(&b).unwrap();
        let recomputed = q.mul(&b).unwrap().add(&r).unwrap();
        assert!(recomputed.eq(&a));
        assert!(r.lt(&b));
    }

    #[test]
    fn div_multi_word_dividend_by_multi_word_divisor() {
        // Exercises the full Algorithm D path (n >= 2).
        let a = U512::new(0xDEAD, 0xBEEF, 0xCAFE, 0xBABE);
        let b = U512::new(0, 0, 0xABCD, 0xEF01);
        let (q, r) = a.div(&b).unwrap();
        let recomputed = q.mul(&b).unwrap().add(&r).unwrap();
        assert!(recomputed.eq(&a));
        assert!(r.lt(&b));
    }

    // ----- errors -----

    #[test]
    fn div_by_zero_returns_error() {
        let a = U512::new(0xDEAD, 0xBEEF, 0xCAFE, 0xBABE);
        let z = U512::new(0, 0, 0, 0);
        assert!(matches!(a.div(&z), Err(SoulMathError::CantBeDividedByZero)));
    }

    #[test]
    fn div_zero_by_zero_returns_error() {
        let z = U512::new(0, 0, 0, 0);
        assert!(matches!(z.div(&z), Err(SoulMathError::CantBeDividedByZero)));
    }

    // ----- exercises q_guess cap / correction loop -----

    #[test]
    fn div_triggers_q_guess_cap() {
        // Crafted so the top word of the partial dividend equals the top word
        // of the normalized divisor — the q_guess > U64_MAX branch must fire.
        // Use a / b where both share leading words: a = 0xFFFF...FFFF, b = 0x8000...0001.
        let a = U512::new(u128::MAX, u128::MAX, u128::MAX, u128::MAX);
        let b = U512::new(0, 0, 1u128 << 127, 1);
        let (q, r) = a.div(&b).unwrap();
        // Verify by reconstruction.
        let recomputed = q.mul(&b).unwrap().add(&r).unwrap();
        assert!(recomputed.eq(&a));
        assert!(r.lt(&b));
    }

    #[test]
    fn div_triggers_correction_decrement() {
        // Carefully picks values where q_guess initially overshoots and must
        // be corrected down. The reconstruction property catches any mistake.
        let a = U512::new(0, 0xDEADBEEF_CAFEBABE, 0x1234567890ABCDEF, 0xFEDCBA0987654321);
        let b = U512::new(0, 0, 0xFFFF_0000_FFFF_0000, 0x0000_FFFF_0000_FFFF);
        let (q, r) = a.div(&b).unwrap();
        let recomputed = q.mul(&b).unwrap().add(&r).unwrap();
        assert!(recomputed.eq(&a));
        assert!(r.lt(&b));
    }

    // ----- properties -----

    #[test]
    fn div_identity_q_times_b_plus_r_equals_a() {
        let pairs = [
            (U512::new(0, 0, 0, 12345), U512::new(0, 0, 0, 67)),
            (U512::new(0, 0, 0xCAFE, 0xBABE), U512::new(0, 0, 0, 0xDEAD)),
            (U512::new(u128::MAX, u128::MAX, u128::MAX, u128::MAX), U512::new(0, 0, 0, 0xFFFF)),
            (U512::new(0, 1, 0, 0), U512::new(0, 0, 0xABCD, 0xDEF0)),
            (U512::new(0xAAAA, 0xBBBB, 0xCCCC, 0xDDDD), U512::new(0, 0, 0xEEEE, 0xFFFF)),
        ];
        for (a, b) in pairs {
            let (q, r) = a.div(&b).unwrap();
            let recomputed = q.mul(&b).unwrap().add(&r).unwrap();
            assert!(recomputed.eq(&a));
            assert!(r.lt(&b)); // remainder strictly less than divisor
        }
    }

    #[test]
    fn div_exact_multiple_has_zero_remainder() {
        // (a * b) / b == a, remainder 0. Validates that mul and div are inverses
        // up to remainder.
        let a = U512::new(0, 0, 0xCAFE, 0xBABE);
        let b = U512::new(0, 0, 0, 0xDEAD_BEEF);
        let product = a.mul(&b).unwrap();
        let (q, r) = product.div(&b).unwrap();
        assert!(q.eq(&a));
        assert!(r.is_zero());
    }

    #[test]
    fn div_power_of_two_equals_right_shift() {
        // Dividing by 2^k is equivalent to shift_right(k).
        let a = U512::new(0xDEAD, 0xBEEF, 0xCAFE, 0xBABE);
        let pow2_128 = U512::new(0, 0, 1, 0);
        let (q, _) = a.div(&pow2_128).unwrap();
        assert!(q.eq(&a.shift_right(128)));
    }
}

mod harsh_money_safety {
    //! Property-based and cross-checked tests. Because this math handles money,
    //! the assertions here are intentionally redundant with the operation-specific
    //! tests above — bug-class coverage matters more than per-test minimalism.

    use super::*;

    /// 22 values covering: zero, single-word boundaries (u64::MAX, 2^64, u128::MAX),
    /// two-word boundary (2^128), four-word boundary (2^256), six-word boundary (2^384),
    /// eight-word boundary (2^511, U512::MAX, MAX-1), mixed bit-patterns,
    /// and DeFi-relevant magnitudes (1e18 wei, 2^96 sqrtPriceX96 base).
    fn test_values() -> Vec<U512> {
        vec![
            U512::new(0, 0, 0, 0),
            U512::new(0, 0, 0, 1),
            U512::new(0, 0, 0, 2),
            U512::new(0, 0, 0, 3),
            U512::new(0, 0, 0, u64::MAX as u128 - 1),
            U512::new(0, 0, 0, u64::MAX as u128),
            U512::new(0, 0, 0, 1u128 << 64),
            U512::new(0, 0, 0, u128::MAX - 1),
            U512::new(0, 0, 0, u128::MAX),
            U512::new(0, 0, 1, 0),
            U512::new(0, 0, u128::MAX, u128::MAX),
            U512::new(0, 1, 0, 0),
            U512::new(0, 1, 0, 1),
            U512::new(0, u128::MAX, u128::MAX, u128::MAX),
            U512::new(1, 0, 0, 0),
            U512::new(1u128 << 127, 0, 0, 0),
            U512::new(u128::MAX, u128::MAX, u128::MAX, u128::MAX),
            U512::new(u128::MAX, u128::MAX, u128::MAX, u128::MAX - 1),
            U512::new(
                0xDEAD_BEEF_CAFE_BABE,
                0x1234_5678_9ABC_DEF0,
                0xFEDC_BA98_7654_3210,
                0xABCD_EF01_2345_6789,
            ),
            U512::new(
                0xAAAA_AAAA_AAAA_AAAA_AAAA_AAAA_AAAA_AAAA,
                0x5555_5555_5555_5555_5555_5555_5555_5555,
                0xAAAA_AAAA_AAAA_AAAA_AAAA_AAAA_AAAA_AAAA,
                0x5555_5555_5555_5555_5555_5555_5555_5555,
            ),
            U512::new(0, 0, 0, 1_000_000_000_000_000_000u128), // 1e18 wei
            U512::new(0, 0, 0, 79_228_162_514_264_337_593_543_950_336u128), // 2^96
        ]
    }

    // ----- algebraic properties (brute-force over all pairs) -----

    #[test]
    fn add_is_commutative_brute_force() {
        for a in test_values() {
            for b in test_values() {
                match (a.add(&b), b.add(&a)) {
                    (Ok(x), Ok(y)) => assert!(x.eq(&y)),
                    (Err(_), Err(_)) => {}
                    _ => panic!("add commutativity asymmetric for {:?}, {:?}", a, b),
                }
            }
        }
    }

    #[test]
    fn mul_is_commutative_brute_force() {
        for a in test_values() {
            for b in test_values() {
                match (a.mul(&b), b.mul(&a)) {
                    (Ok(x), Ok(y)) => assert!(x.eq(&y)),
                    (Err(_), Err(_)) => {}
                    _ => panic!("mul commutativity asymmetric for {:?}, {:?}", a, b),
                }
            }
        }
    }

    #[test]
    fn add_sub_inverse_brute_force() {
        // (a + b) - b == a, and (a + b) - a == b.
        for a in test_values() {
            for b in test_values() {
                if let Ok(sum) = a.add(&b) {
                    assert!(sum.sub(&b).unwrap().eq(&a));
                    assert!(sum.sub(&a).unwrap().eq(&b));
                }
            }
        }
    }

    #[test]
    fn sub_add_inverse_brute_force() {
        // (a - b) + b == a, when a >= b.
        for a in test_values() {
            for b in test_values() {
                if a.gte(&b) {
                    let diff = a.sub(&b).unwrap();
                    assert!(diff.add(&b).unwrap().eq(&a));
                }
            }
        }
    }

    #[test]
    fn mul_div_inverse_brute_force() {
        // (a * b) / b == a, with zero remainder.
        for a in test_values() {
            for b in test_values() {
                if b.is_zero() {
                    continue;
                }
                if let Ok(prod) = a.mul(&b) {
                    let (q, r) = prod.div(&b).unwrap();
                    assert!(q.eq(&a));
                    assert!(r.is_zero());
                }
            }
        }
    }

    #[test]
    fn div_identity_brute_force() {
        // The fundamental theorem: q*b + r == a, with r < b. This is the
        // single strongest test for division correctness.
        for a in test_values() {
            for b in test_values() {
                if b.is_zero() {
                    continue;
                }
                let (q, r) = a.div(&b).unwrap();
                let recomputed = q.mul(&b).unwrap().add(&r).unwrap();
                assert!(recomputed.eq(&a), "q*b + r != a for a={:?}, b={:?}", a, b);
                assert!(r.lt(&b), "remainder >= divisor for a={:?}, b={:?}", a, b);
            }
        }
    }

    #[test]
    fn add_is_associative_brute_force() {
        let vals = test_values();
        for a in &vals {
            for b in &vals {
                for c in &vals {
                    let lhs = a.add(b).and_then(|ab| ab.add(c));
                    let rhs = b.add(c).and_then(|bc| a.add(&bc));
                    match (lhs, rhs) {
                        (Ok(x), Ok(y)) => assert!(x.eq(&y), "add not associative"),
                        (Err(_), Err(_)) => {}
                        _ => panic!("add associativity asymmetric"),
                    }
                }
            }
        }
    }

    #[test]
    fn mul_distributes_over_add_brute_force() {
        // a * (b + c) == a*b + a*c, whenever all intermediates fit.
        let vals = test_values();
        for a in &vals {
            for b in &vals {
                for c in &vals {
                    if let (Ok(bc), Ok(ab), Ok(ac)) = (b.add(c), a.mul(b), a.mul(c)) {
                        if let (Ok(lhs), Ok(rhs)) = (a.mul(&bc), ab.add(&ac)) {
                            assert!(lhs.eq(&rhs), "distributivity violated");
                        }
                    }
                }
            }
        }
    }

    // ----- comparison axioms -----

    #[test]
    fn comparison_total_order_brute_force() {
        let vals = test_values();
        for a in &vals {
            for b in &vals {
                // Trichotomy: exactly one of <, ==, > holds.
                let lt = a.lt(b) as u8;
                let eq = a.eq(b) as u8;
                let gt = a.gt(b) as u8;
                assert_eq!(lt + eq + gt, 1, "trichotomy violated");
                // Symmetry
                assert_eq!(a.gt(b), b.lt(a));
                assert_eq!(a.gte(b), b.lte(a));
                assert_eq!(a.eq(b), b.eq(a));
                // Weak vs strict
                assert_eq!(a.gte(b), a.gt(b) || a.eq(b));
                assert_eq!(a.lte(b), a.lt(b) || a.eq(b));
                // Reflexivity / irreflexivity
                assert!(a.gte(a) && a.lte(a) && a.eq(a));
                assert!(!a.gt(a) && !a.lt(a));
            }
        }
    }

    #[test]
    fn comparison_transitivity_brute_force() {
        let vals = test_values();
        for a in &vals {
            for b in &vals {
                for c in &vals {
                    if a.lt(b) && b.lt(c) {
                        assert!(a.lt(c));
                    }
                    if a.gt(b) && b.gt(c) {
                        assert!(a.gt(c));
                    }
                    if a.lte(b) && b.lte(c) {
                        assert!(a.lte(c));
                    }
                    if a.gte(b) && b.gte(c) {
                        assert!(a.gte(c));
                    }
                }
            }
        }
    }

    // ----- cross-check against native u128 (exact ground truth) -----

    #[test]
    fn arithmetic_matches_native_u128_when_in_range() {
        // For values that fit in u128, our U512 ops must produce IDENTICAL results
        // to Rust's native checked u128 arithmetic. This is the most precise possible
        // ground-truth check — any divergence is a hard bug.
        let vals: [u128; 14] = [
            0,
            1,
            2,
            3,
            100,
            12345,
            67890,
            u64::MAX as u128,
            (u64::MAX as u128) + 1,
            1u128 << 100,
            u128::MAX - 1,
            u128::MAX,
            0xDEAD_BEEF_CAFE_BABE,
            0x1234_5678_9ABC_DEF0,
        ];
        for &a in &vals {
            for &b in &vals {
                let ua = U512::new(0, 0, 0, a);
                let ub = U512::new(0, 0, 0, b);

                // add: U512 always succeeds here (sum < 2^129 < 2^512); native may overflow u128.
                let our_sum = ua.add(&ub).unwrap();
                match a.checked_add(b) {
                    Some(expected) => assert_eq!(
                        our_sum.try_into_u128().unwrap(),
                        expected,
                        "add({}, {})",
                        a,
                        b
                    ),
                    None => {
                        // Native overflowed; our result is the true sum (> u128::MAX).
                        // Verify by round-trip: (a+b) - b should give back a (fits in u128).
                        assert_eq!(our_sum.sub(&ub).unwrap().try_into_u128().unwrap(), a);
                        assert_eq!(our_sum.sub(&ua).unwrap().try_into_u128().unwrap(), b);
                    }
                }
                // sub: should match native checked_sub exactly (no extra room helps here).
                match a.checked_sub(b) {
                    Some(expected) => assert_eq!(
                        ua.sub(&ub).unwrap().try_into_u128().unwrap(),
                        expected,
                        "sub({}, {})",
                        a,
                        b
                    ),
                    None => assert!(matches!(
                        ua.sub(&ub),
                        Err(SoulMathError::SubUnderflow)
                    )),
                }
                // mul: U512 always succeeds here (u128 * u128 < 2^256); native may overflow.
                let our_prod = ua.mul(&ub).unwrap();
                match a.checked_mul(b) {
                    Some(expected) => assert_eq!(
                        our_prod.try_into_u128().unwrap(),
                        expected,
                        "mul({}, {})",
                        a,
                        b
                    ),
                    None => {
                        // Native overflowed; our result is the true product. Round-trip via division.
                        if b != 0 {
                            let (q, r) = our_prod.div(&ub).unwrap();
                            assert_eq!(q.try_into_u128().unwrap(), a);
                            assert!(r.is_zero());
                        }
                    }
                }
                // div
                if b != 0 {
                    let (q, r) = ua.div(&ub).unwrap();
                    assert_eq!(q.try_into_u128().unwrap(), a / b, "div quotient");
                    assert_eq!(r.try_into_u128().unwrap(), a % b, "div remainder");
                } else {
                    assert!(matches!(
                        ua.div(&ub),
                        Err(SoulMathError::CantBeDividedByZero)
                    ));
                }
            }
        }
    }

    // ----- shift/arith equivalence (catches discrepancies between bit ops and arith) -----

    #[test]
    fn shift_left_matches_mul_by_pow2_brute_force() {
        let shifts = [0u32, 1, 31, 63, 64, 65, 100, 127, 128, 129, 200, 255, 256, 384, 511];
        for a in test_values() {
            for &k in &shifts {
                let shifted = a.shift_left(k);
                let pow2 = U512::new(0, 0, 0, 1).shift_left(k);
                if let Ok(via_mul) = a.mul(&pow2) {
                    assert!(shifted.eq(&via_mul), "shift_left disagrees with mul-by-2^k");
                }
                // If mul overflows, shift_left should produce the truncated value;
                // we don't compare in that case (different semantics by design).
            }
        }
    }

    #[test]
    fn shift_right_matches_div_by_pow2_brute_force() {
        let shifts = [0u32, 1, 31, 63, 64, 65, 100, 127, 128, 200, 255, 256, 384, 511];
        for a in test_values() {
            for &k in &shifts {
                let shifted = a.shift_right(k);
                let pow2 = U512::new(0, 0, 0, 1).shift_left(k);
                if pow2.is_zero() {
                    continue;
                }
                let (q, _) = a.div(&pow2).unwrap();
                assert!(shifted.eq(&q), "shift_right disagrees with div-by-2^k");
            }
        }
    }

    // ----- hand-computed exact values for hard cases -----

    #[test]
    fn squared_max_below_2_256_exact() {
        // (2^256 - 1)^2 = 2^512 - 2^257 + 1.
        // Bits 0 and 257..511 are set; bits 1..256 are clear.
        let a = U512::new(0, 0, u128::MAX, u128::MAX);
        let expected = U512::new(u128::MAX, u128::MAX - 1, 0, 1);
        assert!(a.mul(&a).unwrap().eq(&expected));
    }

    #[test]
    fn squared_max_u128_exact() {
        // (2^128 - 1)^2 = 2^256 - 2^129 + 1.
        let a = U512::new(0, 0, 0, u128::MAX);
        let expected = U512::new(0, 0, u128::MAX - 1, 1);
        assert!(a.mul(&a).unwrap().eq(&expected));
    }

    #[test]
    fn mul_2_256_plus_one_times_2_256_minus_one_exact() {
        // (2^256 + 1)(2^256 - 1) = 2^512 - 1 = U512::MAX. The result is
        // exactly the largest representable value — no overflow allowed.
        let a = U512::new(0, 1, 0, 1);
        let b = U512::new(0, 0, u128::MAX, u128::MAX);
        let expected = U512::new(u128::MAX, u128::MAX, u128::MAX, u128::MAX);
        assert!(a.mul(&b).unwrap().eq(&expected));
    }

    // ----- carry/borrow chains exercised at every word boundary -----

    #[test]
    fn add_carry_propagation_at_every_word_boundary() {
        // For each word i in 0..7, place u64::MAX at word i and add 1.
        // The carry must clear word i and set word i+1 to 1, with no other effect.
        for i in 0..7u32 {
            let shift = i * 64;
            let a = U512::new(0, 0, 0, u64::MAX as u128).shift_left(shift);
            let b = U512::new(0, 0, 0, 1).shift_left(shift);
            let sum = a.add(&b).unwrap();
            let expected = U512::new(0, 0, 0, 1).shift_left(shift + 64);
            assert!(sum.eq(&expected), "carry propagation failed at word {}", i);
        }
    }

    #[test]
    fn sub_borrow_propagation_at_every_word_boundary() {
        // 2^k - 1 for each word-aligned k. Verifies borrow ripples correctly
        // by reconstructing: (2^k - 1) + 1 should equal 2^k exactly.
        for k_words in 1..8u32 {
            let k = k_words * 64;
            let a = U512::new(0, 0, 0, 1).shift_left(k);
            let one = U512::new(0, 0, 0, 1);
            let diff = a.sub(&one).unwrap();
            let recomputed = diff.add(&one).unwrap();
            assert!(recomputed.eq(&a), "borrow propagation failed at k={}", k);
            // Also: 2^k - 1 must compare strictly less than 2^k.
            assert!(diff.lt(&a));
        }
    }

    // ----- Algorithm D internals stress -----

    #[test]
    fn div_normalization_at_every_shift_amount() {
        // Construct divisors with each possible leading_zeros count (0..63),
        // so normalization shifts by every value in [0, 63]. The reconstruction
        // identity must hold for all of them.
        let dividend = U512::new(0xDEAD_BEEF, 0xCAFE_BABE, 0x1234_5678, 0x9ABC_DEF0);
        for shift in 0..64u32 {
            let top_bit = 63u32 - shift;
            let divisor = U512::new(0, 0, 0, 1u128 << top_bit);
            let (q, r) = dividend.div(&divisor).unwrap();
            let recomputed = q.mul(&divisor).unwrap().add(&r).unwrap();
            assert!(recomputed.eq(&dividend), "div failed at shift={}", shift);
            assert!(r.lt(&divisor));
        }
    }

    #[test]
    fn div_q_guess_cap_stress() {
        // Pairs (a, b) where the top word of a equals the top word of b — this
        // forces q_guess > U64_MAX inside Algorithm D, triggering the cap.
        let top_words = [
            u64::MAX,
            1u64 << 63,
            0xDEAD_BEEF_CAFE_BABE_u64,
            0x8000_0000_0000_0001_u64,
            0x7FFF_FFFF_FFFF_FFFF_u64,
        ];
        let lows_a = [0u128, 1, u128::MAX, 0xCAFE_BABE];
        let lows_b = [1u128, 2, 0xFFFF, 0xDEAD_BEEF];
        for &top in &top_words {
            for &low_a in &lows_a {
                for &low_b in &lows_b {
                    let a = U512::new(0, 0, (top as u128) << 64, low_a);
                    let b = U512::new(0, 0, (top as u128) << 64, low_b);
                    if a.lt(&b) {
                        continue;
                    }
                    let (q, r) = a.div(&b).unwrap();
                    let recomputed = q.mul(&b).unwrap().add(&r).unwrap();
                    assert!(
                        recomputed.eq(&a),
                        "q_guess cap stress: top={:x} low_a={:x} low_b={:x}",
                        top,
                        low_a,
                        low_b
                    );
                    assert!(r.lt(&b));
                }
            }
        }
    }

    #[test]
    fn div_full_size_dividend_full_size_divisor_stress() {
        // Both operands span 8 words. Heavy exercise of the n=8 Algorithm D path.
        let pairs = [
            (
                U512::new(u128::MAX, u128::MAX, u128::MAX, u128::MAX),
                U512::new(0xDEAD_BEEF_CAFE_BABE, 0, 0, 1),
            ),
            (
                U512::new(u128::MAX, u128::MAX, u128::MAX, u128::MAX - 1),
                U512::new(1u128 << 100, 0xCAFE, 0xDEAD, 0xBEEF),
            ),
            (
                U512::new(0xFFFE_DCBA_9876_5432, 0x1023, 0xABCD, 0xEF01),
                U512::new(0x1234_5678_9ABC_DEF0, 0, 0xFEDC, 0xBA98),
            ),
            (
                U512::new(1u128 << 127, u128::MAX, 0, 1),
                U512::new(0, 0xDEAD_BEEF, u128::MAX, 0xCAFE_BABE),
            ),
        ];
        for (a, b) in pairs {
            let (q, r) = a.div(&b).unwrap();
            let recomputed = q.mul(&b).unwrap().add(&r).unwrap();
            assert!(recomputed.eq(&a));
            assert!(r.lt(&b));
        }
    }

    // ----- DeFi calculation patterns -----

    #[test]
    fn defi_amount_rate_div_denom_loses_no_precision() {
        // The ubiquitous (a * b) / c. Verify q*c + r == a*b for many real
        // DeFi magnitudes. Bugs here would silently misprice swaps/fees.
        let amounts = [
            U512::new(0, 0, 0, 1),
            U512::new(0, 0, 0, 1_000_000u128),                     // 1 USDC
            U512::new(0, 0, 0, 1_000_000_000_000_000_000u128),     // 1 ETH (wei)
            U512::new(0, 0, 0, 10_000_000_000_000_000_000_000u128), // 10_000 ETH
        ];
        let rates = [1u128, 30, 3_000, 997_000, 1_000_000];
        let denoms = [1u128, 10_000, 1_000_000, 1_000_000_000_000_000_000u128];
        for a in &amounts {
            for &r in &rates {
                for &d in &denoms {
                    let rate = U512::new(0, 0, 0, r);
                    let denom = U512::new(0, 0, 0, d);
                    let prod = a.mul(&rate).unwrap();
                    let (q, rem) = prod.div(&denom).unwrap();
                    let recomputed = q.mul(&denom).unwrap().add(&rem).unwrap();
                    assert!(recomputed.eq(&prod), "lost precision in amount*rate/denom");
                    assert!(rem.lt(&denom));
                }
            }
        }
    }

    #[test]
    fn amm_constant_product_invariant_holds() {
        // Constant-product AMM (Uniswap V2): x*y = k must be preserved or grow
        // after a swap (truncation only ever helps the invariant).
        let x = U512::new(0, 0, 0, 100_000_000_000_000_000_000u128); // 100 ETH
        let y = U512::new(0, 0, 0, 300_000_000_000_000_000_000_000u128); // 300_000 USDC scaled
        let dxs = [
            U512::new(0, 0, 0, 100_000_000_000_000_000u128), // 0.1 ETH
            U512::new(0, 0, 0, 1_000_000_000_000_000_000u128), // 1 ETH
            U512::new(0, 0, 0, 10_000_000_000_000_000_000u128), // 10 ETH
        ];
        let original_k = x.mul(&y).unwrap();
        for dx in &dxs {
            let new_x = x.add(dx).unwrap();
            let (dy, _) = y.mul(dx).unwrap().div(&new_x).unwrap();
            assert!(!dy.is_zero());
            assert!(dy.lt(&y));
            let new_y = y.sub(&dy).unwrap();
            let new_k = new_x.mul(&new_y).unwrap();
            assert!(new_k.gte(&original_k), "AMM invariant violated: k decreased");
        }
    }

    #[test]
    fn fee_accumulation_chain_preserves_total() {
        // Simulate splitting a value into many slices, then summing back.
        // If add/sub have any carry bug, the sum will drift from the original.
        let original = U512::new(0, 0, 0, 1_000_000_000_000_000_000_000u128); // 1e21
        let slice_count = 50u128;
        let slice = U512::new(0, 0, 0, 1_000_000_000_000_000_000_000u128 / slice_count); // 2e19
        let remainder = U512::new(
            0,
            0,
            0,
            1_000_000_000_000_000_000_000u128 - (1_000_000_000_000_000_000_000u128 / slice_count) * slice_count,
        );
        let mut acc = U512::new(0, 0, 0, 0);
        for _ in 0..slice_count {
            acc = acc.add(&slice).unwrap();
        }
        acc = acc.add(&remainder).unwrap();
        assert!(acc.eq(&original), "fee chain drifted");
    }

    #[test]
    fn never_creates_money_via_round_trip() {
        // Round-trip property: encode a value, decode it via different operations,
        // ensure no value is ever created or destroyed.
        for a in test_values() {
            for b in test_values() {
                if b.is_zero() {
                    continue;
                }
                // (a / b) * b + (a % b) == a — accounting identity.
                let (q, r) = a.div(&b).unwrap();
                let back = q.mul(&b).unwrap().add(&r).unwrap();
                assert!(back.eq(&a));
                // r < b, always.
                assert!(r.lt(&b));
                // (a + b) - b - a == 0 (when a + b doesn't overflow).
                if let Ok(sum) = a.add(&b) {
                    let zeroed = sum.sub(&b).unwrap().sub(&a).unwrap();
                    assert!(zeroed.is_zero());
                }
            }
        }
    }
}