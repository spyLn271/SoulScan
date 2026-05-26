use rusted_soul_dex::math::errors::SoulMathError;
use rusted_soul_dex::math::i256::I256;
use rusted_soul_dex::math::u256::U256;

// ---------- shared helpers ----------

/// A diverse battery of signed test values: zero, boundaries, mixed-sign
/// patterns, DeFi-relevant magnitudes, and a few high-bit-position powers
/// of two that have no native-i128 equivalent.
fn signed_test_values() -> Vec<I256> {
    vec![
        I256::ZERO,
        I256::ONE,
        I256::MINUS_ONE,
        I256::from_i32(2),
        I256::from_i32(-2),
        I256::from_i32(100),
        I256::from_i32(-100),
        I256::from_i32(i32::MAX),
        I256::from_i32(i32::MIN),
        I256::from_i64(i64::MAX),
        I256::from_i64(i64::MIN),
        I256::from_i128(i128::MAX),
        I256::from_i128(i128::MIN),
        I256::ONE.shl(127),
        I256::ONE.shl(200),
        I256::ONE.shl(254),
        I256::MAX,
        I256::MIN,
        I256::from_i128(0x5555_5555_5555_5555_5555_5555_5555_5555_i128),
        I256::from_i128(-0x5555_5555_5555_5555_5555_5555_5555_5555_i128),
    ]
}

/// Two's-complement negation via the canonical `!x + 1` formula.
/// `I256` does not expose `wrapping_neg`, so this stands in.
fn wrapping_neg(x: &I256) -> I256 {
    x.not().wrapping_add(&I256::ONE)
}

/// Unsigned magnitude as a U256. `wrapping_neg(MIN)` wraps back to MIN, whose
/// raw bits (0x8000…0) equal `2^255` as a `U256` — which is exactly `|MIN|`.
fn unsigned_magnitude(x: &I256) -> U256 {
    if x.is_negative() {
        wrapping_neg(x).bits
    } else {
        x.bits
    }
}

// ---------- mod wrapping_add_harsh ----------

mod wrapping_add_harsh {
    use super::*;

    #[test]
    fn zero_identity_in_both_directions() {
        for a in signed_test_values() {
            assert!(a.wrapping_add(&I256::ZERO).eq(&a));
            assert!(I256::ZERO.wrapping_add(&a).eq(&a));
        }
    }

    #[test]
    fn max_plus_one_wraps_to_min() {
        assert!(I256::MAX.wrapping_add(&I256::ONE).eq(&I256::MIN));
    }

    #[test]
    fn min_plus_minus_one_wraps_to_max() {
        assert!(I256::MIN.wrapping_add(&I256::MINUS_ONE).eq(&I256::MAX));
    }

    #[test]
    fn min_plus_min_is_zero() {
        // 2·MIN ≡ 0 (mod 2^256)
        assert!(I256::MIN.wrapping_add(&I256::MIN).eq(&I256::ZERO));
    }

    #[test]
    fn max_plus_max_wraps_to_minus_two() {
        // 2·MAX = 2·(2^255 − 1) = 2^256 − 2 ≡ −2 (mod 2^256)
        assert!(I256::MAX.wrapping_add(&I256::MAX).eq(&I256::from_i32(-2)));
    }

    #[test]
    fn matches_native_i128_in_range() {
        let vals = [
            0i128,
            1,
            -1,
            100,
            -100,
            i64::MAX as i128,
            i64::MIN as i128,
            i128::MAX,
            i128::MIN,
        ];
        for &a in &vals {
            for &b in &vals {
                let ai = I256::from_i128(a);
                let bi = I256::from_i128(b);
                let got = ai.wrapping_add(&bi);
                if let Some(sum) = a.checked_add(b) {
                    assert_eq!(
                        got.try_to_i128().unwrap(),
                        sum,
                        "({}) + ({}) mismatch",
                        a,
                        b
                    );
                } else {
                    // Native i128 overflowed; I256 has more room.
                    // The round-trip via wrapping_sub must still recover both operands.
                    assert!(got.wrapping_sub(&bi).eq(&ai));
                    assert!(got.wrapping_sub(&ai).eq(&bi));
                }
            }
        }
    }

    #[test]
    fn commutativity_brute_force() {
        for a in signed_test_values() {
            for b in signed_test_values() {
                assert!(
                    a.wrapping_add(&b).eq(&b.wrapping_add(&a)),
                    "commutativity failed"
                );
            }
        }
    }

