import logging
import json
import httpx
import pandas as pd
import datetime
import pytz
import requests

from fastapi import APIRouter, HTTPException, Depends, Query
from src.utils.logger import log_exceptions, logger
from src.schemas.chart import ChartResponse
from src.schemas.tokenvolume import TokenVolumeResponse
from src.schemas.pumpfuntoptokens import PumpFunResponse
from src.schemas.topresponse import TopTradersResponse, TokenHoldersResponse, TrendingTokensResponse
from src.schemas.balance import WalletBalanceResponse
from src.graphql.queries import *
from typing import List, Optional, Dict
from src.config import settings
from urllib.parse import urlparse

router = APIRouter(prefix="/toolcall", tags=["toolcalls"])

BITQUERY_URL = settings.BITQUERY_URL
BITQUERY_API_KEY = settings.BITQUERY_API_KEY

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {BITQUERY_API_KEY}"
}

interval_mapping = {
    "1m": {"unit": "minutes", "count": 1},
    "5m": {"unit": "minutes", "count": 5},
    "15m": {"unit": "minutes", "count": 15},
    "30m": {"unit": "minutes", "count": 30},
    "60m": {"unit": "minutes", "count": 60},
    "1h": {"unit": "hours", "count": 1},
    "4h": {"unit": "hours", "count": 4},
    "6h": {"unit": "hours", "count": 6},
    "8h": {"unit": "hours", "count": 8},
    "12h": {"unit": "hours", "count": 12},
    "1d": {"unit": "days", "count": 1},
    "3d": {"unit": "days", "count": 3},
    "7d": {"unit": "days", "count": 7},
    "30d": {"unit": "days", "count": 30},
}


@router.get("/market-chart", response_model=ChartResponse)
async def get_chart(
    mint_address: str = Query(..., description="Mint address of the token"),
    interval: str = Query("4h", description="Time interval for the chart (1m, 5m, 15m, 30m, 60m, 1d, 3d, 7d, 30d)")
):
    if interval not in interval_mapping:
        interval = "4h"
        raise HTTPException(status_code=400, detail="Invalid interval parameter")

    time_unit = interval_mapping[interval]["unit"]
    time_count = interval_mapping[interval]["count"]

    key, value = await classify_input(mint_address)

    query = {
        "query": chart_query_template.format(key=key, value=value, time_unit=time_unit, time_count=time_count),
        "variables": "{}"
    }

    data = await fetch_bitquery(query)

    if "data" not in data or "Solana" not in data["data"] or "ohcl" not in data["data"]["Solana"]:
        raise HTTPException(status_code=400, detail="Invalid response from Bitquery")

    ohcl = data["data"]["Solana"]["ohcl"]
    token_info = data["data"]["Solana"]["token_info"][0]["Trade"]

    async with httpx.AsyncClient() as client:
        uri = token_info["Currency"].get("Uri")
        metadata = await fetch_ipfs_metadata(uri) if uri else {}
        token_info["Currency"].update({
            "description": metadata.get("description", ""),
            "image": metadata.get("image", ""),
            "twitter": metadata.get("twitter", ""),
            "website": metadata.get("website", ""),
            "createdOn": metadata.get("createdOn", "")
        })

    return {"data": {"ohcl": ohcl, "token_info": token_info}}



@router.get("/pumpfun-top-tokens", response_model=PumpFunResponse)
@log_exceptions
async def get_pumpfun_top_tokens():
    query = {
        "query": pumpfun_token_sorted_by_marketcap,
        "variables": "{}"
    }

    data = await fetch_bitquery(query)

    if "data" not in data or "Solana" not in data["data"] or "DEXTrades" not in data["data"]["Solana"]:
        raise HTTPException(status_code=400, detail="Invalid response from Bitquery")

    trades = data["data"]["Solana"]["DEXTrades"]

    async with httpx.AsyncClient() as client:
        for trade in trades:
            uri = trade["Trade"]["Buy"]["Currency"].get("Uri")
            metadata = await fetch_ipfs_metadata(uri) if uri else {}
            trade["Trade"]["Buy"]["Currency"].update({
                "description": metadata.get("description", ""),
                "image": metadata.get("image", ""),
                "twitter": metadata.get("twitter", ""),
                "website": metadata.get("website", ""),
                "createdOn": metadata.get("createdOn", "")
            })

    return {"data": trades}



