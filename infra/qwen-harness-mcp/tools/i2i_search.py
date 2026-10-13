"""qwen_i2i_search - 图搜图工具"""

import json
import re
import time
from client import call_harness, download_image


def i2i_search(image_url: str, count: int = 4) -> str:
    """Search similar images by providing a reference image URL.

    Uses Qwen's built-in i2i_search harness tool.

    Args:
        image_url: URL of the reference image to search similar images for.
        count: Number of similar images to return (1-10).

    Returns:
        JSON string with similar image URLs and local paths.
    """
    count = max(1, min(10, count))
    input_text = (
        f"请以这张图片为参考，搜索 {count} 张相似的图片：\n{image_url}"
    )

    result = call_harness(input_text, ["i2i_search"])

    if result.get("error"):
        return json.dumps({"error": result["error"]}, ensure_ascii=False)

    text = result["text"]
    urls = _extract_image_urls(text)

    images = []
    for i, url in enumerate(urls[:count]):
        local_path = download_image(url, f"i2i_{int(time.time()*1000)}_{i}.png")
        images.append({
            "url": url,
            "local_path": local_path,
        })

    return json.dumps({
        "reference_image": image_url,
        "description": text,
        "similar_images": images,
        "usage": result["usage"],
    }, ensure_ascii=False)


def _extract_image_urls(text: str) -> list[str]:
    """Extract image URLs from model response text."""
    md_pattern = r'!\[[^\]]*\]\((https?://[^\s\)]+)\)'
    url_pattern = r'(https?://[^\s\)\"\'<>]+\.(?:png|jpg|jpeg|gif|webp|bmp|svg)(?:\?[^\s\)\"\'<>]*)?)'
    any_url_pattern = r'(https?://[^\s\)\"\'<>]+)'

    urls = re.findall(md_pattern, text)
    if not urls:
        urls = re.findall(url_pattern, text)
    if not urls:
        urls = re.findall(any_url_pattern, text)

    seen = set()
    result = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            result.append(u)
    return result