    #[test]
    fn associativity_brute_force() {
        // (a+b)+c == a+(b+c). Always holds under wrapping (mod 2^256 is associative).
        let vals = signed_test_values();
        for a in &vals {
            for b in &vals {
                for c in &vals {
                    let lhs = a.wrapping_add(b).wrapping_add(c);
                    let rhs = a.wrapping_add(&b.wrapping_add(c));
                    assert!(lhs.eq(&rhs), "associativity failed");
                }
            }
        }
    }
}

// ---------- mod wrapping_sub_harsh ----------

mod wrapping_sub_harsh {
    use super::*;

    #[test]
    fn self_minus_self_is_zero() {
        for a in signed_test_values() {
            assert!(a.wrapping_sub(&a).eq(&I256::ZERO));
        }
    }

    #[test]
    fn zero_identity() {
        for a in signed_test_values() {
            assert!(a.wrapping_sub(&I256::ZERO).eq(&a));
        }
    }

    #[test]
    fn zero_minus_one_is_minus_one() {
        assert!(I256::ZERO.wrapping_sub(&I256::ONE).eq(&I256::MINUS_ONE));
    }

    #[test]
    fn min_minus_one_wraps_to_max() {
        assert!(I256::MIN.wrapping_sub(&I256::ONE).eq(&I256::MAX));
    }

    #[test]
    fn max_minus_minus_one_wraps_to_min() {
        assert!(I256::MAX.wrapping_sub(&I256::MINUS_ONE).eq(&I256::MIN));
    }

    #[test]
    fn min_minus_min_is_zero() {
        assert!(I256::MIN.wrapping_sub(&I256::MIN).eq(&I256::ZERO));
    }

    #[test]
    fn anti_commutative_via_negation() {
        // a − b == −(b − a)
        for a in signed_test_values() {
            for b in signed_test_values() {
                let ab = a.wrapping_sub(&b);
                let ba = b.wrapping_sub(&a);
                assert!(ab.eq(&wrapping_neg(&ba)));
            }
        }
    }

    #[test]
    fn via_add_neg_identity() {
        // a − b == a + (−b). Two routes that must coincide.
        for a in signed_test_values() {
            for b in signed_test_values() {
                let via_sub = a.wrapping_sub(&b);
                let via_add_neg = a.wrapping_add(&wrapping_neg(&b));
                assert!(via_sub.eq(&via_add_neg));
            }
        }
    }

    #[test]
    fn matches_native_i128_in_range() {
        let vals = [
            0i128,
            1,
            -1,
            100,
            -100,
            i64::MAX as i128,
            i64::MIN as i128,
            i128::MAX,
            i128::MIN,
        ];
        for &a in &vals {
            for &b in &vals {
                let ai = I256::from_i128(a);
                let bi = I256::from_i128(b);
                let got = ai.wrapping_sub(&bi);
                if let Some(diff) = a.checked_sub(b) {
                    assert_eq!(got.try_to_i128().unwrap(), diff);
                } else {
                    // Round-trip recovery
                    assert!(got.wrapping_add(&bi).eq(&ai));
                }
            }
        }
    }
}

// ---------- mod wrapping_mul_harsh ----------

mod wrapping_mul_harsh {
    use super::*;

    #[test]
    fn zero_annihilates() {
        for a in signed_test_values() {
            assert!(a.wrapping_mul(&I256::ZERO).eq(&I256::ZERO));
            assert!(I256::ZERO.wrapping_mul(&a).eq(&I256::ZERO));
        }
    }

    #[test]
    fn identity_with_one() {
        for a in signed_test_values() {
            assert!(a.wrapping_mul(&I256::ONE).eq(&a));
            assert!(I256::ONE.wrapping_mul(&a).eq(&a));
        }
    }

    #[test]
    fn mul_by_minus_one_negates() {
        // Includes the MIN trap: MIN · (−1) wraps to MIN (because −MIN doesn't fit).
        for a in signed_test_values() {
            let expected = wrapping_neg(&a);
            let got = a.wrapping_mul(&I256::MINUS_ONE);
            assert!(got.eq(&expected), "a · (−1) != −a");
        }
    }

    #[test]
    fn min_times_minus_one_wraps_to_min() {
        // Famous overflow case
        assert!(I256::MIN.wrapping_mul(&I256::MINUS_ONE).eq(&I256::MIN));
    }

    #[test]
    fn two_negatives_make_positive() {
        let positives = [
            I256::from_i32(1),
            I256::from_i32(100),
            I256::from_i32(0xCAFE),
            I256::from_i64(0xDEAD_BEEF),
        ];
        for x in &positives {
            for y in &positives {
                let neg_x = wrapping_neg(x);
                let neg_y = wrapping_neg(y);
                assert!(neg_x.wrapping_mul(&neg_y).eq(&x.wrapping_mul(y)));
            }
        }
    }

