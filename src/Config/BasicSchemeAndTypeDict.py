from pydantic import BaseModel
from typing import TypedDict

class Tick(TypedDict):
    liquidityNet: int
    liquidityGross: int

class TickScheme(BaseModel):
    liquidityNet: int
    liquidityGross: int

class Bins(TypedDict):
    amount_x: int
    amount_y: int

class BinScheme(BaseModel):
    amount_x: int
    amount_y: int

class ColdPath(TypedDict):
    ts: str
    routes: list

class ColdPathScheme(BaseModel):
    ts: str
    routes: list