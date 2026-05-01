use rusted_soul_dex::smart_router::v1::manager::meteora::dlmm::fee_rate_manager::*;
use rusted_soul_dex::smart_router::v1::manager::meteora::dlmm::swap_manager::*;
use rusted_soul_dex::dex::meteora::{MeteoraDlmmPool, ConstantParameters, VariableParameters};

use serde::Deserialize;
use redis;
use std::collections::HashMap;
use redis::TypedCommands;

#[derive(Debug, Deserialize)]
pub struct MeteoraPools {
    pub pool_state: HashMap<String, MeteoraDlmmPool>,
    pub ts: u64
}


fn get_dlmm_pool() -> MeteoraPools {
    let client = redis::Client::open("redis://127.0.0.1:6379/0").unwrap();
    let mut conn = client.get_connection().unwrap();

    let raw_json: String = conn
        .get("snapshot:state:meteora:dlmm")
        .unwrap()
        .unwrap();

    let pools: MeteoraPools = serde_json::from_str(&raw_json).unwrap();

    pools
}



#[test]
fn test_fee_rate_manager() {
    let constant_parameters = ConstantParameters {
        base_factor: 3125,
        filter_period: 10,
        decay_period: 120,
        reduction_factor: 5000,
        variable_fee_control: 40000,
        max_volatility_accumulator: 100000,
        min_bin_id: -218363,
        max_bin_id: 218363,
        protocol_share: 500,
        base_fee_power_factor: 0,
    };

    let variable_parameters = VariableParameters {
        volatility_accumulator: 50979,
        volatility_reference: 10979,
        index_reference: 17966,
        last_update_timestamp: 1769179897,
        crossed_bins: 0
    };

    let x_to_y = true;
    let bin_step = 64;
    let start_active_id = 17962;
    let timestamp: u64 = 1769279897;

    let fee_rate_manager = FeeRateManager::new(
        constant_parameters,
        variable_parameters,
        x_to_y,
        bin_step,
        start_active_id,
        timestamp
    );

    println!("{}", fee_rate_manager.get_fee_rate(7));
}

#[test]
fn test_swap_manger() {
    let pools = get_dlmm_pool();
    println!("{}", pools.ts);

    let some_shit_pool = pools.pool_state
        .get("71QNAbzXJL3tupEL3vyUKzcGLvCcAHsbYWGbK1otBe7P").unwrap();

    println!("{some_shit_pool:?}");

    let timestamp: u64 = 1779179579;

    let swap_res = swap_manager(
        true,
        true,
        2142697,
        timestamp,
        some_shit_pool
    );

    println!("{swap_res:?}");
    println!("{some_shit_pool:?}");
}