    #[test]
    fn squaring_negative_equals_squaring_positive() {
        // (−x) · (−x) == x · x for every x. MIN is special because −MIN = MIN,
        // so squaring it gives the same bit-pattern in both directions trivially.
        for a in signed_test_values() {
            let neg_a = wrapping_neg(&a);
            assert!(neg_a.wrapping_mul(&neg_a).eq(&a.wrapping_mul(&a)));
        }
    }

    #[test]
    fn powers_of_two_match_shl() {
        // a · 2^k == a << k (bit-level identical in modular arithmetic).
        let shifts = [0u32, 1, 32, 63, 64, 100, 127, 200, 254, 255];
        for a in signed_test_values() {
            for &k in &shifts {
                let pow2 = I256::ONE.shl(k);
                let via_mul = a.wrapping_mul(&pow2);
                let via_shl = a.shl(k);
                assert!(via_mul.eq(&via_shl), "mul by 2^{} != shl({})", k, k);
            }
        }
    }

    #[test]
    fn matches_native_i64_in_range() {
        let vals = [-100i64, -10, -1, 0, 1, 10, 100, i32::MAX as i64, i32::MIN as i64];
        for &a in &vals {
            for &b in &vals {
                if let Some(prod) = a.checked_mul(b) {
                    let ai = I256::from_i64(a);
                    let bi = I256::from_i64(b);
                    assert_eq!(
                        ai.wrapping_mul(&bi).try_to_i64().unwrap(),
                        prod,
                        "({}) * ({}) mismatch",
                        a,
                        b
                    );
                }
            }
        }
    }

    #[test]
    fn wrapping_matches_native_i128_wrapping() {
        // I256·I256 of i128-valued operands must agree with i128::wrapping_mul
        // on the low 128 bits.
        let vals = [
            0i128,
            1,
            -1,
            100,
            -100,
            i64::MAX as i128,
            i64::MIN as i128,
            i128::MAX,
            i128::MIN,
        ];
        for &a in &vals {
            for &b in &vals {
                let ai = I256::from_i128(a);
                let bi = I256::from_i128(b);
                let expected_low = a.wrapping_mul(b);
                let got = ai.wrapping_mul(&bi);
                if let Ok(got_i128) = got.try_to_i128() {
                    assert_eq!(got_i128, expected_low);
                } else {
                    // Result doesn't fit in i128, but the low 128 bits must still match.
                    let got_low_u128 = ((got.bits.items[1] as u128) << 64)
                        | (got.bits.items[0] as u128);
                    assert_eq!(got_low_u128 as i128, expected_low);
                }
            }
        }
    }

    #[test]
    fn commutativity_brute_force() {
        for a in signed_test_values() {
            for b in signed_test_values() {
                assert!(a.wrapping_mul(&b).eq(&b.wrapping_mul(&a)));
            }
        }
    }

    #[test]
    fn distributes_over_add_brute_force() {
        // a · (b + c) == a·b + a·c, exact under wrapping (Z/2^256 is a commutative ring).
        let vals = signed_test_values();
        for a in &vals {
            for b in &vals {
                for c in &vals {
                    let lhs = a.wrapping_mul(&b.wrapping_add(c));
                    let rhs = a.wrapping_mul(b).wrapping_add(&a.wrapping_mul(c));
                    assert!(lhs.eq(&rhs), "distributivity failed");
                }
            }
        }
    }
}

// ---------- mod wrapping_div_harsh ----------

mod wrapping_div_harsh {
    use super::*;

    #[test]
    fn by_zero_returns_error() {
        for a in signed_test_values() {
            let res = a.wrapping_div(&I256::ZERO);
            assert!(matches!(res, Err(SoulMathError::CantBeDividedByZero)));
        }
    }

    #[test]
    fn zero_by_any_is_zero_zero() {
        for b in signed_test_values() {
            if b.is_zero() {
                continue;
            }
            let (q, r) = I256::ZERO.wrapping_div(&b).unwrap();
            assert!(q.is_zero());
            assert!(r.is_zero());
        }
    }

    #[test]
    fn by_one_is_self_zero() {
        for a in signed_test_values() {
            let (q, r) = a.wrapping_div(&I256::ONE).unwrap();
            assert!(q.eq(&a));
            assert!(r.is_zero());
        }
    }

