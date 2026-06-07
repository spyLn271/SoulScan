use std::fmt;
use crate::math::errors::SoulMathError;


const NUM_WORDS: usize = 4;
const U64_MAX: u128 = u64::MAX as u128;
const U64_RESOLUTION: u32 = 64;

pub trait LoHi {
    fn lo(self) -> u64;
    fn hi(self) -> u64;
    fn lo_u128(self) -> u128;
    fn hi_u128(self) -> u128;
}

impl LoHi for u128 {
    fn lo(self) -> u64 {
        (self & U64_MAX) as u64
    }

    fn hi(self) -> u64 {
        (self >> U64_RESOLUTION) as u64
    }

    fn lo_u128(self) -> u128 {
        self & U64_MAX
    }

    fn hi_u128(self) -> u128 {
        self >> U64_RESOLUTION
    }
}

pub fn hi_lo(hi: u64, lo: u64) -> u128 {
    (hi as u128) << U64_RESOLUTION | (lo as u128)
}

#[derive(Copy, Clone, Debug, PartialEq, Eq, Hash)]
pub struct U256 {
    pub items: [u64; NUM_WORDS]
}

impl U256 {
    pub const MAX: Self = U256 { items: [u64::MAX; NUM_WORDS] };
    pub const MIN: Self = U256 { items: [0; NUM_WORDS] };
    pub const ONE: Self = U256 { items: [1, 0, 0, 0] };

