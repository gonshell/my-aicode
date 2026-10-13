---
name: hf-dataset-tools
description: "HuggingFace / ModelScope 数据集工具集：下载、探查、目录README生成。零依赖（纯urllib）。"
tags: [dataset, huggingface, modelscope, download, inspection, tools]
triggers:
  - 下载数据集
  - 下载 hf 数据集
  - 查看数据集
  - 数据集统计
  - 生成数据集 README
  - hf download
  - dataset tools
---

# HF Dataset Tools — 数据集工具集

> 三个小工具：下载 / 探查 / 目录 README 生成。
> 零依赖（纯 Python 标准库），不用装 huggingface_hub。

## When to use

- 用户说"下载这个 HF 数据集" / "下这个 ModelScope 数据集"
- 用户说"看看这个数据集有什么字段 / 多少条"
- 用户说"给 datasets 目录写个 README"
- 任何需要快速操作 HF 数据集的场景

## 不做什么

- 不做数据清洗/预处理
- 不做格式转换（jsonl ↔ parquet）
- 不做质量评估（那是 sftquality / llm-as-judge-eval 的事）
- 不上传到 HF

## 三个工具

### 1. download.py — 下载数据集

```bash
python3 scripts/download.py <dataset_id_or_url> [output_dir]
```

**功能**：
- 自动识别来源（HuggingFace / ModelScope）
- 递归下载所有文件，保持目录结构
- 已存在的文件跳过（不重复下载）
- 支持模型和数据集两种类型
- 零依赖（纯 urllib）

**支持的输入**：
- `huggingface.co/datasets/org/name` — HF 数据集
- `huggingface.co/org/name` — HF 模型（自动判断）
- `modelscope.cn/datasets/org/name` — ModelScope 数据集
- `modelscope.cn/models/org/name` — ModelScope 模型
- `org/name` — 默认为 HF 数据集

**输出结构**：
```
output_dir/
├── README.md           # 原始 README
├── meta.json           # API 元信息
├── data/
│   └── train-00000-of-00001.parquet
└── source.txt          # 来源记录
```

### 2. inspect.py — 探查数据集

```bash
python3 scripts/inspect.py <dataset_file_or_dir>
```

**功能**：
- jsonl / json：行数、字段列表、第一条样本预览、各字段长度统计
- parquet：行数、列、样本预览（需 pyarrow，没有则提示安装）
- 目录：遍历所有数据文件，汇总统计
- 输出结构化摘要

**输出内容**：
```
文件: data.jsonl
格式: jsonl
行数: 1,234
大小: 5.2 MB
字段:
  - id (string)
  - conversation (list)
  - output (string, avg: 847 chars)
第一条样本预览:
  {...}
```

### 3. gen_readme.py — 生成目录 README

```bash
python3 scripts/gen_readme.py <datasets_dir> [output_file]
```

**功能**：
- 遍历目录下所有数据集子目录
- 自动生成总览表（名称 / 来源 / 类型 / 条数 / 大小 / 格式 / 许可）
- 自动分类（推理 / 智能体 / 代码 / 对话 / 多模态等，根据 tags 和字段推断）
- 每个数据集自动提取要点（从 README + 字段信息）
- 已存在的 README 会被覆盖（建议先备份）

**输出结构**：
```markdown
# Datasets 目录说明

## 数据集一览
| # | 目录名 | 来源 | 类型 | 条数 | 大小 | 格式 | 教师模型 | 许可 |

## 各数据集详细说明
### 1. xxx
- 字段：...
- 特点：...

## 分类
- 推理蒸馏类：...
- 智能体蒸馏类：...
```

## 配置

默认配置在 `config.json`。

| 配置项 | 默认值 | 说明 |
|---|---|---|
| `default_source` | `huggingface` | 只给 org/name 时的默认来源 |
| `timeout` | `120` | 下载超时时间（秒） |
| `skip_existing` | `true` | 已存在的文件是否跳过 |
| `inspect_preview_chars` | `500` | 探查时样本预览字符数 |
| `readme_template` | `default` | README 模板风格 |

## 工作流（典型场景）

### 场景 1：下载一个新数据集

```
1. 用户给链接 → 识别来源
2. download.py 下载全部文件
3. inspect.py 看一眼数据结构
4. gen_readme.py 更新目录 README
```

### 场景 2：批量下载多个数据集

```
1. 循环调用 download.py
2. 最后 gen_readme.py 一次性更新
```

### 场景 3：快速看一个数据集长什么样

```
直接 inspect.py，不用打开文件翻
```

## Pitfalls

1. **HF 的 web_extract 常被拦截**：不要用 web_extract 拉 HF 页面，直接 urllib 打 raw 端点。download.py 已经这么做了。
2. **parquet 需要 pyarrow**：没有装的话 inspect.py 会降级（只报文件大小，不读内容）。不要为了这个装依赖，用户有需要自己装。
3. **大数据集下载要耐心**：几十 GB 的数据集别在前台跑，用 terminal background + notify_on_complete。
4. **README 生成是"辅助"不是"替代"**：自动生成的是骨架，分类和特点可能不准，需要人工校对。特别是领域分类，准确率大概 70-80%。
5. **ModelScope API 不稳定**：ModelScope 的公开 API 不如 HF 稳定，有时返回格式会变。失败时直接用 raw README 兜底。
6. **文件名特殊字符**：HF 文件名可能含中文/空格，下载时注意 URL 编码。