    #[test]
    fn by_minus_one_negates() {
        // For a ≠ MIN, a / −1 == −a. For a == MIN, wraps to MIN (overflow).
        for a in signed_test_values() {
            let (q, r) = a.wrapping_div(&I256::MINUS_ONE).unwrap();
            assert!(q.eq(&wrapping_neg(&a)), "a / −1 != −a");
            assert!(r.is_zero());
        }
    }

    #[test]
    fn self_by_self_is_one_zero() {
        for a in signed_test_values() {
            if a.is_zero() {
                continue;
            }
            let (q, r) = a.wrapping_div(&a).unwrap();
            assert!(q.eq(&I256::ONE), "a / a should be 1");
            assert!(r.is_zero());
        }
    }

    #[test]
    fn min_by_minus_one_wraps_to_min() {
        let (q, r) = I256::MIN.wrapping_div(&I256::MINUS_ONE).unwrap();
        assert!(q.eq(&I256::MIN));
        assert!(r.is_zero());
    }

    #[test]
    fn remainder_sign_matches_dividend() {
        // Truncation-toward-zero convention: sign(r) == sign(a), or r == 0.
        let vals = signed_test_values();
        for a in &vals {
            for b in &vals {
                if b.is_zero() {
                    continue;
                }
                let (_, r) = a.wrapping_div(b).unwrap();
                if r.is_zero() {
                    continue;
                }
                assert_eq!(
                    r.is_negative(),
                    a.is_negative(),
                    "remainder sign should match dividend's sign"
                );
            }
        }
    }

    #[test]
    fn remainder_magnitude_strictly_less_than_divisor() {
        let vals = signed_test_values();
        for a in &vals {
            for b in &vals {
                if b.is_zero() {
                    continue;
                }
                let (_, r) = a.wrapping_div(b).unwrap();
                let mag_r = unsigned_magnitude(&r);
                let mag_b = unsigned_magnitude(b);
                assert!(mag_r.lt(&mag_b), "|r| should be strictly less than |b|");
            }
        }
    }

    #[test]
    fn quotient_remainder_identity_brute_force() {
        // q · b + r == a (exact under wrapping, even when q · b would overflow).
        let vals = signed_test_values();
        for a in &vals {
            for b in &vals {
                if b.is_zero() {
                    continue;
                }
                let (q, r) = a.wrapping_div(b).unwrap();
                let recomputed = q.wrapping_mul(b).wrapping_add(&r);
                assert!(recomputed.eq(a), "q · b + r != a");
            }
        }
    }

    #[test]
    fn matches_native_i64_all_sign_combos() {
        let nums = [-100i64, -10, -5, -1, 0, 1, 5, 10, 100];
        let dens = [-7i64, -3, -1, 1, 3, 7];
        for &n in &nums {
            for &d in &dens {
                let (q, r) = I256::from_i64(n)
                    .wrapping_div(&I256::from_i64(d))
                    .unwrap();
                assert_eq!(
                    q.try_to_i64().unwrap(),
                    n / d,
                    "{} / {} quotient mismatch",
                    n,
                    d
                );
                assert_eq!(
                    r.try_to_i64().unwrap(),
                    n % d,
                    "{} % {} remainder mismatch",
                    n,
                    d
                );
            }
        }
    }
}

// ---------- mod two_complement_identities ----------

mod two_complement_identities {
    use super::*;

    #[test]
    fn inverse_via_not_plus_one_matches_zero_minus_x() {
        // Two computations of −x must agree: (!x + 1) and (0 − x).
        for a in signed_test_values() {
            let via_not = a.not().wrapping_add(&I256::ONE);
            let via_sub = I256::ZERO.wrapping_sub(&a);
            assert!(via_not.eq(&via_sub), "!a + 1 != 0 − a");
        }
    }

    #[test]
    fn not_x_equals_neg_x_minus_one() {
        // !x == −x − 1 (rearranged: −x = !x + 1).
        for a in signed_test_values() {
            let lhs = a.not();
            let rhs = wrapping_neg(&a).wrapping_sub(&I256::ONE);
            assert!(lhs.eq(&rhs));
        }
    }

    #[test]
    fn negate_round_trip() {
        // −(−x) == x. Holds even for MIN, where each step independently wraps.
        for a in signed_test_values() {
            let double_neg = wrapping_neg(&wrapping_neg(&a));
            assert!(double_neg.eq(&a));
        }
    }

    #[test]
    fn negate_distributes_over_add() {
        // −(a + b) == (−a) + (−b)
        for a in signed_test_values() {
            for b in signed_test_values() {
                let lhs = wrapping_neg(&a.wrapping_add(&b));
                let rhs = wrapping_neg(&a).wrapping_add(&wrapping_neg(&b));
                assert!(lhs.eq(&rhs));
            }
        }
    }

