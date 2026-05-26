use std::fmt;
use crate::math::errors::SoulMathError;
use crate::math::u256::{LoHi, hi_lo, U256};


const NUM_WORDS: usize = 8;
const U64_MAX: u128 = u64::MAX as u128;
const U64_RESOLUTION: u32 = 64;



#[derive(Copy, Clone, Debug)]
pub struct U512 {
    pub items: [u64; NUM_WORDS]
}


impl U512 {

    pub const MAX: Self = U512 { items: [u64::MAX; NUM_WORDS] };
    pub const MIN: Self = U512 { items: [0; NUM_WORDS] };
    pub const ONE: Self = U512 { items: [1, 0, 0, 0, 0, 0, 0, 0] };

    pub fn new(
        hh: u128, hl: u128, lh: u128, ll: u128
    ) -> Self {
        Self {
            items: [
                ll.lo(), ll.hi(), lh.lo(), lh.hi(), hl.lo(), hl.hi(), hh.lo(), hh.hi()
            ]
        }
    }

    pub fn copy(&self) -> Self {
        let mut items: [u64; NUM_WORDS] = [0; NUM_WORDS];
        items.copy_from_slice(&self.items);
        Self { items }
    }

    fn update_word(&mut self, index: usize, value: u64) {
        self.items[index] = value;
    }

    fn size_of(&self) -> usize {
        for i in (0..self.items.len()).rev() {
            if self.items[i] != 0 {
                return i + 1;
            }
        }

        0
    }

    pub fn leading_zeros(&self) -> u32 {
        let mut result: u32 = 0;

        for i in (0..self.items.len()).rev() {
            if self.items[i] == 0 {
                result += 64;
            } else {
                result += self.items[i].leading_zeros();
                break
            }
        }

        result
    }

    fn get_word(&self, index: usize) -> u64 {
        self.items[index]
    }

    fn get_word_u128(&self, index: usize) -> u128 {
        self.items[index] as u128
    }

    fn shift_word_left(&self) -> Self {
        // Because u512 is in little endianness, shifting left(Moving towards MSW)
        // actually means shifting right in code

        let mut result = Self::new(0, 0, 0, 0);

        for i in (1..NUM_WORDS).rev() {
            result.items[i] = self.items[i - 1];
        }

        result
    }

    pub fn shift_left(&self, mut shift_amount: u32) -> Self{
        if shift_amount >= U64_RESOLUTION * (NUM_WORDS as u32) {
            return Self::new(0, 0, 0, 0)
        }

        let mut result = self.copy();

        while shift_amount >= U64_RESOLUTION {
            result = result.shift_word_left();
            shift_amount -= U64_RESOLUTION;
        }

        if shift_amount == 0 {
            return result;
        }

        for i in (1.. NUM_WORDS).rev() {
            result.items[i] = {
                let f1: u64 = result.items[i] << shift_amount;
                let f2: u64 = result.items[i - 1] >> (U64_RESOLUTION - shift_amount);
                f1 | f2
            }
        }

        result.items[0] <<= shift_amount;

        result
    }

    fn shift_word_right(&self) -> Self {
        // Because u512 is in little endianness, shifting right(Moving towards LSW)
        // actually means shifting left in code

        let mut result = Self::new(0, 0, 0, 0);

        for i in 0..NUM_WORDS - 1 {
            result.items[i] = self.items[i + 1];
        }

        result
    }

    pub fn shift_right(&self, mut shift_amount: u32) -> Self {
        if shift_amount >= U64_RESOLUTION * (NUM_WORDS as u32) {
            return Self::new(0, 0, 0, 0);
        }

        let mut result = self.copy();

        while shift_amount >= U64_RESOLUTION {
            result = result.shift_word_right();
            shift_amount -= U64_RESOLUTION;
        }

        if shift_amount == 0 {
            return result;
        }

        for i in 0..NUM_WORDS - 1 {
            result.items[i] = {
                let f1: u64 = result.items[i] >> shift_amount;
                let f2: u64 = result.items[i + 1] << (U64_RESOLUTION - shift_amount);
                f1 | f2
            }
        }

        result.items[NUM_WORDS - 1] >>= shift_amount;

        result
    }

    pub fn eq(&self, other: &Self) -> bool {
        for i in 0..NUM_WORDS {
            if self.items[i] != other.items[i] {
                return false;
            }
        }
        true
    }

    pub fn gt(&self, other: &Self) -> bool {
        for i in (0..NUM_WORDS).rev() {
            if self.items[i] > other.items[i] {
                return true;
            } else if self.items[i] < other.items[i] {
                return false;
            }
        }

        false
    }

    pub fn gte(&self, other: &Self) -> bool {
        for i in (0..NUM_WORDS).rev() {
            if self.items[i] > other.items[i] {
                return true;
            } else if self.items[i] < other.items[i] {
                return false;
            }
        }

        true
    }

