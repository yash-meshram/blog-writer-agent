from config.config import settings
from langchain_groq import ChatGroq

_model = None
def _get_model():
    global _model
    if _model is None:
        _model = ChatGroq(
            api_key = settings.GROQ_API_KEY,
            model = settings.llm.model_name,
            temperature = settings.llm.temperature
        )
        
    return _model

def get_model():
    return _get_model()