import logging
import requests
import json
import pandas as pd
import datetime
import pytz

from fastapi import APIRouter, HTTPException, Depends, Query
from src.utils.logger import log_exceptions, logger
from src.schemas.chart import ChartResponse
from src.schemas.tokenvolume import TokenVolumeResponse
from src.schemas.pumpfuntoptokens import PumpFunResponse
from src.graphql.queries import chart_query_template, pumpfun_token_sorted_by_marketcap, token_info_by_mint_address_template
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
    "1d": {"unit": "days", "count": 1},
    "3d": {"unit": "days", "count": 3},
    "7d": {"unit": "days", "count": 7},
    "30d": {"unit": "days", "count": 30},
}


@router.get("/market-chart", response_model=ChartResponse)
def get_chart(mint_address: str = Query(..., description="Mint address of the token"),
              interval: str = Query("1m", description="Time interval for the chart (1m, 5m, 15m, 30m, 60m, 1d, 3d, 7d, 30d)")):

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

@router.get("/token-volume", response_model=TokenVolumeResponse)
def get_volume(
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
    query = {
        "query": token_info_by_mint_address_template.format(mint_address=mint_address, since_time_formatted=since_time_formatted, now_time_formatted=now_time_formatted),
        "variables": "{}"
    }

    response = requests.post(BITQUERY_URL, headers=headers, data=json.dumps(query))
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Failed to fetch data from Bitquery")
    response_json = response.json()
    response_string =  str(response_json['data']).replace('\'', '"')
    return calculate_volumes(response_string)


IPFS_GATEWAYS = ["https://dweb.link", "https://ipfs.io", "https://cf-ipfs.com"]

def fetch_ipfs_metadata(uri: str) -> Optional[Dict]:
    """Получает метаданные токена по IPFS URI, используя альтернативные шлюзы при ошибках."""
    parsed_uri = urlparse(uri)

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

    for gateway in IPFS_GATEWAYS:
        new_uri = f"{gateway}/ipfs/{ipfs_hash}"
        try:
            response = requests.get(new_uri, timeout=5)
            if response.status_code == 200:
                metadata = response.json() or {}

                # Заменяем ссылку в `image` на ipfs.io
                if "image" in metadata and isinstance(metadata["image"], str):
                    image_parsed = urlparse(metadata["image"])
                    for g in IPFS_GATEWAYS:
                        if image_parsed.netloc in g:
                            metadata["image"] = metadata["image"].replace(image_parsed.netloc, "ipfs.io")
                            break

                return metadata
            else:
                logging.warning(f"Неудачный статус {response.status_code} для {new_uri}")
        except requests.RequestException as e:
            logging.error(f"Ошибка запроса к {new_uri}: {e}")

    return {}

def calculate_volumes(response):
    data = json.loads(response)

    trades = data.get("Solana", {}).get("DEXTradeByTokens", [])
    balance_updates = data.get("Solana", {}).get("BalanceUpdates", [])
    token_supply_updates = data.get("Solana", {}).get("TokenSupplyUpdates", [])

    if not trades:
        logging.error(f"Нет данных для анализа. {mint_address}")
        return {}

    # Создаем DataFrame
    df = pd.DataFrame(trades)

    # Раскрываем вложенные объекты
    df["currency"] = df["Trade"].apply(lambda x: x["Currency"]["Symbol"] if x else None)
    df["dex"] = df["Trade"].apply(lambda x: x["Dex"]["ProtocolName"] if x else None)
    df["market"] = df["Trade"].apply(lambda x: x["Market"]["MarketAddress"] if x else None)
    df["start_price"] = df["Trade"].apply(lambda x: x.get("start", 0) if x else 0)
    df["min5_price"] = df["Trade"].apply(lambda x: x.get("min5", 0) if x else 0)
    df["end_price"] = df["Trade"].apply(lambda x: x.get("end", 0) if x else 0)

    # Преобразуем столбцы в числовой формат, заполняя NaN значением 0
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

    # Обработка BalanceUpdates
    total_balance_updates = sum(int(update.get("count", 0)) for update in balance_updates)

    # Обработка TokenSupplyUpdates
    if token_supply_updates:
        post_balance = float(token_supply_updates[0]["TokenSupplyUpdate"].get("PostBalance", 0))
        post_balance_in_usd = float(token_supply_updates[0]["TokenSupplyUpdate"].get("PostBalanceInUSD", 0))
    else:
        post_balance = 0
        post_balance_in_usd = 0

    # Вычисление метрик
    result = {
        "Общий объем торгов (USD)": total_traded_volume,
        "Средний объем сделки (USD)": total_traded_volume / total_trades if total_trades else 0,
        "Изменение цены (%)": ((df["end_price"].mean() - df["start_price"].mean()) / df["start_price"].mean()) * 100 if df["start_price"].mean() else 0,
        "Buy/Sell Ratio": total_buy_volume / total_sell_volume if total_sell_volume else 0,
        "Среднее число сделок на одного трейдера": total_trades / total_makers if total_makers else 0,
        "Средний объем на одного трейдера (USD)": total_traded_volume / total_makers if total_makers else 0,
        "Количество уникальных DEX-платформ": df["dex"].nunique(),
        "Средний объем торгов на DEX": df.groupby("dex")["traded_volume"].sum().to_dict(),
        "Ликвидность (Liquidity, USD)": total_traded_volume,
        "Общий объем покупок (USD)": total_buy_volume,
        "Общий объем продаж (USD)": total_sell_volume,
        "Процент покупок (%)": buy_percentage,
        "Процент продаж (%)": sell_percentage,
        "Число холдеров": total_balance_updates,
        "Текущий баланс токена": post_balance,
        "Текущий баланс токена в USD": post_balance_in_usd
    }

    # Вывод результатов
    for key, value in result.items():
        logging.info(f"{key}: {value}")

    return TokenVolumeResponse(
        totalTradedVolume=total_traded_volume,
        averageTradeSize=total_traded_volume / total_trades if total_trades else 0,
        priceChangePercentage=((df["end_price"].mean() - df["start_price"].mean()) / df["start_price"].mean()) * 100 if
        df["start_price"].mean() else 0,
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