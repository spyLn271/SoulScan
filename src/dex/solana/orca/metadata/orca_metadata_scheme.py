from src.dex.solana.data_fetcher.api_clients.base_medata_scheme import BaseMetadataScheme

class OrcaMetadataScheme(BaseMetadataScheme):
    feeRate: int
    poolType: str
    af: bool