@router.get("/token-volume", response_model=TokenVolumeResponse)
async def get_volume(
    mint_address: str = Query(..., description="Mint address of the token"),
    interval: str = Query("1d", description="Time interval for the chart (1m, 5m, 15m, 30m, 60m, 1d, 3d, 7d, 30d)")
):
    if interval not in interval_mapping:
        raise HTTPException(status_code=400, detail="Invalid interval parameter")

    time_unit = interval_mapping[interval]["unit"]
    time_count = interval_mapping[interval]["count"]

    now = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
    since_time = now - datetime.timedelta(**{time_unit: time_count})

    since_time_formatted = since_time.strftime("%Y-%m-%dT%H:%M:%SZ")
    now_time_formatted = now.strftime("%Y-%m-%dT%H:%M:%SZ")

    key, value = await classify_input(mint_address)

    query = {
        "query": token_info_template.format(
            key=key,
            value=value,
            since_time_formatted=since_time_formatted,
            now_time_formatted=now_time_formatted
        ),
        "variables": "{}"
    }

    data = await fetch_bitquery(query)

    if "data" not in data:
        raise HTTPException(status_code=400, detail="Invalid response from Bitquery")

    response_string = json.dumps(data["data"])
    return await calculate_volumes(response_string)

@router.get("/top-traders", response_model=TopTradersResponse)
async def get_top_traders(
    mint_address: str = Query(..., description="Mint address of the token"),
    interval: str = Query("1d", description="Time interval of the top (1m, 5m, 15m, 30m, 60m, 1d, 3d, 7d, 30d)")
):
    if interval not in interval_mapping:
        raise HTTPException(status_code=400, detail="Invalid interval parameter")

    time_unit = interval_mapping[interval]["unit"]
    time_count = interval_mapping[interval]["count"]

    now = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
    since_time = now - datetime.timedelta(**{time_unit: time_count})
    since_time_formatted = since_time.strftime("%Y-%m-%dT%H:%M:%SZ")

    key, value = await classify_input(mint_address)

    query = {
        "query": top_traders_template.format(key=key, value=value, since_time_formatted=since_time_formatted),
        "variables": "{}"
    }

    data = await fetch_bitquery(query)

    dex_trades = data.get("data", {}).get("Solana", {}).get("DEXTradeByTokens", [])
    if not dex_trades:
        raise HTTPException(status_code=400, detail="Invalid response from Bitquery")

    return {"data": dex_trades}


@router.get("/top-holders", response_model=TokenHoldersResponse)
async def get_token_holders(
    mint_address: str = Query(..., description="Mint address of the token"),
    interval: str = Query("1d", description="Time interval of the top (1m, 5m, 15m, 30m, 60m, 1d, 3d, 7d, 30d)")
):
    if interval not in interval_mapping:
        raise HTTPException(status_code=400, detail="Invalid interval parameter")

    time_unit = interval_mapping[interval]["unit"]
    time_count = interval_mapping[interval]["count"]

    now = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
    since_time = now - datetime.timedelta(**{time_unit: time_count})
    since_time_formatted = since_time.strftime("%Y-%m-%dT%H:%M:%SZ")

    key, value = await classify_input(mint_address)

    query = {
        "query": top_holders_template.format(key=key, value=value, since_time_formatted=since_time_formatted),
        "variables": "{}"
    }

    data = await fetch_bitquery(query)

    solana_data = data.get("data", {}).get("Solana", {})

    token_supply_update = solana_data.get("TokenSupplyUpdates", [{}])[0].get("TokenSupplyUpdate", {})
    post_balance = float(token_supply_update.get("PostBalance", "0"))

    top_holders = solana_data.get("Top_holders", [])
    processed_holders = []

    for holder in top_holders:
        balance_update = holder.get("BalanceUpdate", {})
        balance = float(balance_update.get("balance", "0"))
        balance_update["percentage_owned"] = (balance / post_balance * 100) if post_balance > 0 else 0
        processed_holders.append(balance_update)

    return {"data": {"TokenSupplyUpdates": token_supply_update, "Top_holders": processed_holders}}


