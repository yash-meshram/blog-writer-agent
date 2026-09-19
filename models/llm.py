from config.config import settings
# from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from google import genai

_model = None
def _get_model():
    global _model
    if _model is None:
        _model = ChatOpenAI(
            api_key = settings.OPENROUTER_API_KEY,
            base_url = settings.llm.base_url,
            model = settings.llm.model_name,
            temperature = settings.llm.temperature
        )
        
    return _model

def get_model():
    return _get_model()


_image_model = None
def _get_image_model():
    global _image_model
    if _image_model is None:
        _image_model = genai.Client(
            api_key = settings.GEMINI_API_KEY
        )
        
    return _image_model

def get_image_model():
    return _get_image_model()



