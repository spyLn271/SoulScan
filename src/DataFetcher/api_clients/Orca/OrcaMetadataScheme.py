from src.DataFetcher.api_clients.BaseMetadataScheme import BaseMetadataScheme

class OrcaMetadataScheme(BaseMetadataScheme):
    feeRate: int
    poolType: str
    af: bool