use rusted_soul_dex::math::errors::SoulMathError;
use rusted_soul_dex::math::i256::I256;

// ---------- shared helpers ----------

/// Same 20-value battery used by `i256_harsh_test.rs`. Covers zero, ±1, ±2, ±100,
/// i32/i64/i128 boundaries, 2^127/2^200/2^254, MAX, MIN, and asymmetric patterns.
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

/// 15 native i128 values for cross-oracle tests. All fit in I256 trivially.
fn i128_test_values() -> [i128; 15] {
    [
        0,
        1,
        -1,
        100,
        -100,
        i32::MAX as i128,
        i32::MIN as i128,
        i64::MAX as i128,
        i64::MIN as i128,
        i128::MAX,
        i128::MIN,
        i128::MAX - 1,
        i128::MIN + 1,
        0xDEAD_BEEF,
        -0xDEAD_BEEF,
    ]
}

/// Two's-complement negation. No `wrapping_neg` method on I256, so inline.
fn wrapping_neg(x: &I256) -> I256 {
    x.not().wrapping_add(&I256::ONE)
}

// ---------- mod checked_add_harsh ----------

mod checked_add_harsh {
    use super::*;

    #[test]
    fn zero_identity_in_both_directions() {
        for a in signed_test_values() {
            assert!(a.checked_add(&I256::ZERO).unwrap().eq(&a));
            assert!(I256::ZERO.checked_add(&a).unwrap().eq(&a));
        }
    }

    #[test]
    fn add_mixed_signs_never_overflows() {
        for a in signed_test_values() {
            for b in signed_test_values() {
                if (a.is_positive() && b.is_negative()) || (a.is_negative() && b.is_positive()) {
                    assert!(
                        a.checked_add(&b).is_ok(),
                        "mixed-sign add must never overflow"
                    );
                }
            }
        }
    }

    #[test]
    fn boundary_just_fits() {
        // (MAX − 1) + 1 == MAX
        let max_minus_one = I256::MAX.wrapping_sub(&I256::ONE);
        assert!(max_minus_one.checked_add(&I256::ONE).unwrap().eq(&I256::MAX));
        // (MIN + 1) + (−1) == MIN
        let min_plus_one = I256::MIN.wrapping_add(&I256::ONE);
        assert!(min_plus_one.checked_add(&I256::MINUS_ONE).unwrap().eq(&I256::MIN));
        // ±boundary + 0 = self
        assert!(I256::MAX.checked_add(&I256::ZERO).unwrap().eq(&I256::MAX));
        assert!(I256::MIN.checked_add(&I256::ZERO).unwrap().eq(&I256::MIN));
    }

    #[test]
    fn pos_pos_overflow_targeted() {
        assert!(matches!(
            I256::MAX.checked_add(&I256::ONE),
            Err(SoulMathError::AddOverflow)
        ));
        assert!(matches!(
            I256::MAX.checked_add(&I256::MAX),
            Err(SoulMathError::AddOverflow)
        ));
        assert!(matches!(
            I256::MAX.checked_add(&I256::from_i32(2)),
            Err(SoulMathError::AddOverflow)
        ));
        // 2^254 + 2^254 = 2^255 (= MIN signed, just over MAX positive)
        let two_to_254 = I256::ONE.shl(254);
        assert!(matches!(
            two_to_254.checked_add(&two_to_254),
            Err(SoulMathError::AddOverflow)
        ));
    }

    #[test]
    fn neg_neg_underflow_targeted() {
        assert!(matches!(
            I256::MIN.checked_add(&I256::MINUS_ONE),
            Err(SoulMathError::AddOverflow)
        ));
        assert!(matches!(
            I256::MIN.checked_add(&I256::MIN),
            Err(SoulMathError::AddOverflow)
        ));
        assert!(matches!(
            I256::MIN.checked_add(&I256::from_i32(-2)),
            Err(SoulMathError::AddOverflow)
        ));
        // −2^254 + (−2^254 − 1) — barely below MIN
        let two_to_254 = I256::ONE.shl(254);
        let neg_two_to_254 = wrapping_neg(&two_to_254);
        let neg_2_254_minus_1 = neg_two_to_254.wrapping_sub(&I256::ONE);
        assert!(matches!(
            neg_two_to_254.checked_add(&neg_2_254_minus_1),
            Err(SoulMathError::AddOverflow)
        ));
    }

