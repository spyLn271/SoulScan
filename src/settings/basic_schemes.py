from pydantic import BaseModel
from typing import TypedDict

# TICKS
class Tick(TypedDict):
    liquidityNet: int
    liquidityGross: int

class TickScheme(BaseModel):
    liquidityNet: int
    liquidityGross: int

# BINS
class Bins(TypedDict):
    amount_x: int
    amount_y: int

class BinScheme(BaseModel):
    amount_x: int
    amount_y: int

# COLD PATH
class ColdPath(TypedDict):
    ts: str
    routes: list

class ColdPathScheme(BaseModel):
    ts: str
    routes: list

# POOL STATE IN REDIS
class PoolState(TypedDict):
    pool_state: dict
    ts: int

class PoolStateScheme(BaseModel):
    pool_state: dict
    ts: int