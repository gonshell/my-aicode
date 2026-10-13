"""Qwen Responses API client with retry and structured output parsing."""

import json
import time
import httpx
from openai import OpenAI, RateLimitError, APITimeoutError, APIConnectionError

import config


def _build_client() -> OpenAI:
    if not config.API_KEY or not config.BASE_URL:
        raise RuntimeError(
            "Qwen Harness not configured. "
            "Fill in api_key and base_url in config.yaml or set "
            "QWEN_HARNESS_API_KEY / QWEN_HARNESS_BASE_URL env vars."
        )
    return OpenAI(api_key=config.API_KEY, base_url=config.BASE_URL)


_client: OpenAI | None = None


def get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = _build_client()
    return _client


def call_harness(
    input_text: str,
    tool_types: list[str],
    timeout: int | None = None,
) -> dict:
    """Call Qwen Responses API with harness tools.

    Returns:
        {
            "text": str,           # final model text
            "tool_outputs": list,  # raw tool call/result items
            "usage": dict,         # token usage
        }
    """
    client = get_client()
    timeout = timeout or config.TIMEOUT
    tools = [{"type": t} for t in tool_types]

    last_err = None
    for attempt in range(config.MAX_RETRIES + 1):
        try:
            resp = client.responses.create(
                model=config.MODEL,
                input=input_text,
                tools=tools,
                timeout=timeout,
            )
            return _parse_response(resp)
        except (RateLimitError, APITimeoutError, APIConnectionError) as e:
            last_err = e
            if attempt < config.MAX_RETRIES:
                time.sleep(2 ** attempt)
            continue
        except Exception as e:
            return {"text": "", "tool_outputs": [], "usage": {}, "error": str(e)}

    return {"text": "", "tool_outputs": [], "usage": {}, "error": str(last_err)}


def _parse_response(resp) -> dict:
    """Extract text, tool outputs, and usage from a Responses API response."""
    text = ""
    tool_outputs = []

    # output_text is the convenience accessor for final message
    if hasattr(resp, "output_text") and resp.output_text:
        text = resp.output_text

    # Parse raw output items for tool call details
    if hasattr(resp, "output") and resp.output:
        for item in resp.output:
            item_type = getattr(item, "type", "")
            if item_type in ("web_search_call", "code_interpreter_call",
                             "web_extractor_call", "t2i_search_call",
                             "i2i_search_call", "function_call"):
                tool_outputs.append({
                    "type": item_type,
                    "id": getattr(item, "id", ""),
                    "status": getattr(item, "status", ""),
                })
            elif item_type in ("web_search_result", "code_interpreter_result",
                               "web_extractor_result", "t2i_search_result",
                               "i2i_search_result", "function_call_output"):
                content = getattr(item, "output", "") or getattr(item, "content", "")
                if isinstance(content, list):
                    content = json.dumps(content, ensure_ascii=False)
                tool_outputs.append({
                    "type": item_type,
                    "id": getattr(item, "id", ""),
                    "output": str(content)[:5000],  # cap size
                })

    usage = {}
    if hasattr(resp, "usage") and resp.usage:
        usage = {
            "input_tokens": getattr(resp.usage, "input_tokens", 0),
            "output_tokens": getattr(resp.usage, "output_tokens", 0),
            "total_tokens": getattr(resp.usage, "total_tokens", 0),
        }

    return {"text": text, "tool_outputs": tool_outputs, "usage": usage}


def download_image(url: str, filename: str | None = None) -> str | None:
    """Download an image to IMAGE_DIR. Returns local path or None."""
    import os
    from pathlib import Path
    from urllib.parse import urlparse

    os.makedirs(config.IMAGE_DIR, exist_ok=True)

    if not filename:
        parsed = urlparse(url)
        ext = Path(parsed.path).suffix or ".png"
        filename = f"{int(time.time() * 1000)}{ext}"

    local_path = os.path.join(config.IMAGE_DIR, filename)

    try:
        with httpx.Client(timeout=30, follow_redirects=True) as http:
            r = http.get(url)
            r.raise_for_status()
            if len(r.content) > config.MAX_IMAGE_SIZE:
                return None
            with open(local_path, "wb") as f:
                f.write(r.content)
        return local_path
    except Exception:
        return None