    #[test]
    fn consistent_with_i128_when_in_range() {
        for &a in &i128_test_values() {
            for &b in &i128_test_values() {
                let ai = I256::from_i128(a);
                let bi = I256::from_i128(b);
                let got = ai.checked_add(&bi);
                match a.checked_add(b) {
                    Some(sum) => {
                        let g = got.expect("native succeeded; I256 must succeed (no false-Err)");
                        assert_eq!(
                            g.try_to_i128().unwrap(),
                            sum,
                            "({}) + ({}) value mismatch",
                            a,
                            b
                        );
                    }
                    None => {
                        // Native overflowed. I256 may still succeed (more range).
                        // If it does, verify round-trip via checked_sub.
                        if let Ok(s) = got {
                            assert!(
                                s.checked_sub(&bi).unwrap().eq(&ai),
                                "i128 overflowed; I256 round-trip via sub failed"
                            );
                        }
                    }
                }
            }
        }
    }
}

// ---------- mod checked_sub_harsh ----------

mod checked_sub_harsh {
    use super::*;

    #[test]
    fn zero_identity() {
        for a in signed_test_values() {
            assert!(a.checked_sub(&I256::ZERO).unwrap().eq(&a));
        }
    }

    #[test]
    fn self_minus_self_is_zero() {
        for a in signed_test_values() {
            assert!(
                a.checked_sub(&a).unwrap().is_zero(),
                "a − a must be 0 for every battery value (incl. MIN)"
            );
        }
    }

    #[test]
    fn sub_same_signs_never_overflows() {
        for a in signed_test_values() {
            for b in signed_test_values() {
                let same_signs = (a.is_negative() && b.is_negative())
                    || (a.is_positive() && b.is_positive());
                if same_signs {
                    assert!(
                        a.checked_sub(&b).is_ok(),
                        "same-sign sub must never overflow"
                    );
                }
            }
        }
    }

    #[test]
    fn boundary_just_fits() {
        assert!(I256::MIN.checked_sub(&I256::ZERO).unwrap().eq(&I256::MIN));
        assert!(I256::MAX.checked_sub(&I256::ZERO).unwrap().eq(&I256::MAX));
        assert!(I256::MAX.checked_sub(&I256::MAX).unwrap().is_zero());
        // MIN − (−1) == MIN + 1 (fits)
        let expected = I256::MIN.wrapping_add(&I256::ONE);
        assert!(I256::MIN.checked_sub(&I256::MINUS_ONE).unwrap().eq(&expected));
    }

    #[test]
    fn pos_minus_neg_overflow_targeted() {
        assert!(matches!(
            I256::MAX.checked_sub(&I256::MINUS_ONE),
            Err(SoulMathError::SubUnderflow)
        ));
        assert!(matches!(
            I256::MAX.checked_sub(&I256::MIN),
            Err(SoulMathError::SubUnderflow)
        ));
        // 0 − MIN = +2^255, doesn't fit
        assert!(matches!(
            I256::ZERO.checked_sub(&I256::MIN),
            Err(SoulMathError::SubUnderflow)
        ));
        // 1 − MIN = +2^255 + 1, doesn't fit
        assert!(matches!(
            I256::ONE.checked_sub(&I256::MIN),
            Err(SoulMathError::SubUnderflow)
        ));
    }

