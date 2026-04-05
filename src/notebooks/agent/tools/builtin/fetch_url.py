"""Fetch URL tool — retrieve the text content of any HTTP/HTTPS URL."""

from __future__ import annotations

import re

import httpx
from pydantic import BaseModel, Field

from notebooks.agent.tools.base import Tool, ToolInvocation, ToolKind, ToolResult

_MAX_BYTES = 200_000  # 200 KB cap


def _strip_html(html: str) -> str:
    """Very light HTML → plain-text conversion (no external deps)."""
    # Remove script and style blocks entirely
    html = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", html, flags=re.DOTALL | re.IGNORECASE)
    # Replace block-level tags with newlines
    html = re.sub(r"<(br|p|div|li|tr|h[1-6])[^>]*>", "\n", html, flags=re.IGNORECASE)
    # Strip all remaining tags
    html = re.sub(r"<[^>]+>", "", html)
    # Collapse whitespace
    lines = [ln.strip() for ln in html.splitlines()]
    return "\n".join(ln for ln in lines if ln)


class FetchUrlParams(BaseModel):
    url: str = Field(..., description="The HTTP/HTTPS URL to fetch")
    timeout: int = Field(30, ge=1, le=120, description="Request timeout in seconds")
    max_length: int = Field(
        10_000,
        ge=100,
        le=100_000,
        description="Maximum number of characters to return",
    )


class FetchUrlTool(Tool):
    name = "fetch_url"
    kind = ToolKind.NETWORK
    description = (
        "Fetch the text content of a URL. "
        "Strips HTML tags and returns readable plain text. "
        "Use for reading documentation, web pages, or any HTTP resource."
    )
    schema = FetchUrlParams

    async def execute(self, invocation: ToolInvocation) -> ToolResult:
        params = FetchUrlParams(**invocation.params)

        try:
            async with httpx.AsyncClient(
                follow_redirects=True,
                timeout=params.timeout,
            ) as client:
                resp = await client.get(
                    params.url,
                    headers={"User-Agent": "Mozilla/5.0 (compatible; CodingAgent/1.0)"},
                )
                resp.raise_for_status()
        except httpx.TimeoutException:
            return ToolResult.error_result(f"Request timed out after {params.timeout}s")
        except httpx.HTTPStatusError as exc:
            return ToolResult.error_result(
                f"HTTP {exc.response.status_code}: {exc.response.reason_phrase}"
            )
        except Exception as exc:
            return ToolResult.error_result(f"Fetch failed: {exc}")

        raw = resp.text[:_MAX_BYTES]
        content_type = resp.headers.get("content-type", "")

        if "html" in content_type:
            text = _strip_html(raw)
        else:
            text = raw

        if len(text) > params.max_length:
            text = text[: params.max_length] + "\n… [truncated]"

        return ToolResult.success_result(
            text,
            metadata={
                "url": str(resp.url),
                "status_code": resp.status_code,
                "content_type": content_type,
                "chars": len(text),
            },
        )
