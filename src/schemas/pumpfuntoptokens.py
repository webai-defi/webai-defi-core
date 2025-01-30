from pydantic import BaseModel
from typing import List, Optional


class PumpFunToken(BaseModel):
    Name: str
    Symbol: str
    MintAddress: str
    Decimals: int
    Fungible: bool
    Uri: Optional[str]
    description: Optional[str] = ""
    image: Optional[str] = ""
    twitter: Optional[str] = ""
    website: Optional[str] = ""
    createdOn: Optional[str] = ""


class PumpFunBuy(BaseModel):
    Price: float
    PriceInUSD: float
    Currency: PumpFunToken


class PumpFunTrade(BaseModel):
    Buy: PumpFunBuy


class PumpFunTradeWrapper(BaseModel):
    Trade: PumpFunTrade


class PumpFunResponse(BaseModel):
    data: List[PumpFunTradeWrapper]
