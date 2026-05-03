"""
LLM Response Utilities
======================
Shared helpers for parsing and retrying LLM JSON responses.
Used by all agents to handle malformed LLM output gracefully.
"""

import json
import re
import time
from typing import Optional

from langchain_ollama import ChatOllama
from langchain_core.messages import BaseMessage


def extract_json_from_text(text: str) -> Optional[dict]:
    """Try to extract a JSON object from text that may contain extra content.

    Handles cases where the LLM wraps JSON in markdown code fences,
    adds commentary before/after, or includes trailing commas.

    Args:
        text: Raw LLM response text.

    Returns:
        Parsed dict if JSON found, None otherwise.
    """
    # Try direct parse first
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    # Try to find JSON within markdown code fences
    code_block = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if code_block:
        try:
            return json.loads(code_block.group(1).strip())
        except json.JSONDecodeError:
            pass

    # Try to find a JSON object using brace matching
    brace_match = re.search(r"\{.*\}", text, re.DOTALL)
    if brace_match:
        candidate = brace_match.group(0)
        # Fix common issues: trailing commas before closing braces/brackets
        candidate = re.sub(r",\s*}", "}", candidate)
        candidate = re.sub(r",\s*]", "]", candidate)
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    return None


def invoke_llm_with_retry(
    llm: ChatOllama,
    messages: list[BaseMessage],
    max_retries: int = 2,
    agent_name: str = "Agent",
    tracer=None,
) -> dict:
    """Invoke the LLM and parse JSON response with automatic retry.

    On JSON parse failure, retries the call up to max_retries times.
    Uses extract_json_from_text as a fallback parser before retrying.

    Args:
        llm: The ChatOllama instance.
        messages: List of messages to send.
        max_retries: Maximum number of retries on failure.
        agent_name: Name for logging.
        tracer: Optional AgentTracer for logging.

    Returns:
        Parsed JSON dict from the LLM response.

    Raises:
        ValueError: If all retries fail to produce valid JSON.
    """
    last_error: str = ""
    last_raw: str = ""

    for attempt in range(max_retries + 1):
        try:
            start = time.time()
            response = llm.invoke(messages)
            duration = time.time() - start
            raw_content = response.content.strip()
            last_raw = raw_content

            if tracer:
                tracer.log_llm_call(
                    agent_name, llm.model,
                    prompt_preview=f"Attempt {attempt + 1}/{max_retries + 1}",
                    response_preview=raw_content[:500],
                    duration_seconds=duration,
                )

            # Try direct JSON parse
            try:
                return json.loads(raw_content)
            except json.JSONDecodeError:
                pass

            # Try fallback extraction
            extracted = extract_json_from_text(raw_content)
            if extracted is not None:
                return extracted

            last_error = f"Could not parse JSON from response (attempt {attempt + 1})"

        except Exception as e:
            last_error = f"{type(e).__name__}: {str(e)}"
            duration = time.time() - start if 'start' in dir() else 0

        # Log retry
        if attempt < max_retries:
            if tracer:
                tracer.log_llm_call(
                    agent_name, llm.model,
                    prompt_preview=f"RETRY {attempt + 2}/{max_retries + 1} — {last_error}",
                    response_preview="retrying...",
                    duration_seconds=0,
                )

    raise ValueError(
        f"Failed to get valid JSON after {max_retries + 1} attempts. "
        f"Last error: {last_error}. Last response: {last_raw[:200]}"
    )
