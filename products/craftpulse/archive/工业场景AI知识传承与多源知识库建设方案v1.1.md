# 工业场景AI知识传承与多源知识库建设方案

## ——基于Skills驱动架构的工业智能知识体系统一实施指南（完整版）——


## 第一部分：方案总览

### 1.1 项目背景与四大核心目标

本方案旨在系统性地解决工业企业知识管理面临的四大核心挑战：

| 序号 | 核心目标 | 具体问题描述 |
|:---:|:---|:---|
| **目标一** | **老专家隐性知识显性化** | 老师傅头脑中的实操经验、故障直觉、判断逻辑长期碎片化存在，面临技术传承断代风险，须系统化沉淀为可复用知识 |
| **目标二** | **多源文本知识整合** | 企业拥有专业技术参考书、国家标准/行业规范、内部规章制度、历史案例报告等大量文本，分散在不同介质，无法统一检索和智能调用 |
| **目标三** | **统一格式标准化输出** | 所有知识产出物须统一为Markdown格式，附带标准化的元数据标注，同时满足人工审阅归档与机器自动解析的双重需求 |
| **目标四** | **多平台智能化消费** | 知识库须能够直接对接大模型RAG检索增强生成、GraphRAG图关系推理、Obsidian知识可视化、Dify智能应用编排等主流AI平台 |

### 1.2 设计理念

