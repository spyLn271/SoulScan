use serde::Deserialize;

const VOLATILITY_ACCUMULATOR_SCALE_FACTOR: u64 = 10_000;
const ADAPTIVE_FEE_CONTROL_FACTOR_DENOMINATOR: u32 = 100_000;
const REDUCTION_FACTOR_DENOMINATOR: u32 = 10_000;
const REDUCTION_FACTOR_BASE_FEE: u32 = 100;
const MAX_FEE: u32 = 100_000;


#[derive(Copy, Clone, Debug, Deserialize)]
pub struct ConstantParameters {
    pub base_factor: u16,
    pub filter_period: u16,
    pub decay_period: u16,
    pub reduction_factor: u16,
    pub variable_fee_control: u32,
    pub max_volatility_accumulator: u32,
    pub min_bin_id: i32,
    pub max_bin_id: i32,
    pub protocol_share: u16,
    pub base_fee_power_factor: u8
}

#[derive(Copy, Clone, Debug, Deserialize)]
pub struct VariableParameters {
    pub volatility_accumulator: u32,
    pub volatility_reference: u32,
    pub index_reference: i32,
    pub last_update_timestamp: u64
}

#[derive(Copy, Clone, Debug)]
pub struct FeeRateManager {
    pub constant_parameters: ConstantParameters,
    pub variable_parameters: VariableParameters,
    pub x_to_y: bool,
    pub bin_step: u32,
    pub start_bin_id: i32,
    pub timestamp: u64
}

impl FeeRateManager {
    pub fn new(
        constant_parameters: ConstantParameters,
        variable_parameters: VariableParameters,
        x_to_y: bool,
        bin_step: u32,
        start_bin_id: i32,
        timestamp: u64
    ) -> Self {
        Self {
            constant_parameters,
            variable_parameters,
            x_to_y,
            bin_step,
            start_bin_id,
            timestamp
        }
    }

    pub fn get_fee_rate(&self, crossed_bins: u16) -> u32 {
        let fee_base: u32 = {
            let base_factor = self.constant_parameters.base_factor as u64;
            let bin_step = self.bin_step as u64;
            let power_multiplier = 10u64.pow(self.constant_parameters.base_fee_power_factor as u32);

            let numerator = base_factor * bin_step * power_multiplier;

            (numerator / REDUCTION_FACTOR_BASE_FEE as u64) as u32
        };

        let delta_time = (self.timestamp - self.variable_parameters.last_update_timestamp) as u128;
        let filter_period = self.constant_parameters.filter_period as u128;
        let decay_period = self.constant_parameters.decay_period as u128;

        let v_r = if delta_time < filter_period {
            self.variable_parameters.volatility_reference
        } else if delta_time < decay_period {
            (self.variable_parameters.volatility_accumulator
                * self.constant_parameters.reduction_factor as u32) / REDUCTION_FACTOR_DENOMINATOR
        } else {
            0
        };

        let bin_index_reference = if delta_time < filter_period {
            self.variable_parameters.index_reference as i64
        } else {
            self.start_bin_id as i64
        };

        let delta_bin_index = if self.x_to_y {
            (bin_index_reference - (self.start_bin_id as i64 - crossed_bins as i64)).unsigned_abs()
        } else {
            (bin_index_reference - (self.start_bin_id as i64 + crossed_bins as i64)).unsigned_abs()
        };

        let v_a = {
            let v_a_calc = v_r as u64 + delta_bin_index * VOLATILITY_ACCUMULATOR_SCALE_FACTOR;

            if v_a_calc > self.constant_parameters.max_volatility_accumulator as u64 {
                self.constant_parameters.max_volatility_accumulator as u128
            } else {
                v_a_calc as u128
            }
        };

        let a = self.constant_parameters.variable_fee_control as u128;
        let s = self.bin_step as u128;

        let dividend = a * v_a * v_a * s * s;
        let divisor = ADAPTIVE_FEE_CONTROL_FACTOR_DENOMINATOR as u128
            * VOLATILITY_ACCUMULATOR_SCALE_FACTOR as u128
            * VOLATILITY_ACCUMULATOR_SCALE_FACTOR as u128;

        let quotient = (dividend / divisor) as u32;
        let remainder = dividend % divisor;

        let fee_variable = if remainder == 0 {
            quotient
        } else {
            quotient + 1
        };

        let total_fee = fee_variable + fee_base;

        if total_fee > MAX_FEE {
            MAX_FEE
        } else {
            total_fee
        }
    }
}