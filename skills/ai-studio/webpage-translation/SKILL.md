---
name: webpage-translation
description: "英文网页翻译成中文 HTML，保留排版，图片 base64 内嵌，单文件离线可用。"
tags: [ai-studio, translation, webpage, html, i18n, 翻译, 网页翻译]
triggers:
  - 翻译网页
  - 翻译这个页面
  - 英文博客翻译
  - 网页中文版
  - translate page
related_skills: [ai-content-imagery, ai-content-production]
---

# Webpage Translation · 网页翻译技能

> 本技能属于 ai-studio 内容生产体系，遵循共享规则 `../shared/RULES.md`：
> 事实零演绎、专业优先、可溯源。

> **⚡ 流程纪律：翻译是流程，不是临时代码。** 机械处理全走 `scripts/translate_pipeline.py`，
> 模型只做翻译。Token 效率铁律见全局 SOUL.md（每次会话注入）。

## 什么时候用

用户提供一个英文网页 URL，要求翻译成中文并生成 HTML 文件。

典型场景：
- 技术博客翻译（OpenAI/Anthropic/Google AI 等官博）
- 技术文档中文化
- 外文新闻深度稿翻译
- 行业报告中文版本

**输入**：网页 URL
**输出**：单文件 HTML（译文 + 内嵌图片，离线可用）

---

## 核心设计原则

### 1. 单文件优先
所有图片 base64 内嵌，CSS 内联，一个 HTML 文件走天下。
不做目录模式，不做外链模式——embedded 是唯一选择。

### 2. 翻译不是直译，是专业重构
- 准确传达原意，不用翻译腔
- 技术术语首次出现：「中文名（英文原名）」+ 一句话背景解释
- 代码、命令、变量名、产品名 不翻译
- 图片不翻译，图注可翻译

### 3. 排版还原
保留原文的标题层级、段落结构、列表、引用、代码块、表格、图片位置。
不是 Markdown 转译，是直接操作 HTML 结构。

### 4. 事实零演绎
只翻译原文有的内容，不添加、不删减、不解读。
分析、判断、背景补充**仅限于**技术术语的一句话解释（标注为「术语解释」）。

---

## 七步工作流

> 步骤 1-5、6、7 的**机械处理全部由 `scripts/translate_pipeline.py` 完成**。
> 模型只做第 4 步"翻译执行"。禁止在会话里重写脚本。

```
Step 1-3: 脚本化（extract）
   python3 translate_pipeline.py extract <url> --workdir ./work
   → 抓取、正文提取、切块、保护数学公式、下载图片 base64、
     自动跳过（数字单元格/参考文献/空节点）、提取链接映射

Step 4: 翻译执行（模型，分批）
   python3 translate_pipeline.py export ./work --start 0 --end 60
   → 模型读取待译节点文本（紧凑格式）
   → 输出紧凑 JSON：{"节点索引": "译文"}
   → 多批 export 分批翻译，merge 成 translations.json

Step 5-7: 脚本化（build）
   python3 translate_pipeline.py build ./work -t translations.json \
       -o 输出.html --theme tech-dark
   → 回填译文、恢复数学公式/链接、嵌入图片 base64、
     自动移除正文重复 H1、渲染 clean/tech-dark 主题
   → 最后人工过一遍质量清单
```

### Token 效率（全局 SOUL.md 铁律，违反即失败）

- **只读 export 输出的待译文本**，禁止读原始 HTML / page.json / 图片字节
- **脚本自动跳过**纯数字、参考文献、空节点——这些不进模型上下文
- **译文只写紧凑 JSON**，不写 HTML / 不写结构 / 不写调试信息
- 长文分 3+ 批翻译，批间保持术语一致

---

## 翻译风格指南

详细版见 `references/translation-style-guide.md`，这里列核心规则：

### 语气
- 技术文：客观、准确、简洁
- 博客文：保留原文语气，但去除翻译腔
- 不口语化，也不过于正式

### 格式
- 段落长度与原文对应（不拆碎、不合并大段）
- 标题层级与原文一致
- 列表保留原有序号和层级
- 代码块保留原样，不翻译

### 技术术语处理
- 首次出现：中文名（英文原名）—— 一句话解释
- 后文出现：直接用中文名
- 没有通用译名的：保留英文原名，加解释
- 详细术语表见 `references/tech-terminology-glossary.md`

