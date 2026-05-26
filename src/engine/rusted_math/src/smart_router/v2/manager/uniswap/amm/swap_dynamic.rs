use crate::math::uniswap::amm::*;
use crate::smart_router::manager_errors::SoulManagerError;
use crate::dex::uniswap::UniswapAmm;

#[derive(Debug)]
pub struct DynamicUniAmmResult {
    pub total_amount_in: u128,
    pub total_amount_out: u128,
    pub total_fee_amount: u128,
    pub new_x_reserves: u128,
    pub new_y_reserves: u128
}


pub fn swap_manager(
    x_to_y: bool,
    amount_specified_is_in: bool,
    delta_amount: u128,
    fee_rate: u32,
    uni_pool: &UniswapAmm
) -> Result<DynamicUniAmmResult, SoulManagerError> {
    let x_reserves = uni_pool.reserve0;
    let y_reserves = uni_pool.reserve1;

    let swap_res = calculate_swap(
        x_reserves,
        y_reserves,
        delta_amount,
        fee_rate,
        x_to_y,
        amount_specified_is_in
    )?;

    let gross_in = swap_res.amount_in + swap_res.fee_amount;

    let (new_x_reserves, new_y_reserves) = if x_to_y {
        (x_reserves + gross_in, y_reserves - swap_res.amount_out)
    } else {
        (x_reserves - swap_res.amount_out, y_reserves + gross_in)
    };


    Ok(
        DynamicUniAmmResult {
            total_amount_in: swap_res.amount_in + swap_res.fee_amount,
            total_amount_out: swap_res.amount_out,
            total_fee_amount: swap_res.fee_amount,
            new_x_reserves,
            new_y_reserves
        }
    )
}