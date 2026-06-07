use crate::math::errors::SoulMathError;
use crate::math::u256::{U256, hi_lo};


use std::fmt;
use std::cmp::Ordering;

const NUM_WORDS: usize = 4;

#[derive(Copy, Clone, Debug, PartialEq, Eq, Hash)]
pub struct I256 {
    pub bits: U256
}


impl I256 {
    pub const ZERO: Self = Self{ bits: U256 { items: [0; 4] } };
    pub const ONE: Self = Self{ bits: U256 { items: [1, 0, 0, 0] } };
    pub const MINUS_ONE: Self = Self{ bits: U256 { items: [u64::MAX; 4] } };
    pub const MAX: Self = Self{ bits: U256 { items: [u64::MAX, u64::MAX, u64::MAX, u64::MAX >> 1] } };
    pub const MIN: Self = Self{ bits: U256 { items: [0, 0, 0, 1u64 << 63] } };

    pub fn from_raw(bits: U256) -> Self {
        Self{
            bits
        }
    }

    pub fn from_i32(x: i32) -> Self {
        if x < 0 {
            Self {
                bits: U256 { items: [x as u64, u64::MAX, u64::MAX, u64::MAX] }
            }
        } else {
            Self {
                bits: U256 { items: [x as u64, 0, 0, 0] }
            }
        }
    }

    pub fn from_i64(x: i64) -> Self {
        if x < 0 {
            Self {
                bits: U256 { items: [x as u64, u64::MAX, u64::MAX, u64::MAX] }
            }
        } else {
            Self {
                bits: U256 { items: [x as u64, 0, 0, 0] }
            }
        }
    }

    pub fn from_i128(x: i128) -> Self {
        if x < 0 {
            Self {
                bits: U256 { items: [x as u64, (x >> 64) as u64, u64::MAX, u64::MAX] }
            }
        } else {
            Self {
                bits: U256 { items: [x as u64, (x >> 64) as u64, 0, 0] }
            }
        }
    }

    pub fn try_to_i32(&self) -> Result<i32, SoulMathError> {
        let word = self.bits.items[0];
        let result = word as i32;

        let mask_u32 = if result < 0 { u32::MAX } else { 0 };
        let mask_u64 = if result < 0 { u64::MAX } else { 0 };

        if ((word >> 32) as u32) != mask_u32 {
            return Err(SoulMathError::NumberDownCastError);
        }

        for i in 1..NUM_WORDS {
            if self.bits.items[i] != mask_u64 {
                return Err(SoulMathError::NumberDownCastError);
            }
        }

        Ok(result)
    }

    pub fn try_to_i64(&self) -> Result<i64, SoulMathError> {
        let result = self.bits.items[0] as i64;
        let mask = if result < 0 { u64::MAX } else { 0 };

        for i in 1..NUM_WORDS {
            if self.bits.items[i] != mask {
                return Err(SoulMathError::NumberDownCastError);
            }
        }

        Ok(result)
    }

    pub fn try_to_i128(&self) -> Result<i128, SoulMathError> {
        let result = hi_lo(self.bits.items[1], self.bits.items[0]) as i128;
        let mask = if result < 0 { u64::MAX } else { 0 };

        for i in 2..NUM_WORDS {
            if self.bits.items[i] != mask {
                return Err(SoulMathError::NumberDownCastError);
            }
        }

        Ok(result)
    }
    

    pub fn not(&self) -> Self {
        let mut result: I256 = I256 { bits: U256::new(0, 0) };

        for i in 0..NUM_WORDS {
            result.bits.items[i] = !self.bits.items[i]
        }

        result
    }

    pub fn and(&self, other: &Self) -> Self {
        let mut result: I256 = I256 { bits: U256::new(0, 0) };

        for i in 0..NUM_WORDS {
            result.bits.items[i] = self.bits.items[i] & other.bits.items[i]
        }

        result
    }

    pub fn or(&self, other: &Self) -> Self {
        let mut result: I256 = I256 { bits: U256::new(0, 0) };

        for i in 0..NUM_WORDS {
            result.bits.items[i] = self.bits.items[i] | other.bits.items[i]
        }

        result
    }

    pub fn xor(&self, other: &Self) -> Self {
        let mut result: I256 = I256 { bits: U256::new(0, 0) };

        for i in 0..NUM_WORDS {
            result.bits.items[i] = self.bits.items[i] ^ other.bits.items[i]
        }

        result
    }


    pub fn is_negative(&self) -> bool {
        let sign_bit: u64 = self.bits.items[3] >> 63;
        if sign_bit == 1 { true } else { false }
    }

    pub fn is_zero(&self) -> bool {
        self.bits.is_zero()
    }

    pub fn is_positive(&self) -> bool {
        !self.is_negative() && !self.is_zero()
    }

    pub fn signum(&self) -> Self {
        if self.is_positive() {
            Self::ONE
        } else if self.is_negative() {
            Self::MINUS_ONE
        } else {
            Self::ZERO
        }
    }


    pub fn shl(&self, n: u32) -> Self {
        Self {
            bits: self.bits.shift_left(n)
        }
    }

    pub fn shr(&self, n: u32) -> Self {
        if !self.is_negative() {
            return Self {
                bits: self.bits.shift_right(n)
            }
        }

        if n == 0 {
            return Self {
                bits: self.bits
            }
        }

        if n >= 256 {
            return Self::MINUS_ONE
        }

        let mut shifted = self.bits.shift_right(n);
        let mask = U256 { items: [u64::MAX; 4] }.shift_left(256 - n);

        for i in 0..NUM_WORDS {
            shifted.items[i] |= mask.items[i];
        }

        Self { bits: shifted }
    }


