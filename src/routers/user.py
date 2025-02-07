from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from src.db.session import get_db
from src.models.user import User
from src.models.chat import Chat
from src.models.chat_history import ChatHistory
from src.schemas.user import UserCreate, UserResponse
from src.schemas.chat import ChatResponse, ChatCreateUpdate, ChatHistoryResponse
from src.utils.logger import log_exceptions, logger

from typing import List

router = APIRouter(prefix="/user", tags=["users"])


@router.post("/", response_model=UserResponse)
@log_exceptions
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    logger.info(f"Creating user with wallet_id: {user.wallet_id}")

    db_user = db.query(User).filter(User.wallet_id == user.wallet_id).first()
    if db_user:
        logger.warning(f"User with wallet_id {user.wallet_id} already exists")
        raise HTTPException(status_code=400, detail="User with this wallet_id already exists")

    new_user = User(wallet_id=user.wallet_id)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    logger.info(f"User {new_user.wallet_id} created successfully")
    return new_user


@router.get("/{wallet_id}", response_model=UserResponse)
@log_exceptions
def login_user(wallet_id: str, db: Session = Depends(get_db)):
    logger.info(f"Fetching user with wallet_id: {wallet_id}")

    db_user = db.query(User).filter(User.wallet_id == wallet_id).first()
    if not db_user:
        logger.warning(f"User with wallet_id {wallet_id} not found")
        raise HTTPException(status_code=404, detail="User not found")

    logger.info(f"User {wallet_id} found")
    return db_user

@router.post("/chats/",
             description="Create a new chat or update an existing one based on the provided UUID from frontend. "
                         "Adds new question and answer messages to the chat history.")
@log_exceptions
def create_or_update_chat(chat_data: ChatCreateUpdate, wallet_id: str, db: Session = Depends(get_db)):
    logger.info(f"Creating or updating chat for wallet_id: {wallet_id}")
    db_chat = db.query(Chat).filter(Chat.uuid == chat_data.uuid).first()
    if not db_chat:
        logger.info(f"Chat not found with chat_uuid: {chat_data.uuid}, creating new")
        db_user = db.query(User).filter(User.wallet_id == wallet_id).first()
        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")
        db_chat = Chat(uuid=chat_data.uuid, name=chat_data.name or "New Chat", wallet_id=wallet_id)
        db.add(db_chat)
        db.commit()
        db.refresh(db_chat)
    new_question = ChatHistory(chat_id=db_chat.id, message=chat_data.question)
    new_answer = ChatHistory(chat_id=db_chat.id, message=chat_data.answer)
    db.add_all([new_question, new_answer])
    db.commit()
    return {"status": "ok"}

@router.get("/chats/", response_model=List[ChatResponse])
@log_exceptions
def get_chats(wallet_id: str, db: Session = Depends(get_db)):
    logger.info(f"Fetching chats for user: {wallet_id}")

    db_chats = db.query(Chat).filter(Chat.wallet_id == wallet_id).all()
    logger.info(f"Found {len(db_chats)} chats for user {wallet_id}")

    return db_chats


@router.get("/chats/{uuid}", response_model=List[ChatHistoryResponse])
@log_exceptions
def get_chat_history(uuid: str, db: Session = Depends(get_db)):
    logger.info(f"Fetching chat history for chat {uuid}")

    db_chat = db.query(Chat).filter(Chat.uuid == uuid).first()
    if not db_chat:
        logger.warning(f"Chat {uuid} not found")
        raise HTTPException(status_code=404, detail="Chat not found")

    history = db.query(ChatHistory).filter(ChatHistory.chat_id == db_chat.id).order_by(ChatHistory.timestamp).all()
    logger.info(f"Chat history for {uuid}: {len(history)} messages")

    response = []
    for i in range(0, len(history), 2):
        if i + 1 < len(history):
            response.append({
                "question": history[i].message,
                "answer": history[i + 1].message,
                "timestamp": history[i + 1].timestamp,
            })

    return response
