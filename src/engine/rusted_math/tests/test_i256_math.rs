use rusted_soul_dex::math::i256::I256;
use std::cmp::Ordering;
use rusted_soul_dex::math::u256::U256;

#[test]
fn cmp_returns_correct_ordering() {
    assert_eq!(I256::from_i32(-5).cmp(&I256::from_i32(3)),  Ordering::Less);
    assert_eq!(I256::from_i32(3).cmp(&I256::from_i32(-5)),  Ordering::Greater);
    assert_eq!(I256::from_i32(7).cmp(&I256::from_i32(7)),   Ordering::Equal);
    assert_eq!(I256::MIN.cmp(&I256::MAX),                    Ordering::Less);
    assert_eq!(I256::MIN.cmp(&I256::MINUS_ONE),              Ordering::Less);
    assert_eq!(I256::ZERO.cmp(&I256::ZERO),                  Ordering::Equal);
}

#[test]
fn wrapping_add_sub_match_native_i64() {
    let vals = [0i64, 1, -1, 100, -100, i32::MAX as i64, i32::MIN as i64,
        i64::MAX, i64::MIN, i64::MAX - 1, i64::MIN + 1];
    for &a in &vals {
        for &b in &vals {
            let ai = I256::from_i64(a);
            let bi = I256::from_i64(b);

            // For values whose sum fits in i64, our wrapping_add should match.
            if let Some(sum) = a.checked_add(b) {
                assert_eq!(ai.wrapping_add(&bi).try_to_i64().unwrap(), sum);
            }
            if let Some(diff) = a.checked_sub(b) {
                assert_eq!(ai.wrapping_sub(&bi).try_to_i64().unwrap(), diff);
            }
        }
    }
}

#[test]
fn wrapping_mul_matches_native_u128_for_small_values() {
    let vals = [0u128, 1, 2, 100, u64::MAX as u128, u128::MAX, 0xDEAD_BEEF];
    for &a in &vals {
        for &b in &vals {
            let ua = U256::new(0, a);
            let ub = U256::new(0, b);
            // Native u128 wrapping mul gives the same low 128 bits as ours.
            let expected_lo = a.wrapping_mul(b);
            let got = ua.wrapping_mul(&ub);
            assert_eq!(got.items[0], expected_lo as u64);
            assert_eq!(got.items[1], (expected_lo >> 64) as u64);
        }
    }
}

#[test]
fn add_sub_inverse() {
    // (a + b) - b == a, (a - b) + b == a — for all values, since wrapping is exact.
    let vals = [I256::ZERO, I256::ONE, I256::MINUS_ONE, I256::MAX, I256::MIN,
        I256::from_i64(12345), I256::from_i64(-67890)];
    for a in &vals {
        for b in &vals {
            assert!(a.wrapping_add(b).wrapping_sub(b).eq(a));
            assert!(a.wrapping_sub(b).wrapping_add(b).eq(a));
        }
    }
}

#[test]
fn boundary_wraps() {
    assert!(I256::MAX.wrapping_add(&I256::ONE).eq(&I256::MIN));
    assert!(I256::MIN.wrapping_sub(&I256::ONE).eq(&I256::MAX));
    assert!(I256::MIN.wrapping_sub(&I256::MIN).eq(&I256::ZERO));
    assert!(I256::MIN.wrapping_add(&I256::MIN).eq(&I256::ZERO));
}


#[test]
fn test_1_display() {
    // let a = I256::from_i128(i128::MIN);

    // let b = I256::from_i128(i128::MAX);

    // let c = a.wrapping_mul(&b);

    // println!("{:0b}", c);

    // let (_a, _r1) = c.wrapping_div(&b).unwrap();
    // let (_b, _r2) = c.wrapping_div(&a).unwrap();


    // println!("{:0b}", _a);
    // println!("{:0b}", _b);

    // println!("{:0b}", I256::MAX);

    // println!("{}", i64::MIN);
    // println!("{}", i64::MAX);


    // let a = I256::MAX;
    // let b = I256::from_i128(123444);

    // println!("{:0b}", b.checked_sub(&a).unwrap());


    // println!("{:?}", a.wrapping_add(&b));

    // println!("{:0b}", 0i128.wrapping_sub(i128::MIN));
    // println!("{:0b}", i128::MIN);
    // println!("{:?}", 0i128 - i128::MIN); attempt to compute `0_i128 - i128::MIN`, which would overflow

    // let i256_394583 = I256::from_i32(394583);
    // let i256_neg_39849683452346 = I256::from_i128(-39849683452346);
    // println!("{:0b}", i256_394583.wrapping_sub(&i256_neg_39849683452346));
    // println!("{:0b}", i256_394583.wrapping_add(&i256_neg_39849683452346));
    // println!("{:?}", i256_394583.wrapping_add(&i256_neg_39849683452346).try_to_i64())



    // println!("{:0b}", i64::MAX.wrapping_mul(288230376151711743));
    // println!("{:0b}", 190i128.wrapping_div(-1));

    // println!("{:0b}", U256::MAX.wrapping_mul(&U256::MAX));
    // println!("{:0b}", U256::MAX.wrapping_mul(&U256::new(340282366920938463463374607431768211455, 20282409603651670423947251286015)));

    // println!("{:0b}", I256::MAX.wrapping_mul(&I256::MAX));
    // println!("{:?}", I256::from_i128(-283456).wrapping_mul(&I256::from_i128(-2938562923)).try_to_i128());


    // println!("{:0b}", I256::MAX.checked_mul(&I256::MINUS_ONE).unwrap());

    // let a = I256::from_i32(2);                                  // = 2

    // let neg_b = I256::ONE.shl(254)                              //   = 2^254
    //     .wrapping_add(&I256::ONE);                              //   = 2^254 + 1  (positive)

    // let b = neg_b.not().wrapping_add(&I256::ONE);

    // let result = a.checked_mul(&b);
    // println!("{:?}", result);

    // println!("{:?}", I256::MIN.checked_mul(&I256::MINUS_ONE));
    // println!("{:?}", I256::MIN.checked_div(&I256::MINUS_ONE));

    println!("{:?}", I256::MIN.checked_add(&I256::MINUS_ONE));


    // println!("{}", i128::MIN * (-1)); attempt to compute `i128::MIN * -1_i128`, which would overflow
    // println!("{}", i128::MIN / (-1)); attempt to compute `i128::MIN / -1_i128`, which would overflow



    // println!("{:?}", b.try_to_i128());
    // println!("{:0b}", (-1i8).not());
    // println!("{:0b}", 12i8);

    // println!("{:0b}", b.not());
    // println!("{:0b}", b);

    // println!("{:0b}", 90i16 & 88i16);

    // let a = I256 { bits: U256::new(1274823, 3457345342) };
    // let b = I256::from_i64(88);

    // println!("{:0b}", a.and(&b))
}