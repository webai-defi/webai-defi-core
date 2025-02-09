from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"] = Field(description="Role of message sender user/assistant")
    content: str = Field(description="Content of the message")

class ChatRequest(BaseModel):
    messages: List[ChatMessage] = Field(description="List of messages in current chat")

class ToolResponse(BaseModel):
    type: Literal["chart-and-stats", "stats-volume", "token-top", "backend"]
    endpoint: Optional[str] = Field(
        default=None, 
        description="Endpoint to call, if None - no endpoint needed", 
        example="/api/toolcall/market-chart"
    )
    args: Optional[dict] = Field(default=None, description="Args for desired endpoint, if None - no args needed")
    response: Optional[str] = Field(default=None, description="Predefined response of the tool, if None - agent is used")

class TokenVolumeToolRequest(BaseModel):
    token_ca: str
    timeframe: Optional[Literal["1m", "5m", "15m", "30m", "60m", "1d", "3d", "7d", "30d"]] = None

class ChatCreateUpdate(BaseModel):
    uuid: str = Field(description="uuid, generated on frontend")
    name: Optional[str] = None
    question: str = Field(description="Question from user")
    answer: str = Field(description="Answer from model")

class ChatResponse(BaseModel):
    id: int = Field(description="Internal id")
    uuid: str = Field(description="uuid, generated on frontend")
    name: str = Field(description="Chat name")
    wallet_id: str = Field(description="Wallet id (user id)")

    class Config:
        orm_mode = True

class ChatHistoryResponse(BaseModel):
    question: str = Field(description="Question from user")
    answer: str = Field(description="Answer from model")
    timestamp: datetime

    class Config:
        orm_mode = True