"""Qwen Harness MCP Server - Main entry point.

Exposes 5 Qwen Token Plan harness tools as MCP tools for Hermes Agent:
  - qwen_web_search:    联网搜索
  - qwen_web_extract:   网页抓取
  - qwen_code_interpreter: 代码解释器（云端沙箱，有网络）
  - qwen_t2i_search:    文搜图
  - qwen_i2i_search:    图搜图

Transport: stdio (Hermes spawns this as a subprocess).
"""

import sys
import json
from mcp.server.fastmcp import FastMCP

import config
from tools.web_search import web_search
from tools.web_extract import web_extract
from tools.code_interpreter import code_interpreter
from tools.t2i_search import t2i_search
from tools.i2i_search import i2i_search

# Create MCP server
mcp = FastMCP(
    "qwen-harness",
    instructions="Qwen Token Plan Harness tools: web search, web extract, code interpreter, text-to-image search, image-to-image search",
)


@mcp.tool()
def qwen_web_search(query: str, max_results: int = 5) -> str:
    """联网搜索 - Search the web via Qwen's built-in web_search tool.
    Returns structured search results with titles, snippets, and URLs.
    Best for Chinese-language queries and China-specific content.

    Args:
        query: Search query string.
        max_results: Max results to return (1-10, default 5).
    """
    return web_search(query, max_results)


@mcp.tool()
def qwen_web_extract(url: str, instruction: str = "") -> str:
    """网页抓取 - Extract content from a web page via Qwen's web_extractor tool.
    Handles JavaScript-rendered pages better than simple HTTP fetch.

    Args:
        url: The URL to extract content from.
        instruction: Optional: what to extract or how to summarize.
    """
    return web_extract(url, instruction)


@mcp.tool()
def qwen_code_interpreter(code: str, language: str = "python", instruction: str = "") -> str:
    """代码解释器 - Execute code in Qwen's cloud sandbox.
    Unlike local execution, the sandbox HAS network access.
    Supports Python, JavaScript, and other languages.

    Args:
        code: The code to execute.
        language: Programming language (default: python).
        instruction: Optional additional instruction.
    """
    return code_interpreter(code, language, instruction)


@mcp.tool()
def qwen_t2i_search(query: str, count: int = 4) -> str:
    """文搜图 - Search images by text description via Qwen's t2i_search tool.
    Downloads images locally for use with vision_analyze.

    Args:
        query: Text description of images to find.
        count: Number of images to return (1-10, default 4).
    """
    return t2i_search(query, count)


@mcp.tool()
def qwen_i2i_search(image_url: str, count: int = 4) -> str:
    """图搜图 - Find similar images by providing a reference image URL.
    Uses Qwen's i2i_search tool. Downloads results locally.

    Args:
        image_url: URL of the reference image.
        count: Number of similar images to return (1-10, default 4).
    """
    return i2i_search(image_url, count)


def main():
    """Run the MCP server via stdio."""
    # Validate config early
    if not config.API_KEY or not config.BASE_URL:
        print(
            "ERROR: Qwen Harness not configured.\n"
            "Edit config.yaml in the project directory and fill in:\n"
            "  api_key: your-token-plan-api-key\n"
            "  base_url: https://{WorkspaceId}.cn-beijing.maas.aliyuncs.com/compatible-mode/v1\n",
            file=sys.stderr,
        )
        sys.exit(1)

    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