本方案借鉴 [mattpocock/skills](https://github.com/mattpocock/skills/tree/main) 项目架构哲学，将知识全生命周期的每个环节封装为 **AI Agent可加载执行的标准化技能（Skill）**，每个技能通过唯一的 `SKILL.md` 文件定义其行为：

- **小而专、可组合**：每个技能只做一件事，技能之间通过标准化的输入/输出衔接，可灵活编排
- **Prompt驱动，非代码**：技能的核心是结构化指令集，通过精准的Prompt约束和引导AI行为，而非编写传统软件代码
- **状态无关、上下文在文件中**：所有配置、术语表、待办事项等状态信息全部记录在项目目录的Markdown文件中，不依赖外部数据库
- **人机共享统一语言**：通过 `CONTEXT.md` 定义项目专属术语和Schema，确保人与AI对同一概念的理解完全一致

### 1.3 工业AI平台选型说明

本方案选择 **Dify** 作为核心AI应用编排平台，原因如下：

| 对比维度 | **Dify（本方案选择）** | **OpenClaw** | **Hermes Agent** | **WorkBuddy** |
|:---|:---|:---|:---|:---|
| **核心定位** | AI应用开发平台 / LLMOps | 个人AI助手 / 系统级"数字员工" | 自进化AI代理 | 全场景AI智能体工作台 |
| **核心能力** | 编排、集成、管理；可视化工作流、RAG知识库、API交付 | 执行、操作；直接运行Shell命令、操作本地文件 | 学习、记忆；跨会话持久记忆 | 办公、协作；腾讯生态集成 |
| **与本方案匹配度** | **高度匹配**：完美承接知识库导入、工具注册、Agent编排 | 辅助角色：可作为Dify的"执行手脚" | 补充角色：可增强长期记忆能力 | 无关：不涉及工业知识管理 |

**选择Dify的三大核心理由**：
1. **能力完美匹配**：RAG知识库可承载 `knowledge/` 目录的Markdown文档；可视化工作流可编排"检索→计算→回答"全链路；工具集成可注册专家公式为精确计算工具
2. **架构完美契合**：方案产出的 `knowledge/`、`publish/tools/`、`skills/` 三类文件均可直接对接Dify的对应模块
3. **开放可扩展**：Dify产出的API服务可被OpenClaw等工具调用，形成"大脑+Dify+手脚+OpenClaw"的协同体系

### 1.4 核心创新：知识分类承载策略

不同类型知识须采用不同的承载形式，遵循 **"最适合的容器装最适合的内容"** 原则：

| 知识类型 | 核心特征 | 最适合的承载形式 | 在本方案中的载体 | 在Dify中的消费方式 |
|:---|:---|:---|:---|:---|
| **原理/现象/案例** | 语义密集型，依赖上下文理解 | **向量知识库（RAG）** | `knowledge/**/*.md` 正文区 | 上传至Dify知识库，做Embedding |
| **实体关系/因果链** | 关系密集型，需多跳推理 | **图知识库（GraphRAG/Neo4j）** | `knowledge/**/*.md` 内嵌的 ````json` 实体关系块 | 导入Neo4j，通过Dify图谱插件查询 |
| **经验公式** | 数值计算敏感，严禁幻觉 | **可执行工具（API/Code Interpreter）** | `publish/tools/*.py` | 注册为Dify自定义工具（OpenAPI） |
| **参数表格** | 精确匹配、区间查找，不容模糊 | **轻量化映射表（JSON/SQLite）** | `publish/tables/*.json` | 注册为Dify精确查询工具 |
| **动态操作/决策流** | 多步骤、分支逻辑、依赖状态 | **技能（Skills/SKILL.md）** | `skills/industry/*/SKILL.md` | 复制为Dify系统提示词（System Prompt） |
| **实时/时序数据** | 时效性强、速率计算 | **时序数据库（API连接器）** | Dify工作流中的MES/SCADA连接器 | 配置为Dify HTTP请求节点 |
| **硬性安全红线** | 确定性布尔逻辑，不可推理 | **规则引擎（Rule Engine/DMN）** | `knowledge/regulations/` 导出决策表 | 前置过滤节点，优先于RAG执行 |


## 第二部分：整体架构（7+1个核心技能）

### 2.1 技能全景图

```
┌───────────────────────────────────────────────────────────────────────────────────┐
│                        工业知识全生命周期（7+1个核心技能）                          │
├───────────────────────────────────────────────────────────────────────────────────┤
│                                                                                   │
│  ┌──────────────────────────────────────────────────────────────────────────┐    │
│  │  Skill 1 ：知识库初始化（setup-industry-kb）                              │    │
│  │  定位：配置层 · 必须先执行，无任何依赖                                    │    │
│  │  产出：CONTEXT.md + 目录骨架 + 配置文件                                   │    │
│  └──────────────────────────────┬───────────────────────────────────────────┘    │
│                                 │                                                 │
│                                 ▼                                                 │
│  ┌──────────────────────────────┴───────────────────────────────────────────┐    │
│  │                    知识捕获层（三个技能可并行执行）                         │    │
│  ├──────────────────────┬─────────────────────┬─────────────────────────────┤    │
│  │  Skill 2             │  Skill 3            │  Skill 4                    │    │
│  │  专业技术书捕获       │  专家隐性经验捕获     │  规章制度/标准转化          │    │
│  │  ingest-book         │  capture-expertise  │  to-spec                    │    │
│  │  产出：书籍结构化知识  │  产出：经验结构化知识 │  产出：规程结构化知识        │    │
│  └──────────┬───────────┴──────────┬──────────┴──────────┬──────────────────┘    │
│             │                      │                     │                       │
│             └──────────────────────┼─────────────────────┘                       │
│                                    ▼                                             │
│  ┌─────────────────────────────────┴─────────────────────────────────────────┐   │
│  │  Skill 5 ：知识融合与冲突消解（fuse-knowledge）                             │   │
│  │  定位：融合层 · 依赖Skill 2/3/4全部完成                                    │   │
│  │  产出：企业工业知识主库（融合去重后的唯一化条目）                            │   │
│  └─────────────────────────────────┬─────────────────────────────────────────┘   │
│                                    ▼                                             │
│  ┌─────────────────────────────────┴─────────────────────────────────────────┐   │
│  │  Skill 6 ：知识服务发布与平台对接（publish-to-platform）                    │   │
│  │  定位：服务层 · 依赖Skill 5完成                                            │   │
│  │  产出：Dify导入包 + Neo4j脚本 + 工具注册配置 + 发布包                      │   │
│  └─────────────────────────────────┬─────────────────────────────────────────┘   │
│                                    ▼                                             │
│  ┌─────────────────────────────────┴─────────────────────────────────────────┐   │
│  │  Skill 7 ：知识纠错与反馈闭环（feedback-correction）                        │   │
│  │  定位：治理层 · 持续运行，随时可触发                                       │   │
│  │  产出：更新后的知识版本 + 治理日志 + 变更通知                               │   │
│  └───────────────────────────────────────────────────────────────────────────┘   │
│                                                                                   │
└───────────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 技能依赖关系与执行顺序

```
【强制执行顺序】

第一步（唯一入口）：
  ┌─────────────────────────────────────────────────────────────────────┐
  │  /setup-industry-kb                                                │
  │  产出：CONTEXT.md、目录骨架、标签体系                               │
  │  ⬇ 必须最先执行，无任何依赖                                        │
  └─────────────────────────────────────────────────────────────────────┘
                              ⬇
第二步（三类并行，顺序无关）：
  ┌───────────────────┐  ┌───────────────────┐  ┌───────────────────┐
  │ /ingest-book      │  │ /capture-expertise│  │ /to-spec          │
  │ 处理专业技术书      │  │ 处理专家经验       │  │ 处理规章制度       │
  │ ⬇                 │  │ ⬇                 │  │ ⬇                 │
  │ knowledge/books/  │  │ knowledge/experts/│  │ knowledge/regs/   │
  └───────────────────┘  └───────────────────┘  └───────────────────┘
                              ⬇
            【三者全部完成后，方可进入下一步】
                              ⬇
第三步（依赖前序全部完成）：
  ┌─────────────────────────────────────────────────────────────────────┐
  │  /fuse-knowledge                                                   │
  │  动作：多源知识对齐 → 冲突标定 → 人工裁决 → 融合产出               │
  │  产出：master/ 目录下的融合主库条目                                │
  └─────────────────────────────────────────────────────────────────────┘
                              ⬇
第四步（依赖融合完成）：
  ┌─────────────────────────────────────────────────────────────────────┐
  │  /publish-to-platform                                              │
  │  动作：生成Dify导入包 → Neo4j脚本 → 工具注册配置 → 发布包          │
  │  产出：publish/ 目录下的平台发布包                                 │
  └─────────────────────────────────────────────────────────────────────┘
                              ⬇
第五步（持续运营，随时触发）：
  ┌─────────────────────────────────────────────────────────────────────┐
  │  /feedback-correction                                              │
  │  动作：接收纠错 → 评估有效性 → 版本更新 → 自动提交Git → 触发CI/CD  │
  │  产出：更新后的知识版本 + governance/ 治理日志 + 自动同步至Dify     │
  └─────────────────────────────────────────────────────────────────────┘
```


## 第三部分：统一规范体系（所有技能必须遵守的刚性标准）

### 3.1 知识文件元数据强制Schema

每个知识条目 `.md` 文件的YAML Frontmatter必须包含以下 **11个核心字段**，缺一不可：

```yaml
---
# ========== 必填：唯一标识与来源 ==========
knowledge_id: "KB-20260128-001"         # 全局唯一ID，格式：KB-YYYYMMDD-序号
source_type: "expert"                  # 枚举：book | expert | regulation | case | fused
title: "离心机振动异常处理经验"         # 知识标题
author: "张工"                          # 作者/来源人

# ========== 必填：适用范围与标签 ==========
equipment_scope:                       # 适用设备清单（至少1个）
  - "MCO-101"
knowledge_tags:                        # 关键词标签（至少3个）
  - "振动"
  - "油温"
  - "频谱分析"

# ========== 必填：版本与生命周期 ==========
version: "v1.0"                        # 语义化版本号
status: "active"                       # 枚举：draft | active | superseded | deprecated
effective_date: "2026-01-28"
expiry_date: "2027-01-28"              # 专家经验默认1年，规程默认3年

# ========== 必填：置信度与溯源 ==========
confidence_score: 0.95                 # 0-1区间，计算规则见第3.2节
source_references:                     # 溯源引用（至少1个）
  - "张工访谈记录_20260128"

# ========== 必填：治理追踪 ==========
last_reviewed: "2026-01-28"
change_log: "初版创建"

# ========== 可选：公式标记（专家经验公式专用） ==========
has_executable_formula: true           # 当包含可执行公式时，此字段必须为true
formula_tool_name: "calculate_correction_factor"  # 工具名称，供Skill 6自动注册
---
```

### 3.2 置信度（confidence_score）计算规则

| 知识来源类型 | 基础分 | 修正项（累加） | 封顶值 |
|:---|:---:|:---|:---:|
| **专家经验** | 0.70 | ① 经另一位专家交叉验证 → +0.15<br>② 有运行数据佐证 → +0.10<br>③ 与历史案例一致 → +0.05 | 0.98 |
| **专业书/标准** | 0.85 | ① 为最新版本 → +0.10<br>② 已在本厂实际应用验证 → +0.05 | 0.99 |
| **规章制度** | 0.80 | ① 为最新发布版本 → +0.10<br>② 有合规部门审批 → +0.05 | 0.98 |
| **融合知识** | 0.75 | ① 多源完全一致 → +0.20<br>② 有冲突但已裁决 → +0.10<br>③ 经总工审批 → +0.05 | 0.98 |

### 3.3 GraphRAG实体与关系枚举（Schema强制约束）

所有知识文件内嵌的 ````json` 代码块必须严格遵循以下枚举：

**实体类型（Entity Types）**：
```
Equipment | Component | Parameter | Material | Procedure | Fault | Personnel
```

**关系类型（Relation Types）**：
```
causes | solves | indicates | requires | has_parameter | located_in | applies_to | supersedes
```

**正确示例**：
```json
{
  "entities": [
    {"id": "MCO-101", "type": "Equipment", "name": "离心压缩机"},
    {"id": "VIB-01", "type": "Parameter", "name": "轴振动振幅"}
  ],
  "relations": [
    {"head": "MCO-101", "relation": "has_parameter", "tail": "VIB-01"},
    {"head": "高振幅", "relation": "causes", "tail": "轴承损坏"}
  ]
}
```

### 3.4 目录结构与版本分仓规范

```
industrial-kb/                                 # 知识库根目录
│
├── _index.md                                  # 执行顺序依赖图（供用户查阅）
├── CONTEXT.md                                 # 术语表 + GraphRAG Schema + 置信度规则
├── .github/workflows/                         # CI/CD自动化流水线
│   └── sync_to_dify.yml                       # 自动同步至Dify
│
├── docs/agents/
│   ├── issue-tracker.md                       # 待办事项与反馈清单
│   └── labels.md                              # 标签分类体系
│
├── skills/industry/                           # 【核心】技能定义目录
│   ├── setup-industry-kb/SKILL.md             # 技能1：初始化
│   ├── ingest-technical-book/SKILL.md         # 技能2：专业书捕获
│   ├── capture-expertise/SKILL.md             # 技能3：专家经验捕获
│   ├── to-spec/SKILL.md                       # 技能4：规章转化
│   ├── fuse-knowledge/SKILL.md                # 技能5：融合
│   ├── publish-to-platform/SKILL.md           # 技能6：发布
│   └── feedback-correction/SKILL.md           # 技能7：纠错闭环
│
├── knowledge/                                 # 【核心】知识资产
│   ├── books/[书名]/v1.0/提取结果.md
│   ├── experts/[专家名]/v1.0/[主题]_经验.md
│   └── regulations/[规程名]/v3.0/结构化.md
│
├── master/                                    # 【核心】融合主库
│   └── [设备]_[主题]_融合知识.md
│
├── governance/
│   ├── 版本变更日志.md
│   └── 过期知识清理清单.md
│
└── publish/                                   # 平台发布包
    ├── dify_import.jsonl                      # Dify批量导入格式
    ├── neo4j_import.cypher                    # Neo4j Cypher脚本
    ├── openapi.yaml                           # Dify工具注册（OpenAPI规范）
    ├── tools/                                 # 可执行工具（公式函数）
    │   └── [tool_name].py
    ├── tables/                                # 精确映射表（JSON）
    │   └── [table_name].json
    └── obsidian_config/
```


## 第四部分：各技能详细定义与完整执行路径

### 技能1：知识库初始化（`/setup-industry-kb`）

**定位**：企业首次部署知识库时的启动技能。**必须先执行，无任何依赖。**

#### SKILL.md 核心指令

```markdown
---
name: setup-industry-kb
description: 初始化工业知识库的目录结构、术语表、标签体系和全局配置
---

# 触发条件
当用户说以下任一指令时激活：
- "/setup-industry-kb"
- "初始化知识库"

# 执行流程

## Step 1: 检查环境
- 检查当前目录是否存在 CONTEXT.md
- 若存在，提示："知识库已初始化。如需重新配置，请指定 --force 参数"

## Step 2: 向用户收集配置信息（清单式提问，依次进行）
Q1：请列出本企业涉及的核心设备类型（逗号分隔）
Q2：请列出常用的故障分类（逗号分隔）
Q3：请指定知识库存放的本地目录路径
Q4：是否同步至Git仓库？若是，请提供仓库地址

## Step 3: 生成配置文件
- CONTEXT.md：术语表 + GraphRAG Schema + 置信度规则
- docs/agents/issue-tracker.md：待办跟踪
- docs/agents/labels.md：标签体系
- 按第3.4节创建完整目录骨架

## Step 4: 生成 _index.md
写入技能依赖关系图（见第2.2节）

## Step 5: 汇报
"✅ 知识库初始化完成！请按 _index.md 中的依赖顺序开始执行。"
```


### 技能2：专业技术参考书知识捕获（`/ingest-technical-book`）

**定位**：处理PDF/Word格式的专业技术参考书，提取理论公式、设计参数、原理说明。**与技能3、4可并行执行。**

#### SKILL.md 核心指令

```markdown
---
name: ingest-technical-book
description: 从专业技术参考书中提取理论知识、公式、设计参数
---

# 触发条件
当用户说 "/ingest-technical-book --file=<文件路径>"

# 前置依赖
必须已完成 /setup-industry-kb

# 执行流程

## Step 1: 验证输入
- 检查文件是否存在，支持 .pdf、.docx、.txt

## Step 2: PDF预处理
- 使用 pypdf 检测是否含文本层
- 若无文本层（扫描版），提示用户选择：A)提供电子版 B)使用OCR C)手动录入

