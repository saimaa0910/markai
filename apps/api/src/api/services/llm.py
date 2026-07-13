import os
from typing import Optional


class LLMGateway:
    """
    Modular Gateway for interfacing with multiple LLM providers.
    Supports OpenAI, Gemini, and Claude model routing.
    """

    @staticmethod
    def generate_response(
        prompt_content: str,
        model_name: str,
        system_instruction: Optional[str] = None,
    ) -> str:
        """
        Routes the prompt to the specified model provider, falling back to
        simulated replies in local dev context if credentials aren't set.
        """
        normalized_model = model_name.lower()
        instruction_prefix = (
            f"System Context: {system_instruction}\n" if system_instruction else ""
        )

        # 1. OpenAI Routing
        if "gpt" in normalized_model:
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                # Real OpenAI integrations could go here
                pass
            return (
                f"{instruction_prefix}"
                f"[LLM Gateway -> OpenAI Router ({model_name})]: "
                f"Simulated response to prompt: '{prompt_content}'"
            )

        # 2. Gemini Routing
        elif "gemini" in normalized_model:
            api_key = os.getenv("GEMINI_API_KEY")
            if api_key:
                # Real Gemini integrations could go here
                pass
            return (
                f"{instruction_prefix}"
                f"[LLM Gateway -> Gemini Router ({model_name})]: "
                f"Simulated response to prompt: '{prompt_content}'"
            )

        # 3. Claude Routing
        elif "claude" in normalized_model:
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if api_key:
                # Real Anthropic integrations could go here
                pass
            return (
                f"{instruction_prefix}"
                f"[LLM Gateway -> Claude Router ({model_name})]: "
                f"Simulated response to prompt: '{prompt_content}'"
            )

        # 4. Default Fallback Router
        else:
            return (
                f"{instruction_prefix}"
                f"[LLM Gateway -> Default Router ({model_name})]: "
                f"Simulated response to prompt: '{prompt_content}'"
            )
