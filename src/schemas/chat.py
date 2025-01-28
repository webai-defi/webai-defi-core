from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"] = Field(description="Role of message sender user/assistant")
    content: str = Field(description="Content of the message")

class ChatRequest(BaseModel):
    messages: List[ChatMessage] = Field(description="List of messages in current chat")

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