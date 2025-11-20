from pydantic import BaseModel
from typing import TypedDict

class Tick(TypedDict):
    liquidityNet: int
    liquidityGross: int

class TickScheme(BaseModel):
    liquidityNet: int
    liquidityGross: int