@router.get("/trending-tokens", response_model=TrendingTokensResponse)
async def get_trending_tokens(
    interval: str = Query("1d", description="Time interval of the top (1m, 5m, 15m, 30m, 60m, 1d, 3d, 7d, 30d)")
):
    if interval not in interval_mapping:
        raise HTTPException(status_code=400, detail="Invalid interval parameter")

    time_unit = interval_mapping[interval]["unit"]
    time_count = interval_mapping[interval]["count"]

    now = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
    since_time = now - datetime.timedelta(**{time_unit: time_count})
    since_time_formatted = since_time.strftime("%Y-%m-%dT%H:%M:%SZ")

    query = {
        "query": top_trending_template.format(since_time_formatted=since_time_formatted),
        "variables": "{}"
    }

    data = await fetch_bitquery(query)

    trending_tokens = data.get("data", {}).get("Solana", {}).get("DEXTradeByTokens", [])

    if not trending_tokens:
        raise HTTPException(status_code=400, detail="Invalid response from Bitquery")

    for token in trending_tokens:
        price_last = token.get("Trade", {}).get("price_last", 0)
        price_1h_ago = token.get("Trade", {}).get("price_1h_ago", 0)
        token["price_change_percent"] = ((price_last - price_1h_ago) / price_1h_ago) * 100 if price_1h_ago > 0 else 0

    async with httpx.AsyncClient() as client:
        for token in trending_tokens:
            uri = token["Trade"]["Currency"].get("Uri")
            metadata = await fetch_ipfs_metadata(uri) if uri else {}
            token["Trade"]["Currency"].update({
                "description": metadata.get("description", ""),
                "image": metadata.get("image", ""),
                "twitter": metadata.get("twitter", ""),
                "website": metadata.get("website", ""),
                "createdOn": metadata.get("createdOn", "")
            })

    return {"data": trending_tokens}



@router.get("/wallet-balance", response_model=WalletBalanceResponse)
@log_exceptions
async def get_wallet_balance(
    mint_address: str = Query(..., description="Mint address of wallet")
):
    """Retrieve balance of wallet and modify it with ipfs data"""
    query = {
        "query": balance_template.format(mint_address=mint_address),
        "variables": "{}"
    }

    data = await fetch_bitquery(query)

    balance_updates = data.get("data", {}).get("Solana", {}).get("BalanceUpdates", [])

    # Exclude lines without uri
    balance_updates = [b for b in balance_updates if b["BalanceUpdate"]["Currency"]["Uri"]]

    # Modify with ipfs metadata
    async with httpx.AsyncClient() as client:
        for balance_update in balance_updates:
            uri = balance_update["BalanceUpdate"]["Currency"]["Uri"]
            metadata = await fetch_ipfs_metadata(uri) if uri else {}
            balance_update["BalanceUpdate"]["Currency"].update(metadata)

    result = {
        "data": {
            "BalanceUpdates": [
                {
                    "Balance": b["BalanceUpdate"]["Balance"],
                    "Currency": {
                        "MintAddress": b["BalanceUpdate"]["Currency"]["MintAddress"],
                        "Name": b["BalanceUpdate"]["Currency"].get("Name", ""),
                        "Symbol": b["BalanceUpdate"]["Currency"].get("Symbol", ""),
                        "Uri": b["BalanceUpdate"]["Currency"]["Uri"],
                        "description": b["BalanceUpdate"]["Currency"].get("description", ""),
                        "image": b["BalanceUpdate"]["Currency"].get("image", ""),
                        "twitter": b["BalanceUpdate"]["Currency"].get("twitter", ""),
                        "website": b["BalanceUpdate"]["Currency"].get("website", ""),
                        "createdOn": b["BalanceUpdate"]["Currency"].get("createdOn", "")
                    }
                }
                for b in balance_updates if "BalanceUpdate" in b and "Currency" in b["BalanceUpdate"]
            ]
        }
    }

    return result