## Step 3: 扫描目录并提问
- 读取目录，让用户选择与本企业设备直接相关的章节

## Step 4: 逐章深度提取（核心）
对选中的每一章执行：
### 4.1 理论公式提取
- 识别数学公式 → LaTeX 格式（```math）
- **额外产出**：生成对应的Python函数代码（```python），标记 has_executable_formula: true

### 4.2 设计阈值参数提取
- 识别数值型参数 → 存入 YAML：参数名、最小值、最大值、单位、适用条件

### 4.3 原理说明提取
- 保留核心论述（100-300字）作为"人工解读"正文，标注原文页码

### 4.4 图表处理
- 记录图号、标题、描述；扫描版标记 image_reference

### 4.5 生成差异对照表
- "理论 vs 本厂实际"差异清单

## Step 5: 产出
路径：knowledge/books/[书名]/v1.0/提取结果.md

## Step 6: 汇报
"提取完成：X条参数、Y条公式、Z条原理。待办：复核图X-X标注。"
```


### 技能3：专家隐性知识捕获（`/capture-expertise`）

**定位**：通过结构化访谈捕获专家隐性经验。**与技能2、4可并行执行。**

#### SKILL.md 核心指令

```markdown
---
name: capture-expertise
description: 通过结构化访谈捕获专家隐性经验
---

