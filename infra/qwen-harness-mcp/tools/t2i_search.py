"""qwen_t2i_search - 文搜图工具"""

import json
import re
from client import call_harness, download_image


def t2i_search(query: str, count: int = 4) -> str:
    """Search images by text query via Qwen's built-in t2i_search harness tool.

    Downloads found images to local directory for use with vision_analyze.

    Args:
        query: Text description of images to search for.
        count: Number of images to return (1-10).

    Returns:
        JSON string with image URLs and local paths.
    """
    count = max(1, min(10, count))
    input_text = f"请搜索与「{query}」相关的图片，返回 {count} 张最相关的图片URL"

    result = call_harness(input_text, ["t2i_search"])

    if result.get("error"):
        return json.dumps({"error": result["error"]}, ensure_ascii=False)

    # Extract image URLs from the response text
    text = result["text"]
    urls = _extract_image_urls(text)

    # Download images locally
    images = []
    for i, url in enumerate(urls[:count]):
        local_path = download_image(url, f"t2i_{int(__import__('time').time()*1000)}_{i}.png")
        images.append({
            "url": url,
            "local_path": local_path,  # None if download failed
        })

    return json.dumps({
        "query": query,
        "description": text,
        "images": images,
        "usage": result["usage"],
    }, ensure_ascii=False)


def _extract_image_urls(text: str) -> list[str]:
    """Extract image URLs from model response text."""
    # Match markdown images: ![...](url)
    md_pattern = r'!\[[^\]]*\]\((https?://[^\s\)]+)\)'
    # Match bare URLs that look like images
    url_pattern = r'(https?://[^\s\)\"\'<>]+\.(?:png|jpg|jpeg|gif|webp|bmp|svg)(?:\?[^\s\)\"\'<>]*)?)'
    # Match any http(s) URL as fallback
    any_url_pattern = r'(https?://[^\s\)\"\'<>]+)'

    urls = re.findall(md_pattern, text)
    if not urls:
        urls = re.findall(url_pattern, text)
    if not urls:
        urls = re.findall(any_url_pattern, text)

    # Deduplicate preserving order
    seen = set()
    result = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            result.append(u)
    return result