IPFS_GATEWAYS = ["https://dweb.link", "https://ipfs.io", "https://cf-ipfs.com"]


async def fetch_ipfs_metadata(uri: str) -> Optional[Dict]:
    """Retrieve tokens metadata by  IPFS URI, using alternative gateways on errors."""
    parsed_uri = urlparse(uri)

    async with httpx.AsyncClient(follow_redirects=True) as client:
        try:
            response = await client.get(uri, timeout=5)

            if response.status_code == 302 and "Location" in response.headers:
                redirected_url = response.headers["Location"]
                logging.info(f"Redirect to {redirected_url}")
                response = await client.get(redirected_url, timeout=5)

            if response.status_code == 200:
                metadata = response.json() or {}

                if "image" in metadata and isinstance(metadata["image"], str):
                    return metadata
            else:
                logging.warning(f"Error code {response.status_code} for {uri}")
        except httpx.RequestError as e:
            logging.error(f"Bad request: {uri}. Error: {e}")

    # Проверяем, является ли URL IPFS-шлюзом
    ipfs_hash = None
    for gateway in IPFS_GATEWAYS:
        if parsed_uri.netloc in gateway:
            ipfs_hash = parsed_uri.path.lstrip("/ipfs/")
            break

    # Если не нашли в списке известных шлюзов, извлекаем хеш по умолчанию
    if not ipfs_hash:
        path_parts = parsed_uri.path.split('/')
        if "ipfs" in path_parts:
            ipfs_hash = path_parts[path_parts.index("ipfs") + 1]
        else:
            logging.error(f"Некорректный IPFS URI: {uri}")
            return {}

    async with httpx.AsyncClient() as client:
        for gateway in IPFS_GATEWAYS:
            new_uri = f"{gateway}/ipfs/{ipfs_hash}"
            try:
                response = await client.get(new_uri, timeout=5)
                if response.status_code == 200:
                    metadata = response.json() or {}

                    if "image" in metadata and isinstance(metadata["image"], str):
                        image_parsed = urlparse(metadata["image"])
                        for g in IPFS_GATEWAYS:
                            if image_parsed.netloc in g:
                                metadata["image"] = metadata["image"].replace(image_parsed.netloc, "ipfs.io")
                                break

                    return metadata
                else:
                    logging.warning(f"Неудачный статус {response.status_code} для {new_uri}")
            except httpx.RequestError as e:
                logging.error(f"Ошибка запроса к {new_uri}: {e}")

    return {}

async def fetch_bitquery(query):
    async with httpx.AsyncClient() as client:
        response = await client.post(BITQUERY_URL, headers=headers, json=query, timeout=30.0)

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Ошибка запроса к Bitquery")

    data = response.json()
    return data

