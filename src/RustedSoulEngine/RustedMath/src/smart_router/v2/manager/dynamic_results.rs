use crate::smart_router::v2::manager::meteora::dlmm::swap_dynamic::DynamicMeteoraResult;
use crate::smart_router::v2::manager::orca::clmm::swap_dynamic::DynamicOrcaResult;
use crate::smart_router::v2::manager::raydium::clmm::swap_dynamic::DynamicRayClmmResult;
use crate::smart_router::v2::manager::raydium::amm::swap_dynamic::DynamicRayAmmResult;

#[derive(Debug)]
pub enum DynamicResult {
    DynamicMeteoraResult(DynamicMeteoraResult),
    DynamicOrcaResult(DynamicOrcaResult),
    DynamicRayClmmResult(DynamicRayClmmResult),
    DynamicRayAmmResult(DynamicRayAmmResult)
}