import re
from dataclasses import dataclass

from groq import Groq
from openai import OpenAI


@dataclass
class TagContentResult:
    content: list[str]
    found: bool


def extract_tag_content(text: str, tag: str) -> TagContentResult:
    """
    Extracts all content enclosed by specified tags,
    e.g. <thought>, <response>, etc.
    Parameters:
        text (str): The input string containing multiple potential tags
        tag  (str): The name of the tag to search for
    """
    tag_pattern = rf"<{tag}>(.*?)</{tag}>"
    matched_contents = re.findall(tag_pattern, text, re.DOTALL)

    return TagContentResult(
        content=[content.strip() for content in matched_contents],
        found=bool(matched_contents),
    )


LLM_CLIENTS = {
    "groq": Groq,
    "openai": OpenAI,
}

def get_client(client):
    if isinstance(client, str):
        return LLM_CLIENTS[client]()
    else:
        assert type(client) in LLM_CLIENTS.values(), "unsupported LLM provider"
        return client


class Deployment:
    def __init__(self, client, model: str):
        client = get_client(client)
        self.model = model
        self.client = client
        self.metadata = client.models.retrieve(model).model_dump()
        
    def __repr__(self) -> str:
        provider = type(self.client).__module__
        return f"{provider}:{self.model}"

    @classmethod
    def list_models(cls, client) -> list[str]:
        client = get_client(client)
        return [m.id for m in client.models.list().data]
