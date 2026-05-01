from src.dex.solana.data_fetcher.api_clients.base_metadata_tp import BaseMetadata

class OrcaMetadata(BaseMetadata):
    feeRate: int
    poolType: str
    af: bool