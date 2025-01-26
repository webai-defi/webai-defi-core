from fastapi import APIRouter, Depends
from starlette.responses import StreamingResponse

from src.schemas.chat import ChatMessage, ChatRequest
from src.config import settings
from src.utils.chat import get_agent, stream_response

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
async def generate(data: ChatRequest, agent_executor=Depends(get_agent)) -> str:
    return StreamingResponse(stream_response(agent_executor, data.messages), media_type="text/plain")
