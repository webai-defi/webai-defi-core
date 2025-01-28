from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from src.db.session import Base

class Chat(Base):
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    wallet_id = Column(String, ForeignKey("users.wallet_id"), nullable=False)
    history = relationship("ChatHistory", back_populates="chat")
    owner = relationship("User", back_populates="chats")