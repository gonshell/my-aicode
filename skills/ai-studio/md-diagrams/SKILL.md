---
name: md-diagrams
description: "Use when md 里的 ASCII 框图/mermaid/目录树要变成高清内联 SVG（交付 HTML/Word/PPT/飞书文档时）。先绑定标题、再用模板渲染、最后程序化自检。"
tags: [svg, diagram, markdown, ascii, mermaid, html]
triggers:
  - ASCII 架构图转 SVG
  - md 里的图渲染成图
  - mermaid 转高清图
  - 文档配图
  - diagram to svg
---

# md 图块 → 高清内联 SVG

> 把 md 里出现的**框图/时序图/目录树**转成**内联 SVG**（白底、真 `<text>`、无外部依赖），产出图文件 + 清单，供 HTML/Word/PPT/飞书文档消费。
> 只管「图对不对」；文档排版（hero/TOC/灯箱/表格样式）归 `md-to-styled-html`。

## When to use
- md 含 ASCII 框图（`┌┐└┘│─▼`）、mermaid 围栏、目录树（`├└`），要变成图交付
- 「html 里的图为什么是字符图 / 之前的图不这样」——必须重画，不能端字符画
- 纯代码块、纯文本表**不触发**本技能

## 硬前提（顺序不可颠倒）
1. **先 `scan.py`** 出清单：每个图块绑定「上方最近标题」+ 类型 + 指纹。围栏奇数**不许渲染**；同一标题下有多个图块是合法的，`scan.py` 自动编号为 `标题#2`/`标题#3`。**图题只由脚本分配，人不手写**——手写图题是张冠李戴的成因。
   —— 凭行号/印象建图题清单会张冠李戴（`fig01 设计哲学` 里装五层架构），这是本技能存在的第一理由。
2. **再渲染**：`mermaid` 走 `render_mermaid.py`；ASCII/树按类型选 `layouts.py` 原语。
3. **后 `check.py`** 全量程序化自检（零 token）；视觉只抽 ≤3 张看美学。

## 图类型 → 渲染器（8 类，套不上就保留代码块）
| 源形态 | 渲染器 | 说明 |
|---|---|---|
| mermaid 时序/流程 | `render_mermaid.py` | mmdc→SVG，`htmlLabels:false` |
| 目录树（`├└│`） | `layouts.tree_card` | 浅色代码卡，文件夹/注释着色 |
| 纵向分层栈（L1–L5/T1–T5） | `layouts.stack` | 层名+能力+包路径 |
| 依赖树/汇聚关系 | `layouts.dep_tree` | |
| 容器+注入子块（Context） | `layouts.container` | |
| 编号步骤/阶段流 | `layouts.phaseflow` | 左色条卡+主线箭头 |
| `seq/type` 事件序列 | `layouts.event_seq` | 含 shadow 红框 |
| 分栏对照/公式 | `layouts.columns` | |

**套不进以上 8 类 → 保留为等宽代码块，不硬画。**

## 图元与配色（唯一真源 `scripts/figlib.py`）
`box / arrow / path / text / elbl / chip / rrect / wrap`；配色 `#e8eefc/#1a56db/#1e3a8a` 主 + `#f8faff/#93b4f5` 次 + `#6b7280` 旁注，语义色 `#16a34a/#dc2626/#d97706/#7c3aed`。
**与 `md-to-styled-html` v1.15 的 `gen_figures_vNNN.py` 同一套视觉语言——不要另起一套。**
`wrap()` 自动加全幅白底 `<rect>` + `role="img"` + `font-family`。

## 清单格式（manifest.json）
```json
[{"i":1,"file":"fig1.svg","w":880,"h":490,"title":"图 2-1 · COP 三层",
  "note":"注：……（ASCII 块里的「注：」是内容，必须移到图注）",
  "fence_open":349,"fingerprint":"a1b2c3d4e5f6"}]
```
`title` 只能取**该围栏上方最近标题**；`fence_open`+`fingerprint` 供下游替换时校验（md 被编辑后行号会漂移）。

## 自检（`check.py`，全量、零 token）
- **C1** XML 合法 + viewBox
- **C2** 全幅白底：认 `<rect fill="#fff">`，也认根节点 `style="background-color:white"`（mmdc 输出走后者），两者皆无才判失败。只认 rect 会对 mermaid 分支误报。
- **C3** 无 `foreignObject`（标签必须真 `<text>`）
- **C4** 文字不越界（按 `figlib.tw()` 估宽 + anchor 推算落在 viewBox 内）
- **C5** **文字保真**：源 ASCII 的标识符（事件名/函数名/路径/字段）在 SVG 中逐字命中；中文说明可压缩、**不得增删语义**
- 生成期 `figlib.report()` 宽度自检**必须清零后再交付**；宽度一律由内容算出（`columns(w=None)` 自动定宽），**不写死画布宽度**——写死的画布要等内容变了才暴露溢出。`check.py` 是交付前最后一道。

## 流程
```bash
S=~/.hermes/skills/ai-studio/md-diagrams/scripts
python3 $S/scan.py doc.md --json figs/manifest.json     # 1. 出清单（不过不许继续）
# 2. 按清单为每个图块写 DSL（选原语+填字段），文字逐条取自 ASCII 原文
python3 $S/render_mermaid.py figs/x.mmd figs/x.svg      # mermaid 分支
python3 $S/check.py figs --manifest figs/manifest.json --md doc.md   # 3. 自检
```

## 不做（v1 边界）
- 不自动解析 ASCII 结构（画法千变万化）——由人/模型填 DSL，**文字只能引用原文串**
- 不做几何断言、manifest 指纹校验、深层 references（需要时再加）
- 不对未识别图块硬画

## 与 md-to-styled-html 集成
下游按 manifest 的 `fence_open`/`fingerprint` 定位围栏 → 替换为内联 SVG + `figcaption`（含 `note`）；未装本技能时，转换器降级为等宽代码块。
详见 `md-to-styled-html` 的「ASCII 图块」节。