async def calculate_volumes(response: str) -> TokenVolumeResponse:
    data = json.loads(response)

    trades = data.get("Solana", {}).get("DEXTradeByTokens", [])
    balance_updates = data.get("Solana", {}).get("BalanceUpdates", [])
    token_supply_updates = data.get("Solana", {}).get("TokenSupplyUpdates", [])

    if not trades:
        raise HTTPException(status_code=400, detail="No trade data found")

    df = pd.DataFrame(trades)

    df["currency"] = df["Trade"].apply(lambda x: x["Currency"]["Symbol"] if x else None)
    df["dex"] = df["Trade"].apply(lambda x: x["Dex"]["ProtocolName"] if x else None)
    df["market"] = df["Trade"].apply(lambda x: x["Market"]["MarketAddress"] if x else None)
    df["start_price"] = df["Trade"].apply(lambda x: x.get("start", 0) if x else 0)
    df["min5_price"] = df["Trade"].apply(lambda x: x.get("min5", 0) if x else 0)
    df["end_price"] = df["Trade"].apply(lambda x: x.get("end", 0) if x else 0)

    numeric_columns = ["buy_volume", "sell_volume", "traded_volume", "trades", "makers"]
    for col in numeric_columns:
        df[col] = pd.to_numeric(df.get(col, 0), errors="coerce").fillna(0)

    total_traded_volume = df["traded_volume"].sum()
    total_trades = df["trades"].sum()
    total_makers = df["makers"].sum()

    total_buy_volume = df["buy_volume"].sum()
    total_sell_volume = df["sell_volume"].sum()
    buy_percentage = (total_buy_volume / total_traded_volume) * 100 if total_traded_volume else 0
    sell_percentage = (total_sell_volume / total_traded_volume) * 100 if total_traded_volume else 0

    total_balance_updates = sum(int(update.get("count", 0)) for update in balance_updates)

    if token_supply_updates:
        post_balance = float(token_supply_updates[0]["TokenSupplyUpdate"].get("PostBalance", 0))
        post_balance_in_usd = float(token_supply_updates[0]["TokenSupplyUpdate"].get("PostBalanceInUSD", 0))
    else:
        post_balance = 0
        post_balance_in_usd = 0

    return TokenVolumeResponse(
        totalTradedVolume=total_traded_volume,
        averageTradeSize=total_traded_volume / total_trades if total_trades else 0,
        priceChangePercentage=((df["end_price"].mean() - df["start_price"].mean()) / df["start_price"].mean()) * 100 if df["start_price"].mean() else 0,
        buySellRatio=total_buy_volume / total_sell_volume if total_sell_volume else 0,
        averageTradesPerMaker=total_trades / total_makers if total_makers else 0,
        averageVolumePerMaker=total_traded_volume / total_makers if total_makers else 0,
        uniqueDexPlatforms=df["dex"].nunique(),
        averageVolumeByDex=df.groupby("dex")["traded_volume"].sum().to_dict(),
        liquidity=total_traded_volume,
        totalBuyVolume=total_buy_volume,
        totalSellVolume=total_sell_volume,
        buyPercentage=buy_percentage,
        sellPercentage=sell_percentage,
        holdersCount=total_balance_updates,
        marketCap=post_balance,
        marketCapInUSD=post_balance_in_usd
    )

async def classify_input(mint_address: str):
    if mint_address.startswith("$"):
        key = "Symbol"
        #value = mint_address - тикеры в битквери можно отправлять и с долларом и без, но кажется без находит реальные токены
        value = mint_address[1:].upper()
        query = {
            "query": find_ca_by_symbol_template.format(value=value),
            "variables": "{}"
        }
        data = await fetch_bitquery(query)

        data = data.get("data", {}).get("Solana", {}).get("TokenSupplyUpdates", [])
        if data:
            key = "MintAddress"
            value = data[0]["TokenSupplyUpdate"]["Currency"]["MintAddress"]

    elif len(mint_address) <= 6 and " " not in mint_address:
        key = "Symbol"
        #value = f"${mint_address}"
        value = mint_address.upper()

        query = {
            "query": find_ca_by_symbol_template.format(value=value),
            "variables": "{}"
        }
        data = await fetch_bitquery(query)

        data = data.get("data", {}).get("Solana", {}).get("TokenSupplyUpdates", [])
        if data:
            key = "MintAddress"
            value = data[0]["TokenSupplyUpdate"]["Currency"]["MintAddress"]

    elif " " in mint_address or mint_address.isalpha():
        key = "Name"
        value = mint_address
    else:
        key = "MintAddress"
        value = mint_address
    return key, value