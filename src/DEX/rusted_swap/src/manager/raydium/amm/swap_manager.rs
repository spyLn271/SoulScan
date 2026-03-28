use crate::math::raydium::amm::*;
use crate::manager::errors::SoulManagerError;

use serde::Deserialize;

#[derive(Deserialize, Debug, Clone)]
pub struct Vault {
    pub mint: String,
    pub amount: u128
}

#[derive(Deserialize, Debug, Clone)]
#[serde(rename_all = "camelCase")]
pub struct BaseInfo {
    pub status: u8,
    pub base_vault: String,
    pub quote_vault: String,
    pub base_need_take_pnl: u64,
    pub quote_need_take_pnl: u64
}
#[derive(Deserialize, Debug)]
#[serde(rename_all = "camelCase")]
pub struct RayAmmPool {
    pub base_vault: Vault,
    pub quote_vault: Vault,

    #[serde(rename = "BaseInfo")]
    pub base_info: BaseInfo
}



#[derive(Copy, Clone, Debug)]
pub struct SwapResult {
    pub total_amount_in: u128,
    pub total_amount_out: u128,
    pub total_fee_amount: u128
}

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