    #[test]
    fn neg_minus_pos_underflow_targeted() {
        assert!(matches!(
            I256::MIN.checked_sub(&I256::ONE),
            Err(SoulMathError::SubUnderflow)
        ));
        assert!(matches!(
            I256::MIN.checked_sub(&I256::MAX),
            Err(SoulMathError::SubUnderflow)
        ));
        // −1 − MAX == −2^255 (= MIN, just fits, must NOT overflow)
        assert!(I256::MINUS_ONE.checked_sub(&I256::MAX).unwrap().eq(&I256::MIN));
        // −2 − MAX == −2^255 − 1, one below MIN, MUST overflow
        assert!(matches!(
            I256::from_i32(-2).checked_sub(&I256::MAX),
            Err(SoulMathError::SubUnderflow)
        ));
    }

    #[test]
    fn consistent_with_i128_when_in_range() {
        for &a in &i128_test_values() {
            for &b in &i128_test_values() {
                let ai = I256::from_i128(a);
                let bi = I256::from_i128(b);
                let got = ai.checked_sub(&bi);
                match a.checked_sub(b) {
                    Some(diff) => {
                        let g = got.expect("native succeeded; I256 must succeed");
                        assert_eq!(g.try_to_i128().unwrap(), diff);
                    }
                    None => {
                        if let Ok(d) = got {
                            assert!(d.checked_add(&bi).unwrap().eq(&ai));
                        }
                    }
                }
            }
        }
    }
}

// ---------- mod checked_mul_harsh ----------

mod checked_mul_harsh {
    use super::*;

    #[test]
    fn zero_annihilates_in_both_directions() {
        for a in signed_test_values() {
            assert!(a.checked_mul(&I256::ZERO).unwrap().is_zero());
            assert!(I256::ZERO.checked_mul(&a).unwrap().is_zero());
        }
    }

    #[test]
    fn one_is_identity() {
        for a in signed_test_values() {
            assert!(a.checked_mul(&I256::ONE).unwrap().eq(&a));
            assert!(I256::ONE.checked_mul(&a).unwrap().eq(&a));
        }
    }

    #[test]
    fn minus_one_negates_except_min() {
        for a in signed_test_values() {
            if a.eq(&I256::MIN) {
                // MIN × −1 must overflow
                assert!(matches!(
                    a.checked_mul(&I256::MINUS_ONE),
                    Err(SoulMathError::MulOverflow)
                ));
                continue;
            }
            let got = a.checked_mul(&I256::MINUS_ONE).unwrap();
            assert!(got.eq(&wrapping_neg(&a)));
        }
    }

    #[test]
    fn max_times_minus_one_is_min_plus_one() {
        let expected = I256::MIN.wrapping_add(&I256::ONE);
        assert!(I256::MAX.checked_mul(&I256::MINUS_ONE).unwrap().eq(&expected));
        assert!(I256::MINUS_ONE.checked_mul(&I256::MAX).unwrap().eq(&expected));
    }

    #[test]
    fn boundary_at_min_magnitude() {
        // 1 × MIN = MIN (negative magnitude exactly 2^255)
        assert!(I256::ONE.checked_mul(&I256::MIN).unwrap().eq(&I256::MIN));
        assert!(I256::MIN.checked_mul(&I256::ONE).unwrap().eq(&I256::MIN));
    }

    #[test]
    fn min_times_minus_one_overflows() {
        assert!(matches!(
            I256::MIN.checked_mul(&I256::MINUS_ONE),
            Err(SoulMathError::MulOverflow)
        ));
        assert!(matches!(
            I256::MINUS_ONE.checked_mul(&I256::MIN),
            Err(SoulMathError::MulOverflow)
        ));
    }

    #[test]
    fn max_times_max_overflows() {
        assert!(matches!(
            I256::MAX.checked_mul(&I256::MAX),
            Err(SoulMathError::MulOverflow)
        ));
    }

    #[test]
    fn min_times_min_overflows() {
        assert!(matches!(
            I256::MIN.checked_mul(&I256::MIN),
            Err(SoulMathError::MulOverflow)
        ));
    }

