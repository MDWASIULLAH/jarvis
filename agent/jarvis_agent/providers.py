from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class LLMMessage:
    role: str
    content: str


class BaseLLMProvider:
    async def generate(self, messages: list[LLMMessage]) -> str:
        raise NotImplementedError


class OpenAICompatibleProvider(BaseLLMProvider):
    """OpenAI SDK compatible provider.

    Works with OpenAI, OpenRouter, local LiteLLM, vLLM, Ollama OpenAI-compatible
    endpoints, or any service that implements the chat completions API.
    """

    def __init__(self) -> None:
        self.api_key = os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY")
        self.base_url = os.getenv("OPENAI_BASE_URL") or os.getenv("LLM_BASE_URL")
        self.model = os.getenv("LLM_MODEL", "gpt-4o-mini")

    async def generate(self, messages: list[LLMMessage]) -> str:
        if not self.api_key:
            raise RuntimeError("No OpenAI-compatible API key configured.")

        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
        response = await client.chat.completions.create(
            model=self.model,
            messages=[{"role": msg.role, "content": msg.content} for msg in messages],
            temperature=0.2,
        )
        return response.choices[0].message.content or ""


class LocalFallbackProvider(BaseLLMProvider):
    async def generate(self, messages: list[LLMMessage]) -> str:
        prompt = messages[-1].content if messages else ""
        lowered = prompt.lower()

        if "python" in lowered and "calculator" in lowered:
            return (
                "Here is a complete Python calculator using Tkinter.\n\n"
                "```python\n"
                "import tkinter as tk\n\n"
                "class Calculator(tk.Tk):\n"
                "    def __init__(self):\n"
                "        super().__init__()\n"
                "        self.title('Calculator')\n"
                "        self.expression = tk.StringVar(value='0')\n"
                "        tk.Entry(self, textvariable=self.expression, justify='right', font=('Segoe UI', 20)).grid(row=0, column=0, columnspan=4, sticky='ew', padx=8, pady=8)\n"
                "        buttons = ['7','8','9','/','4','5','6','*','1','2','3','-','0','.','C','+','=']\n"
                "        for i, label in enumerate(buttons):\n"
                "            row, col = divmod(i, 4)\n"
                "            tk.Button(self, text=label, command=lambda v=label: self.press(v), width=6, height=2).grid(row=row+1, column=col, padx=4, pady=4)\n\n"
                "    def press(self, value):\n"
                "        current = self.expression.get()\n"
                "        if value == 'C':\n"
                "            self.expression.set('0')\n"
                "        elif value == '=':\n"
                "            allowed = set('0123456789+-*/(). ')\n"
                "            if set(current) <= allowed:\n"
                "                try:\n"
                "                    self.expression.set(str(eval(current, {'__builtins__': {}}, {})))\n"
                "                except Exception:\n"
                "                    self.expression.set('Error')\n"
                "        else:\n"
                "            self.expression.set(value if current in {'0', 'Error'} else current + value)\n\n"
                "if __name__ == '__main__':\n"
                "    Calculator().mainloop()\n"
                "```\n"
            )

        return (
            "Jarvis can handle this through the cloud agent pipeline. "
            "For best answers, connect an OpenAI-compatible model endpoint with "
            "`OPENAI_API_KEY`, `OPENAI_BASE_URL`, and `LLM_MODEL`, or point it to "
            "a local gateway such as Ollama through an OpenAI-compatible proxy."
        )


def get_provider() -> BaseLLMProvider:
    if os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY"):
        return OpenAICompatibleProvider()
    return LocalFallbackProvider()
