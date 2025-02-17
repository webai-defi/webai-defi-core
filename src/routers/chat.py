import logging

from fastapi import APIRouter, Depends
from starlette.responses import StreamingResponse

from src.schemas.chat import ChatMessage, ChatRequest
from src.config import settings
from src.utils.chat import get_agent, stream_response
from src.utils.logger import log_exceptions

router = APIRouter(prefix="/chat", tags=["chats"])


@router.post("/generate", responses={
    200: {
        "description": "Streamed response with tokens",
        "content": {
            "text/plain": {
                "example": "Hello world! This is a streamed response."
            }
        }
    }
})
@log_exceptions
async def generate(data: ChatRequest, agent_executor=Depends(get_agent)) -> str:
    logging.info(f"Request to /generate {data}")
    return StreamingResponse(stream_response(agent_executor, data.messages), media_type="text/plain")
