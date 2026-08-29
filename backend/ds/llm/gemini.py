import google.generativeai as genai
from langchain_core.documents import Document
from ds.llm.base import LLMModel  # import your abstract class

class GeminiLLM(LLMModel):
    def __init__(self, model_name: str = "gemini-2.0-flash-exp", api_key: str | None = None):
        genai.configure(api_key=api_key) # type: ignore
        self.model = genai.GenerativeModel(model_name) # type: ignore

    def generate(self, query: str, context: list[Document]) -> str:
        context_text = "\n".join(doc.page_content for doc in context)
        prompt = f"Context:\n{context_text}\n\nQuestion:\n{query}"
        response = self.model.generate_content(prompt)
        return response.text

    def generate_json(self, prompt: str, format_schema: dict | None = None) -> dict:
        if format_schema:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(response_mime_type="application/json") # type: ignore
            )
            return response.text # type: ignore
        else:
            response = self.model.generate_content(prompt)
            return {"response": response.text}

    def chat(
        self, system_prompt: str, message: str, chat_history: list[dict] | None = None
    ) -> str:
        messages = [{"role": "system", "content": system_prompt}]
        if chat_history:
            messages.extend(chat_history)
        messages.append({"role": "user", "content": message})

        chat_session = self.model.start_chat(history=messages) # type: ignore
        response = chat_session.send_message(message)
        return response.text

    def chat_stream( # type: ignore
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

