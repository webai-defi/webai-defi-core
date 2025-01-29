import asyncio

from langchain import hub
from fastapi import Request
from langchain_core.tools import Tool
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_tool_calling_agent

from src.config import settings
from src.schemas.chat import ChatMessage
from src.utils.websearch import ai_websearch
from time import sleep

def search(search_query: str) -> str:
    """Perform a web search for provided search query"""
    return ai_websearch(search_query)


async def create_agent():
    tools = [
        Tool(
            name="WebSearch",
            func=search,
            description="Perform a web search for provided search query"
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
    response = None
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
            print(content, end="|")
            if content:
                yield content


def mock_responses(input_message: str) -> str:
    match input_message:
        case "  how to buy bitcoin":
            return "very easy, ligma balls"
        case _:
            return None
        

def word_generator(input_string):
    words = input_string.split()
    for word in words:
        sleep(0.05)
        yield word + " "