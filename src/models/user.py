from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from src.db.session import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    wallet_id = Column(String, unique=True, nullable=False)
    chats = relationship("Chat", back_populates="owner")