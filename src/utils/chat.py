import json
import logging
import asyncio

from time import sleep
from typing import Optional, Literal
from langchain import hub
from fastapi import Request
from langchain_core.tools import Tool, StructuredTool
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_tool_calling_agent

from src.pasta import (
    CHART_DETAILS_PASTA, 
    TOP_PUMPFUN_TOKENS_BY_MARKET_CAP, 
    TOKEN_VOLUME, 
    TOP_TOKEN_HOLDERS,
    TOP_TOKEN_TRADERS,
    WALLET_BALANCE,
    )
from src.mock_chats_config import MOCK_CHATS_CONFIG
from src.config import settings
from src.schemas.chat import ChatMessage, ToolResponse, TokenSwapModel, ToolRequestWithTokenAndTimeframe
from src.utils.websearch import perplexity_search, deep_research_twitter, web_deep_search


async def chart_details_and_stats(
    token_ca: str, 
    timeframe: Optional[str] = None
) -> ToolResponse:
    """Extract token ca from user question for further processing
    Calling this function will result in widget trigger for user, which shows token chart and stats
    you MUST answer to user question only with text from response field
    in the output of this function"""
    args = {
        "mint_address": token_ca,
    }
    
    if timeframe in settings.TIME_INTERVALS:
        args["interval"] = timeframe

    return ToolResponse(
        type="chart-and-stats",
        endpoint="/api/toolcall/market-chart",
        args=args,
        response=CHART_DETAILS_PASTA.format(token_ca=token_ca)
    )


async def tokens_holded_by_wallet(mint_address: str) -> ToolResponse:
    """Extract wallet mint address from user question for further processing
    Calling this function will result in widget trigger for user, which shows
    tokens and their volumes holded by a wallet
    you MUST answer to user question only with text from response field
    in the output of this function"""
    return ToolResponse(
        type="tokens-holded-by-wallet",
        endpoint="/api/toolcall/wallet-balance",
        args= {
            "mint_address": mint_address
        },
        response=WALLET_BALANCE.format(mint_address=mint_address)
    )


async def top_pump_fun_tokens_by_market_cap(*args, **kwargs) -> ToolResponse:
    """Get top PumpFun tokens by market capitalization
    Calling this function will result in widget trigger for user,
    you MUST answer to user question only with text from response field
    in the output of this function
    """
    return ToolResponse(
        type="token-top",
        endpoint="/api/toolcall/pumpfun-top-tokens",
        response=TOP_PUMPFUN_TOKENS_BY_MARKET_CAP
    )


async def top_trending_tokens(timeframe: Optional[str] = None) -> ToolResponse:
    """Get top trending tokens from DEX
    Calling this function will result in widget trigger for user,
    you MUST answer to user question only with text from response field
    in the output of this function
    """
    if timeframe in settings.TIME_INTERVALS:
        return ToolResponse(
            type="token-top",
            endpoint="/api/toolcall/trending-tokens",
            args= {
                "interval": timeframe if timeframe in settings.TIME_INTERVALS else None
            },
            response=TOP_PUMPFUN_TOKENS_BY_MARKET_CAP
        )
    else:
        return ToolResponse(
            type="token-top",
            endpoint="/api/toolcall/trending-tokens",
            response=TOP_PUMPFUN_TOKENS_BY_MARKET_CAP
        )


async def top_token_traders(
    token_ca: str, 
    timeframe: Optional[str] = None
) -> ToolResponse:
    """Extract token ca and timeframe (if presented) from user question for further processing
    Calling this function will result in widget trigger for user,
    you MUST answer to user question only with text from response field
    in the output of this function"""
    args = {
        "mint_address": token_ca,
    }
    
    if timeframe in settings.TIME_INTERVALS:
        args["interval"] = timeframe

    return ToolResponse(
        type="top-traders",
        endpoint="/api/toolcall/top-traders",
        args=args,
        response=TOP_TOKEN_TRADERS.format(token_ca=token_ca)
    )

