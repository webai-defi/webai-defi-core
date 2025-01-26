"""Config"""
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    STREAMING: bool = True
    MODEL: str = "gpt-4o"
    TEMPERATURE: float = 0
    PROMPT: str = "hwchase17/openai-tools-agent"

    PROJECT_NAME: str = "Web Search Agent"
    PROJECT_DESC: str = "Агент с web поиском"
    DEBUG_LOGS: bool = False


settings = Settings()