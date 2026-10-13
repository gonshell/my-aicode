#!/usr/bin/env python3
"""
download.py — 下载 HuggingFace / ModelScope 数据集或模型
零依赖：纯 Python 标准库（urllib / json / os）

用法:
    python3 download.py <url_or_id> [output_dir]

示例:
    python3 download.py Jackrong/Qwen3.5-reasoning-700x
    python3 download.py https://huggingface.co/datasets/nohurry/Opus-4.6-Reasoning-3000x-filtered
    python3 download.py https://modelscope.cn/models/xxx/yyy ./data
"""

import sys
import os
import json
import re
import urllib.request
import urllib.parse
import urllib.error
from urllib.parse import urlparse, quote

TIMEOUT = 120
SKIP_EXISTING = True


def fetch_text(url, timeout=None):
    """GET 请求返回文本"""
    if timeout is None:
        timeout = TIMEOUT
    req = urllib.request.Request(url, headers={
        "User-Agent": "hf-dataset-tools/1.0",
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace"), resp.status
    except urllib.error.HTTPError as e:
        return f"HTTP {e.code}: {e.reason}", e.code
    except Exception as e:
        return f"ERROR: {str(e)}", 0


def fetch_binary(url, local_path, timeout=None):
    """下载文件到本地，返回下载字节数"""
    if timeout is None:
        timeout = TIMEOUT
    if SKIP_EXISTING and os.path.exists(local_path):
        return os.path.getsize(local_path), "skipped"

    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    req = urllib.request.Request(url, headers={
        "User-Agent": "hf-dataset-tools/1.0",
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            total = int(resp.headers.get("Content-Length", 0))
            downloaded = 0
            tmp_path = local_path + ".part"
            with open(tmp_path, "wb") as f:
                while True:
                    chunk = resp.read(65536)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
            os.rename(tmp_path, local_path)
            return downloaded, "ok"
    except Exception as e:
        if os.path.exists(local_path + ".part"):
            os.remove(local_path + ".part")
        return 0, f"error: {str(e)}"


def detect_source(input_str):
    """识别输入类型，返回 (source_type, entity_type, entity_id)

    source_type: huggingface / modelscope
    entity_type: dataset / model
    entity_id: org/name
    """
    # 直接 org/name 格式
    if "/" in input_str and not input_str.startswith("http"):
        parts = input_str.split("/")
        if len(parts) == 2:
            return "huggingface", "dataset", input_str

    # URL 格式
    p = urlparse(input_str)
    netloc = p.netloc.lower()
    path = p.path.strip("/")
    parts = path.split("/")

    if "huggingface.co" in netloc:
        if parts and parts[0] == "datasets" and len(parts) >= 2:
            return "huggingface", "dataset", f"{parts[1]}/{parts[2]}" if len(parts) >= 3 else parts[1]
        elif len(parts) >= 2:
            return "huggingface", "model", f"{parts[0]}/{parts[1]}"

    if "modelscope.cn" in netloc:
        if parts and parts[0] == "datasets" and len(parts) >= 2:
            return "modelscope", "dataset", f"{parts[1]}/{parts[2]}" if len(parts) >= 3 else parts[1]
        elif parts and parts[0] == "models" and len(parts) >= 2:
            return "modelscope", "model", f"{parts[1]}/{parts[2]}" if len(parts) >= 3 else parts[1]
        elif len(parts) >= 2:
            return "modelscope", "model", f"{parts[0]}/{parts[1]}"

    return None, None, None


def list_hf_files(entity_id, entity_type):
    """列出 HF 数据集/模型的所有文件（递归）"""
    api_base = "https://huggingface.co/api"
    kind = "datasets" if entity_type == "dataset" else "models"

    def _list_tree(path=""):
        url = f"{api_base}/{kind}/{entity_id}/tree/main/{path}"
        text, status = fetch_text(url)
        if status != 200:
            return []
        try:
            items = json.loads(text)
        except:
            return []
        result = []
        for item in items:
            item_path = item.get("path", item.get("rfilename", ""))
            if item.get("type") == "directory" or item.get("type") == "folder":
                result.extend(_list_tree(item_path))
            else:
                result.append(item_path)
        return result

    return _list_tree()


def download_hf(entity_id, entity_type, output_dir):
    """下载 HF 数据集或模型"""
    kind = "datasets" if entity_type == "dataset" else "models"
    raw_base = f"https://huggingface.co"
    api_base = "https://huggingface.co/api"

    os.makedirs(output_dir, exist_ok=True)

    # 1. 元信息
    meta_url = f"{api_base}/{kind}/{entity_id}"
    meta_text, status = fetch_text(meta_url)
    if status == 200:
        with open(f"{output_dir}/meta.json", "w") as f:
            f.write(meta_text)
        print(f"  ✓ 元信息")
    else:
        print(f"  - 元信息获取失败: {meta_text[:80]}")

    # 2. 列文件
    files = list_hf_files(entity_id, entity_type)
    if not files:
        print(f"  ✗ 未找到文件")
        return False
    print(f"  发现 {len(files)} 个文件")

    # 3. 下载所有文件
    ok = 0
    skipped = 0
    failed = 0
    for fpath in files:
        if entity_type == "dataset":
            url = f"{raw_base}/datasets/{entity_id}/resolve/main/{fpath}"
        else:
            url = f"{raw_base}/{entity_id}/resolve/main/{fpath}"
        local_path = f"{output_dir}/{fpath}"
        size, result = fetch_binary(url, local_path)

        if result == "skipped":
            skipped += 1
            print(f"  - [跳过] {fpath} ({size:,} bytes)")
        elif result == "ok":
            ok += 1
            print(f"  ✓ [下载] {fpath} ({size:,} bytes)")
        else:
            failed += 1
            print(f"  ✗ [失败] {fpath}: {result}")

    # 4. 来源记录
    with open(f"{output_dir}/source.txt", "w") as f:
        f.write(f"source: huggingface\n")
        f.write(f"type: {entity_type}\n")
        f.write(f"id: {entity_id}\n")
        f.write(f"url: https://huggingface.co/{'datasets/' if entity_type == 'dataset' else ''}{entity_id}\n")

    print(f"\n  完成: {ok} 下载, {skipped} 跳过, {failed} 失败")
    return failed == 0


def download_modelscope(entity_id, entity_type, output_dir):
    """下载 ModelScope 数据集或模型（简化版，下 README + 主数据文件）"""
    os.makedirs(output_dir, exist_ok=True)
    print(f"  ⚠ ModelScope 下载为简化版（API 不稳定）")

    # 尝试下载 README
    for branch in ["master", "main"]:
        if entity_type == "dataset":
            url = f"https://modelscope.cn/datasets/{entity_id}/raw/{branch}/README.md"
        else:
            url = f"https://modelscope.cn/models/{entity_id}/raw/{branch}/README.md"
        text, status = fetch_text(url)
        if status == 200 and len(text) > 100:
            with open(f"{output_dir}/README.md", "w") as f:
                f.write(text)
            print(f"  ✓ README ({branch}): {len(text):,} bytes")
            break
    else:
        print(f"  ✗ README 获取失败")

    # 来源记录
    with open(f"{output_dir}/source.txt", "w") as f:
        f.write(f"source: modelscope\n")
        f.write(f"type: {entity_type}\n")
        f.write(f"id: {entity_id}\n")
        f.write(f"url: https://modelscope.cn/{'datasets/' if entity_type == 'dataset' else 'models/'}{entity_id}\n")

    print(f"  ⚠ 仅下载了 README，更多文件请手动下载或用 modelscope 官方 CLI")
    return True


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    input_str = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None

    source, etype, eid = detect_source(input_str)
    if not source:
        print(f"✗ 无法识别输入: {input_str}")
        print("支持: HuggingFace URL, ModelScope URL, 或 org/name 格式")
        sys.exit(1)

    # 默认输出目录
    if not output_dir:
        safe_name = eid.replace("/", "_")
        output_dir = f"./{safe_name}"

    print(f"来源: {source}")
    print(f"类型: {etype}")
    print(f"ID: {eid}")
    print(f"输出: {output_dir}")
    print()

    if source == "huggingface":
        ok = download_hf(eid, etype, output_dir)
    elif source == "modelscope":
        ok = download_modelscope(eid, etype, output_dir)
    else:
        ok = False

    if ok:
        print(f"\n✅ 下载完成 → {output_dir}/")
        # 列出结果
        total_size = 0
        total_files = 0
        for root, dirs, files in os.walk(output_dir):
            for f in files:
                fpath = os.path.join(root, f)
                total_size += os.path.getsize(fpath)
                total_files += 1
        print(f"   共 {total_files} 个文件，{total_size:,} bytes")
    else:
        print(f"\n❌ 下载失败")
        sys.exit(1)


if __name__ == "__main__":
    main()