async def top_token_holders(
    token_ca: str, 
    timeframe: Optional[str] = None
) -> ToolResponse:
    """Extract token ca and timeframe (if presented) from user question for further processing
    Calling this function will result in widget trigger for user,
    you MUST answer to user question only with text from response field
    in the output of this function"""
    args = {
        "mint_address": token_ca,
    }
    
    if timeframe in settings.TIME_INTERVALS:
        args["interval"] = timeframe

    return ToolResponse(
        type="top-holders",
        endpoint="/api/toolcall/top-holders",
        args=args,
        response=TOP_TOKEN_HOLDERS.format(token_ca=token_ca)
    )

async def token_volume(
    token_ca: str, 
    timeframe: Optional[str] = None
) -> ToolResponse:
    """Extract token ca and timeframe (if presented) from user question for further processing
    Calling this function will result in widget trigger for user,
    you MUST answer to user question only with text from response field
    in the output of this function"""
    args = {
        "mint_address": token_ca,
    }
    
    if timeframe in settings.TIME_INTERVALS:
        args["interval"] = timeframe

    return ToolResponse(
        type="stats-volume",
        endpoint="/api/toolcall/token-volume",
        args=args,
        response=TOKEN_VOLUME.format(token_ca=token_ca)
    )

async def swap_tokens(
    swapA: str,
    swapB: str
) -> ToolResponse:
    """Initiate token swap between two assets. 
    Calling this function will trigger swap interface for user.
    You MUST answer with text from response field.
    
    Args:
        swapA: Address or symbol of token to swap FROM (required)
        swapB: Address or symbol of token to swap TO (required)
    """
    return ToolResponse(
        type="swap",
        endpoint=None,
        args={
            "swapA": swapA,
            "swapB": swapB
        },
        response=f"I've prepared the swap interface for you to exchange {swapA} for {swapB}. Please review the details and confirm the transaction."
    )


async def create_agent():
    tools = [
        Tool(
            name="PerplexitySearch",
            func=perplexity_search,
            coroutine=perplexity_search,
            description="Perform a search using Perplexity"
        ),
        Tool(
            name="DeepResearchTwitter",
            func=deep_research_twitter,
            coroutine=deep_research_twitter,
            description="Perform a deep research on Twitter. Useful for understanding trends, sentiments, and expert opinions."
        ),
        Tool(
            name="WebDeepSearch",
            func=web_deep_search,
            coroutine=web_deep_search,
            description="Perform a search using Perplexity, very deep and advanced mode, use only for two-three level questions cause it works 20 seconds"
        ),
        Tool(
            name="TokenBalanceAndTokens",
            func=tokens_holded_by_wallet,
            coroutine=tokens_holded_by_wallet,
            description="Extract wallet mint address for further processing: retrieving wallet balance and tokens holded by it"
        ),
        Tool(
            name="TopPumpFunTokensByMarketCap",
            func=top_pump_fun_tokens_by_market_cap,
            coroutine=top_pump_fun_tokens_by_market_cap,
            description="Get top PumpFun tokens by market capitalization",
        ),
        Tool(
            name="TopTrendingTokens",
            func=top_trending_tokens,
            coroutine=top_trending_tokens,
            description="""Get top trending tokens, you have to extract timeframe (if presented) from user question for further processing, timeframe might be None or one of the following "1m", "5m", "15m", "30m", "60m", "1h", "4h", "6h", "8h", "12h", "1d", "3d", "7d", "30d" where m - minutes, d - days."""
        ),
        StructuredTool(
            name="ChartDetailsAndStats",
            func=chart_details_and_stats,
            coroutine=chart_details_and_stats,
            args_schema=ToolRequestWithTokenAndTimeframe,
            description="""Extract token ca and timeframe (if presented) from user question for further processing, example of ca: '2Bs4MW8NKBDy6Bsn2RmGLNYNn4ofccVWMHEiRcVvpump', timeframe might be None or one of the following "1m", "5m", "15m", "30m", "60m", "1h", "4h", "6h", "8h", "12h", "1d", "3d", "7d", "30d" where m - minutes, d - days."""
        ),
        # StructuredTool(
        #     name="TokenVolume",
        #     func=token_volume,
        #     coroutine=token_volume,
        #     args_schema=ToolRequestWithTokenAndTimeframe,
        #     description="""Extract token ca and timeframe (if presented) from user question to retrieve token volume, example of ca: '2Bs4MW8NKBDy6Bsn2RmGLNYNn4ofccVWMHEiRcVvpump', timeframe might be None or one of the following "1m", "5m", "15m", "30m", "60m", "1h", "4h", "6h", "8h", "12h", "1d", "3d", "7d", "30d" where m - minutes, d - days."""
        # ),
        StructuredTool(
            name="TopTokenTraders",
            func=top_token_traders,
            coroutine=top_token_traders,
            args_schema=ToolRequestWithTokenAndTimeframe,
            description="""Extract token ca and timeframe (if presented) from user question to retrieve top token traders, example of ca: '2Bs4MW8NKBDy6Bsn2RmGLNYNn4ofccVWMHEiRcVvpump', timeframe might be None or one of the following "1m", "5m", "15m", "30m", "60m", "1h", "4h", "6h", "8h", "12h", "1d", "3d", "7d", "30d" where m - minutes, d - days."""
        ),
        StructuredTool(
            name="TopTokenHolders",
            func=top_token_holders,
            coroutine=top_token_holders,
            args_schema=ToolRequestWithTokenAndTimeframe,
            description="""Extract token ca and timeframe (if presented) from user question to retrieve top token holders, example of ca: '2Bs4MW8NKBDy6Bsn2RmGLNYNn4ofccVWMHEiRcVvpump', timeframe might be None or one of the following "1m", "5m", "15m", "30m", "60m", "1h", "4h", "6h", "8h", "12h", "1d", "3d", "7d", "30d" where m - minutes, d - days."""
        ),
        StructuredTool.from_function(
            name="TokenSwap",
            func=swap_tokens,
            coroutine=swap_tokens,
            description="Initiate token swap between two assets. Requires EXACTLY TWO parameters: swapA (token to swap from) and swapB (token to swap to). Must use format: 'TokenSwap' with {'swapA': 'TOKEN1', 'swapB': 'TOKEN2'}. Example: 'Swap BTC to SOL' becomes swapA='BTC', swapB='SOL'",
            args_schema=TokenSwapModel
        ),
    ]
    llm = ChatOpenAI(
        temperature=settings.TEMPERATURE, 
        model=settings.MODEL, 
        streaming=settings.STREAMING
    )
    prompt = hub.pull("hwchase17/openai-tools-agent")
    agent = create_tool_calling_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    return agent_executor


