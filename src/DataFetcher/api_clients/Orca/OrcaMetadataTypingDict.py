from src.DataFetcher.api_clients.BaseMetadataTypingDict import BaseMetadata

class OrcaMetadata(BaseMetadata):
    feeRate: int
    poolType: str
    af: bool