    #[test]
    fn one_shifted_to_top_is_min() {
        assert!(I256::ONE.shl(255).eq(&I256::MIN));
    }

    #[test]
    fn cyclic_predecessor_of_zero_is_minus_one() {
        assert!(I256::ZERO.wrapping_sub(&I256::ONE).eq(&I256::MINUS_ONE));
    }

    #[test]
    fn cyclic_successor_of_max_is_min() {
        assert!(I256::MAX.wrapping_add(&I256::ONE).eq(&I256::MIN));
    }

    #[test]
    fn signum_consistent_with_predicates() {
        for a in signed_test_values() {
            let s = a.signum();
            if a.is_positive() {
                assert!(s.eq(&I256::ONE));
            } else if a.is_negative() {
                assert!(s.eq(&I256::MINUS_ONE));
            } else {
                assert!(s.eq(&I256::ZERO));
            }
        }
    }
}

// ---------- mod property_battery ----------

mod property_battery {
    use super::*;
    use std::cmp::Ordering;

    #[test]
    fn add_sub_inverse_brute_force() {
        // (a + b) − b == a and (a − b) + b == a, always (wrapping is exact).
        let vals = signed_test_values();
        for a in &vals {
            for b in &vals {
                assert!(a.wrapping_add(b).wrapping_sub(b).eq(a));
                assert!(a.wrapping_sub(b).wrapping_add(b).eq(a));
            }
        }
    }

    #[test]
    fn mul_div_inverse_when_no_overflow() {
        // For values whose i128 product fits in I256 (always true for i64×i64),
        // (a · b) / b must equal a exactly.
        let vals = [
            -100i64,
            -10,
            -1,
            1,
            10,
            100,
            i32::MAX as i64,
            i32::MIN as i64,
        ];
        for &a in &vals {
            for &b in &vals {
                let prod_i128 = (a as i128) * (b as i128); // never overflows i128
                let ai = I256::from_i64(a);
                let bi = I256::from_i64(b);
                let prod = ai.wrapping_mul(&bi);
                // Cross-check: I256's mul matches i128's true product
                assert_eq!(
                    prod.try_to_i128().unwrap(),
                    prod_i128,
                    "{} * {} product mismatch",
                    a,
                    b
                );
                let (q, r) = prod.wrapping_div(&bi).unwrap();
                assert!(q.eq(&ai), "(a · b) / b != a");
                assert!(r.is_zero(), "(a · b) mod b != 0");
            }
        }
    }

    #[test]
    fn div_identity_brute_force() {
        // For every (a, b) with b != 0: q · b + r == a, AND |r| < |b|.
        let vals = signed_test_values();
        for a in &vals {
            for b in &vals {
                if b.is_zero() {
                    continue;
                }
                let (q, r) = a.wrapping_div(b).unwrap();
                let recomputed = q.wrapping_mul(b).wrapping_add(&r);
                assert!(recomputed.eq(a), "q · b + r != a");
                assert!(
                    unsigned_magnitude(&r).lt(&unsigned_magnitude(b)),
                    "|r| should be < |b|"
                );
            }
        }
    }

    #[test]
    fn cmp_total_order_brute_force() {
        let vals = signed_test_values();
        for a in &vals {
            for b in &vals {
                let ord = a.cmp(b);
                let lt = a.lt(b);
                let eq = a.eq(b);
                let gt = a.gt(b);
                // Trichotomy: exactly one of <, ==, > is true.
                let count = lt as u8 + eq as u8 + gt as u8;
                assert_eq!(count, 1, "trichotomy violated");
                // cmp consistent with the boolean predicates.
                match ord {
                    Ordering::Less => assert!(lt && !eq && !gt),
                    Ordering::Equal => assert!(!lt && eq && !gt),
                    Ordering::Greater => assert!(!lt && !eq && gt),
                }
                // a.cmp(b) is the reverse of b.cmp(a).
                assert_eq!(ord, b.cmp(a).reverse());
                // le == lt | eq; ge == gt | eq.
                assert_eq!(a.le(b), lt || eq);
                assert_eq!(a.ge(b), gt || eq);
            }
        }
    }

    #[test]
    fn cmp_transitivity_brute_force() {
        let vals = signed_test_values();
        for a in &vals {
            for b in &vals {
                for c in &vals {
                    if a.lt(b) && b.lt(c) {
                        assert!(a.lt(c), "lt not transitive");
                    }
                    if a.gt(b) && b.gt(c) {
                        assert!(a.gt(c), "gt not transitive");
                    }
                }
            }
        }
    }
}
