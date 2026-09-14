from pathlib import Path
import yaml
from pydantic import BaseModel
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent

with open(BASE_DIR/"config.yaml", "r") as file:
    yaml_config = yaml.safe_load(file)
    
class LLMConfig(BaseModel):
    model_name: str
    temperature: float

class Settings(BaseSettings):
    GROQ_API_KEY: str
    llm: LLMConfig
    
    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings(
    llm = yaml_config["llm"]
)