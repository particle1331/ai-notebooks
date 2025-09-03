from typing import Optional


class Role:
    USER = "user"
    TOOL = "tool"
    SYSTEM = "system"
    ASSISTANT = "assistant"

    @classmethod
    def get_valid_roles(cls) -> set:
        """Automatically detect all uppercase constant roles"""
        return {value for name, value in vars(cls).items() 
                if name.isupper() and isinstance(value, str)}
    
    @classmethod
    def validate(cls, role: str) -> str:
        valid_roles = cls.get_valid_roles()
        if role not in valid_roles:
            raise ValueError(f"Invalid role: {role}")
        return role


def completions_create(client, messages: list, model: str) -> str:
    """Return generated string from model based on messages."""
    response = client.chat.completions.create(messages=messages, model=model)
    return str(response.choices[0].message.content)


def message_dict(prompt: str, role: str, tag: str = "") -> dict:
    """Return a message dictionary for the chat completions API."""
    role = Role.validate(role)
    prompt = f"<{tag}>{prompt}</{tag}>" if tag else prompt
    return {"role": role, "content": prompt}



class ChatHistory(list):
    def __init__(self, 
        system_prompt: Optional[str] = None, 
        messages: Optional[list] = None,
        max_len: int = -1, 
        fixed_n: int = 1
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
            self.pop(self.fixed_n)    # i.e. keep 0, 1, ..., n-1 (first n)
        chat["role"] = Role.validate(chat["role"])
        super().append(chat)

    def update(self, prompt: str, role: str):
        """Append a message to the chat history."""
        self.append(message_dict(prompt=prompt, role=role))