### 专有名词
- 公司名：OpenAI、Google、Microsoft → 保留英文（业界通用）
- 产品名：GPT、Codex、Claude → 保留英文
- 人名：首次出现可加中文译名（如「萨姆·阿尔特曼（Sam Altman）」），后文用姓

---

## 正文提取策略

不同网站结构不同，提取策略分三级：

| 级别 | 策略 | 适用网站 |
|------|------|----------|
| L1 | 语义标签查找 | 有 `<article>` 的现代博客/文档站 |
| L2 | 内容区域启发式 | 有明确 main/content 容器的站点 |
| L3 | 文本密度分析 | 结构混乱的老网站 |

详细策略和实现见 `references/extraction-strategies.md`。

---

## HTML 模板

### 默认模板：clean-reading
- 白底、760px 阅读宽度、17px 字号
- 简洁无干扰，适合所有类型内容
- 响应式，移动端自适应

### 可选模板：tech-dark
- 深蓝渐变、科技感
- 适合 AI/技术类内容
- 复用 ai-content-imagery 的设计语言

模板文件在 `templates/` 目录。

---

## 核心脚本

`scripts/translate_pipeline.py` — 网页翻译管线主脚本（v2.0）。

```bash
# ① 抓取+提取+切块（生成工作目录）
python3 scripts/translate_pipeline.py extract <url> --workdir ./work

# ② 导出待译节点（模型读取，分批）
python3 scripts/translate_pipeline.py export ./work [--start N --end M]

# ③ 回填译文+恢复+渲染（成品）
python3 scripts/translate_pipeline.py build ./work -t translations.json \
    -o 输出.html --theme clean|tech-dark [--title 自定义标题]
```

**模型职责只有一项：翻译 export 输出的文本，返回紧凑 JSON。**
结构处理（切块/跳过/回填/链接/图片/math/双 H1）全部脚本化，禁止临时代码。

---

## 质量检查清单（交付前必过）

- [ ] **完整翻译**：正文所有段落都已翻译，没有漏译的英文段落
- [ ] **术语一致**：同一术语全文统一，首次出现有解释
- [ ] **代码保留**：所有代码块、命令、变量名保持原文
- [ ] **图片内嵌**：所有图片 base64 嵌入，没有外链图片
- [ ] **排版还原**：标题层级、列表、引用、表格结构正确
- [ ] **链接保留**：超链接指向原地址，相对路径已补全
- [ ] **来源标注**：顶部和底部都有原文链接和翻译声明
- [ ] **无翻译腔**：读起来像中文原文，不是机翻感
- [ ] **单文件可用**：断网情况下 HTML 能正常打开和显示

---

## 与 ai-studio 体系的关系

```
用户提供 URL
    ↓
webpage-translation（本技能：英文网页 → 中文 HTML）
    ↓  成品/素材
ai-content-production  →  作为深度长文素材改编
ai-content-imagery     →  样式主题复用
```

- 与 `video-to-deep-blog` 是兄弟技能：同属「素材转化层」
- 翻译成品可直接交付，也可作为其他内容生产技能的输入
- HTML 模板设计语言与 `ai-content-imagery` 保持一致

---

## Pitfalls

1. **⚡ 写临时代码（最严重）**：翻译流程已脚本化（extract/export/build），模型只翻译。每次重写切块/回填/恢复逻辑 = 每篇浪费 30%+ token。
2. **读原始 HTML 进上下文**：6MB 页面（图片 base64）只有 40KB 可翻译文本。只读 `export` 输出。检测方法：正文 < 500 字符 → 可能 SPA/WAF，需浏览器渲染。
3. **参考文献被当正文翻译**：`is_ref_li` 启发式已处理 `(2024a)` 后缀与换行。若仍有漏网，报告修脚本，不要手工翻译 45 条引用。
4. **译文写 HTML 而非 JSON**：模型只需 `{"index": "译文"}`。回填是脚本的事。
5. **图片下载失败**：保留原 URL，不阻塞整体。build 自动嵌入成功的图。
6. **术语一致性**：长文分 3+ 批翻译，用术语表 + 全文检查统一译法。
7. **中英文混排空格**：数字/英文与中文之间加空格（中文排版基本规范）。
8. **超长文分批**：>5000 词分 3+ 批，批间上下文连贯，不逐段独立翻。
9. **图中文字不翻译**：OCR + 重排成本太高，诚实说明，图注翻译即可。
10. **不要停下来问确认**：按管线流程走完，默认 tech-dark + 术语解释，用户有要求再调整。