# 触发条件
当用户说 "/capture-expertise --expert=<姓名> --topic=<主题>"

# 前置依赖
必须已完成 /setup-industry-kb

# 执行流程

## Step 1: 加载上下文
- 读取 CONTEXT.md 获取统一术语表
- 读取 docs/agents/labels.md 获取标签体系

## Step 2: 确认访谈范围
"即将访谈 [专家名]，主题为 [主题]。预计30-45分钟。"

## Step 3: 结构化访谈（严格按以下清单推进）

**第一轮：场景还原**
- Q1："请回想最近一次印象深刻的 [主题] 事件，当时设备参数是多少？"
- Q2："您最先注意到的异常信号是什么？"

**第二轮：诊断推理**
- Q3："您的第一个判断是什么？为什么？"
- Q4："您采取的第一步操作是什么？为什么？"
- Q5："如果情况A发生怎么办？如果情况B呢？"（穷尽分支）

**第三轮：边界条件**
- Q6："什么情况下会改变判断？"
- Q7："这个经验有没有例外？"

**第四轮：量化确认**
- Q8："请给出关键的数值阈值"

**4.5 经验公式提取与工具化（专家口头公式专项处理）**

当专家提到类似"根据经验，我一般按这个公式来估算……"时，执行：

1. **记录原始口语**：原样保留专家说的公式
2. **标准化数学表达**：翻译为 LaTeX 数学公式（供人类审阅）
3. **定义输入/输出变量**：逐一向专家确认变量含义、单位、取值范围
4. **生成可执行代码**：转化为 Python 函数，存入 ```python 代码块
5. **标记元数据**：在YAML中增加 has_executable_formula: true

**示例**：
专家口语："修正系数 K = 1.2 乘以实际流量除以设计流量的0.3次方"

标准化输出：
```math
K_{corr} = 1.2 \times (Q_{actual} / Q_{design})^{0.3}
```

```python
def calculate_correction_factor(q_actual: float, q_design: float) -> float:
    """张工经验公式：轴承寿命修正系数。约束：q_actual >= 0.7 * q_design"""
    if q_actual < 0.7 * q_design:
        raise ValueError("实际流量低于设计值70%，此公式不适用")
    return round(1.2 * (q_actual / q_design) ** 0.3, 4)
