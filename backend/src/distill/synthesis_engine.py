import json
import re
from dataclasses import dataclass


class SynthesisError(Exception):
    pass


@dataclass
class ExaResult:
    title: str
    url: str
    text: str


@dataclass
class Source:
    title: str
    url: str


@dataclass
class TopicCard:
    tldr: str
    bullets: list[str]
    sources: list[Source]


_PROMPT = """\
You are a research assistant. Given the topic and source articles below, produce a concise summary.

Topic: {topic}

Sources:
{sources}

Respond with JSON only, in this exact shape:
{{
  "tldr": "<one sentence>",
  "bullets": ["<point 1>", "<point 2>", "<point 3>", "<point 4>"],
  "sources": [{{"title": "<title>", "url": "<url>"}}]
}}

Rules:
- tldr must be a single sentence
- bullets must contain exactly 4 or 5 items
- sources must include every article you used
"""


def _extract_json(raw: str) -> str:
    """Pull the JSON object out of a model response that may be wrapped in a
    ```json fence or surrounded by prose. Falls back to the raw text."""
    raw = raw.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)\s*```", raw, re.DOTALL)
    if fence:
        raw = fence.group(1).strip()
    start, end = raw.find("{"), raw.rfind("}")
    if start != -1 and end != -1 and end > start:
        return raw[start : end + 1]
    return raw


class SynthesisEngine:
    def __init__(self, claude_client):
        self._client = claude_client

    def synthesize(self, topic: str, exa_results: list[ExaResult]) -> TopicCard:
        if not exa_results:
            raise SynthesisError("No Exa results provided")

        sources_text = "\n".join(
            f"[{r.title}]({r.url})\n{r.text}" for r in exa_results
        )
        prompt = _PROMPT.format(topic=topic, sources=sources_text)

        last_error = None
        for _ in range(3):
            message = self._client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = message.content[0].text
            try:
                data = json.loads(_extract_json(raw))
                return TopicCard(
                    tldr=data["tldr"],
                    bullets=data["bullets"],
                    sources=[Source(**s) for s in data["sources"]],
                )
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                last_error = e

        raise SynthesisError(f"Claude returned unparseable output after 3 attempts: {last_error}")