    #[test]
    fn max_times_min_overflows() {
        assert!(matches!(
            I256::MAX.checked_mul(&I256::MIN),
            Err(SoulMathError::MulOverflow)
        ));
        assert!(matches!(
            I256::MIN.checked_mul(&I256::MAX),
            Err(SoulMathError::MulOverflow)
        ));
    }

    #[test]
    fn max_times_two_overflows() {
        // MAX × 2 = 2^256 − 2, fits in U256 but exceeds MAX → narrow positive overflow
        assert!(matches!(
            I256::MAX.checked_mul(&I256::from_i32(2)),
            Err(SoulMathError::MulOverflow)
        ));
    }

    #[test]
    fn min_times_two_overflows() {
        // MIN × 2 = −2^256, U256 magnitude product = 2^256 which doesn't fit U256 → caught at U256 gate
        assert!(matches!(
            I256::MIN.checked_mul(&I256::from_i32(2)),
            Err(SoulMathError::MulOverflow)
        ));
    }

    #[test]
    fn narrow_positive_overflow_2_254_plus_1_times_2() {
        // (2^254 + 1) × 2 = 2^255 + 2 > MAX = 2^255 − 1
        let pos = I256::ONE.shl(254).wrapping_add(&I256::ONE);
        assert!(matches!(
            pos.checked_mul(&I256::from_i32(2)),
            Err(SoulMathError::MulOverflow)
        ));
        assert!(matches!(
            I256::from_i32(2).checked_mul(&pos),
            Err(SoulMathError::MulOverflow)
        ));
    }

    #[test]
    fn narrow_negative_overflow_2_times_neg_2_254_plus_1() {
        // 2 × −(2^254 + 1) = −(2^255 + 2) < MIN = −2^255  (the regression case)
        let pos = I256::ONE.shl(254).wrapping_add(&I256::ONE);
        let neg = wrapping_neg(&pos);
        assert!(matches!(
            I256::from_i32(2).checked_mul(&neg),
            Err(SoulMathError::MulOverflow)
        ));
        // symmetric form: (−2) × (2^254 + 1)
        assert!(matches!(
            I256::from_i32(-2).checked_mul(&pos),
            Err(SoulMathError::MulOverflow)
        ));
    }

    #[test]
    fn consistent_with_i128_when_in_range() {
        for &a in &i128_test_values() {
            for &b in &i128_test_values() {
                let ai = I256::from_i128(a);
                let bi = I256::from_i128(b);
                let got = ai.checked_mul(&bi);
                match a.checked_mul(b) {
                    Some(prod) => {
                        let g = got.expect("native mul succeeded; I256 must succeed");
                        assert_eq!(
                            g.try_to_i128().unwrap(),
                            prod,
                            "({}) * ({}) value mismatch",
                            a,
                            b
                        );
                    }
                    None => {
                        // Native i128 overflowed. I256 may still succeed (more range).
                        // Verify by dividing the result back if it succeeds.
                        if let Ok(p) = got {
                            if b != 0 {
                                // p / b should equal a (and we know a fits in i128)
                                let (q, r) = p.checked_div(&bi).unwrap();
                                assert!(q.eq(&ai));
                                assert!(r.is_zero());
                            }
                        }
                    }
                }
            }
        }
    }
}

// ---------- mod checked_div_harsh ----------

mod checked_div_harsh {
    use super::*;

    #[test]
    fn zero_dividend_succeeds() {
        // The regression case from earlier development.
        for b in signed_test_values() {
            if b.is_zero() {
                continue;
            }
            let (q, r) = I256::ZERO.checked_div(&b).unwrap();
            assert!(q.is_zero());
            assert!(r.is_zero());
        }
    }

    #[test]
    fn divide_by_one() {
        for a in signed_test_values() {
            let (q, r) = a.checked_div(&I256::ONE).unwrap();
            assert!(q.eq(&a));
            assert!(r.is_zero());
        }
    }

