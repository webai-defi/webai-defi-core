from pydantic import BaseModel
from typing import List, Optional


class TokenVolumeResponse(BaseModel):
    totalTradedVolume: float
    averageTradeSize: float
    priceChangePercentage: float
    buySellRatio: float
    averageTradesPerMaker: float
    averageVolumePerMaker: float
    uniqueDexPlatforms: int
    averageVolumeByDex: dict
    liquidity: float
    totalBuyVolume: float
    totalSellVolume: float
    buyPercentage: float
    sellPercentage: float
    holdersCount: int
    marketCap: float
    marketCapInUSD: float