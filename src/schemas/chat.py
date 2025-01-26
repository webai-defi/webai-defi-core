from pydantic import BaseModel, Field
from typing import List, Literal


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"] = Field(description="Role of message sender user/assistant")
    content: str = Field(description="Content of the message")

class ChatRequest(BaseModel):
    messages: List[ChatMessage] = Field(description="List of messages in current chat")