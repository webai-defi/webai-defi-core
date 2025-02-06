import logging
import requests
import json

from fastapi import APIRouter, HTTPException, Depends, Query
from src.utils.logger import log_exceptions
from src.schemas.chart import ChartResponse
from src.schemas.pumpfuntoptokens import PumpFunResponse
from src.graphql.queries import chart_query_template, pumpfun_token_sorted_by_marketcap
from typing import List, Optional
from src.config import settings

router = APIRouter(prefix="/toolcall", tags=["toolcalls"])

BITQUERY_URL = settings.BITQUERY_URL
BITQUERY_API_KEY = settings.BITQUERY_API_KEY

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {BITQUERY_API_KEY}"
}

def fetch_ipfs_metadata(uri: str) -> Optional[dict]:
    """Получает метаданные токена по IPFS URI."""
    try:
        response = requests.get(uri, timeout=5)
        if response.status_code == 200:
            return response.json() or {}
    except requests.RequestException as e:
        logging.error(f"Ошибка запроса к {uri}: {e}")
    return {}

@router.get("/market-chart", response_model=ChartResponse)
def get_chart(mint_address: str = Query(..., description="Mint address of the token"),
              interval: str = Query("1m", description="Time interval for the chart (1m, 5m, 15m, 30m, 60m, 1d, 3d, 7d, 30d)")):
    interval_mapping = {
        "1m": {"unit": "minutes", "count": 1},
        "5m": {"unit": "minutes", "count": 5},
        "15m": {"unit": "minutes", "count": 15},
        "30m": {"unit": "minutes", "count": 30},
        "60m": {"unit": "minutes", "count": 60},
        "1d": {"unit": "days", "count": 1},
        "3d": {"unit": "days", "count": 3},
        "7d": {"unit": "days", "count": 7},
        "30d": {"unit": "days", "count": 30},
    }

    if interval not in interval_mapping:
        raise HTTPException(status_code=400, detail="Invalid interval parameter")

    time_unit = interval_mapping[interval]["unit"]
    time_count = interval_mapping[interval]["count"]

    query = {
        "query": chart_query_template.format(mint_address=mint_address, time_unit=time_unit, time_count=time_count),
        "variables": "{}"
    }

    response = requests.post(BITQUERY_URL, headers=headers, data=json.dumps(query))

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Failed to fetch data from Bitquery")

    data = response.json()

    if "data" not in data or "Solana" not in data["data"] or "DEXTradeByTokens" not in data["data"]["Solana"]:
        raise HTTPException(status_code=400, detail="Invalid response from Bitquery")

    return {"data": data["data"]["Solana"]["DEXTradeByTokens"]}


@router.get("/pumpfun-top-tokens", response_model=PumpFunResponse)
@log_exceptions
def get_pumpfun_top_tokens():
    response = requests.post(BITQUERY_URL, headers=headers,
                             data=json.dumps({"query": pumpfun_token_sorted_by_marketcap, "variables": "{}"}))

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Failed to fetch data from Bitquery")

    data = response.json()

    if "data" not in data or "Solana" not in data["data"] or "DEXTrades" not in data["data"]["Solana"]:
        raise HTTPException(status_code=400, detail="Invalid response from Bitquery")

    trades = data["data"]["Solana"]["DEXTrades"]

    for trade in trades:
        uri = trade["Trade"]["Buy"]["Currency"].get("Uri")
        metadata = fetch_ipfs_metadata(uri) if uri else {}
        trade["Trade"]["Buy"]["Currency"].update({
            "description": metadata.get("description", ""),
            "image": metadata.get("image", ""),
            "twitter": metadata.get("twitter", ""),
            "website": metadata.get("website", ""),
            "createdOn": metadata.get("createdOn", "")
        })

    return {"data": trades}

