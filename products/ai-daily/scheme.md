# AI 前沿日报 · 完整方案

> 文档版本：v1.0｜更新：2026-08-10
> 来源：飞书会话确认的全部设计决策

---

## 一、整体架构

```
采集层 → 过滤/排序层 → 生成层 → 飞书文档
  4 源      规则引擎      markdown    滚动追加
```

- **无 LLM 环节**（摘要用简单方法：HF 自带 summary / TC meta description / YT 描述截断）
- **无数据库**（状态用状态文件 + 本地 master.md，轻量）
- **单飞书文档滚动追加**（最新在上，文档名固定为"最新国外AI日报"）

---

## 二、四大数据源

| # | 源 | API/方式 | 频率 | 量级 |
|---|---|---|---|---|
| 1 | **YouTube**（15 关注频道） | **YouTube Data API v3**（用户提供 key） | 日 | ~20-30 条/周 |
| 2 | **HuggingFace 论文** | HF Papers API（公开，无 key） | 日 | ~30-50 篇/周 |
| 3 | **HuggingFace 模型** | HF Models API（公开，无 key） | 日 | ~60-80 个/周（过滤后） |
| 4 | **TechCrunch AI** | RSS Feed | 日 | ~20 条/周 |

### 2.1 YouTube 15 关注频道

NVIDIA、OpenAI、Andrej Karpathy、Google DeepMind、Anthropic、AI Explained、3Blue1Brown、Lex Fridman、Y Combinator、Two Minute Papers、Matt Wolfe、Matthew Berman、Yannic Kilcher、Wes Roth、HuggingFace

### 2.2 YouTube Data API 方案

- 调用 `search.list`（按 channelId + 时间范围，type=video）→ 拿视频 ID 列表
- 调 `videos.list`（批量，最多 50 个 ID 一次）→ viewCount / likeCount / duration 全拿
- **配额消耗**：每天 ~50 个视频 = 1 次 search（100 单位） + 1 次 videos.list（1 单位）≈ **101 单位/天**，远低于免费 1 万单位/天限额
- 附带收益：点赞数、时长、评论数、分类标签

---

## 三、过滤与排序规则

### 3.1 YouTube

| 规则 | 内容 |
|---|---|
| 时间窗口 | 近 7 天（周一~周日） |
| AI 过滤 | **NVIDIA 频道**只保留 AI 关键词（词边界：`ai\|gpu\|model\|llm\|agent\|cuda\|dgx\|nim\|robotics\|robot\|training\|compute\|superchip` + deep learning / machine learning / artificial intelligence / data center），其他频道不过滤 |
| 每频道上限 | 最多 3 条 |
| 频道内排序 | **观看数降序**（Data API viewCount） |
| 频道间排序 | 按本周条数降序 → 条数相同按频道内最大观看数降序 |
| 0 条频道 | 统一列在末尾"本周无更新的频道" |

### 3.2 HF 论文

- 时间：本周内
- 排序：upvotes 降序
- 展示：**TOP 5** 带摘要（HF 自带 summary）

### 3.3 HF 模型

- 时间：本周创建
- 过滤：`downloads ≥ 100` 或 `likes ≥ 5`
- 排序：`downloads + likes × 100` 降序
- 展示：**TOP 10**

### 3.4 TechCrunch AI

- 时间：**近 2 日**
- 排序：日期倒序
- 摘要：抓 meta description

---

## 四、输出格式

### 文档结构

```
最新国外AI日报
  ↓（每日新增一级 H1，最新在上）
  ├─ # AI 日报 08-10（xx 条）
  ├─ # AI 日报 08-09（xx 条）
  └─ ...
```

### 每个日期块

```
# AI 日报 MM-DD（N 条）
> 说明（时间窗口 / 排序方式）

## 📺 YouTube 本周（N 条，按观看数排序，每频道最多 3 条）
### 频道名（x 条）
- [标题](url)｜日期｜▶观看数｜摘要（描述截断）
...

**本周无更新的频道（n）**：xxx、xxx、...

## 📄 HF 论文 本周高赞 TOP 5（本周共 N 篇）
- [标题](url)｜日期｜⬆赞数｜摘要

## 🤖 HF 模型 本周 TOP 10（过滤后共 N 个）
- [模型名](url)｜日期｜⬇下载数｜♥赞数｜pipeline

## 📰 TechCrunch AI 近 2 日（N 条）
- [标题](url)｜日期｜摘要（meta desc）
```

---

## 五、部署方案

### 目录结构

```
/root/workspace/ai-daily/
├── collect.py          # 四源采集
├── render.py           # 生成 markdown
├── publish.py          # 同步到飞书
├── config.json         # 配置（key / 频道列表 / 过滤规则）
├── state.json          # 状态（上次采集时间 / 已处理 ID）
├── master.md           # 滚动累积全文
└── data/               # 每日原始数据存档（可选）
```

### 每日 cron

- **时间**：每天 8:00 AM CST
- **流程**：采集 → 渲染（插入到 master.md 顶部）→ 全量同步飞书文档
- **成功**：静默（打开飞书文档可见）
- **失败**：飞书告警

### 飞书文档

- 固定文档 token：`PNU8dyleWoYXlDxmcIbcXSHdn8f`
- 权限：用户已有可编辑
- 更新方式：`lark-cli docs +update` 整体替换

---

## 六、用户需要做的事

**申请 YouTube Data API v3 key**，流程：

1. 打开 Google Cloud Console → 新建项目
2. API Library → 搜索 "YouTube Data API v3" → Enable
3. Credentials → Create Credentials → API key
4. （推荐）给 key 加限制：只允许 YouTube Data API v3

拿到 key 后发给我，我就：
1. 把采集脚本从 HTML 抓取替换为 Data API
2. 把 /tmp 下的零散脚本整理成 `/root/workspace/ai-daily/` 正式项目
3. 建 cron（每天 8:00 自动跑）
4. 先手动跑一次验证效果

---

## 七、待确认决策

| # | 问题 | 建议 |
|---|---|---|
| 1 | NVIDIA 本周 0 AI 条，文案写"无更新"还是"2 条均非 AI 已过滤"？ | 写"2 条非 AI 已过滤"更诚实 |
| 2 | 除了日报，要不要每周一自动生成**周报**（合并上周 7 天去重，给一个总览）？ | 先不上，跑一周日报看效果再定 |

---

## 八、方案演进记录

| 日期 | 决策 |
|---|---|
| 08-08 | 四源初选：YouTube / HF 论文 / HF 模型 / TechCrunch |
| 08-08 | YouTube 15 关注频道确定（从 163 候选中选） |
| 08-09 | 试跑 v1 → v2 → v3，确认排序/条数/摘要格式 |
| 08-09 | 确认单文档滚动追加，文档名"最新国外AI日报" |
| 08-09 | 确认摘要用简单方法（HF summary / meta desc / 描述截断） |
| 08-10 | 确认 YouTube 改用 Data API v3（弃用 HTML 抓取） |
