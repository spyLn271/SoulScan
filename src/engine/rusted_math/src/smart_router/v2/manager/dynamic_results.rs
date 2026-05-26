use crate::smart_router::v2::manager::meteora::dlmm::swap_dynamic::DynamicMeteoraResult;
use crate::smart_router::v2::manager::orca::clmm::swap_dynamic::DynamicOrcaResult;
use crate::smart_router::v2::manager::raydium::clmm::swap_dynamic::DynamicRayClmmResult;
use crate::smart_router::v2::manager::raydium::amm::swap_dynamic::DynamicRayAmmResult;
use crate::smart_router::v2::manager::uniswap::amm::swap_dynamic::DynamicUniAmmResult;
use crate::smart_router::v2::manager::uniswap::clmm::swap_dynamic::DynamicUniClmmResult;

#[derive(Debug)]
pub enum DynamicResult {
    DynamicMeteoraResult(DynamicMeteoraResult),
    DynamicOrcaResult(DynamicOrcaResult),
    DynamicRayClmmResult(DynamicRayClmmResult),
    DynamicRayAmmResult(DynamicRayAmmResult),
    DynamicUniAmmResult(DynamicUniAmmResult),
    DynamicUniClmmResult(DynamicUniClmmResult)
}