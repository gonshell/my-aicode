#!/usr/bin/env python3
"""
inspect.py — 快速探查数据集文件
支持: jsonl, json, parquet, 目录

用法:
    python3 inspect.py <file_or_dir>
"""

import sys
import os
import json

PREVIEW_CHARS = 500


def sizeof_fmt(num):
    """人类可读的文件大小"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if abs(num) < 1024.0:
            return f"{num:.1f} {unit}"
        num /= 1024.0
    return f"{num:.1f} PB"


def infer_type(value):
    """推断值的类型"""
    if isinstance(value, str):
        return "string"
    elif isinstance(value, int):
        return "int"
    elif isinstance(value, float):
        return "float"
    elif isinstance(value, bool):
        return "bool"
    elif isinstance(value, list):
        return f"list[{infer_type(value[0]) if value else '?'}]"
    elif isinstance(value, dict):
        return "dict"
    elif value is None:
        return "null"
    else:
        return type(value).__name__


def inspect_jsonl(filepath):
    """探查 jsonl 文件"""
    size = os.path.getsize(filepath)
    count = 0
    fields = {}  # name -> type
    first_sample = None
    field_lengths = {}  # name -> [min, max, sum]

    with open(filepath) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            count += 1
            try:
                obj = json.loads(line)
            except:
                continue

            if first_sample is None:
                first_sample = obj

            for k, v in obj.items():
                if k not in fields:
                    fields[k] = infer_type(v)
                # 长度统计（字符串）
                if isinstance(v, str):
                    if k not in field_lengths:
                        field_lengths[k] = [len(v), len(v), 1]
                    else:
                        fl = field_lengths[k]
                        fl[0] = min(fl[0], len(v))
                        fl[1] = max(fl[1], len(v))
                        fl[2] += 1

    print(f"文件: {os.path.basename(filepath)}")
    print(f"格式: JSONL")
    print(f"大小: {sizeof_fmt(size)} ({size:,} bytes)")
    print(f"行数: {count:,}")
    print()

    print(f"字段 ({len(fields)} 个):")
    for name, ftype in sorted(fields.items()):
        extra = ""
        if name in field_lengths:
            fl = field_lengths[name]
            avg = fl[2] // max(1, count) if count > 0 else 0
            extra = f"  (字符串: min={fl[0]}, max={fl[1]}, avg≈{avg} chars)"
        print(f"  - {name}: {ftype}{extra}")

    if first_sample is not None:
        print()
        print("第一条样本预览:")
        preview = json.dumps(first_sample, ensure_ascii=False, indent=2)[:PREVIEW_CHARS]
        # 每行加前缀
        for line in preview.split("\n")[:20]:
            print(f"  {line}")
        if len(json.dumps(first_sample, ensure_ascii=False)) > PREVIEW_CHARS:
            print(f"  ... (共 {len(json.dumps(first_sample, ensure_ascii=False)):,} 字符，已截断)")


def inspect_json(filepath):
    """探查 json 文件"""
    size = os.path.getsize(filepath)
    with open(filepath) as f:
        data = json.load(f)

    print(f"文件: {os.path.basename(filepath)}")
    print(f"格式: JSON")
    print(f"大小: {sizeof_fmt(size)} ({size:,} bytes)")

    if isinstance(data, list):
        print(f"类型: list[{infer_type(data[0]) if data else '?'}]")
        print(f"长度: {len(data):,}")
        if data and isinstance(data[0], dict):
            fields = {}
            for k, v in data[0].items():
                fields[k] = infer_type(v)
            print(f"字段: {len(fields)} 个")
            for name, ftype in sorted(fields.items()):
                print(f"  - {name}: {ftype}")
    elif isinstance(data, dict):
        print(f"类型: dict ({len(data)} 个键)")
        for k, v in list(data.items())[:20]:
            print(f"  - {k}: {infer_type(v)}")
    else:
        print(f"类型: {infer_type(data)}")


def inspect_parquet(filepath):
    """探查 parquet 文件（需 pyarrow）"""
    size = os.path.getsize(filepath)
    print(f"文件: {os.path.basename(filepath)}")
    print(f"格式: Parquet")
    print(f"大小: {sizeof_fmt(size)} ({size:,} bytes)")

    try:
        import pyarrow.parquet as pq
    except ImportError:
        print()
        print("⚠ 未安装 pyarrow，无法读取 parquet 内容")
        print("  安装方法: pip install pyarrow")
        return

    table = pq.read_table(filepath)
    print(f"行数: {table.num_rows:,}")
    print(f"列数: {table.num_columns}")
    print()
    print(f"字段 ({table.num_columns} 个):")
    for name in table.column_names:
        col = table.column(name)
        dtype = str(col.type)
        null_count = col.null_count
        print(f"  - {name}: {dtype} (null: {null_count:,})")

    # 预览第一条
    if table.num_rows > 0:
        print()
        print("第一条样本预览:")
        first = table.slice(0, 1).to_pylist()[0]
        preview = json.dumps(first, ensure_ascii=False, default=str, indent=2)[:PREVIEW_CHARS]
        for line in preview.split("\n")[:20]:
            print(f"  {line}")


def inspect_dir(dirpath):
    """探查目录（找数据文件）"""
    data_files = []
    for root, dirs, files in os.walk(dirpath):
        for f in sorted(files):
            if f.endswith((".jsonl", ".json", ".parquet", ".jsonl.gz")):
                fpath = os.path.join(root, f)
                data_files.append(fpath)

    print(f"目录: {dirpath}")
    print(f"发现数据文件: {len(data_files)} 个")
    print()

    for i, fpath in enumerate(data_files):
        rel = os.path.relpath(fpath, dirpath)
        sz = sizeof_fmt(os.path.getsize(fpath))
        print(f"[{i+1}] {rel}  ({sz})")

    if data_files:
        print()
        print("=" * 60)
        # 探查第一个
        inspect_file(data_files[0])


def inspect_file(filepath):
    """自动识别格式并探查"""
    if not os.path.exists(filepath):
        print(f"✗ 文件不存在: {filepath}")
        return False

    if os.path.isdir(filepath):
        inspect_dir(filepath)
        return True

    ext = os.path.splitext(filepath)[1].lower()
    if ext == ".jsonl":
        inspect_jsonl(filepath)
    elif ext == ".json":
        inspect_json(filepath)
    elif ext == ".parquet":
        inspect_parquet(filepath)
    elif ext == ".gz":
        print(f"⚠ 压缩文件: {filepath}")
        print("  暂不支持直接读取压缩文件，请先解压")
    else:
        print(f"⚠ 未知格式: {ext}")
        # 试试当 jsonl 读
        try:
            with open(filepath) as f:
                first_line = f.readline()
                json.loads(first_line)
            print("  检测到 JSON 格式，尝试按 JSONL 读取...")
            print()
            inspect_jsonl(filepath)
        except:
            print("  无法识别为数据文件")

    return True


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    path = sys.argv[1]
    inspect_file(path)


if __name__ == "__main__":
    main()
