use crate::dex::orca::Whirlpool;
use crate::dex::raydium::{RayClmmPool, RayAmmPool};
use crate::dex::meteora::MeteoraDlmmPool;

pub enum Pool {
    Whirlpool(Whirlpool),
    RayClmmPool(RayClmmPool),
    RayAmmPool(RayAmmPool),
    MeteoraDlmmPool(MeteoraDlmmPool)
}