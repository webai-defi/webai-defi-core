from fastapi import FastAPI
from src.db.session import Base, engine
from src.routers import user

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(user.router, prefix="/api", tags=["users"])