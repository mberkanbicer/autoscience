"""JSON parsing utilities for LLM outputs."""

import json
import re
from typing import Any

import structlog

logger = structlog.get_logger()


def parse_llm_json(content: str) -> dict[str, Any]:
    """Parse JSON from LLM output, handling markdown blocks and other common issues."""
    if not content:
        return {}

    # 1. Try direct parsing first
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    # 2. Try extracting from markdown blocks (```json ... ``` or ``` ... ```)
    # The non-greedy .*? is important here
    markdown_match = re.search(r"```(?:json)?\s*(.*?)\s*```", content, re.DOTALL)
    if markdown_match:
        try:
            return json.loads(markdown_match.group(1))
        except json.JSONDecodeError:
            content = markdown_match.group(1)  # If failed, try parsing the content inside block further

    # 3. Try to find the first '{' and last '}'
    try:
        start_index = content.find("{")
        end_index = content.rfind("}")
        if start_index != -1 and end_index != -1:
            json_str = content[start_index : end_index + 1]
            return json.loads(json_str)
    except (json.JSONDecodeError, ValueError):
        pass

    # 4. If all fails, log warning and return empty dict
    logger.warning("json_parsing_failed", content=content[:500])
    return {}
