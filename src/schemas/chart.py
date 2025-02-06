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

class ChartRequest(BaseModel):
    mint_address: str
    interval: str  # Возможные значения: "1m", "5m", "15m", "30m", "60m", "1d", "3d", "7d", "30d"

class ChartResponse(BaseModel):
    data: List[ChartData]