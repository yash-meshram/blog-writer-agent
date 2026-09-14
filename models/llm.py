from config.config import settings
# from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI

_model = None
def _get_model():
    global _model
    if _model is None:
        _model = ChatOpenAI(
            api_key = settings.OPENROUTER_API_KEY,
            base_url = settings.llm.openrouter_base_url,
            model = settings.llm.model_name,
            temperature = settings.llm.temperature
        )
        
    return _model

def get_model():
    return _get_model()