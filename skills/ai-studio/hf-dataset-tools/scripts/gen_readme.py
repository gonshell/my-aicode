#!/usr/bin/env python3
"""
gen_readme.py — 生成数据集目录的 README.md

遍历目录下所有数据集子目录，自动生成总览表 + 详细说明 + 分类索引。

用法:
    python3 gen_readme.py <datasets_dir> [output_file]
"""

import sys
import os
import json
import re
import datetime


def sizeof_fmt(num):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if abs(num) < 1024.0:
            return f"{num:.1f} {unit}"
        num /= 1024.0
    return f"{num:.1f} PB"


def count_jsonl(filepath):
    """统计 jsonl 行数和字段"""
    count = 0
    fields = set()
    first = True
    with open(filepath) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            count += 1
            try:
                obj = json.loads(line)
                if first:
                    fields = set(obj.keys())
                    first = False
                else:
                    fields &= set(obj.keys())
            except:
                pass
            if count >= 5 and not first:
                # 继续统计总行数，但字段已经够了
                pass
    # 精确统计总行数
    total = sum(1 for l in open(filepath) if l.strip())
    return total, sorted(fields)


def find_data_file(dirpath):
    """找主数据文件"""
    candidates = []
    for root, dirs, files in os.walk(dirpath):
        for f in files:
            if f.endswith((".jsonl", ".parquet", ".json")) and not f.startswith("."):
                fpath = os.path.join(root, f)
                size = os.path.getsize(fpath)
                candidates.append((size, fpath))
    if not candidates:
        return None
    # 返回最大的那个
    candidates.sort(reverse=True)
    return candidates[0][1]


def parse_readme_frontmatter(readme_path):
    """解析 README 的 YAML frontmatter（轻量版，足够用）"""
    info = {}
    if not os.path.exists(readme_path):
        return info

    with open(readme_path) as f:
        content = f.read()

    # 提取 frontmatter
    if not content.startswith("---"):
        return info

    parts = content.split("---", 2)
    if len(parts) < 3:
        return info

    fm_text = parts[1]

    # 逐行解析（只处理一层键 + 列表值）
    current_key = None
    for line in fm_text.split("\n"):
        stripped = line.rstrip()
        if not stripped or stripped.startswith("#"):
            continue

        # 列表项（可以是 "- val" 或 "  - val"）
        list_match = False
        for indent in ["  - ", "- ", "    - "]:
            if stripped.startswith(indent):
                val = stripped[len(indent):].strip()
                # 去掉冒号后的值（嵌套结构只取键）
                if ":" in val and not val.startswith("'"):
                    val = val.split(":", 1)[0].strip()
                if current_key and current_key not in info:
                    info[current_key] = []
                if current_key:
                    info[current_key].append(val)
                list_match = True
                break
        if list_match:
            continue

        # 键值对
        if ":" in stripped and not stripped.startswith(" "):
            key, val = stripped.split(":", 1)
            key = key.strip()
            val = val.strip()
            if val:
                info[key] = val
                current_key = key  # 允许后续空值列表覆盖
            else:
                current_key = key
                if key not in info:
                    info[key] = []

    # 提取第一段正文作为摘要
    body = parts[2]
    lines = [l.strip() for l in body.split("\n") if l.strip() and not l.startswith("#")]
    if lines:
        info["_summary"] = lines[0][:200]

    return info


def read_source_info(dirpath):
    """读取 source.txt（如果有）"""
    src_path = os.path.join(dirpath, "source.txt")
    info = {}
    if os.path.exists(src_path):
        with open(src_path) as f:
            for line in f:
                if ":" in line:
                    k, v = line.strip().split(":", 1)
                    info[k.strip()] = v.strip()
    return info


