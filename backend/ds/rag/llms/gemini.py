import json

import google.generativeai as genai

from core.config.settings import settings
from ds.rag.prompts import load_prompt

from .base import LLMModel


class GeminiLLM(LLMModel):
    def __init__(self, model_name: str | None = None, api_key: str | None = None):
        model_name = model_name or settings.LLM_MODEL_NAME
        api_key = api_key or settings.GEMINI_API_KEY or None
        genai.configure(api_key=api_key)  # type: ignore
        self.model = genai.GenerativeModel(model_name)  # type: ignore

    def generate(self, query: str, context: list[str]) -> str:
        prompt = load_prompt("qa").format(
            context="\n".join(context),
            query=query,
        )
        response = self.model.generate_content(prompt)
        return response.text

    def generate_json(self, prompt: str, format_schema: dict | None = None) -> dict:
        if format_schema:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    response_mime_type="application/json"
                ),  # type: ignore
            )
            return json.loads(response.text)
        response = self.model.generate_content(prompt)
        try:
            return json.loads(response.text)
        except json.JSONDecodeError:
            return {"response": response.text}

    def chat(
        self, system_prompt: str, message: str, chat_history: list[dict] | None = None
    ) -> str:
        messages = [{"role": "system", "content": system_prompt}]
        if chat_history:
            messages.extend(chat_history)
        messages.append({"role": "user", "content": message})

        chat_session = self.model.start_chat(history=messages)  # type: ignore
        response = chat_session.send_message(message)
        return response.text

    def chat_stream(  # type: ignore
        self, system_prompt: str, message: str, chat_history: list[dict] | None = None
    ):
        # Start with system prompt
        prompt = system_prompt + "\n"

        # Append chat history if present
        if chat_history:
            for entry in chat_history:
                role = entry.get("role", "user")  # could be "user" or "assistant"
                content = entry.get("content", "")
                prompt += f"{role}: {content}\n"

        # Append current user message
        prompt += f"user: {message}\n"

        # Stream the response
        stream = self.model.generate_content(prompt, stream=True)
        for chunk in stream:
            if chunk.text:
                yield chunk.text
