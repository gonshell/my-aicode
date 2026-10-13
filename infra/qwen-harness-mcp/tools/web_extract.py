"""qwen_web_extract - 网页抓取工具"""

import json
from client import call_harness


def web_extract(url: str, instruction: str = "") -> str:
    """Extract content from a web page via Qwen's built-in web_extractor harness tool.

    Args:
        url: The URL to extract content from.
        instruction: Optional instruction on what to extract or how to summarize.

    Returns:
        JSON string with extracted page content.
    """
    if instruction:
        input_text = f"请抓取以下网页内容，{instruction}：\n{url}"
    else:
        input_text = f"请抓取以下网页的完整正文内容并以 Markdown 格式返回：\n{url}"

    result = call_harness(input_text, ["web_extractor"])

    if result.get("error"):
        return json.dumps({"error": result["error"]}, ensure_ascii=False)

    return json.dumps({
        "url": url,
        "content": result["text"],
        "tool_details": result["tool_outputs"],
        "usage": result["usage"],
    }, ensure_ascii=False)