    #[test]
    fn divide_by_minus_one_except_min() {
        for a in signed_test_values() {
            if a.eq(&I256::MIN) {
                continue; // tested separately as overflow
            }
            let (q, r) = a.checked_div(&I256::MINUS_ONE).unwrap();
            assert!(q.eq(&wrapping_neg(&a)), "a / −1 should equal −a");
            assert!(r.is_zero());
        }
    }

    #[test]
    fn self_divided_by_self() {
        for a in signed_test_values() {
            if a.is_zero() {
                continue;
            }
            let (q, r) = a.checked_div(&a).unwrap();
            assert!(q.eq(&I256::ONE), "a / a should be 1");
            assert!(r.is_zero());
        }
    }

    #[test]
    fn mixed_sign_zero_quotient_succeeds() {
        // Regression guard for the bug we found and fixed.
        let cases: [(I256, I256, I256, I256); 4] = [
            (I256::from_i32(3),  I256::from_i32(-5),  I256::ZERO, I256::from_i32(3)),
            (I256::from_i32(-3), I256::from_i32(5),   I256::ZERO, I256::from_i32(-3)),
            (I256::ONE,          I256::MIN,           I256::ZERO, I256::ONE),
            (I256::ONE,          I256::from_i32(-100), I256::ZERO, I256::ONE),
        ];
        for (a, b, expected_q, expected_r) in cases {
            let (q, r) = a.checked_div(&b).expect("should succeed (regression guard)");
            assert!(q.eq(&expected_q));
            assert!(r.eq(&expected_r));
        }
    }

    #[test]
    fn max_by_minus_one_succeeds() {
        let expected = I256::MIN.wrapping_add(&I256::ONE);
        let (q, r) = I256::MAX.checked_div(&I256::MINUS_ONE).unwrap();
        assert!(q.eq(&expected));
        assert!(r.is_zero());
    }

    #[test]
    fn min_by_one_succeeds() {
        let (q, r) = I256::MIN.checked_div(&I256::ONE).unwrap();
        assert!(q.eq(&I256::MIN));
        assert!(r.is_zero());
    }

    #[test]
    fn min_by_minus_one_overflows() {
        assert!(matches!(
            I256::MIN.checked_div(&I256::MINUS_ONE),
            Err(SoulMathError::DivisionOverflow)
        ));
    }

    #[test]
    fn divide_by_zero_returns_correct_error() {
        for a in signed_test_values() {
            assert!(
                matches!(a.checked_div(&I256::ZERO), Err(SoulMathError::CantBeDividedByZero)),
                "a / 0 must return CantBeDividedByZero, not DivisionOverflow"
            );
        }
    }

    #[test]
    fn consistent_with_i64_all_sign_combos() {
        let nums = [-100i64, -10, -5, -1, 0, 1, 5, 10, 100];
        let dens = [-7i64, -3, -1, 1, 3, 7];
        for &n in &nums {
            for &d in &dens {
                let (q, r) = I256::from_i64(n)
                    .checked_div(&I256::from_i64(d))
                    .unwrap();
                assert_eq!(q.try_to_i64().unwrap(), n / d, "{} / {} quotient", n, d);
                assert_eq!(r.try_to_i64().unwrap(), n % d, "{} % {} remainder", n, d);
            }
        }
    }

    #[test]
    fn quotient_remainder_identity_for_battery() {
        // q · b + r == a, exact under wrapping (because the true product fits).
        for a in signed_test_values() {
            for b in signed_test_values() {
                if b.is_zero() {
                    continue;
                }
                let res = a.checked_div(&b);
                if let Ok((q, r)) = res {
                    let recomputed = q.wrapping_mul(&b).wrapping_add(&r);
                    assert!(recomputed.eq(&a), "q · b + r != a");
                }
                // If checked_div errored (MIN / MINUS_ONE), it's the one overflow case.
                if res.is_err() {
                    assert!(a.eq(&I256::MIN) && b.eq(&I256::MINUS_ONE));
                }
            }
        }
    }
}

