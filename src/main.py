import os
import time

from fastapi import FastAPI, Depends, Request
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
from redis import asyncio as aioredis

from src.routers import user
from src.routers import chat
from src.routers import toolcall
from src.config import settings
from src.db.session import Base, engine
from src.utils.chat import create_agent
from src.utils.logger import logger
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.middleware.cors import CORSMiddleware


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        logger.info(f"Incoming request: {request.method} {request.url} | Headers: {dict(request.headers)}")

        response = await call_next(request)

        process_time = time.time() - start_time
        logger.info(f"Response: {response.status_code} | Time: {process_time:.3f}s")

        return response

async def create_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

app = FastAPI()

def create_app() -> FastAPI:
    """Creates app instance"""
    application = FastAPI(
        title=settings.PROJECT_NAME,
        description=settings.PROJECT_DESC,
        openapi_url="/openapi.json",
        docs_url="/swagger",
    )

    application.add_middleware(LoggingMiddleware)

    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    routers = [user.router, chat.router, toolcall.router]
    for router in routers:
        application.include_router(
            router,
            prefix="/api",
            dependencies=[Depends(RateLimiter(times=20, seconds=60))],
        )

    return application


app = create_app()

@app.on_event("startup")
async def startup_event():
    app.state.agent = await create_agent()

    redis = await aioredis.from_url(
        f"redis://{settings.REDIS_HOST}",
        encoding="utf-8",
        decode_responses=True,
    )
    await FastAPILimiter.init(redis)
    await create_database()