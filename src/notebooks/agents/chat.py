import json

from typing import Union, Optional
from pydantic import BaseModel
from functools import lru_cache

from notebooks.agents.utils import Deployment


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


class ChatCompletions:
    def __init__(self, deployment: Deployment):
        self.model = deployment.model
        self.client = deployment.client
        self.completions = self.client.chat.completions

    def _args(self, messages, tools, response_format, **extra) -> dict:
        args = {"messages": messages, "model": self.model, **extra}
        if response_format is not None:
            assert issubclass(response_format, BaseModel)
            args["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": response_format.__name__,
                    "schema": response_format.model_json_schema()
                }
            }
        if tools:
            args["tools"] = tools
        return args
    
    def _process_tool_calls(self, response) -> list:
        tool_calls = response.choices[0].message.tool_calls
        calls = []
        for i, call in enumerate(tool_calls):
            call_dict = call.model_dump()
            call_dict["id"] = str(i)
            calls.append(call_dict)
        return calls

    def _process_response(self, response, parse=False) -> Union[str, dict, list]:
        finish_reason = response.choices[0].finish_reason
        if finish_reason == "tool_calls":
            return self._process_tool_calls(response)
        else:
            message = response.choices[0].message
            content = message.content
            return json.loads(content) if parse else content

    def create(self, 
        messages: Union[list, ChatHistory],
        tools: Optional[list[dict]] = None, 
        response_format: Optional[BaseModel] = None, 
        temperature: float = 1.0,
        **extra
    ) -> Union[str, dict, list]:
        args = self._args(messages, tools, response_format, temperature=temperature, **extra)
        parse = response_format is not None
        response = self.completions.create(**args)
        return self._process_response(response, parse=parse)
