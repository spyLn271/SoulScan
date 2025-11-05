import pydantic

# DLMM V2 Schemes
class LbPairDependenciesScheme(pydantic.BaseModel):
    Address: str
    PDA: list[str]
    LbPair: list[str]
    start_indexes: list[int]

