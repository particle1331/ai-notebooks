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


def get_client(provider: str):
    return {"openai": OpenAI, "groq": Groq}[provider]()
