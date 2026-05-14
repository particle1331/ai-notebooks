"""Web search tool — query DuckDuckGo and return text snippets."""

from __future__ import annotations

import urllib.parse

import httpx
from pydantic import BaseModel, Field

from notebooks.agent.tools.base import Tool, ToolInvocation, ToolKind, ToolResult

_DDG_URL = "https://api.duckduckgo.com/"
_MAX_RESULTS = 10


class WebSearchParams(BaseModel):
    query: str = Field(..., description="The search query")
    num_results: int = Field(
        5, ge=1, le=_MAX_RESULTS, description="Number of results to return"
    )


class WebSearchTool(Tool):
    name = "web_search"
    kind = ToolKind.NETWORK
    description = (
        "Search the web using DuckDuckGo and return a list of results "
        "(title, URL, and snippet for each). Use this to look up current information, "
        "documentation, or anything not in the local codebase."
    )
    schema = WebSearchParams

    async def execute(self, invocation: ToolInvocation) -> ToolResult:
        params = WebSearchParams(**invocation.params)

        # DuckDuckGo Instant Answer API (no auth required)
        query_params = {
            "q": params.query,
            "format": "json",
            "no_html": "1",
            "skip_disambig": "1",
        }
        url = _DDG_URL + "?" + urllib.parse.urlencode(query_params)

        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=15) as client:
                resp = await client.get(
                    url,
                    headers={"User-Agent": "Mozilla/5.0 (compatible; CodingAgent/1.0)"},
                )
                resp.raise_for_status()
                data = resp.json()
        except httpx.TimeoutException:
            return ToolResult.error_result("Search timed out")
        except Exception as exc:
            return ToolResult.error_result(f"Search failed: {exc}")

        lines: list[str] = []

        # Abstract (direct answer)
        if data.get("AbstractText"):
            lines.append(f"Summary: {data['AbstractText']}")
            if data.get("AbstractURL"):
                lines.append(f"Source: {data['AbstractURL']}")
            lines.append("")

        # Related topics / results
        count = 0
        for topic in data.get("RelatedTopics", []):
            if count >= params.num_results:
                break
            # Topics can be nested groups
            if "Topics" in topic:
                for sub in topic["Topics"]:
                    if count >= params.num_results:
                        break
                    text = sub.get("Text", "")
                    href = sub.get("FirstURL", "")
                    if text:
                        lines.append(f"[{count + 1}] {text}")
                        if href:
                            lines.append(f"    URL: {href}")
                        count += 1
            else:
                text = topic.get("Text", "")
                href = topic.get("FirstURL", "")
                if text:
                    lines.append(f"[{count + 1}] {text}")
                    if href:
                        lines.append(f"    URL: {href}")
                    count += 1

        if not lines:
            return ToolResult.error_result(
                f"No results found for: {params.query}. "
                "Try a more specific query or use fetch_url to retrieve a specific page."
            )

        output = "\n".join(lines)
        return ToolResult.success_result(
            output,
            metadata={"query": params.query, "result_count": count},
        )
