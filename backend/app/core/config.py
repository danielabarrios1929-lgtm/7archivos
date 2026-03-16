from pydantic_settings import BaseSettings
from functools import lru_cache
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "PTAFI-AI"
    API_V1_STR: str = "/api/v1"
    
    # API Keys - se leen desde variables de entorno del sistema (Vercel) o del .env local
    GROQ_API_KEY: str = os.environ.get("GROQ_API_KEY", "")
    GOOGLE_API_KEY: str = os.environ.get("GOOGLE_API_KEY", "")
    GOOGLE_API_KEY_2: str = os.environ.get("GOOGLE_API_KEY_2", "")


    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "allow"
    }

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()