// ---------- mod cross_native_i128 ----------

mod cross_native_i128 {
    use super::*;

    #[test]
    fn add_matches_i128_oracle() {
        for &a in &i128_test_values() {
            for &b in &i128_test_values() {
                let ai = I256::from_i128(a);
                let bi = I256::from_i128(b);
                let got = ai.checked_add(&bi);
                match (a.checked_add(b), &got) {
                    (Some(sum), Ok(g)) => assert_eq!(g.try_to_i128().unwrap(), sum),
                    (Some(_), Err(_)) => panic!("false-Err: native {} + {} succeeded", a, b),
                    (None, _) => { /* I256 may succeed (bigger range); no constraint */ }
                }
            }
        }
    }

    #[test]
    fn sub_matches_i128_oracle() {
        for &a in &i128_test_values() {
            for &b in &i128_test_values() {
                let ai = I256::from_i128(a);
                let bi = I256::from_i128(b);
                let got = ai.checked_sub(&bi);
                match (a.checked_sub(b), &got) {
                    (Some(diff), Ok(g)) => assert_eq!(g.try_to_i128().unwrap(), diff),
                    (Some(_), Err(_)) => panic!("false-Err: native {} − {} succeeded", a, b),
                    (None, _) => {}
                }
            }
        }
    }

    #[test]
    fn mul_matches_i128_oracle() {
        for &a in &i128_test_values() {
            for &b in &i128_test_values() {
                let ai = I256::from_i128(a);
                let bi = I256::from_i128(b);
                let got = ai.checked_mul(&bi);
                match (a.checked_mul(b), &got) {
                    (Some(prod), Ok(g)) => assert_eq!(g.try_to_i128().unwrap(), prod),
                    (Some(_), Err(_)) => panic!("false-Err: native {} × {} succeeded", a, b),
                    (None, _) => {}
                }
            }
        }
    }

    #[test]
    fn div_matches_i128_oracle() {
        for &a in &i128_test_values() {
            for &b in &i128_test_values() {
                let ai = I256::from_i128(a);
                let bi = I256::from_i128(b);
                let got = ai.checked_div(&bi);
                let native = a.checked_div(b);
                match (native, &got) {
                    (Some(q_native), Ok((q, r))) => {
                        assert_eq!(q.try_to_i128().unwrap(), q_native);
                        assert_eq!(r.try_to_i128().unwrap(), a % b);
                    }
                    (Some(_), Err(_)) => panic!("false-Err: native {} / {} succeeded", a, b),
                    (None, Err(_)) => {
                        // both fail — expected for /0
                        assert_eq!(b, 0, "If native fails but b ≠ 0, this is i128::MIN/−1 which I256 should handle");
                    }
                    (None, Ok((q, _))) => {
                        // Native overflowed (i128::MIN / -1), but I256 has range.
                        // Verify: q = -(i128::MIN as I256) = +2^127
                        assert!(a == i128::MIN && b == -1, "Unexpected I256-only success: {} / {}", a, b);
                        let expected_q = wrapping_neg(&I256::from_i128(i128::MIN));
                        assert!(q.eq(&expected_q));
                    }
                }
            }
        }
    }
}

// ---------- mod inverse_properties ----------

mod inverse_properties {
    use super::*;

    #[test]
    fn checked_add_then_sub_recovers_operand() {
        for a in signed_test_values() {
            for b in signed_test_values() {
                if let Ok(sum) = a.checked_add(&b) {
                    // sum − b should equal a; sum − a should equal b.
                    // These subs might overflow (e.g., MAX − (very negative b)), so use wrapping
                    // for the round-trip verification — modular identity holds.
                    assert!(sum.wrapping_sub(&b).eq(&a));
                    assert!(sum.wrapping_sub(&a).eq(&b));
                }
            }
        }
    }

