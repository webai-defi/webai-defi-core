from pydantic import BaseModel
from typing import List, Optional

class TradeData(BaseModel):
    close: float
    high: float
    low: float
    open: float

class BlockData(BaseModel):
    Timefield: str  # Время блока

class ChartData(BaseModel):
    Block: BlockData
    Trade: TradeData
    count: str
    volume: str

class ChartResponse(BaseModel):
    data: List[ChartData]