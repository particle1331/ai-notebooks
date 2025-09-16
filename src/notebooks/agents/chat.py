from functools import lru_cache
from typing import Any, Optional, Union


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

    def _not_given(self) -> Any:
        if "groq" in str(type(self.client)).lower():
            import groq
            return groq.NOT_GIVEN
        else:
            import openai
            return openai.NOT_GIVEN

    def _args(self, messages, model, tools, **extra) -> dict:
        return {
            "messages": messages,
            "model": model or self.default_model,
            "tools": tools or self._not_given(),
            **extra,
        }
    
    def _process_tool_calls(self, response) -> list:
        tool_calls = response.choices[0].message.tool_calls
        calls = []
        for i, call in enumerate(tool_calls):
            call_dict = call.model_dump()
            call_dict["id"] = i
            calls.append(call_dict)
        return calls

    def _process_response(self, response, parse=False) -> Union[str, dict, list]:
        if response.choices[0].finish_reason == "tool_calls":
            return self._process_tool_calls(response)
        msg = response.choices[0].message
        return msg.parsed.model_dump() if parse else msg.content

    def create(self, messages, model="", tools=None, **extra) -> str | list:
        args = self._args(messages, model, tools, **extra)
        response = self.completions.create(**args)
        return self._process_response(response, parse=False)

    def parsed(self, messages, schema, model="", tools=None, **extra) -> dict | list:
        payload = self._args(messages, model, tools, response_format=schema, **extra)
        response = self.completions.parse(**payload)
        return self._process_response(response, parse=True)


class ChatHistory(list):
    def __init__(self, system_prompt=None, messages=None, max_len=-1, fixed_n=1):
        """Fixed message list with a optional total length and number of fixed initial messages."""
        messages = [] if messages is None else messages
        super().__init__(messages)
        assert max_len > 1 or max_len == -1, "max_len must be -1 (no limit) or > 1"
        assert bool(system_prompt) + bool(messages) <= 1
        self.fixed_n = fixed_n
        self.max_len = max_len
        if system_prompt:
            self.update(prompt=system_prompt, role=Role.SYSTEM)

    def append(self, message: dict):
        if len(self) == self.max_len:
            self.pop(self.fixed_n)  # i.e. keep 0, 1, ..., n-1 (first n)
        message["role"] = Role.validate(message["role"])
        super().append(message)

    def update(self, prompt: str, role: str, tag="", **extra):
        """Append a message to the chat history."""
        self.append(message_dict(prompt=prompt, role=role, tag=tag, **extra))
