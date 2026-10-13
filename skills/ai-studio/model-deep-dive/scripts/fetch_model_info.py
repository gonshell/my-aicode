#!/usr/bin/env python3
"""
model-deep-dive 信息采集脚本
支持 HuggingFace / ModelScope / GitHub 三种来源
零依赖：只用 Python 标准库（urllib / json / re / os）

用法:
    python3 fetch_model_info.py <url> [output_dir]
"""

import sys
import os
import json
import re
import urllib.request
import urllib.error
from urllib.parse import urlparse, quote


def fetch_url(url, timeout=30, binary=False):
    """GET 请求，返回文本或 bytes"""
    req = urllib.request.Request(url, headers={
        "User-Agent": "model-deep-dive/1.0",
        "Accept": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read()
            if binary:
                return data, resp.status
            return data.decode("utf-8", errors="replace"), resp.status
    except urllib.error.HTTPError as e:
        return f"HTTP {e.code}: {e.reason}", e.code
    except Exception as e:
        return f"ERROR: {str(e)}", 0


def detect_source(url):
    """识别 URL 来源类型和实体 ID"""
    p = urlparse(url)
    netloc = p.netloc.lower()
    path = p.path.strip("/")

    # HuggingFace
    if "huggingface.co" in netloc:
        parts = path.split("/")
        if parts[0] == "datasets" and len(parts) >= 3:
            return "hf_dataset", f"{parts[1]}/{parts[2]}"
        elif len(parts) >= 2:
            return "hf_model", f"{parts[0]}/{parts[1]}"

    # ModelScope
    if "modelscope.cn" in netloc:
        parts = path.split("/")
        if parts[0] == "datasets" and len(parts) >= 3:
            return "ms_dataset", f"{parts[1]}/{parts[2]}"
        elif parts[0] == "models" and len(parts) >= 3:
            return "ms_model", f"{parts[1]}/{parts[2]}"
        elif len(parts) >= 2:
            return "ms_model", f"{parts[0]}/{parts[1]}"

    # GitHub
    if "github.com" in netloc:
        parts = path.split("/")
        if len(parts) >= 2:
            return "github_repo", f"{parts[0]}/{parts[1]}"

    return "unknown", None


def fetch_hf_model(model_id, output_dir):
    """拉取 HuggingFace 模型信息"""
    api_base = "https://huggingface.co/api"
    raw_base = "https://huggingface.co"

    os.makedirs(output_dir, exist_ok=True)

    # 1. 元信息（API）
    meta_url = f"{api_base}/models/{model_id}"
    meta_text, status = fetch_url(meta_url)
    if status == 200:
        with open(f"{output_dir}/meta.json", "w") as f:
            f.write(meta_text)
        meta = json.loads(meta_text)
        print(f"  ✓ 元信息: {meta.get('id', model_id)}")
    else:
        print(f"  ✗ 元信息获取失败: {meta_text}")
        meta = {}

    # 2. README
    readme_url = f"{raw_base}/{model_id}/raw/main/README.md"
    readme, status = fetch_url(readme_url)
    if status == 200 and len(readme) > 100:
        with open(f"{output_dir}/README.md", "w") as f:
            f.write(readme)
        print(f"  ✓ README: {len(readme):,} 字符")
    else:
        # 试试其他默认分支
        for branch in ["master", "main"]:
            alt_url = f"{raw_base}/{model_id}/raw/{branch}/README.md"
            readme, status = fetch_url(alt_url)
            if status == 200 and len(readme) > 100:
                with open(f"{output_dir}/README.md", "w") as f:
                    f.write(readme)
                print(f"  ✓ README ({branch}): {len(readme):,} 字符")
                break
        else:
            print(f"  ✗ README 获取失败")

    # 3. 文件列表
    files_url = f"{api_base}/models/{model_id}/tree/main"
    files_text, status = fetch_url(files_url)
    if status == 200:
        with open(f"{output_dir}/files.json", "w") as f:
            f.write(files_text)
        files = json.loads(files_text)
        print(f"  ✓ 文件列表: {len(files)} 项")
    else:
        print(f"  ✗ 文件列表获取失败")

    # 4. 关联数据集
    if meta.get("tags"):
        datasets = [t.replace("dataset:", "") for t in meta["tags"] if t.startswith("dataset:")]
        if datasets:
            with open(f"{output_dir}/related_datasets.json", "w") as f:
                json.dump(datasets, f, indent=2, ensure_ascii=False)
            print(f"  ✓ 关联数据集: {len(datasets)} 个")

    # 5. 来源记录
    with open(f"{output_dir}/source.txt", "w") as f:
        f.write(f"type: hf_model\nid: {model_id}\nurl: https://huggingface.co/{model_id}\n")

    return True


def fetch_ms_model(model_id, output_dir):
    """拉取 ModelScope 模型信息"""
    api_base = "https://modelscope.cn/api/v1"
    raw_base = "https://modelscope.cn"

    os.makedirs(output_dir, exist_ok=True)

    # 1. 元信息
    meta_url = f"{api_base}/models/{model_id}"
    meta_text, status = fetch_url(meta_url)
    if status == 200:
        with open(f"{output_dir}/meta.json", "w") as f:
            f.write(meta_text)
        print(f"  ✓ 元信息: {model_id}")
    else:
        # ModelScope API 路径可能不同，试试列表接口
        search_url = f"{api_base}/models?Name={quote(model_id)}"
        search_text, status2 = fetch_url(search_url)
        if status2 == 200:
            with open(f"{output_dir}/search.json", "w") as f:
                f.write(search_text)
            print(f"  ✓ 搜索结果")
        else:
            print(f"  ✗ 元信息获取失败: {meta_text}")

    # 2. README
    readme_url = f"{raw_base}/models/{model_id}/raw/master/README.md"
    readme, status = fetch_url(readme_url)
    if status != 200 or len(readme) < 100:
        readme_url = f"{raw_base}/models/{model_id}/blob/master/README.md"
        readme, status = fetch_url(readme_url)
    if status == 200 and len(readme) > 100:
        # 如果是 HTML 页面（blob 返回的），提取 md 内容
        if "<!DOCTYPE" in readme[:100]:
            # 尝试找 raw 链接
            m = re.search(r'href="([^"]*README\.md[^"]*)"', readme)
            if m:
                raw_url = "https:" + m.group(1) if m.group(1).startswith("//") else m.group(1)
                readme, _ = fetch_url(raw_url)
        with open(f"{output_dir}/README.md", "w") as f:
            f.write(readme)
        print(f"  ✓ README: {len(readme):,} 字符")
    else:
        print(f"  ✗ README 获取失败")

    # 3. 文件列表（用模型详情页的文件树）
    files_url = f"{api_base}/models/{model_id}/files"
    files_text, status = fetch_url(files_url)
    if status == 200:
        with open(f"{output_dir}/files.json", "w") as f:
            f.write(files_text)
        print(f"  ✓ 文件列表")
    else:
        print(f"  - 文件列表: API 不可用")

    with open(f"{output_dir}/source.txt", "w") as f:
        f.write(f"type: ms_model\nid: {model_id}\nurl: https://modelscope.cn/models/{model_id}\n")

    return True


def fetch_github_repo(repo_id, output_dir):
    """拉取 GitHub 项目信息"""
    api_base = "https://api.github.com"
    raw_base = "https://raw.githubusercontent.com"

    os.makedirs(output_dir, exist_ok=True)

    # 1. 仓库元信息
    meta_url = f"{api_base}/repos/{repo_id}"
    meta_text, status = fetch_url(meta_url)
    if status == 200:
        with open(f"{output_dir}/meta.json", "w") as f:
            f.write(meta_text)
        meta = json.loads(meta_text)
        print(f"  ✓ 仓库信息: {meta.get('full_name', repo_id)}")
        default_branch = meta.get("default_branch", "main")
    else:
        print(f"  ✗ 仓库信息获取失败: {meta_text}")
        default_branch = "main"
        meta = {}

    # 2. README
    readme_found = False
    for branch in [default_branch, "main", "master"]:
        readme_url = f"{raw_base}/{repo_id}/{branch}/README.md"
        readme, status = fetch_url(readme_url)
        if status == 200 and len(readme) > 50:
            with open(f"{output_dir}/README.md", "w") as f:
                f.write(readme)
            print(f"  ✓ README ({branch}): {len(readme):,} 字符")
            readme_found = True
            break
    if not readme_found:
        print(f"  ✗ README 获取失败")

    # 3. 文件树（顶层）
    tree_url = f"{api_base}/repos/{repo_id}/git/trees/{default_branch}"
    tree_text, status = fetch_url(tree_url)
    if status == 200:
        with open(f"{output_dir}/files.json", "w") as f:
            f.write(tree_text)
        tree = json.loads(tree_text)
        print(f"  ✓ 文件树: {len(tree.get('tree', []))} 项")
    else:
        print(f"  - 文件树: API 不可用")

    # 4. 找训练脚本/配置文件（关键词匹配）
    keywords = ["train", "finetune", "config", "lora", "sft", "dpo"]
    interesting_files = []
    tree_data = json.loads(tree_text) if status == 200 else {"tree": []}
    for item in tree_data.get("tree", []):
        name = item.get("path", "").lower()
        if any(kw in name for kw in keywords) and item.get("type") == "blob":
            interesting_files.append(item["path"])
    if interesting_files:
        # 拉取前 5 个有趣的文件
        for fpath in interesting_files[:5]:
            file_url = f"{raw_base}/{repo_id}/{default_branch}/{fpath}"
            content, fstatus = fetch_url(file_url)
            if fstatus == 200:
                safe_name = fpath.replace("/", "__")
                with open(f"{output_dir}/src_{safe_name}", "w") as f:
                    f.write(content)
        print(f"  ✓ 关键文件: {len(interesting_files)} 个（已下载 {min(5, len(interesting_files))} 个）")

    with open(f"{output_dir}/source.txt", "w") as f:
        f.write(f"type: github_repo\nid: {repo_id}\nurl: https://github.com/{repo_id}\nbranch: {default_branch}\n")

    return True


def main():
    if len(sys.argv) < 2:
        print("用法: python3 fetch_model_info.py <url> [output_dir]")
        print("支持: HuggingFace 模型/数据集, ModelScope 模型, GitHub 仓库")
        sys.exit(1)

    url = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "./model-info"

    source_type, entity_id = detect_source(url)
    print(f"识别来源: {source_type} / {entity_id}")
    print(f"输出目录: {output_dir}")
    print()

    if source_type == "hf_model":
        ok = fetch_hf_model(entity_id, output_dir)
    elif source_type == "ms_model":
        ok = fetch_ms_model(entity_id, output_dir)
    elif source_type == "github_repo":
        ok = fetch_github_repo(entity_id, output_dir)
    else:
        print(f"不支持的 URL 类型: {url}")
        print("支持: huggingface.co, modelscope.cn, github.com")
        sys.exit(1)

    if ok:
        print(f"\n✅ 采集完成 → {output_dir}/")
        # 列出文件
        for f in sorted(os.listdir(output_dir)):
            fpath = os.path.join(output_dir, f)
            sz = os.path.getsize(fpath)
            print(f"   {f:30s} {sz:>8,} bytes")
    else:
        print("\n❌ 采集失败")
        sys.exit(1)


if __name__ == "__main__":
    main()
