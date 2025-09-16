from typing import Optional
from pydantic import BaseModel
from functools import lru_cache

import groq
import openai


class Role:
    USER = "user"
    TOOL = "tool"
    SYSTEM = "system"
    ASSISTANT = "assistant"

    @classmethod
    @lru_cache(maxsize=1)
    def get_valid_roles(cls) -> set:
        """Automatically detect all uppercase constant roles"""
        return {
            value
            for name, value in vars(cls).items()
            if name.isupper() and isinstance(value, str)
        }

    @classmethod
    def validate(cls, role: str) -> str:
        valid_roles = cls.get_valid_roles()
        if role not in valid_roles:
            raise ValueError(f"Invalid role: {role}")
        return role


def message_dict(prompt: str, role: str, tag: str = "", **extra) -> dict:
    """Return a message dictionary for the chat completions API."""
    role = Role.validate(role)
    prompt = f"<{tag}>{prompt}</{tag}>" if tag else prompt
    return {"role": role, "content": prompt, **extra}


class ChatCompletions:
    def __init__(self, client, default_model: str = ""):
        self.client = client
        self.completions = client.chat.completions
        self.default_model = default_model

    def _not_given(self):
        return groq.NOT_GIVEN if isinstance(self.client, groq.Groq) else openai.NOT_GIVEN

    def _build_payload(self, messages, model, tools, **extra):
        return {
            "messages": messages,
            "model": model or self.default_model,
            "tools": tools or self._not_given(),
            **extra
        }
    
    def _process_tool_calls(self, response, parse: bool = False):
        if response.choices[0].finish_reason == "tool_calls":
            out = []
            for i, call in enumerate(response.choices[0].message.tool_calls):
                call_dict = call.model_dump()
                call_dict["id"] = i
                out.append(call_dict)
            return out
        
        if parse:
            return response.choices[0].message.parsed.model_dump()
        else:
            return response.choices[0].message.content

    def create(self, messages: list, model: str = "", tools=None, **extra) -> str:
        payload = self._build_payload(messages, model, tools, **extra)
        response = self.completions.create(**payload)
        return self._process_tool_calls(response, parse=False)

    def parsed(self, messages: list, schema: BaseModel, model: str = "", tools=None, **extra) -> dict:
        payload = self._build_payload(messages, model, tools, response_format=schema, **extra)
        response = self.completions.parse(**payload)
        return self._process_tool_calls(response, parse=True)


class ChatHistory(list):
    def __init__(
        self,
        system_prompt: Optional[str] = None,
        messages: Optional[list] = None,
        max_len: int = -1,
        fixed_n: int = 1,
    ):
        """Fixed message list with a optional total length and number of fixed initial messages."""
        messages = [] if messages is None else messages
        super().__init__(messages)
        assert max_len > 1 or max_len == -1, "max_len must be -1 (no limit) or > 1"
        assert bool(system_prompt) + bool(messages) <= 1
        self.fixed_n = fixed_n
        self.max_len = max_len
        if system_prompt:
            self.update(prompt=system_prompt, role=Role.SYSTEM)

    def append(self, chat: dict):
        if len(self) == self.max_len:
            self.pop(self.fixed_n)  # i.e. keep 0, 1, ..., n-1 (first n)
        chat["role"] = Role.validate(chat["role"])
        super().append(chat)

    def update(self, prompt: str, role: str, tag: str = "", **extra):
        """Append a message to the chat history."""
        self.append(message_dict(prompt=prompt, role=role, tag=tag, **extra))