    pub fn new(h: u128, l: u128) -> Self {
        U256 {
            items: [l.lo(), l.hi(), h.lo(), h.hi()]
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
        // Because u256 is in little endianness, shifting left(Moving towards MSW)
        // actually means shifting right in code

        let mut result = Self::new(0, 0);

        for i in (1..NUM_WORDS).rev() {
            result.items[i] = self.items[i - 1];
        }

        result
    }

    pub fn shift_left(&self, mut shift_amount: u32) -> Self{
        if shift_amount >= U64_RESOLUTION * (NUM_WORDS as u32) {
            return Self::new(0, 0)
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
        // Because u256 is in little endianness, shifting right(Moving towards LSW)
        // actually means shifting left in code

        let mut result = Self::new(0, 0);

        for i in 0..NUM_WORDS - 1 {
            result.items[i] = self.items[i + 1];
        }

        result
    }

    pub fn shift_right(&self, mut shift_amount: u32) -> Self {
        if shift_amount >= U64_RESOLUTION * (NUM_WORDS as u32) {
            return Self::new(0, 0);
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

    pub fn add(&self, other: &Self) -> Result<Self, SoulMathError> {
        let mut result = Self::new(0, 0);
        let mut carry: bool = false;

        for i in 0..NUM_WORDS {
            let (partial_sum, carry1) = self.items[i].overflowing_add(other.items[i]);
            let (sum, carry2) = partial_sum.overflowing_add(carry as u64);

            result.items[i] = sum;
            carry = carry1 | carry2;
        }

        if carry {
            return Err(SoulMathError::AddOverflow);
        }

        Ok(result)
    }

    pub fn wrapping_add(&self, other: &Self) -> Self {
        let mut result = Self::new(0, 0);
        let mut carry: bool = false;

        for i in 0..NUM_WORDS {
            let (partial_sum, carry1) = self.items[i].overflowing_add(other.items[i]);
            let (sum, carry2) = partial_sum.overflowing_add(carry as u64);

            result.items[i] = sum;
            carry = carry1 | carry2;
        }

        result
    }

    pub fn sub(&self, other: &Self) -> Result<Self, SoulMathError> {
        let mut result = Self::new(0, 0);
        let mut borrow: bool = false;

        if self.lt(other) {
            return Err(SoulMathError::SubUnderflow);
        }

        for i in 0..NUM_WORDS {
            let (partial_diff, borrow1) = self.items[i].overflowing_sub(borrow as u64);
            let (diff, borrow2) = partial_diff.overflowing_sub(other.items[i]);

            result.items[i] = diff;
            borrow = borrow1 | borrow2;
        }

        Ok(result)
    }

    pub fn wrapping_sub(&self, other: &Self) -> Self {
        let mut result = Self::new(0, 0);
        let mut borrow: bool = false;

        for i in 0..NUM_WORDS {
            let (partial_diff, borrow1) = self.items[i].overflowing_sub(borrow as u64);
            let (diff, borrow2) = partial_diff.overflowing_sub(other.items[i]);

            result.items[i] = diff;
            borrow = borrow1 | borrow2;
        }

        result
    }

    pub fn mul(&self, other: &Self) -> Result<Self, SoulMathError> {
        let mut result = Self::new(0, 0);

        let n = self.size_of();
        let m = other.size_of();


        for i in 0..n {
            let mut carry: u128 = 0;

            for j in 0..m {
                let position = i + j;

                if position >= NUM_WORDS {
                    return Err(SoulMathError::MulOverflow);
                }

                let a = self.get_word_u128(i);
                let b = other.get_word_u128(j);
                let sum  = a * b + result.get_word_u128(position) + carry;

                result.update_word(position, sum.lo());
                carry = sum.hi_u128();
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
        let mut result = Self::new(0, 0);

        let n = self.size_of();
        let m = other.size_of();


        for i in 0..n {
            let mut carry: u128 = 0;

            for j in 0..m {
                let position = i + j;

                if position >= NUM_WORDS {
                    break
                }

                let a = self.get_word_u128(i);
                let b = other.get_word_u128(j);
                let sum  = a * b + result.get_word_u128(position) + carry;

                result.update_word(position, sum.lo());
                carry = sum.hi_u128();
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
        let mut quotient = Self::new(0, 0);
        let mut remainder = Self::new(0, 0);

        if other.is_zero() {
            return Err(SoulMathError::CantBeDividedByZero);
        }

        if self.lt(other) {
            remainder = self.copy();
            return Ok((quotient, remainder));
        }

        let shift_amount = other.items[other.size_of() - 1].leading_zeros();

        let mut dividend: [u64; NUM_WORDS + 1] = dividend_normalization(self, shift_amount);
        let divisor= other.shift_left(shift_amount);
        let mini_divisor = divisor.items[divisor.size_of() - 1] as u128;

        let n = divisor.size_of();
        let div_loop_iterations = NUM_WORDS + 1 - n;

        'main_div_loop: for i in (0..div_loop_iterations).rev() {
            let mut q_guess = hi_lo(dividend[i + n], dividend[i + n - 1]) / mini_divisor;

            if q_guess > U64_MAX {
                q_guess = U64_MAX
            }


            'q_correlation: for _ in 0..3 {
                let mut clone_dividend = dividend.clone();
                let mut borrow: u64 = 0;
                let mut underflow_borrowing: u64 = 0;


                'mul_sub_loop: for k in 0..n {
                    let product = divisor.get_word_u128(k) * q_guess;

                    let subtrahend = product.lo();
                    let minuend = clone_dividend[i + k];

                    let (diff1, underflow1) = minuend.overflowing_sub(borrow);
                    let (diff2, underflow2) = diff1.overflowing_sub(underflow_borrowing);
                    let (diff, underflow3) = diff2.overflowing_sub(subtrahend);

                    borrow = product.hi();
                    underflow_borrowing = underflow1 as u64 + underflow2 as u64 + underflow3 as u64;
                    clone_dividend[i + k] = diff;
                }

                let (diff1, critical_underflow1) = clone_dividend[i + n].overflowing_sub(borrow);
                let (diff, critical_underflow2) = diff1.overflowing_sub(underflow_borrowing);
                clone_dividend[i + n] = diff;

                if critical_underflow1 | critical_underflow2  {
                    q_guess -= 1;
                } else {
                    dividend = clone_dividend;
                    break 'q_correlation;
                }

            }

            quotient.update_word(i, q_guess as u64);
        }

        remainder_normalization(&mut remainder, dividend, shift_amount);

        Ok((quotient, remainder))
    }
}

pub fn mul_q64x64(v: u128, n: u128) -> U256 {
    // This function is only for multiplying Q64.64
    // Q64.64 it means the first 64 parts are for integer and the last 64 parts are for fraction.
    //                          nh   nl
    //                          *
    //                          vh   vl
    //                        ---------
    //a0 =                      vl * nl
    //a1 =                 vl * nh
    //b0 =                 vh * nl
    //b1 =          + vh * nh

    let a0: u128 = v.lo_u128() * n.lo_u128();  // Pure fraction
    let a1: u128 = v.lo_u128() * n.hi_u128();  // 64 integers and 64 fractions
    let b0: u128 = v.hi_u128() * n.lo_u128();  // 64 integers and 64 fractions
    let b1: u128 = v.hi_u128() * n.hi_u128();  // Pure integer

    let int_a1: u128 = a1.hi_u128();
    let frac_a1: u128 = a1.lo_u128() << U64_RESOLUTION;

    let int_b0: u128 = b0.hi_u128();
    let frac_b0: u128 = b0.lo_u128() << U64_RESOLUTION;

    let (partial_frac, carry1) = a0.overflowing_add(frac_a1);
    let (final_frac, carry2) = partial_frac.overflowing_add(frac_b0);


    let integer_part: u128 = {
        int_a1 + int_b0 + b1 + carry1 as u128 + carry2 as u128
    };
    let fraction_part: u128 = {
        final_frac
    };

    U256::new(integer_part, fraction_part)
}

fn dividend_normalization(words: &U256, shift_amount: u32) -> [u64; NUM_WORDS + 1] {
    // This function is only for internal use and not supposed to be used outside u256_math.rs
    // It is supposed that words are in little endian order and being used in U256::div func
    // P.S it is know that shift_amount is less than U64_RESOLUTION.
    let mut result = [0; NUM_WORDS + 1];
    let mut target = [0; NUM_WORDS + 1];

    for (i, &item) in words.items.iter().enumerate() {
        target[i] = item;
    }

    if shift_amount == 0 {
        result = target;
        return result
    }

    for i in (1..NUM_WORDS + 1).rev() {
        result[i] = {
            let f1: u64 = target[i] << shift_amount;
            let f2: u64 = target[i - 1] >> (U64_RESOLUTION - shift_amount);
            f1 | f2
        }
    }

    result[0] = target[0] << shift_amount;

    result
}

fn remainder_normalization(remainder: &mut U256, dividend: [u64; NUM_WORDS + 1],
                           shift_amount: u32, ) {
    // This function is only for internal use and not supposed to be used outside u256_math.rs
    // It is supposed that words are in little endian order and being used in U256::div func
    // P.S it is know that shift_amount is less than U64_RESOLUTION.

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

impl fmt::Binary for U256 {

    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            f,
            "{:064b}_{:064b}_{:064b}_{:064b}",
            self.items[3],
            self.items[2],
            self.items[1],
            self.items[0],
        )
    }

}