    pub fn lt(&self, other: &Self) -> bool {
        other.gt(self)
    }

    pub fn lte(&self, other: &Self) -> bool {
        other.gte(self)
    }

    pub fn is_zero(&self) -> bool {
        for i in 0..NUM_WORDS {
            if self.items[i] != 0 {
                return false;
            }
        }

        true
    }

    pub fn try_into_u128(&self) -> Result<u128, SoulMathError> {
        // I take this function from Orca::math::tick_math.rs
        if self.size_of() > 2 {
            return Err(SoulMathError::NumberDownCastError);
        }

        Ok(((self.items[1] as u128) << U64_RESOLUTION) | (self.items[0] as u128))
    }

    pub fn try_into_u256(&self) -> Result<U256, SoulMathError> {
        // My own U256
        if self.size_of() > 4 {
            return Err(SoulMathError::NumberDownCastError);
        }

        Ok(
            U256::new(
                ((self.items[3] as u128) << U64_RESOLUTION) | (self.items[2] as u128),
                ((self.items[1] as u128) << U64_RESOLUTION) | (self.items[0] as u128)
            )
        )
    }

    pub fn from_u128(x: u128) -> Self {
        Self {
            items: [x.lo(), x.hi(), 0, 0, 0, 0, 0, 0]
        }
    }

    pub fn from_u256(x: &U256) -> Self {
        Self {
            items: [x.items[0], x.items[1], x.items[2], x.items[3], 0, 0, 0, 0]
        }
    }

    pub fn add(&self, other: &Self) -> Result<Self, SoulMathError> {
        let mut result: U512 = U512::new(0, 0, 0, 0);
        let mut carry: bool = false;

        for i in 0..NUM_WORDS {
            let (partial_sum, carry1) = self.get_word(i)
                .overflowing_add(other.get_word(i));

            let (sum, carry2) = partial_sum
                .overflowing_add(carry as u64);

            result.update_word(i, sum);
            carry = carry1 | carry2;
        }

        if carry {
            return Err(SoulMathError::AddOverflow);
        }

        Ok(result)
    }

    pub fn wrapping_add(&self, other: &Self) -> Self {
        let mut result: U512 = U512::new(0, 0, 0, 0);
        let mut carry: bool = false;

        for i in 0..NUM_WORDS {
            let (partial_sum, carry1) = self.get_word(i)
                .overflowing_add(other.get_word(i));

            let (sum, carry2) = partial_sum
                .overflowing_add(carry as u64);

            result.update_word(i, sum);
            carry = carry1 | carry2;
        }

        result
    }

    pub fn sub(&self, other: &Self) -> Result<Self, SoulMathError> {
        let mut result: U512 = U512::new(0, 0, 0, 0);
        let mut borrow: bool = false;

        if self.lt(other) {
            return Err(SoulMathError::SubUnderflow);
        }

        for i in 0..NUM_WORDS {
            let (partial_diff, borrow1) = self.get_word(i)
                .overflowing_sub(other.get_word(i));

            let (diff, borrow2) = partial_diff
                .overflowing_sub(borrow as u64);

            result.update_word(i, diff);
            borrow = borrow1 | borrow2;
        }

        Ok(result)
    }

    pub fn wrapping_sub(&self, other: &Self) -> Self {
        let mut result: U512 = U512::new(0, 0, 0, 0);
        let mut borrow: bool = false;

        for i in 0..NUM_WORDS {
            let (partial_diff, borrow1) = self.get_word(i)
                .overflowing_sub(other.get_word(i));

            let (diff, borrow2) = partial_diff
                .overflowing_sub(borrow as u64);

            result.update_word(i, diff);
            borrow = borrow1 | borrow2;
        }

        result
    }

    pub fn mul(&self, other: &Self) -> Result<Self, SoulMathError> {
        let mut result = U512::new(
            0, 0, 0, 0
        );

        let n = self.size_of();
        let m = other.size_of();

        for i in 0..n {
            let mut  carry: u128 = 0;

            for j in 0..m {
                let position = i + j;

                if position >= NUM_WORDS {
                    return Err(SoulMathError::MulOverflow);
                }

                let a = self.get_word_u128(i);
                let b = other.get_word_u128(j);
                let product = a * b + result.get_word_u128(position) + carry;

                result.update_word(position, product.lo());
                carry = product.hi_u128();
            }

            if carry != 0 {
                let mut carry_pos = i + m;

                while carry != 0 {
                    if carry_pos >= NUM_WORDS {
                        return Err(SoulMathError::MulOverflow);
                    }

                    let sum = result.get_word_u128(carry_pos) + carry;

                    result.update_word(carry_pos, sum.lo());
                    carry = sum.hi_u128();

                    carry_pos += 1;
                }
            }
        }

        Ok(result)
    }

