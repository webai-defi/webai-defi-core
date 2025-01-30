from fastapi import FastAPI

from src.routers import user
from src.routers import chat
from src.routers import toolcall
from src.config import settings
from src.db.session import Base, engine
from src.utils.chat import create_agent
import logging
import os
Base.metadata.create_all(bind=engine)

os.makedirs(settings.LOGS_URL, exist_ok=True)
logging.basicConfig(
    filename=settings.LOGS_FILE,
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

app = FastAPI()

def create_app() -> FastAPI:
    """Creates app instance"""
    application = FastAPI(
        title=settings.PROJECT_NAME,
        description=settings.PROJECT_DESC,
        openapi_url="/openapi.json",
        docs_url="/swagger",
    )

    routers = [user.router, chat.router, toolcall.router]
    for router in routers:
        application.include_router(router, prefix="/api")

    return application


app = create_app()

@app.on_event("startup")
async def startup_event():
    app.state.agent = await create_agent()
