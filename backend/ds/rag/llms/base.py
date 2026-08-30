from abc import ABC, abstractmethod
from langchain_core.documents import Document


class LLMModel(ABC):
    """
    Abstract class for generating answers using an LLM based on query + context.
    """

    @abstractmethod
    def generate(self, query: str, context: list[Document]) -> str:
        pass

    @abstractmethod
    def generate_json(self, prompt: str, format_schema: dict | None = None) -> dict:
        pass

    @abstractmethod
    def chat(
        self, system_prompt: str, message: str, chat_history: list[dict] | None = None
    ) -> str:
        pass

    @abstractmethod
    def chat_stream(
        self, system_prompt: str, message: str, chat_history: list[dict] | None = None
    ) -> str:
        pass
