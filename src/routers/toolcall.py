import logging

import requests
import json

from fastapi import APIRouter, HTTPException, Depends, Query
from src.utils.logger import log_exceptions
from src.schemas.chart import ChartResponse
from src.graphql.queries import chart_query_template
from typing import List
from src.config import settings
router = APIRouter(prefix="/toolcall", tags=["toolcalls"])

BITQUERY_URL = settings.BITQUERY_URL
BITQUERY_API_KEY = settings.BITQUERY_API_KEY


@router.get("/market-chart", response_model=ChartResponse)
@log_exceptions
def get_chart(mint_address: str = Query(..., description="Mint address of the token")):
    print(BITQUERY_API_KEY)
    print(BITQUERY_URL)
    query = {
        "query": chart_query_template.format(mint_address=mint_address),
        "variables": "{}"
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {BITQUERY_API_KEY}"
    }

    response = requests.post(BITQUERY_URL, headers=headers, data=json.dumps(query))

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Failed to fetch data from Bitquery")

    data = response.json()

    if "data" not in data or "Solana" not in data["data"] or "DEXTradeByTokens" not in data["data"]["Solana"]:
        raise HTTPException(status_code=400, detail="Invalid response from Bitquery")

    return {"data": data["data"]["Solana"]["DEXTradeByTokens"]}