    pub fn lt(&self, other: &Self) -> bool {
        if self.is_negative() && !other.is_negative() {
            return true
        } else if !self.is_negative() && other.is_negative() {
            return false
        }

        self.bits.lt(&other.bits)
    }

    pub fn le(&self, other: &Self) -> bool {
        if self.is_negative() && !other.is_negative() {
            return true
        } else if !self.is_negative() && other.is_negative() {
            return false
        }

        self.bits.lte(&other.bits)
    }

    pub fn gt(&self, other: &Self) -> bool {
        other.lt(self)
    }

    pub fn ge(&self, other: &Self) -> bool {
        other.le(self)
    }

    pub fn eq(&self, other: &Self) -> bool {
        self.bits.eq(&other.bits)
    }

    pub fn cmp(&self, other: &Self) -> Ordering {
        match (self.is_negative(), other.is_negative()) {
            (true, false) => Ordering::Less,
            (false, true) => Ordering::Greater,
            _ => {
                if self.bits.lt(&other.bits) {
                    Ordering::Less
                } else if self.bits.gt(&other.bits) {
                    Ordering::Greater
                } else {
                    Ordering::Equal
                }
            }
        }
    }


    pub fn wrapping_add(&self, other: &Self) -> Self {
        Self {
            bits: self.bits.wrapping_add(&other.bits)
        }
    }

    pub fn wrapping_sub(&self, other: &Self) -> Self {
        let negative_other = other.not().wrapping_add(&I256::ONE);

        self.wrapping_add(&negative_other)
    }

    pub fn wrapping_mul(&self, other: &Self) -> Self {
        Self {
            bits: self.bits.wrapping_mul(&other.bits)
        }
    }

    pub fn wrapping_div(&self, other: &Self) -> Result<(Self, Self), SoulMathError> {
        let dividend: U256 = if self.is_negative() {
            self.not().wrapping_add(&I256::ONE).bits
        } else {
            self.bits
        };

        let divisor: U256 = if other.is_negative() {
            other.not().wrapping_add(&I256::ONE).bits
        } else {
            other.bits
        };

        let (mut quotient, mut remainder) = dividend.div(&divisor)?;

        if (other.is_negative() && self.is_positive()) || (other.is_positive() && self.is_negative()) {
            quotient = I256::from_raw(quotient)
                .not()
                .wrapping_add(&I256::ONE)
                .bits;
        };

        if self.is_negative() {
            remainder = I256::from_raw(remainder)
                .not()
                .wrapping_add(&I256::ONE)
                .bits;
        }

        Ok(
            (I256::from_raw(quotient), I256::from_raw(remainder))
        )
    }


    pub fn checked_add(&self, other: &Self) -> Result<Self, SoulMathError> {
        let result = self.wrapping_add(other);

        if self.is_negative() && other.is_negative() && result.bits.lt(&I256::MIN.bits) {
            return Err(SoulMathError::AddOverflow)
        }

        if self.is_positive() && other.is_positive() && result.bits.gt(&I256::MAX.bits) {
            return Err(SoulMathError::AddOverflow)
        }

        Ok(result)
    }

    pub fn checked_sub(&self, other: &Self) -> Result<Self, SoulMathError> {
        let result = self.wrapping_sub(other);

        if !self.is_negative() && other.is_negative() && result.bits.gt(&I256::MAX.bits) {
            return Err(SoulMathError::SubUnderflow)
        }

        if !self.is_positive() && other.is_positive() && result.bits.lt(&I256::MIN.bits) {
            return Err(SoulMathError::SubUnderflow)
        }

        Ok(result)
    }

    pub fn checked_mul(&self, other: &Self) -> Result<Self, SoulMathError> {
        let a = if self.is_negative() {
            self.not().wrapping_add(&I256::ONE)
        } else {
            *self
        };

        let b = if other.is_negative() {
            other.not().wrapping_add(&I256::ONE)
        } else {
            *other
        };

        let mut result = I256::from_raw(a.bits.mul(&b.bits)?);

        if (self.is_negative() && other.is_positive()) || (self.is_positive() && other.is_negative()) {
            result = result.not().wrapping_add(&I256::ONE);

            if result.bits.lt(&I256::MIN.bits) {
                return Err(SoulMathError::MulOverflow)
            }
        }


        if (self.is_positive() && other.is_positive()) || (self.is_negative() && other.is_negative()) {
            if result.bits.gt(&I256::MAX.bits) {
                return Err(SoulMathError::MulOverflow)
            }
        }

        Ok(result)
    }

    pub fn checked_div(&self, other: &Self) -> Result<(Self, Self), SoulMathError> {
        let (quotient, remainder) = self.wrapping_div(other)?;

        if (self.is_positive() && other.is_positive())
            || (self.is_negative() && other.is_negative())
        {
            if quotient.bits.gt(&I256::MAX.bits) {
                return Err(SoulMathError::DivisionOverflow);
            }
        }

        Ok((quotient, remainder))
    }

}




impl fmt::Binary for I256 {

    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            f,
            "{:064b}_{:064b}_{:064b}_{:064b}",
            self.bits.items[3],
            self.bits.items[2],
            self.bits.items[1],
            self.bits.items[0],
        )
    }

}