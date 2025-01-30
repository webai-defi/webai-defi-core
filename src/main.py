import os
import logging

from fastapi import FastAPI

from src.routers import user
from src.routers import chat
from src.routers import toolcall
from src.config import settings
from src.db.session import Base, engine
from src.utils.chat import create_agent


logging.basicConfig(
    filename=os.path.join(settings.LOGS_URL, settings.LOGS_FILE),
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.DEBUG if settings.DEBUG_LOGS else logging.ERROR
)


logger = logging.getLogger(__name__) 
Base.metadata.create_all(bind=engine)

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