    #[test]
    fn checked_sub_then_add_recovers_operand() {
        for a in signed_test_values() {
            for b in signed_test_values() {
                if let Ok(diff) = a.checked_sub(&b) {
                    assert!(diff.wrapping_add(&b).eq(&a));
                }
            }
        }
    }

    #[test]
    fn checked_mul_then_div_recovers_operand() {
        for a in signed_test_values() {
            for b in signed_test_values() {
                if b.is_zero() {
                    continue;
                }
                if let Ok(prod) = a.checked_mul(&b) {
                    // prod / b must succeed and give (a, 0).
                    let (q, r) = prod
                        .checked_div(&b)
                        .expect("mul succeeded → div by b must succeed");
                    assert!(q.eq(&a), "(a · b) / b should equal a");
                    assert!(r.is_zero());
                }
            }
        }
    }

    #[test]
    fn checked_div_identity() {
        // For successful div: q · b + r == a (using wrapping for the reconstruction).
        for a in signed_test_values() {
            for b in signed_test_values() {
                if b.is_zero() {
                    continue;
                }
                if let Ok((q, r)) = a.checked_div(&b) {
                    let recomputed = q.wrapping_mul(&b).wrapping_add(&r);
                    assert!(recomputed.eq(&a));
                }
            }
        }
    }
}

// ---------- mod wrapping_checked_consistency ----------

mod wrapping_checked_consistency {
    use super::*;

    #[test]
    fn checked_equals_wrapping_when_succeeds_add() {
        for a in signed_test_values() {
            for b in signed_test_values() {
                if let Ok(v) = a.checked_add(&b) {
                    assert!(v.eq(&a.wrapping_add(&b)));
                }
            }
        }
    }

    #[test]
    fn checked_equals_wrapping_when_succeeds_sub() {
        for a in signed_test_values() {
            for b in signed_test_values() {
                if let Ok(v) = a.checked_sub(&b) {
                    assert!(v.eq(&a.wrapping_sub(&b)));
                }
            }
        }
    }

    #[test]
    fn checked_equals_wrapping_when_succeeds_mul() {
        for a in signed_test_values() {
            for b in signed_test_values() {
                if let Ok(v) = a.checked_mul(&b) {
                    assert!(v.eq(&a.wrapping_mul(&b)));
                }
            }
        }
    }

    #[test]
    fn checked_equals_wrapping_when_succeeds_div() {
        for a in signed_test_values() {
            for b in signed_test_values() {
                if b.is_zero() {
                    continue;
                }
                if let Ok((q, r)) = a.checked_div(&b) {
                    let (wq, wr) = a.wrapping_div(&b).unwrap();
                    assert!(q.eq(&wq));
                    assert!(r.eq(&wr));
                }
            }
        }
    }

    #[test]
    fn wrapping_diverges_from_checked_for_known_overflow_cases() {
        // MAX + 1: wrapping → MIN, checked → Err
        assert!(I256::MAX.wrapping_add(&I256::ONE).eq(&I256::MIN));
        assert!(I256::MAX.checked_add(&I256::ONE).is_err());

        // MIN − 1: wrapping → MAX, checked → Err
        assert!(I256::MIN.wrapping_sub(&I256::ONE).eq(&I256::MAX));
        assert!(I256::MIN.checked_sub(&I256::ONE).is_err());

        // MIN × −1: wrapping → MIN (the trap), checked → Err
        assert!(I256::MIN.wrapping_mul(&I256::MINUS_ONE).eq(&I256::MIN));
        assert!(I256::MIN.checked_mul(&I256::MINUS_ONE).is_err());

        // MIN / −1: wrapping → (MIN, 0), checked → Err
        let (wq, _) = I256::MIN.wrapping_div(&I256::MINUS_ONE).unwrap();
        assert!(wq.eq(&I256::MIN));
        assert!(I256::MIN.checked_div(&I256::MINUS_ONE).is_err());
    }
}
