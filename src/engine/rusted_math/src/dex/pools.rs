use crate::dex::orca::Whirlpool;
use crate::dex::raydium::{RayClmmPool, RayAmmPool};
use crate::dex::meteora::MeteoraDlmmPool;
use crate::dex::uniswap::{UniswapClmm, UniswapAmm};

#[derive(Debug)]
pub enum Pool {
    Whirlpool(Whirlpool),
    RayClmmPool(RayClmmPool),
    RayAmmPool(RayAmmPool),
    MeteoraDlmmPool(MeteoraDlmmPool),
    UniswapClmmPool(UniswapClmm),
    UniswapAmmPool(UniswapAmm)
}