```

## Step 4: 结构化整理（AI内部）
- 口语转化为"条件→判断→行动"逻辑链
- 提取关键参数阈值
- 生成Mermaid决策树草稿
- 标注风险等级

## Step 5: 回读确认（关键质量控制闸门）
向专家复述总结，专家确认或修正，循环直至准确

## Step 6: 产出
路径：knowledge/experts/[专家名]/v1.0/[主题]_经验.md

## Step 7: 提交融合待办
在 issue-tracker.md 记录冲突检测待办
```


### 技能4：规章制度/标准文档转化（`/to-spec`）

**定位**：将规章制度、操作规程、国家标准转化为结构化知识。**与技能2、3可并行执行。**

#### SKILL.md 核心指令

```markdown
---
name: to-spec
description: 将规章制度/标准文档转化为结构化规范知识
---

# 触发条件
当用户说 "/to-spec --file=<文件路径>"

# 前置依赖
必须已完成 /setup-industry-kb

# 执行流程

## Step 1: 验证输入
- 检查文件是否存在，支持 .docx、.txt、.pdf

## Step 2: 解析文档结构
- 提取章节、条款编号
- 识别强制关键词："必须"、"禁止"、"不得" → is_mandatory: true
- 识别建议关键词："宜"、"可"、"建议" → is_mandatory: false

## Step 3: 结构化拆解
- 每一条"规定"抽取为独立条目
- 提取定量指标（数值+单位）→ 存入YAML
- 提取执行条件 → 存入YAML的condition字段

## Step 4: 参数表格的特殊处理
若文档含参数表格：
- 保留Markdown表格（给人看）
- 额外生成 ```json 映射数组（供精确查询工具使用）
- 标注查询逻辑类型：exact_match 或 range_lookup

## Step 5: 冲突检测
- 搜索 master/ 目录中相同设备/主题的已有条目
- 若冲突，向用户汇报并请求裁决

## Step 6: 产出
路径：knowledge/regulations/[规程名]/[版本号]/结构化.md