    pub fn wrapping_mul(&self, other: &Self) -> Self {
        let mut result = U512::new(
            0, 0, 0, 0
        );

        let n = self.size_of();
        let m = other.size_of();

        for i in 0..n {
            let mut  carry: u128 = 0;

            for j in 0..m {
                let position = i + j;

                if position >= NUM_WORDS {
                    break
                }

                let a = self.get_word_u128(i);
                let b = other.get_word_u128(j);
                let product = a * b + result.get_word_u128(position) + carry;

                result.update_word(position, product.lo());
                carry = product.hi_u128();
            }

            if carry != 0 {
                let mut carry_pos = i + m;

                while carry != 0 {
                    if carry_pos >= NUM_WORDS {
                        break
                    }

                    let sum = result.get_word_u128(carry_pos) + carry;

                    result.update_word(carry_pos, sum.lo());
                    carry = sum.hi_u128();

                    carry_pos += 1;
                }
            }
        }

        result
    }

    pub fn div(&self, other: &Self) -> Result<(Self, Self), SoulMathError> {
        let mut quotient: U512 = Self::new(0, 0, 0, 0);
        let mut remainder: U512 = Self::new(0, 0, 0, 0);

        if other.is_zero() {
            return Err(SoulMathError::CantBeDividedByZero);
        }

        if self.lt(other) {
            remainder = self.copy();
            return Ok((quotient, remainder));
        }

        let shift_amount: u32 = other.get_word(other.size_of() - 1)
            .leading_zeros();

        let mut dividend: [u64; NUM_WORDS + 1] = normalize_dividend(self, shift_amount);

        let divisor: U512 = other.shift_left(shift_amount);
        let mini_divisor: u128 = divisor.get_word_u128(other.size_of() - 1);

        let n = divisor.size_of();

        for i in (n..NUM_WORDS + 1).rev() {
            let mut q_guess = hi_lo(dividend[i], dividend[i - 1]) / mini_divisor;

            if q_guess > U64_MAX {
                q_guess = U64_MAX;
            }

            for _ in 0..3 {
                let mut result = dividend.clone();
                let mut borrow1: u64 = 0;
                let mut borrow2: u64 = 0;

                for j in 0..n {
                    let product = divisor.get_word_u128(j) * q_guess;

                    let (diff, underflow1) = result[i - n + j]
                        .overflowing_sub(product.lo());

                    let (diff, underflow2) = diff
                        .overflowing_sub(borrow1);

                    let (diff, underflow3) = diff
                        .overflowing_sub(borrow2);

                    borrow1 = product.hi();
                    borrow2 = underflow1 as u64 + underflow2 as u64 + underflow3 as u64;

                    result[i - n + j] = diff
                }

                let (diff, critical_overflow1) = result[i]
                    .overflowing_sub(borrow1);

                let (diff, critical_overflow2) = diff.overflowing_sub(borrow2);

                result[i] = diff;

                if critical_overflow1 | critical_overflow2 {
                    q_guess -= 1;
                } else {
                    dividend = result;
                    break
                }
            }

            quotient.update_word(i - n, q_guess as u64);
        }

        remainder_normalization(&mut remainder, dividend, shift_amount);

        Ok((quotient, remainder))
    }
}

fn normalize_dividend(
    dividend: &U512,
    shift_amount: u32
) -> [u64; NUM_WORDS + 1] {
    let mut result = [0; NUM_WORDS + 1];
    let mut target = [0; NUM_WORDS + 1];

    for i in 0..NUM_WORDS {
        target[i] = dividend.get_word(i);
    }

    if shift_amount == 0 {
        return target
    }

    for i in 1..(NUM_WORDS + 1) {
        result[i] = {
            let f1: u64 = target[i] << shift_amount;
            let f2: u64 = target[i - 1] >> (U64_RESOLUTION - shift_amount);

            f1 | f2
        }
    }

    result[0] = target[0] << shift_amount;

    result
}

fn remainder_normalization(
    remainder: &mut U512,
    dividend: [u64; NUM_WORDS + 1],
    shift_amount: u32
) {

    let mut normalized_dividend = [0; NUM_WORDS + 1];

    if shift_amount != 0 {
        for i in 0..NUM_WORDS {
            normalized_dividend[i] = {
                let f1: u64 = dividend[i] >> shift_amount;
                let f2: u64 = dividend[i + 1] << (U64_RESOLUTION - shift_amount);
                f1 | f2
            }
        }

        normalized_dividend[NUM_WORDS] = dividend[NUM_WORDS] >> shift_amount;
    } else {
        normalized_dividend = dividend;
    }

    for i in 0..NUM_WORDS {
        remainder.update_word(i, normalized_dividend[i]);
    }

}


impl fmt::Binary for U512 {

    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            f,
            "{:064b}_{:064b}_{:064b}_{:064b}_{:064b}_{:064b}_{:064b}_{:064b}",
            self.items[7],
            self.items[6],
            self.items[5],
            self.items[4],
            self.items[3],
            self.items[2],
            self.items[1],
            self.items[0],
        )
    }

}