from __future__ import annotations

import re
from typing import Literal

TYPES = ("feat", "fix", "docs", "style", "refactor", "perf", "test", "build", "ci", "chore", "other", "revert")
TASK_CATEGORY_MAP = {
    "feat": "Feature & Behavior", "fix": "Feature & Behavior", "perf": "Feature & Behavior",
    "docs": "Docs & Style", "style": "Docs & Style",
    "build": "Infrastructure", "ci": "Infrastructure", "chore": "Infrastructure",
    "refactor": "Internal Quality", "test": "Internal Quality",
}
SYSTEM_PROMPT = "You are a Conventional Commit classifier. Given a PR title and body, pick **exactly one** label from:\n" + ", ".join(TYPES) + "\nRespond in JSON with schema: {reason, output, confidence (1-10)}."

def regex_task(title: str) -> str | None:
    first_line = (title or "").splitlines()[0] if title else ""
    for task in TYPES:
        if re.match(rf"^{re.escape(task)}(\([^)]*\))?!?(?=\W|$)", first_line, re.IGNORECASE): return task
    return None

def classify_task(title: str, body: str | None, api_key: str | None) -> tuple[str | None, str | None]:
    matched = regex_task(title)
    if matched: return matched, "regex"
    if not api_key: return None, None
    from openai import OpenAI
    import tiktoken
    encoder = tiktoken.encoding_for_model("gpt-4.1-mini")
    text = f"Title: {title}\n\nBody: {body or ''}"
    text = encoder.decode(encoder.encode(text)[:10_000])
    response = OpenAI(api_key=api_key).chat.completions.create(
        model="gpt-4.1-mini", temperature=0,
        response_format={"type": "json_schema", "json_schema": {"name": "task_classification", "strict": True, "schema": {"type": "object", "properties": {"reason": {"type": "string"}, "output": {"type": "string", "enum": list(TYPES)}, "confidence": {"type": "integer", "minimum": 1, "maximum": 10}}, "required": ["reason", "output", "confidence"], "additionalProperties": False}}},
        messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": text}],
    )
    import json
    return json.loads(response.choices[0].message.content or "{}") .get("output"), "llm"
