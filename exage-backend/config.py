from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env")

    openai_api_key: str
    model: str = "gpt-4o"

settings = Settings()