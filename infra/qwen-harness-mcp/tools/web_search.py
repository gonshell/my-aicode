"""qwen_web_search - 联网搜索工具"""

import json
from client import call_harness


def web_search(query: str, max_results: int = 5) -> str:
    """Search the web via Qwen's built-in web_search harness tool.

    Args:
        query: Search query string.
        max_results: Maximum number of results to return (1-10).

    Returns:
        JSON string with search results and model summary.
    """
    max_results = max(1, min(10, max_results))
    input_text = (
        f"请搜索以下内容，返回最相关的前 {max_results} 条结果，"
        f"每条包含标题、摘要和URL：\n{query}"
    )
    result = call_harness(input_text, ["web_search"])

    if result.get("error"):
        return json.dumps({"error": result["error"]}, ensure_ascii=False)

    return json.dumps({
        "query": query,
        "answer": result["text"],
        "tool_details": result["tool_outputs"],
        "usage": result["usage"],
    }, ensure_ascii=False)
