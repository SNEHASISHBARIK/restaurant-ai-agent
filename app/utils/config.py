from functools import lru_cache
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseModel):
    openai_api_key: str = Field(default="")
    openai_model: str = Field(default="gpt-4o-mini")
    database_url: str = Field(default="sqlite:///./restaurant.db")
    log_level: str = Field(default="INFO")
    max_tool_calls: int = Field(default=5, ge=1, le=20)
    llm_timeout_seconds: float = Field(default=20.0, gt=0, le=120)
    max_message_length: int = Field(default=2000, ge=100, le=10000)

@lru_cache
def get_settings() -> Settings:
    return Settings(
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        database_url=os.getenv("DATABASE_URL", "sqlite:///./restaurant.db"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        max_tool_calls=int(os.getenv("MAX_TOOL_CALLS", "5")),
        llm_timeout_seconds=float(os.getenv("LLM_TIMEOUT_SECONDS", "20")),
        max_message_length=int(os.getenv("MAX_MESSAGE_LENGTH", "2000")),
    )
