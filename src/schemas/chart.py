from pydantic import BaseModel
from typing import List, Optional, Dict, Union

class TradeData(BaseModel):
    close: float
    high: float
    low: float
    open: float
    price_last: float

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

class Token(BaseModel):
    Name: str
    Symbol: str
    MintAddress: str
    Uri: Optional[str]
    description: Optional[str] = ""
    image: Optional[str] = ""
    twitter: Optional[str] = ""
    website: Optional[str] = ""
    createdOn: Optional[str] = ""

class TokenInfo(BaseModel):
    Price: float
    PriceInUSD: float
    Currency: Token


class ChartResponse(BaseModel):
    data: Dict[str, Union[List[ChartData], TokenInfo]]