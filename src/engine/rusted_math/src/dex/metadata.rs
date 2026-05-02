use serde::Deserialize;

#[derive(Clone, Debug, Deserialize)]
pub struct Metadata  {
    pub token0: String,
    pub token1: String,
    pub mint0: String,
    pub mint1: String,
    pub decimals0: u8,
    pub decimals1: u8,
    pub volume24h: f64,
    pub dex: String,
    pub version: String,
    pub is_blacklisted: Option<bool>,

    #[serde(alias = "feeRate", alias = "fee_rate", alias = "fee-rate")]
    pub fee_rate: Option<f64>,

    #[serde(alias = "poolType")]
    pub pool_type: Option<String>,

    pub tick_spacing: Option<u16>,

    pub af: Option<bool>
}


pub type Path = Vec<String>;
#[derive(Clone, Debug, Deserialize)]
pub struct ColdPath {
    pub ts: String,
    pub routes: Vec<Path>
}