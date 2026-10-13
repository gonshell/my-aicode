---
name: deep-research-report
description: 撰写基于原始论文的深度技术报告。多批次检索→一次性撰写→飞书交付。
---

## 触发条件

用户要求："写一份技术报告"、"检索查找...形成技术报告"、"从论文中查找...使其能完全再现"、"撰写之前请深度思考"。

## 核心原则

1. **一次性完成，不中间汇报。** 用户明确要求"一次性写完发给我"——不要问"要不要先看看"或分批发送中间结果。即使撰写时间较长，也一次性交付。
2. **优先检索原始论文**（arXiv、官方技术报告、会议论文、Nature）而非二手解读。
3. **每条结论有来源，可追溯。** 记录论文标题、作者、会议/年份、arXiv编号。

## 工作流

### 阶段一：规划与多批次检索

1. **拆解为独立子主题**，并行检索。
2. **搜索优先级**：
   - 内置 `web_search`（Tavily）——可能未配置API key，会报错
   - 回退：`mcp__qwen_harness__qwen_web_search`（需 tool_search + tool_describe + tool_call 调用链）
   - 补充：`mcp__websearch_searxng__searxng_web_search`
3. **多批次策略**：
   - 第一批：整体方向搜索，覆盖所有子主题，每主题5-8条
   - 第二批：针对第一批发现的空白点补充检索
   - 第三批：抓取核心论文的详细内容（如架构参数、训练超参数表）
   - 每批之间更新 todo 列表，标记已完成和待补充的主题
4. **搜索技巧**：
   - 使用精确英文论文标题搜索原始论文
   - 搜索词包含 "technical report" / "original paper" / "formula" / "hyperparameters" / "architecture parameters"
   - 特定参数搜索：`"model_name" architecture parameters hidden_dim n_layers`
   - 特定论文搜索：`"paper title" author year conference`
5. **URL读取限制**：
   - `mcp__websearch_searxng__web_url_read` 可能被安全策略拦截
   - `mcp__qwen_harness__qwen_web_extract` 要求先执行同次 web_search 调用
   - 当读取不可用时，依赖搜索结果摘要信息已足够撰写报告

### 阶段二：组织与撰写

0. **先给用户过目录再动笔**（2026-09 复盘确认的偏好）："撰写之前请深度思考目录结构" = 想好后先向用户展示目录获确认再写正文；同时 clarify 报告定位口径（技术架构 vs 商业分析、敏感内容尺度、是否补"对己方业务的启示"章）。
1. **先设计目录结构**，统一组织方式。
2. **推荐结构模板**（每项技术/模型逐节展开）：

```
摘要
目录
1. 技术/模型A
   1.1 技术定位 / 解决的问题
   1.2 原始论文出处（标题、作者、会议、年份、引用量）
   1.3 核心原理与公式
   1.4 数据格式 / 参数配置表
   1.5 典型效果（对比表）
2. 技术/模型B
   ...
N. 对比与总结
参考文献（按章节分类）
```

3. 每项技术统一按"出处→问题→原理→公式→数据→效果"展开，便于对比查阅。
4. 使用结构化元素：多级标题 + 对比表格 + 代码块（超参配置/数据格式）+ 列表。
5. 参考文献按章节分类，每篇标注 arXiv / 会议名、年份、引用量（可选）。
6. 保存到本地 Markdown 文件再交付。

### 阶段三：飞书交付

1. 用 `lark-cli docs +create --title "..." --content @./file.md --format pretty` 创建飞书文档。
2. 创建后立即用 `lark-cli drive +member-add --token <doc_id> --type docx --member-type openid --member-id <open_id> --perm full_access --yes` 授权用户。
3. 在回复中给出飞书文档链接。

## 交付形态扩展

用户要求的"md+html 发给我"= 三件套：① 亮色 HTML 发群附件（--file 相对路径）② md 建飞书文档+授权 ③ 交付说明含实测数字。详见 `references/tech-research-report-workflow.md`（检索兜底链、/tmp 缓存复用、验证命令、锚点 slug 陷阱、Lattice×Palantir 案例领域知识）。

## 参考文献格式

对于每篇论文，记录：
- 标题（完整）
- 作者（第一作者 + et al.）
- 发表会议/期刊 + 年份
- arXiv编号（如有）
- 引用量（可选，说明来源可靠性）
- URL