from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    GROQ_API_KEY: str
    META_VISION_MODEL: str
    TEMPERATURE: str
    
    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()