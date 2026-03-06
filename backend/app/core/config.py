from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    PROJECT_NAME: str = "PTAFI-AI"
    API_V1_STR: str = "/api/v1"
    
    # API Keys
    GOOGLE_API_KEY: str = ""
    GROQ_API_KEY: str = ""

    model_config = {
        "env_file": ".env",
        "extra": "allow"
    }

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()
