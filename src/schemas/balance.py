from pydantic import BaseModel
from typing import List, Dict


class Currency(BaseModel):
    MintAddress: str
    Name: str
    Symbol: str
    Uri: str
    description: str = ""
    image: str = ""
    twitter: str = ""
    website: str = ""
    createdOn: str = ""


class BalanceUpdate(BaseModel):
    Balance: str
    Currency: Currency


class WalletBalanceResponse(BaseModel):
    data: Dict[str, List[BalanceUpdate]]