def get_agent(request: Request) -> AgentExecutor:
    agent = request.app.state.agent
    if asyncio.iscoroutine(agent):
        raise RuntimeError("Agent was not properly initialized. Please check the startup event.")
    return agent


async def stream_response(agent_executor: AgentExecutor, messages: list[ChatMessage]):
    tools_used_num = 0
    input_message = messages[-1] if messages else None
    chat_history = messages[:-1]

    if not input_message:
        raise ValueError("Messages list is empty. Cannot process the request.")
    
    input_text = input_message.content
    if input_text.startswith("  "):
        response = mock_responses(input_text)

        if response:
            for word in word_generator(response):
                yield word
            return

    history = [{"role": msg.role, "content": msg.content} for msg in chat_history]
    async for event in agent_executor.astream_events(
        {"input": input_text, "chat_history": history},
        version="v1",
    ):
        kind = event["event"]
        if kind == "on_chat_model_stream":
            content = event["data"]["chunk"].content
            if content:
                yield content
        elif kind == "on_tool_start" and "input" in event["data"]:
            # Пропускаем начало выполнения инструментов
            continue
        elif kind == "on_tool_end":
            output_data = event["data"].get("output", {})
            logging.info(f"Used tool {output_data}")
            tool_name = event.get("name", "")
            
            if tool_name in ["PerplexitySearch", "DeepResearchTwitter", "WebDeepSearch"]:
                # Для поисковых инструментов возвращаем только текстовый ответ от гпт-шки
                continue
            else:
                # Для остальных инструментов сохраняем оригинальное поведение
                if hasattr(output_data, "dict"):
                    if tools_used_num < settings.MAX_NUM_OF_TOOLS:
                        event["data"]["output"] = output_data.dict()
                        tools_used_num += 1
                        yield json.dumps(event) + "\n"
            

def mock_responses(input_message: str) -> Optional[str]:
    return MOCK_CHATS_CONFIG.get(input_message, None)
    

def word_generator(input_string):
    words = input_string.split()
    for word in words:
        sleep(0.05)
        yield word + " "
