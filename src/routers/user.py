from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.db.session import get_async_db
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
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_async_db)):
    logger.info(f"Creating user with wallet_id: {user.wallet_id}")

    result = await db.execute(select(User).filter(User.wallet_id == user.wallet_id))
    db_user = result.scalars().first()
    if db_user:
        logger.warning(f"User with wallet_id {user.wallet_id} already exists")
        raise HTTPException(status_code=400, detail="User with this wallet_id already exists")

    new_user = User(wallet_id=user.wallet_id)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    logger.info(f"User {new_user.wallet_id} created successfully")
    return new_user


@router.get("/{wallet_id}", response_model=UserResponse)
@log_exceptions
async def login_user(wallet_id: str, db: AsyncSession = Depends(get_async_db)):
    logger.info(f"Fetching user with wallet_id: {wallet_id}")

    result = await db.execute(select(User).filter(User.wallet_id == wallet_id))
    db_user = result.scalars().first()
    if not db_user:
        logger.warning(f"User with wallet_id {wallet_id} not found")
        raise HTTPException(status_code=404, detail="User not found")

    logger.info(f"User {wallet_id} found")
    return db_user


@router.post("/chats/")
@log_exceptions
async def create_or_update_chat(chat_data: ChatCreateUpdate, wallet_id: str, db: AsyncSession = Depends(get_async_db)):
    logger.info(f"Creating or updating chat for wallet_id: {wallet_id}")

    result = await db.execute(select(Chat).filter(Chat.uuid == chat_data.uuid))
    db_chat = result.scalars().first()
    if not db_chat:
        logger.info(f"Chat not found with chat_uuid: {chat_data.uuid}, creating new")
        result = await db.execute(select(User).filter(User.wallet_id == wallet_id))
        db_user = result.scalars().first()
        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")

        db_chat = Chat(uuid=chat_data.uuid, name=chat_data.name or "New Chat", wallet_id=wallet_id)
        db.add(db_chat)
        await db.commit()
        await db.refresh(db_chat)

    new_question = ChatHistory(chat_id=db_chat.id, message=chat_data.question)
    new_answer = ChatHistory(chat_id=db_chat.id, message=chat_data.answer)
    db.add_all([new_question, new_answer])
    await db.commit()

    return {"status": "ok"}


@router.get("/chats/", response_model=List[ChatResponse])
@log_exceptions
async def get_chats(wallet_id: str, db: AsyncSession = Depends(get_async_db)):
    logger.info(f"Fetching chats for user: {wallet_id}")

    result = await db.execute(select(Chat).filter(Chat.wallet_id == wallet_id))
    db_chats = result.scalars().all()

    logger.info(f"Found {len(db_chats)} chats for user {wallet_id}")
    return db_chats


@router.get("/chats/{uuid}", response_model=List[ChatHistoryResponse])
@log_exceptions
async def get_chat_history(uuid: str, db: AsyncSession = Depends(get_async_db)):
    logger.info(f"Fetching chat history for chat {uuid}")

    result = await db.execute(select(Chat).filter(Chat.uuid == uuid))
    db_chat = result.scalars().first()
    if not db_chat:
        logger.warning(f"Chat {uuid} not found")
        raise HTTPException(status_code=404, detail="Chat not found")

    result = await db.execute(
        select(ChatHistory).filter(ChatHistory.chat_id == db_chat.id).order_by(ChatHistory.timestamp))
    history = result.scalars().all()

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