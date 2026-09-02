from core.config.settings import settings

from .base import LLMModel
from .gemini import GeminiLLM

__all__ = ["LLMModel", "GeminiLLM", "get_llm"]


def get_llm() -> LLMModel:
    name = settings.CURRENT_LLM.lower()
    if name == "gemini":
        return GeminiLLM()
    raise ValueError(f"Unsupported LLM '{settings.CURRENT_LLM}'.")
