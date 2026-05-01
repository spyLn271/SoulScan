use crate::math::raydium::amm::*;
use crate::smart_router::manager_errors::SoulManagerError;
use crate::smart_router::v1::manager::common_struct::SwapResult;
use crate::dex::raydium::RayAmmPool;




pub fn swap_manager(
    x_to_y: bool,
    amount_specified_is_in: bool,
    delta_amount: u128,
    fee_rate: u32,
    ray_pool: &RayAmmPool
) -> Result<SwapResult, SoulManagerError> {
    let x_reserves = ray_pool.base_vault.amount
        .checked_sub(ray_pool.base_info.base_need_take_pnl as u128)
        .unwrap_or(0);
    let y_reserves = ray_pool.quote_vault.amount
        .checked_sub(ray_pool.base_info.quote_need_take_pnl as u128)
        .unwrap_or(0);

    let swap_res = calculate_swap(
        x_reserves, y_reserves, delta_amount, fee_rate, x_to_y, amount_specified_is_in
    )?;

    Ok(
        SwapResult {
            total_amount_in: swap_res.amount_in + swap_res.fee_amount,
            total_amount_out: swap_res.amount_out,
            total_fee_amount: swap_res.fee_amount
        }
    )
}