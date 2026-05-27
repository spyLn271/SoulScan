use serde::Deserialize;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum MarketKind {
    OrcaClmm,
    RaydiumClmm,
    RaydiumAmm,
    MeteoraDlmm,
    UniswapV2,
    UniswapV3,
    UniswapV4,
}

#[derive(Clone, Debug, Deserialize)]
pub struct MetadataRaw  {
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

#[derive(Clone, Debug, Deserialize)]
#[serde(try_from = "MetadataRaw")]
pub struct Metadata {
    pub kind: MarketKind,

    pub token0: String,
    pub token1: String,
    pub mint0: String,
    pub mint1: String,
    pub decimals0: u8,
    pub decimals1: u8,
    pub volume24h: f64,
    pub is_blacklisted: Option<bool>,

    pub fee_rate: Option<f64>,
    pub pool_type: Option<String>,
    pub tick_spacing: Option<u16>,
    pub af: Option<bool>,
}


impl TryFrom<MetadataRaw> for Metadata {
    type Error = String;

    fn try_from(value: MetadataRaw) -> Result<Self, Self::Error> {
        let kind = match (value.dex.as_str(), value.version.as_str()) {
            ("orca", "clmm")     => MarketKind::OrcaClmm,
            ("raydium", "clmm")  => MarketKind::RaydiumClmm,
            ("raydium", "amm")   => MarketKind::RaydiumAmm,
            ("meteora", "dlmm")  => MarketKind::MeteoraDlmm,
            ("uniswap", "v2") | ("pancakeswap", "v2") | ("sushiswap", "v2") => MarketKind::UniswapV2,
            ("uniswap", "v3") | ("pancakeswap", "v3") | ("sushiswap", "v3") => MarketKind::UniswapV3,
            ("uniswap", "v4")    => MarketKind::UniswapV4,
            (d, v) => return Err(format!("unknown market kind: {d}/{v}")),
        };

        Ok(
            Metadata {
                kind,
                token0: value.token0,
                token1: value.token1,
                mint0: value.mint0,
                mint1: value.mint1,
                decimals0: value.decimals0,
                decimals1: value.decimals1,
                volume24h: value.volume24h,
                is_blacklisted: value.is_blacklisted,
                fee_rate: value.fee_rate,
                pool_type: value.pool_type,
                tick_spacing: value.tick_spacing,
                af: value.af,
            }
        )
    }
}


pub type Path = Vec<String>;
#[derive(Clone, Debug, Deserialize)]
pub struct ColdPath {
    pub ts: String,
    pub routes: Vec<Path>
}