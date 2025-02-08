import asyncio

from time import sleep
from typing import Optional, Literal
from langchain import hub
from fastapi import Request
from langchain_core.tools import Tool
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_tool_calling_agent

from src.pasta import CHART_DETAILS_PASTA, TOP_PUMPFUN_TOKENS_BY_MARKET_CAP, TOKEN_VOLUME
from src.mock_chats_config import MOCK_CHATS_CONFIG
from src.config import settings
from src.schemas.chat import ChatMessage, ToolResponse
from src.utils.websearch import ai_websearch


def sync_search(search_query: str) -> ToolResponse:
    """Synchronous wrapper for async search function"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        search_results = loop.run_until_complete(search(search_query))
        return ToolResponse(type="backend", response=search_results)
    finally:
        loop.close()


async def search(search_query: str) -> str:
    """Perform a web search for provided search query"""
    return await ai_websearch(search_query)


def chart_details_and_stats(token_ca: str) -> ToolResponse:
    """Extract token ca from user question for further processing
    Calling this function will result in widget trigger for user, which shows token chart and stats
    you MUST answer to user question only with text from response field
    in the output of this function"""
    return ToolResponse(
        type="chart-and-stats",
        endpoint="/api/toolcall/market-chart",
        args= {
            "token_ca": token_ca
        },
        response=CHART_DETAILS_PASTA.format(token_ca=token_ca)
    )


def top_pump_fun_tokens_by_market_cap(*args, **kwargs) -> ToolResponse:
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


def top_trading_tokens(*args, **kwargs) -> ToolResponse:
    """Get top trading tokens from DEX?
    Calling this function will result in widget trigger for user,
    you MUST answer to user question only with text from response field
    in the output of this function
    """
    return ToolResponse(
        type="token-top",
        endpoint="/api/toolcall/top-trading-tokens",
        response=TOP_PUMPFUN_TOKENS_BY_MARKET_CAP
    )


def token_volume(
    token_ca: str, 
    timeframe: Optional[Literal["1h", "4h", "8h", "16h", "24h", "2d", "7d"]] = None
) -> ToolResponse:
    """Extract token ca and timeframe (if presented) from user question for further processing
    The timeframes might be None or one of the following "1h", "4h", "8h", "16h", "24h", "2d", "7d",
    where h - hours, d - days.
    Calling this function will result in widget trigger for user,
    you MUST answer to user question only with text from response field
    in the output of this function"""
    return ToolResponse(
        type="stat-volume",
        endpoint="/api/toolcall/token-volume",
        args= {
            "token_ca": token_ca,
            "timeframe": timeframe
        },
        response=TOKEN_VOLUME.format(token_ca=token_ca)
    )


async def create_agent():
    tools = [
        Tool(
            name="WebSearch",
            func=sync_search,
            description="Perform a web search for provided search query"
        ),
        Tool(
            name="ChartDetailsAndStats",
            func=chart_details_and_stats,
            description="Extract token ca from user question for further processing, example: '2Bs4MW8NKBDy6Bsn2RmGLNYNn4ofccVWMHEiRcVvpump'"
        ),
        Tool(
            name="TopPumpFunTokensByMarketCap",
            func=top_pump_fun_tokens_by_market_cap,
            description="Get top PumpFun tokens by market capitalization"
        ),
        Tool(
            name="TopTradingTokens",
            func=top_pump_fun_tokens_by_market_cap,
            description="Get top trading tokens by market capitalization"
        ),
        Tool(
            name="TokenVolume",
            func=token_volume,
            description="Extract token ca and timeframe (if presented) from user question for further processing, example of ca: '2Bs4MW8NKBDy6Bsn2RmGLNYNn4ofccVWMHEiRcVvpump'"
        )
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
        elif kind == "on_tool_end":
            yield str(event) + "\n"
            

def mock_responses(input_message: str) -> Optional[str]:
    return MOCK_CHATS_CONFIG.get(input_message, None)
    

def word_generator(input_string):
    words = input_string.split()
    for word in words:
        sleep(0.05)
        yield word + " "
