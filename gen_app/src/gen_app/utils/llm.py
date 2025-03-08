# File: gen_app/utils/llm.py
"""
LLM interaction utilities.

Defines abstract classes and implementations for LLM providers,
including retry logic for robust code generation.
"""

import asyncio
import logging


class LLMProvider:
    """
    Abstract base class for LLM interactions.
    """

    async def generate(self, prompt: str, model: str) -> dict:
        """
        Generate code or text using the LLM.

        Parameters
        ----------
        prompt : str
            The prompt to send to the LLM.
        model : str
            The model identifier.

        Returns
        -------
        dict
            A dictionary containing the LLM response.
        """
        raise NotImplementedError("Subclasses must implement the generate method.")

    async def generate_with_retry(
        self, prompt: str, model: str, max_retries: int = 3, backoff_factor: float = 1.5
    ) -> dict:
        """
        Generate response with retry logic.

        Parameters
        ----------
        prompt : str
            The prompt to send.
        model : str
            The model identifier.
        max_retries : int, optional
            Maximum number of retries.
        backoff_factor : float, optional
            Factor for exponential backoff.

        Returns
        -------
        dict
            The LLM response.

        Raises
        ------
        Exception
            If all retries fail.
        """
        retries = 0
        while retries < max_retries:
            try:
                return await self.generate(prompt, model)
            except Exception as e:
                retries += 1
                if retries >= max_retries:
                    logging.error(
                        f"LLM generation failed after {max_retries} attempts: {e}"
                    )
                    raise e
                wait_time = backoff_factor**retries
                logging.warning(f"LLM generation retry {retries} in {wait_time}s: {e}")
                await asyncio.sleep(wait_time)


class OllamaProvider(LLMProvider):
    """
    LLM provider implementation for Ollama.
    """

    async def generate(self, prompt: str, model: str) -> dict:
        """
        Generate code using Ollama's API.

        This function simulates an API call; in a production environment,
        it should invoke the actual Ollama API.
        """
        await asyncio.sleep(0.5)  # Simulate network latency
        return {
            "response": f"```python\n# Generated code for prompt:\n# {prompt}\nprint('Hello, world!')\n```"
        }

    def get_available_models(self) -> list:
        """
        Return a list of available LLM models.
        """
        return ["mistral-nemo:12b-instruct-2407-q8_0", "another-model"]
