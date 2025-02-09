from pydantic import BaseModel
from typing import List, Dict, Any

class TradeAccount(BaseModel):
    Owner: str


class Trade(BaseModel):
    Account: TradeAccount

class TraderData(BaseModel):
    Trade: Trade
    bought: str
    buys: str
    sells: str
    sold: str
    volume: str
    volumeUsd: str

class TopTradersResponse(BaseModel):
    data: List[TraderData]


class HolderAccount(BaseModel):
    Owner: str

class BalanceUpdate(BaseModel):
    Account: HolderAccount
    balance: str
    percentage_owned: float

class TokenSupplyUpdate(BaseModel):
    PostBalance: str
    PostBalanceInUSD: str

class TokenHoldersResponse(BaseModel):
    data: Dict[str, Any]

class TrendingTokensResponse(BaseModel):
    data: List[Any]
