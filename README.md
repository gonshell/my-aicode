# my-aicode

我所有 AI 编码相关项目的聚合私有仓库，减少维护成本。

- **给人读的手册** → 本文件
- **给 agent 读的约定** → [AGENTS.md](./AGENTS.md)（Hermes / Codex / Copilot / Cursor 等自动加载）

---

## 📂 目录结构

截至 2026-10-13，共 **163 个文件 / 1515 KB**。

```
my-aicode/
├── README.md                 本文件：人类手册
├── AGENTS.md                 agent 约定（每次动手前自动加载）
├── LICENSE                   MIT
├── .gitignore                Python/Node/编辑器通用忽略
│
├── infra/                    基础设施层 · 35 文件 / 147 KB
│   ├── autoloop/             22 文件 / 127 KB
│   └── qwen-harness-mcp/     13 文件 /  20 KB
│
├── skills/                   技能包 · 77 文件 / 488 KB
│   ├── ai-studio/            16 项 · 56 文件 / 417 KB
│   └── reading-suite/        1 个技能包 · 21 文件 / 72 KB
│
├── products/                 产品与研究 · 45 文件 / 872 KB
│   ├── craftpulse/           37 文件 / 827 KB
│   ├── kino/                  5 文件 /  20 KB
│   ├── ai-daily/              2 文件 /  15 KB
│   └── ai-session-knowledge-base/  1 文件 / 10 KB
│
├── labs/                     实验层 · 空（仅 .gitkeep）
├── tools/                    小工具层 · 空（仅 .gitkeep）
└── docs/                     公共文档层 · 空（仅 .gitkeep）
```

### 每个目录里是什么

| 目录 | 里面有什么 | 状态 |
|------|-----------|------|
| `infra/` | 通用基础设施，所有产品可用 | ✅ 有内容 |
| `infra/autoloop/` | 自动化代理循环执行引擎：`engine.py`(11K) `executor.py`(7K) `verifier.py`(7K) `llm_client.py`(7K) `state.py`(7K) `context.py`(7K) `prompts.py` `controller.py` `config.py` `run.py`；`tools/`(4 个：base/file/shell)、`examples/buggy_project/`、`docs/spec-v1-original.md`(52K) | ⚠️ 开发中 |
| `infra/qwen-harness-mcp/` | 通义千问 MCP 服务：`server.py`、`client.py`、`config.py`、`config.yaml.example`；`tools/`（5 个：`code_interpreter` `web_search` `web_extract` `t2i_search` `i2i_search`） | ✅ 可用 |
| `skills/` | Hermes 技能包，面向 Agent 的工具链 | ✅ 有内容 |
| `skills/ai-studio/` | 内容/研究类技能组，16 项（见下方清单）；`shared/RULES.md` 为组内共享规范 | ✅ 可用 |
| `skills/reading-suite/` | 知识库精读技能链：`main.py`、`scripts/`(`cards` `read` `review`)、`shared/`(9 个：`state_manager` `intent_analyzer` `dialogue_writer` `role_validator` `file_utils` `anchor_generator` `file_lock` `logger`)、`templates/`(3)、`docs/`(总体设计 v2.0) | ✅ 可用 |
| `tools/` | 独立小工具、脚本 | ⬜ 空，待用 |
| `products/` | 面向终端用户的完整产品、研究项目 | ✅ 有内容 |
| `products/craftpulse/` | 专家知识传承方法论研究：`docs/articles/`(9 篇)、`docs/decisions/`(8 个 ADR)、`docs/`(完整版 v2 md+html)、`archive/`(历史旧版 15 文件，含 html 原型) | ✅ 已完成 |
| `products/kino/` | Kino 企业知识库产品：`docs/KINO-DEVELOPMENT-GUIDE.html`、`docs/agents/`(glossary、issue-tracker) | ⚠️ 领域建模中 |
| `products/ai-daily/` | AI 日更方案：`scheme.md` + `scheme.html` | 📝 方案 |
| `products/ai-session-knowledge-base/` | AI 会话知识资产管理完整方案（单文档） | 📝 方案 |
| `labs/` | 实验性项目，未定型（POC、原型、临时脑洞） | ⬜ 空，待用 |
| `docs/` | 跨项目公共文档（commit 规范、发布流程等） | ⬜ 空，待用 |

---

## 📦 现有项目清单

| 路径 | 项目 | 状态 | tag 前缀 |
|------|------|------|----------|
| `infra/autoloop` | 自动化代理引擎 | ⚠️ 开发中 | `autoloop-` |
| `infra/qwen-harness-mcp` | 通义千问 MCP 服务 | ✅ 可用 | `qwen-` |
| `skills/reading-suite` | 知识库精读技能链（7 合 1） | ✅ 可用 | `reading-` |
| `skills/ai-studio` | 内容/研究技能组（16 项） | ✅ 可用 | `ai-studio-` |
| `products/craftpulse` | 专家知识传承研究 | ✅ 完成 | `craftpulse-` |
| `products/kino` | Kino 企业知识库 | ⚠️ 领域建模中 | `kino-` |
| `products/ai-daily` | AI 日更方案 | 📝 方案 | `ai-daily-` |
| `products/ai-session-knowledge-base` | AI 会话知识资产管理 | 📝 方案 | `askb-` |

### `skills/ai-studio/` 的 16 项

