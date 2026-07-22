import os
from typing import Optional


class LLMGateway:
    """
    Modular Gateway for interfacing with LLM providers.
    Routes execution to Groq / active AI Gateway provider.
    """

    @staticmethod
    def generate_response(
        prompt_content: str,
        model_name: str,
        system_instruction: Optional[str] = None,
    ) -> str:
        """
        Routes prompt to Groq or configured LLM provider.
        """
        from api.ai.providers.groq import GroqProvider
        provider = GroqProvider()
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt_content})

        try:
            res = provider.chat(messages=messages, model=model_name or "llama-3.3-70b-versatile")
            return res.get("content", "")
        except Exception as e:
            # Re-raise runtime error if execution failed
            raise RuntimeError(f"LLM execution failed: {str(e)}")