## Step 7: 更新治理台账
在 governance/版本变更日志.md 追加记录
```


### 技能5：知识融合与冲突消解（`/fuse-knowledge`）

**定位**：将技能2/3/4产出的三类知识进行对齐、融合。**依赖技能2/3/4全部完成。**

#### SKILL.md 核心指令

```markdown
---
name: fuse-knowledge
description: 多源知识对齐、冲突消解、融合去重
---

# 触发条件
当用户说 "/fuse-knowledge --topic=<主题>"

# 前置依赖
knowledge/books/、knowledge/experts/、knowledge/regulations/ 均有内容

# 执行流程

## Step 1: 召回所有相关条目
- 扫描 knowledge/ 下所有目录，匹配 --topic

## Step 2: 对比分析
对每个知识点，对比三类来源：专业书 vs 专家经验 vs 规章制度

## Step 3: 标定冲突
- 完全一致 → 直接融合，取最高置信度
- 互补（适用场景不同）→ 标记"互补融合"
- 直接矛盾 → 标记"待裁决"，提交人工审批

## Step 4: 生成融合草案
- 在 issue-tracker.md 创建待办（如有冲突需裁决）

## Step 5: 人工审批后产出
路径：master/[设备]_[主题]_融合知识.md
```


### 技能6：知识服务发布与平台对接（`/publish-to-platform`）

**定位**：将融合主库知识打包发布到Dify、Obsidian、Neo4j。**依赖技能5完成。**

#### SKILL.md 核心指令

```markdown
---
name: publish-to-platform
description: 将知识库发布到 Dify RAG / Obsidian / Neo4j GraphRAG
---

# 触发条件
当用户说 "/publish-to-platform --targets=dify,neo4j"

# 前置依赖
master/ 目录中有 status: approved 的融合知识

# 执行流程

## Step 1: 检查就绪状态
- 扫描 master/ 目录，确认所有条目 status 为 approved

## Step 2: 生成Dify导入包
- 抽取YAML元数据作为 Metadata
- 正文作为 chunk 内容
- 生成 dify_import.jsonl

## Step 3: 生成Obsidian优化
- 确保所有 [[双链]] 正确

## Step 4: 生成Neo4j导入脚本
- 遍历所有JSON实体与关系，生成 Cypher 脚本