| 技能 | 做什么 | 文件 |
|------|--------|------|
| `ai-content-production` | 多平台 AI 内容生产（一鱼三吃、来源分级） | 9 |
| `ai-content-imagery` | AI 内容配图/封面/长图（HTML 模板 + Chromium 渲染） | 3 |
| `ai-content-metrics` | 三平台指标复盘、爆款归因、A/B 测试 | 1 |
| `tech-blog-production` | 技术深度调研 → 公众号技术博客 | 4 |
| `video-to-deep-blog` | 视频字幕 → 专业深度长文 | 1 |
| `deep-research-report` | 基于原始论文的深度技术报告 | 2 |
| `arxiv-paper-reading` | arXiv 论文 → 可用纯文本（HTML 提取 + 表格交叉验证） | 1 |
| `model-deep-dive` | 开源模型/项目深度技术分析 | 4 |
| `hf-dataset-tools` | HF / ModelScope 数据集下载、探查、README 生成 | 5 |
| `sft-dataset-construction` | SFT 数据集构建全流程编排 | 1 |
| `sft-dataset-assessment` | SFT 数据集质量评估（规则 + 统计 + LLM 抽检） | 3 |
| `sft-dataset-augmentation` | SFT 数据增强（垂域种子 QA → 分级扩充） | 3 |
| `md-to-styled-html` | 大型技术 markdown → 样式化单文件 HTML | 7 |
| `md-diagrams` | md 内 ASCII/mermaid/目录树 → 高清内联 SVG | 6 |
| `webpage-translation` | 英文网页 → 中文 HTML（图片 base64 内嵌） | 5 |
| `shared` | 组内共享规范 `RULES.md` | 1 |

---

## 🎯 核心原则（3 条，没有其他约束）

1. **零侵入**：每个子项目完全独立，不改变任何代码、配置、设计、迭代目标
2. **零额外成本**：不引入任何新工具链，开发流程和独立 repo 完全一样
3. **完全可逆**：任何子项目随时可以完整拆成独立 repo，无任何历史损失

---

## 📖 完整操作手册

### 1. 新建项目

#### 第一步：判断分类，选对目录
按以下顺序判断：
1. 是不是**通用基础设施**，所有产品都能用？→ `infra/`
2. 是不是**Hermes 技能包**？→ `skills/`
3. 是不是**独立小工具/脚本**？→ `tools/`
4. 是不是**面向终端用户的完整产品/研究项目**？→ `products/`
5. 不确定/还在实验/临时脑洞？→ `labs/`（以后成熟了再挪，零成本）

#### 第二步：初始化项目
```bash
cd skills/
mkdir video-gen && cd video-gen
# 用到什么就建什么，和独立 repo 完全一样
```
每个子项目必须保留：自己的 `README.md`（讲清楚是什么、怎么用）、自己的配置文件（`package.json`、`pyproject.toml` 等）。

#### 第三步：更新文档 + 打初始 tag
```bash
# 1) 更新本文件的两个表格（目录结构、项目清单）
# 2) 打初始版本 tag，必须加项目前缀
git tag video-gen-v0.1.0
```

### 2. 迭代现有项目

和操作独立 repo **完全一样**：
```bash
cd skills/reading-suite/
# 改代码、测试，按原项目流程走

git add .
git commit -m "fix(reading): 修复 xx bug"

git tag reading-v2.1.1
# 按原项目发布流程发布（如 npm publish / 飞书文档更新）
```

### 3. 移动项目（比如从 labs 成熟了移到 products）

```bash
git mv labs/ai-podcast/ products/
git commit -m "chore: ai-podcast 从实验层移到产品层"
```
> 记得同步更新本文件的目录结构与项目清单表格。

### 4. 把子项目拆成独立 repo（完全可逆）

```bash
# 把 skills/video-gen 完整拆成独立分支，保留所有历史
git subtree split --prefix=skills/video-gen --branch=video-gen-split

# 推到新的独立 GitHub repo
git push git@github.com:gonshell/video-gen.git video-gen-split:main
```

### 5. 查看某个子项目的完整历史

```bash
git log --oneline skills/reading-suite/
```

### 6. commit 规范

```
格式：{type}({项目名}): {内容}

type：feat 新功能 | fix 修复 | docs 文档 | chore 构建/工具/配置 | refactor 重构 | test 测试

示例：
feat(reading): 新增批量提取卡片功能
fix(qwen): 修复流式输出卡顿问题
docs(kino): 更新产品需求文档
chore(craftpulse): 归档研究成果
```

### 7. tag 规范

格式 `{项目名}-v{版本号}`，例：`reading-v2.1.0`、`kino-v0.1.0`、`autoloop-v0.2.0`。
**同名重发是事故**——改内容必须递增版本号，不要用同名 tag 覆盖。

---

## ❓ 常见问题

**Q：跨项目引用代码怎么办？**
A：不要用相对路径直接引用其他子项目的代码，用 npm 依赖、MCP 协议、API 调用等松耦合方式，保证随时可以拆出去。

**Q：每个子项目需要自己的 .gitignore 吗？**
A：可以有，根目录和子项目自己的 `.gitignore` 同时生效，和独立 repo 一样。

**Q：多个子项目共用的依赖怎么办？**
A：每个子项目自己管理依赖，不要在根目录装统一依赖，避免版本冲突，以后拆出去也不用改。

**Q：以后想拆回去会不会很麻烦？**
A：不会，一条 `git subtree split` 就能完整拆出，commit 历史全保留。

**Q：会不会出现 tag 冲突？**
A：只要遵守「tag 必须加项目前缀」，就永远不会冲突。

---

## 📋 迁移说明

原各独立仓库已完整迁入并保留 commit 历史，原仓库已删除。后续所有更新均在此仓库进行。

本仓库为私有仓库，仅本人可见。