def detect_category(tags, fields, summary):
    """根据 tags/字段/摘要推断数据集分类"""
    rules = {
        "推理蒸馏类": ["reasoning", "cot", "chain-of-thought", "math", "思考", "think", "r1"],
        "智能体蒸馏类": ["agent", "tool", "function-call", "智能体", "工具调用", "agentic", "tool_use"],
        "代码类": ["code", "programming", "coding", "代码"],
        "对话闲聊类": ["chat", "conversation", "对话", "聊天", "instruction"],
        "多模态类": ["vision", "image", "video", "audio", "多模态"],
    }

    text = " ".join(tags + fields + [summary or ""]).lower()
    categories = []
    for cat, keywords in rules.items():
        for kw in keywords:
            if kw.lower() in text:
                categories.append(cat)
                break

    return categories if categories else ["其他"]


def detect_teacher_model(summary, tags):
    """推断教师模型（从摘要和 tags）"""
    text = " ".join(tags + [summary or ""]).lower()
    models = [
        ("Claude Opus 4.7", ["opus 4.7", "opus-4-7", "claude opus"]),
        ("Claude Opus 4.6", ["opus 4.6", "opus-4-6", "4.6 opus"]),
        ("Claude Fable-5", ["fable-5", "fable 5", "fable5"]),
        ("Qwen 3.5-27B", ["qwen3.5-27b", "qwen 3.5 27b"]),
        ("Qwen 3.5-9B", ["qwen3.5-9b", "qwen 3.5 9b"]),
        ("DeepSeek R1", ["deepseek-r1", "r1 distill", "deepseek r1"]),
        ("GPT-4", ["gpt-4", "gpt4"]),
    ]
    for name, keywords in models:
        for kw in keywords:
            if kw.lower() in text:
                return name
    return "—"


def inspect_dataset(dirpath):
    """探查一个数据集目录，返回结构化信息"""
    name = os.path.basename(dirpath)

    # 基本信息
    info = {
        "name": name,
        "dirpath": dirpath,
        "total_size": 0,
        "file_count": 0,
    }

    # 统计目录大小
    for root, dirs, files in os.walk(dirpath):
        for f in files:
            info["file_count"] += 1
            info["total_size"] += os.path.getsize(os.path.join(root, f))

    # 读 README
    readme_path = os.path.join(dirpath, "README.md")
    fm = parse_readme_frontmatter(readme_path)
    info["license"] = fm.get("license", "—")
    info["tags"] = fm.get("tags", [])
    info["languages"] = fm.get("language", [])
    info["size_category"] = fm.get("size_categories", "—")
    info["summary"] = fm.get("_summary", "")
    info["task_categories"] = fm.get("task_categories", [])

    # 读 source.txt
    src = read_source_info(dirpath)
    info["source"] = src.get("source", "—")
    info["source_type"] = src.get("type", "—")
    info["source_id"] = src.get("id", name)
    info["source_url"] = src.get("url", "—")

    # 找主数据文件
    data_file = find_data_file(dirpath)
    info["data_file"] = data_file
    info["data_format"] = os.path.splitext(data_file)[1].lstrip(".") if data_file else "—"

    # 统计数据（jsonl）
    if data_file and data_file.endswith(".jsonl"):
        count, fields = count_jsonl(data_file)
        info["row_count"] = count
        info["fields"] = fields
    elif data_file and data_file.endswith(".parquet"):
        info["row_count"] = "见 README"
        info["fields"] = ["(需 pyarrow 读取)"]
    elif data_file and data_file.endswith(".json"):
        try:
            with open(data_file) as f:
                data = json.load(f)
            if isinstance(data, list):
                info["row_count"] = len(data)
                info["fields"] = sorted(data[0].keys()) if data and isinstance(data[0], dict) else []
            else:
                info["row_count"] = "—"
                info["fields"] = []
        except:
            info["row_count"] = "—"
            info["fields"] = []
    else:
        info["row_count"] = "—"
        info["fields"] = []

    # 推断分类
    info["categories"] = detect_category(
        info.get("tags", []),
        info.get("fields", []),
        info.get("summary", "")
    )

    # 推断教师模型
    info["teacher_model"] = detect_teacher_model(
        info.get("summary", ""),
        info.get("tags", [])
    )

    return info


