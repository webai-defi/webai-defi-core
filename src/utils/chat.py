import asyncio

from time import sleep
from typing import Optional
from langchain import hub
from fastapi import Request
from langchain_core.tools import Tool, StructuredTool
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_tool_calling_agent

from src.pasta import CHART_DETAILS_PASTA, TOP_PUMPFUN_TOKENS_BY_MARKET_CAP
from src.mock_chats_config import MOCK_CHATS_CONFIG
from src.config import settings
from src.schemas.chat import ChatMessage, ToolResponse, TokenSwapModel
from src.utils.websearch import perplexity_search, deep_research_twitter, web_deep_search


def chart_details(token_ca: str) -> ToolResponse:
    """Extract token ca from user question for further processing
    Calling this function will result in widget trigger for user,
    you MUST answer to user question only with text from response field
    in the output of this function"""
    return ToolResponse(
        type="chart",
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


def swap_tokens(
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
            description="Perform a search using Perplexity, very deep and advanced mode"
        ),
        Tool(
            name="ChartDetails",
            func=chart_details,
            description="Extract token ca from user question for further processing, example: '2Bs4MW8NKBDy6Bsn2RmGLNYNn4ofccVWMHEiRcVvpump'"
        ),
        Tool(
            name="TopPumpFunTokensByMarketCap",
            func=top_pump_fun_tokens_by_market_cap,
            description="Get top PumpFun tokens by market capitalization"
        ),
        StructuredTool.from_function(
            name="TokenSwap",
            func=swap_tokens,
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