## Step 5: 全量工具注册（含专家公式）
- **扫描范围**：knowledge/books/**/*.md 和 knowledge/experts/**/*.md
- **筛选条件**：YAML中 has_executable_formula: true
- **抽取内容**：其中的 ```python 函数块
- **生成输出**：publish/openapi.yaml + publish/tools/*.py

## Step 6: 表格映射注册
- 扫描 knowledge/regulations/ 中的 ```json 映射数组
- 生成 publish/tables/*.json

## Step 7: 产出发布包
放置于 publish/ 目录，附 README 使用说明
```


### 技能7：知识纠错与反馈闭环（`/feedback-correction`）

**定位**：处理知识纠错反馈，触发知识更新与版本迭代，**自动触发CI/CD同步**。**持续运行，随时可触发。**

#### SKILL.md 核心指令

```markdown
---
name: feedback-correction
description: 处理知识纠错反馈，触发知识更新与版本迭代
---

# 触发条件
当用户说 "/feedback-correction --source=<来源> --claim=<纠错内容>"

# 执行流程

## Step 1: 定位原始知识
- 根据 knowledge_id 在 knowledge/ 中检索对应文件

## Step 2: 评估反馈有效性
- 如有MES/运行数据接入，自动比对验证
- 如需人工判断，在 issue-tracker.md 创建待办

## Step 3: 触发知识更新
- 原条目标记 status: superseded
- 生成新版本文件（版本号递增）
- 更新融合主库对应条目
- 在 governance/版本变更日志.md 追加记录

## Step 4: 自动提交Git（关键步骤）
- 执行 git add .
- 执行 git commit -m "纠错更新：[知识ID] 版本升级"
- 执行 git push

## Step 5: 通知相关方
- "✅ 知识已更新，已推送到Git仓库。CI/CD将自动同步至Dify。"
```


## 第五部分：知识库产出物的实际使用（专家智能体构造指南）

### 5.1 专家智能体的三个文件来源

生成一个"专家智能体"，例如"张工（离心机振动专家）"，需要且仅需要从知识库中提取以下 **3类具体文件**：

| 文件来源 | 具体文件名（示例） | 它是什么？ | 在智能体中充当的角色 |
|:---|:---|:---|:---|
| **`skills/` 目录** | `skills/industry/diagnose-expert/SKILL.md` | 行为规则书（纯文本Prompt） | **"大脑皮层/性格"**：规定智能体必须按什么流程思考、先查什么后查什么、禁止做什么 |
| **`knowledge/` 目录** | `knowledge/experts/张工/v1.0/振动经验.md`（含所有子条目） | 静态知识语料（Markdown文本） | **"长期记忆"**：存入向量库，供语义检索 |
| **`publish/tools/` 目录** | `publish/tools/zhanggong_correction.py` + `publish/openapi.yaml` | 可执行脚本 + 接口描述 | **"手脚/计算器"**：当需要代入公式算数时，智能体调用这个工具 |

> **注意**：`publish/neo4j_import.cypher` 不是智能体的直接文件，但如果您做图谱增强，需要先在Neo4j中跑通它，再把Neo4j的查询接口挂载到智能体上。

### 5.2 在Dify中构造专家智能体（三步配置）

| 步骤 | 操作内容 | 具体做法 |
|:---|:---|:---|
| **第1步：装填"大脑"** | 将 `SKILL.md` 的内容复制为系统提示词 | 打开Dify应用编排 → 系统提示词输入框 → 复制 `SKILL.md` 中的"执行流程"和"约束条件"全部内容 |
| **第2步：装填"长期记忆"** | 将 `knowledge/` 下的 `.md` 文件上传至知识库 | Dify左侧"知识库" → 创建"张工经验库" → 上传 `knowledge/experts/张工/` 下所有 `.md` 文件 → 分段规则选"自定义"，标识符设为 `---` |
| **第3步：装填"计算器"** | 将 `publish/tools/*.py` 注册为工具 | Dify左侧"工具" → 创建自定义工具 → 选择"OpenAPI/Swagger"导入 → 上传 `publish/openapi.yaml` |

### 5.3 专家智能体的使用场景（一线操作员视角）

**场景**：操作员小王在Dify对话界面提问：

> "张工，MCO-102今天振动到50μm了，负荷90%，我该怎么办？"

**智能体内部运作流程（毫秒级）**：

| 步骤 | 动作 | 数据来源 | 说明 |
|:---|:---|:---|:---|
| ① | 激活"大脑" | `SKILL.md`（系统提示词） | 强制智能体先反问"油温和进气温度多少？"，而不是直接给答案 |
| ② | 等待用户回复 | 用户回复"油温55℃" | 满足条件后继续推理 |
| ③ | 召回"长期记忆" | `knowledge/` 向量库 | 命中张工原话："油温超50℃且振动飙升，优先开启备用冷却器降温，别急着停机" |
| ④ | 调用"计算器" | `publish/tools/*.py` | 用户追问"降温后负荷能提上去吗？"，智能体自动调用公式计算最大安全负荷系数 |
| ⑤ | 组织最终回答 | 综合①②③④ | "张工建议优先开备用冷却器降油温。根据经验公式，建议最高负荷不超过92%，待油温回落到45℃再缓慢加负荷。" |


## 第六部分：自动化升级与CI/CD流水线

### 6.1 自动化升级触发机制

"张工智能体"的更新完全自动化，无需人工进入Dify界面操作：

| 触发事件 | 具体场景 | 后续动作 |
|:---|:---|:---|
| **事件A：常规更新** | 工程师对 `knowledge/experts/张工/` 中的案例做了修订，合并了Pull Request | CI/CD自动触发同步 |
| **事件B：纠错闭环** | 操作工发现AI引用错误，发送 `/feedback-correction` 指令 | Skill 7自动修改文件 → 自动Git Push → CI/CD触发同步 |

> **核心逻辑**：只要 `industrial-kb` 仓库的 `main` 分支发生变更，自动化流水线自动将最新的"知识"和"规则"同步给运行中的Dify智能体。

### 6.2 CI/CD流水线配置

在仓库根目录创建 `.github/workflows/sync_to_dify.yml`：

```yaml
name: 自动同步张工智能体到Dify

on:
  push:
    branches: [ main ]  # 主分支更新即触发

jobs:
  update-agent:
    runs-on: ubuntu-latest
    steps:
      - name: 拉取最新知识库
        uses: actions/checkout@v3

      - name: 安装依赖
        run: pip install requests PyYAML

      - name: 执行自动化同步
        env:
          DIFY_API_KEY: ${{ secrets.DIFY_API_KEY }}
          DIFY_APP_ID: ${{ secrets.DIFY_APP_ID }}
          DIFY_DATASET_ID: ${{ secrets.DIFY_DATASET_ID }}
        run: python scripts/sync_dify_production.py
```

### 6.3 同步脚本 `sync_dify_production.py` 的核心逻辑

| 步骤 | 脚本操作（对应产出物） | 调用的Dify API | 智能体的变化 |
|:---|:---|:---|:---|
| **① 刷新行为规则** | 读取 `skills/**/SKILL.md` 的流程指令文本 | `POST /v1/apps/{app_id}/workflows/update` | 智能体自动遵守新的推理规则 |
| **② 刷新向量知识库** | 扫描 `knowledge/` 下新增/修改的 `.md` 文件 | `DELETE` 旧文档 + `POST` 新文档上传 | 新知识被向量化，成为可检索记忆 |
| **③ 刷新计算工具** | 扫描 `publish/tools/*.py` 是否有变动 | `POST /v1/tools/api-providers` 更新OpenAPI | 公式逻辑自动更新，下次调用即最新版本 |

### 6.4 灰度发布（安全机制）

脚本不会直接覆盖生产环境智能体，而是先创建 **"张工智能体-测试版"** ：

1. 用新知识跑自动化测试用例（问已知答案的问题）
2. 测试通过率 > 95% 后
3. 通过API将测试版的工作流一键发布至正式版

**实现效果**：升级过程用户无感知，智能体始终在线可用。


## 第七部分：实施路线图（MVP快速验证）

| 阶段 | 时间 | 核心任务 | 验收标准 |
|:---|:---:|:---|:---|
| **Phase 1：单机试点** | 第1周 | ① `/setup-industry-kb` 初始化<br>② 选取1台核心设备，访谈1位专家，产出2-3份经验知识<br>③ 存入Obsidian验证可视化 | Obsidian Dataview正确显示标签和双链；专家确认内容准确 |
| **Phase 2：三源并行** | 第2周 | ① 选1本技术书执行 `/ingest-book`<br>② 选1份规程执行 `/to-spec`<br>③ 执行 `/fuse-knowledge` 融合 | 融合主库含三源知识；冲突已裁决 |
| **Phase 3：平台对接** | 第3周 | ① 执行 `/publish-to-platform`<br>② 在Dify中配置智能体（复制SKILL.md + 上传知识库 + 注册工具）<br>③ 导入Neo4j验证图关系 | Dify能区分"专家建议"与"标准规定"；Neo4j展示关系路径 |
| **Phase 4：CI/CD自动化** | 第4周 | ① 配置GitHub Actions流水线<br>② 测试纠错闭环 `/feedback-correction`<br>③ 验证自动同步 | 修改知识文件后，Dify智能体自动更新；灰度发布机制有效 |
| **Phase 5：全量推广** | 第5周起 | 批量处理全部设备/规程/专家 | 全厂覆盖；命中率>80% |


## 第八部分：CI/CD持续集成保障

在Git仓库配置Pre-commit Hook，自动化校验：

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: validate-yaml-frontmatter
        name: 校验YAML元数据完整性
        entry: python scripts/validate_metadata.py
        language: python
        files: \.md$
      - id: validate-json-entities
        name: 校验JSON实体关系枚举
        entry: python scripts/validate_entities.py
        language: python
        files: \.md$
      - id: check-file-size
        name: 检查单文件<50KB
        entry: python scripts/check_size.py
        language: python
        files: \.md$
      - id: validate-formula-tools
        name: 校验公式工具可执行性
        entry: python scripts/validate_formula.py
        language: python
        files: \.md$
```

**校验规则**：
1. 每个 `.md` 文件必须包含完整的11个YAML字段
2. ````json` 代码块中的实体/关系必须在第3.3节枚举范围内
3. 单文件大小 ≤ 50KB（违规提示拆分）
4. 标记 `has_executable_formula: true` 的文件必须包含可执行的 ````python` 函数块


## 第九部分：最终知识库资产清单

```
industrial-kb/
│
├── _index.md                                 # 执行顺序依赖图
├── CONTEXT.md                                # 术语表 + Schema + 置信度规则
├── .github/workflows/sync_to_dify.yml        # CI/CD自动同步
│
├── docs/agents/
│   ├── issue-tracker.md                      # 待办与反馈清单
│   └── labels.md                             # 标签体系
│
├── skills/industry/                          # 7个核心技能
│   ├── setup-industry-kb/SKILL.md
│   ├── ingest-technical-book/SKILL.md
│   ├── capture-expertise/SKILL.md
│   ├── to-spec/SKILL.md
│   ├── fuse-knowledge/SKILL.md
│   ├── publish-to-platform/SKILL.md
│   └── feedback-correction/SKILL.md
│
├── knowledge/                                 # 知识资产
│   ├── books/[书名]/v1.0/提取结果.md
│   ├── experts/[姓名]/v1.0/[主题]_经验.md
│   └── regulations/[规程名]/v3.0/结构化.md
│
├── master/                                    # 融合主库
│   └── [设备]_[主题]_融合知识.md
│
├── governance/
│   ├── 版本变更日志.md
│   └── 过期知识清理清单.md
│
└── publish/                                   # 平台发布包
    ├── dify_import.jsonl                     # Dify RAG导入
    ├── neo4j_import.cypher                   # Neo4j图库脚本
    ├── openapi.yaml                          # Dify工具注册
    ├── tools/                                 # 可执行工具
    │   └── [tool_name].py
    ├── tables/                                # 精确映射表
    │   └── [table_name].json
    └── obsidian_config/
```
