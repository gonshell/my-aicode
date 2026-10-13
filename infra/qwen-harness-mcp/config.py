"""Configuration loader for Qwen Harness MCP Server.

Priority: environment variables > config.yaml > defaults.
"""

import os
import yaml
from pathlib import Path

_CONFIG_PATH = Path(__file__).parent / "config.yaml"


def _load_yaml_config() -> dict:
    if _CONFIG_PATH.exists():
        with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


_yaml = _load_yaml_config()


def get(key: str, default=None):
    """Get config value: env var > yaml > default."""
    env_key = f"QWEN_HARNESS_{key.upper()}"
    return os.environ.get(env_key) or _yaml.get(key) or default


# Resolved config
API_KEY = get("api_key", "")
BASE_URL = get("base_url", "")
MODEL = get("model", "qwen3.7-plus")
TIMEOUT = int(get("timeout", "60"))
CODE_TIMEOUT = int(get("code_timeout", "120"))
IMAGE_DIR = get("image_dir", "/tmp/qwen_harness")
MAX_IMAGE_SIZE = int(get("max_image_size", str(10 * 1024 * 1024)))  # 10MB
MAX_RETRIES = int(get("max_retries", "2"))