def generate_readme(datasets, output_path):
    """生成 README.md"""
    today = datetime.date.today().isoformat()

    lines = []
    lines.append("# Datasets 目录说明")
    lines.append("")
    lines.append("本目录存放用于模型训练/研究的各类数据集。")
    lines.append("")
    lines.append("## 数据集一览")
    lines.append("")
    lines.append(f"共 **{len(datasets)}** 个数据集。")
    lines.append("")
    lines.append("| # | 目录名 | 来源 | 类型 | 条数 | 大小 | 格式 | 教师模型 | 许可 |")
    lines.append("|---|---|---|---|---|---|---|---|---|")

    for i, ds in enumerate(datasets, 1):
        row_count = ds["row_count"] if isinstance(ds["row_count"], str) else f"{ds['row_count']:,}"
        size = sizeof_fmt(ds["total_size"])
        src = ds["source"]
        src_type = ds.get("source_type", "—")
        lic = ds.get("license", "—")
        teacher = ds.get("teacher_model", "—")
        cats = "/".join(ds["categories"])

        lines.append(
            f"| {i} | `{ds['name']}` | {src} | {cats} | {row_count} | {size} | {ds['data_format']} | {teacher} | {lic} |"
        )

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 各数据集详细说明")
    lines.append("")

    for i, ds in enumerate(datasets, 1):
        lines.append(f"### {i}. {ds['name']}")
        lines.append("")
        lines.append(f"- **来源**：{ds.get('source_url', ds['name'])}")
        lines.append(f"- **主文件**：`{os.path.relpath(ds['data_file'], ds['dirpath'])}`" if ds.get("data_file") else "- **主文件**：—")
        lines.append(f"- **文件数**：{ds['file_count']} 个")
        lines.append(f"- **大小**：{sizeof_fmt(ds['total_size'])}")

        row_count = ds["row_count"] if isinstance(ds["row_count"], str) else f"{ds['row_count']:,}"
        lines.append(f"- **条数**：{row_count}")

        if ds.get("fields"):
            fields_str = ", ".join(f"`{f}`" for f in ds["fields"][:10])
            if len(ds["fields"]) > 10:
                fields_str += f" 等 {len(ds['fields'])} 个"
            lines.append(f"- **字段**：{fields_str}")

        if ds.get("summary"):
            lines.append(f"- **简介**：{ds['summary']}")

        lines.append(f"- **分类**：{' / '.join(ds['categories'])}")
        lines.append(f"- **许可**：{ds.get('license', '—')}")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## 分类索引")
    lines.append("")

    # 按分类聚合
    cat_map = {}
    for ds in datasets:
        for cat in ds["categories"]:
            cat_map.setdefault(cat, []).append(ds["name"])

    for cat, names in sorted(cat_map.items()):
        lines.append(f"### {cat}")
        for n in names:
            lines.append(f"- `{n}`")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append(f"*自动生成于 {today}*")

    with open(output_path, "w") as f:
        f.write("\n".join(lines))

    return len(lines)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    datasets_dir = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else os.path.join(datasets_dir, "README.md")

    if not os.path.isdir(datasets_dir):
        print(f"✗ 目录不存在: {datasets_dir}")
        sys.exit(1)

    print(f"扫描目录: {datasets_dir}")
    print()

    # 找所有数据集子目录
    datasets = []
    for d in sorted(os.listdir(datasets_dir)):
        dpath = os.path.join(datasets_dir, d)
        if not os.path.isdir(dpath):
            continue
        if d.startswith("."):
            continue

        # 判断是不是数据集目录（有数据文件或有 README）
        has_data = False
        has_readme = os.path.exists(os.path.join(dpath, "README.md"))
        for root, dirs, files in os.walk(dpath):
            for f in files:
                if f.endswith((".jsonl", ".parquet", ".json")) and not f.startswith("."):
                    has_data = True
                    break
            if has_data:
                break

        if has_data or has_readme:
            print(f"  发现数据集: {d}")
            ds_info = inspect_dataset(dpath)
            datasets.append(ds_info)

    print(f"\n共发现 {len(datasets)} 个数据集")
    print(f"生成 README: {output_file}")

    line_count = generate_readme(datasets, output_file)
    print(f"完成: {line_count} 行")


if __name__ == "__main__":
    main()
