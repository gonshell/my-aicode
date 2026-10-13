---
name: md-to-styled-html
description: "Convert large technical markdown to styled single-file HTML."
tags: [html, markdown, conversion, technical-doc, feishu, report]
triggers:
  - md 转 html
  - 生成 HTML 文件
  - 技术方案转 HTML
  - convert plan to html
  - 参考 qwen2.5_lora_finetune_plan.html 的格式
---

# Markdown 技术文档 → 精美 HTML

> 把大篇幅技术方案（1000-4000+ 行 md）转换成**单文件自包含 HTML**，交付飞书/Web 查看。
> 风格基准：`/root/workspace/modeltrain/qwen2.5_lora_finetune_plan.html`（用户认可的组件体系）。

## When to use
- 用户要求把 `.md` 技术方案/计划/评审文档转成 HTML
- 用户明确说"参考 qwen2.5_lora_finetune_plan.html 的格式"（组件体系标准）
- 长文档（几百行以上），通用 `generate_article.py` 渲染效果不够（无目录/代码块无高亮/ASCII 图丑）
- **重构/改版已有长文档**：新内容写回同一路径（**先归档旧版！**），并同步再生成 HTML/DOCX/飞书派生件 → 先读「版本与再生成纪律」节

## 核心决策：通用脚本 vs 定制转换脚本
- **不要改 `ai-content-imagery/scripts/generate_article.py`**（用户否决过：它是博客长文渲染器，不是技术文档渲染器）
- 正确做法：写**一次性定制转换脚本**（如 `convert_plan.py`），复用 qwen2.5 HTML 的 CSS 组件体系，输出同风格 HTML
- 脚本保留在文档目录（如 `/root/workspace/modeltrain/convert_plan.py`），可复用给同目录后续文档

## 组件体系（qwen2.5 风格）
| 组件 | HTML 结构 | 用途 |
|------|----------|------|
| Header | `<header>` 渐变蓝 + h1 + subtitle + meta chips | 文档标题区 |
| TOC | `<div class="toc">` + `<ol><li><a href="#slug">` | 章节导航（自动生成） |
| 代码块 | `<div class="code-block">` + 语言 tag + span 高亮 | 语法高亮 |
| 目录树/ASCII 图 | `<pre class="dir-tree">` + `.folder`/`.file`/`.comment` span | 目录结构、流程图 |
| 表格 | `<table><thead><tbody>` | 数据表 |
| Callout | `.callout-warn/danger/success` + `.callout-title` | 引用块按 emoji 分类 |
| 行内代码 | `<code class="inline-code">` | 行内 `code` |

完整 CSS 可从 `qwen2.5_lora_finetune_plan.html` 的 `<style>` 块直接复制（约 5KB）。

## 转换脚本要点
工作版本见 `scripts/convert_plan.py`（可直接运行/改写）。

关键实现逻辑：
1. **围栏配对用行号集合，不用布尔状态机**：先扫描所有 ` ``` ` 行号，配对成 `fence_pairs`，主循环按行号精确跳转
2. **TOC 自动生成**：扫描 `## ` 标题 → slugify 成锚点 id，正文标题带 `id="slug"`
3. **文档自带"目录"章节要跳过**：源 md 常有 `## 目录` + markdown 链接列表，其锚点格式与 slug 不一致会产生死链，直接跳过该章节（含内容），只保留自动 TOC
4. **语法高亮必须用占位符保护**：先替换字符串/注释为 `\x00S{idx}\x00` 占位符，再做关键字/函数高亮，最后还原。否则正则会把已插入的 `<span class="c-str">` 里的 `class` 再当关键字处理（嵌套错误）
5. **ASCII 图检测**：代码块内容含 `┌│└├┐┘┤─` 字符 > 2 个 → 用 dir-tree 渲染

## 已知陷阱（都是实际踩过的）
1. **源 md 代码围栏必须是偶数个**。奇数个围栏 → 配对错位 → 后续所有 `## ` 章节被当成"代码块内"吞掉，TOC 只剩一半。排查方法：统计 ` ``` ` 行数，奇数时逐个检查配对块是否"含标题行"
2. **JSONL/JSON 数据字符串里嵌 ` ``` `**：数据样本的 value 字段可能含 ` ```python ` 代码示例，不是真围栏。围栏检测必须只看**行首** ` ``` `（`l.strip().startswith('```')` 已足够，但不能用 `'```' in line`）
3. **源 md 本身可能有缺失闭合围栏**（如 yaml 块漏了 ` ``` `）。修正文档（补 ` ``` `）比绕开更干净，修正后重新统计围栏数验证为偶数
4. **语法高亮二次处理已插入 HTML**：注释替换后做字符串替换，会把 `<span class="c-comment">` 里的引号当字符串。解法见上（占位符）
5. **slug 一致性**：TOC 和正文必须用同一 slugify 函数+同一 used_ids 集合，否则 `#一项目概述` vs `#一-项目概述` 死链
6. **同风格文档复用脚本**：优先用本技能的通用脚本 `scripts/convert_generic.py`（参数化，无需克隆改文件名）：
   `python3 scripts/convert_generic.py 输入.md "标题" 输出.html "副标题"`（自带内联 CSS，不依赖 qwen2.5 HTML 存在；要 qwen2.5 组件体系时仍用旧法：`sed 's/旧名.md/新名.md/g; s/旧名.html/新名.html/g' convert_plan.py > convert_plan_new.py && python3 convert_plan_new.py`）
7. **交付后版本残留审计**：内容含版本号（如 Qwen3.5/3.6）的方案转换后，grep 旧版本字符串确认每个"引用他人原文"的句子能在源页找到——用户会主动查这个（曾有 Qwen3.8 模型卡原文被误引到 Qwen3.6 方案）
8. **不要在 execute_code 里内联写转换脚本**：Python <3.12 的 f-string 不允许表达式含反斜杠（如 `f"{html.count('<div class=\"x\">')}"` 直接 SyntaxError），而转换脚本必然大量出现这种模式，内联执行会反复撞墙浪费轮次。正确做法：write_file 落一个 .py 文件（write_file 的 lint 顺带查语法），再 terminal 运行。CSS 同理：先用正则从基准 HTML 抠 `<style>` 块存成独立文件（`re.search(r'<style>(.*?)</style>', content, re.DOTALL)`），转换脚本读文件，不要硬编码进脚本字符串。

9. **围栏紧跟段落后会被"吞"成普通段落（行流解析器高频 bug）**：段落处理器的内层循环遇到 ` ``` ` 行 break 后，尾部若无条件 `i += 1`，会把 break 行（围栏**起始**行）跳过——当围栏块紧跟在正文之后（中间无空行）时，整块代码被当普通段落合并输出：**内容还在，但没了 `<pre><code>` 包裹**。只影响"开 fence 前一行是正文"的块。
    **检测**：grep 已知代码块首行（如 `STANDBY   → ACTIVE`）是否出现在 `<p>…</p>` 而非 `<pre><code>`；或对比 `<pre><code>` 数 vs 预期围栏对数。
    **修复**：段落内循环 break 后，仅当 break 行不是围栏起始行才 `i += 1`：
    ```python
    is_fence_open = i < n and any(a == i for a, _ in fence_pairs)
    if not is_fence_open:
        i += 1
    ```
10. **连续 `>` 行被合并成一段（Markdown 语义，HTML 与 DOCX 同时中招）**：头部元数据块若逐行写 `> **材料类型**：…` / `> **证据范围**：…`，渲染后塌成**一整段**——粗体标签夹在长段落中间、行结构全丢，用户会直接报"内容重复、排版有问题"。**这不是脚本 bug**：`pandoc` 与自写行流解析器行为一致，单一源文件同时污染 HTML 与 DOCX。
    **检测**（发稿前一行）：`awk 'prev ~ /^>/ && $0 ~ /^>/ {print NR": 连续引用行，需插入空 > 分隔"} {prev=$0}' file.md`
    **修复**：在连续 `>` 行之间插入**只含 `>` 的空行**（首选改 md，HTML 与 DOCX 同时生效）；转换器侧兜底为"段落内各行用 `<br>` 连接"，注意**先 `esc()` 转义、后拼 `<br>`**，顺序反了标签会被转义吃掉。
11. **高亮替换顺序**：字符串 → 注释 → 关键字/函数 → 还原。行内注释正则用 `#[^\s<]` 排除已插入的标签；bash 无关键字替换，但字符串也须先于注释。
12. **锚点有效性验证**：`href="#..."` 必须在 `id="..."` 中存在，两侧分别提取后比对（文档自带"目录"章节的锚点格式与自动 slug 不一致，必须整章跳过）。

13. **mermaid 图必须走 SVG 内联，且关掉 htmlLabels（清晰度 + 兼容性双坑）**：PNG 默认只有 **784px 宽**，放进 1000px 内容区就是上采样发虚，用户会直接说"图不清晰"。正确做法：mmdc 输出 `.svg` → 转换器**内联**（去 `<?xml?>` 头、注入 `role="img" aria-label`、CSS 加 `figure svg{max-width:100%;height:auto;display:block;margin:0 auto}`）。同时**必须**给 mmdc 传配置 `{"htmlLabels": false}`（`-c cfg.json`），否则标签是 `<foreignObject><div>`，`<text>` 节点数为 0——部分查看器/打印链路不渲染文字。验收断言：`<svg>` 数 == 图数 且 每图 `<text>` 节点 > 0 且 `foreignObject` == 0。
13.5 **分段落盘再拼接时，段间缺空行 → 紧邻的 `## ` 标题被吞（标题、正文、TOC 锚点三处同时出问题）**：长文档常拆成 `part1/2/3.md` 分次 write_file 再 `cat` 合并，若前一段末尾是正文行而下一段以 `## X` 开头（无空行），行流解析器的段落循环会在标题行 break 后 `i += 1` 跳过它——**该章标题整行消失，正文直接从下一级 `###` 开始**，而 TOC 仍由标题扫描生成 → 表现是"目录有、正文没有"。 **一行检测**：转换后 `href="#..."` 与 `id="..."` 的差集（dangling anchors）非空即中招，本次实测正是 `{'5-训练方案','9-执行计划'}`。 **修法**：`cat` 前给每段尾部补空行，或整稿后跑一遍 `re.match(r'^#{2,4} ', lines[i]) and lines[i-1].strip()!=""` 找出所有"标题行前无空行"的位置补空行。**另**：`python3 -c` 拼接用 `cat a b c > out` 不补分隔符，是最高频触发场景。

14. **HTML 注释行紧贴标题会被吞（本次实测丢掉整个附录 A）**：源 md 里 `<!-- 说明 -->` 紧跟 `## 附录 A` 时，行流解析器把注释当 HTML 块吞到下一个空行，**连标题和其后第一个小节标题一起吞掉**，正文直接从第二小节开始。TOC 仍会列出被吞标题（TOC 由标题扫描生成）→ 表现是"目录有、正文没有"。对策：① 装配/转换前剥离 `^<!--.*-->$` 行（保留 `<!--@marker-->` 占位）；② 构建脚本产出后必查「附录/章标题锚点数 == 预期数」。
15. **预渲染脚本非幂等**：mermaid→图替换是**就地改写**产物 md（`![](diag.svg)`），重复运行第二次渲染 0 张图并静默产出无图 HTML。每次必须从主源 `cp` 一份到 `_build/rendered.md` 再渲染。
16. **反斜杠转义不会渲染成字面量**：表格脚注写法 `\* 条件必填…` 在 HTML 里原样显示 `\*`。不要在表格里用星号脚注机制——把"必填"列写 `条件`，条件用表下独立条文写清；并在装配校验里加断言 `反斜杠转义 == 0`。

## 版本与再生成纪律（重构长文档必读）

**① 覆写源 md 前先归档旧版（最高优先级）**：重构 = 把新内容写回**同一路径**，`write_file` 是整体覆盖，**先 mv 再写**。
血泪教训：本类报告曾直接覆写 v1，而同目录**不是 git 仓库**，只能靠管道中间件还原（实测 38,936B/462 行 vs 原件 38,935B/461 行，8 项抽查通过）。
**无 VCS 时的恢复顺序**：① 转换管道中间件 `_build/<x>/<x>_processed.md`（通常只把 mermaid 块换成 `![]()`，其余逐字一致）② 源碎片（`.mmd` 源码 + docx + 图片）③ 派生 HTML 正文。
👉 由此：**每个 mermaid 块都落盘 `.mmd` 源码**与 PNG 并存——它就是 md 的备份碎片；交付链每一环产物都留在项目里。

**② mermaid 图号/图题随章节号同步改名**：`MERMAID_IMGS` 是**按出现顺序**的映射表，章节重排后图号会变（`图 2-1` → `图 0-1`），忘改就是"图题与章节完全对不上"的交付事故。

**③ DOCX 再生成（pandoc）**：`--reference-doc` 指向的文件**必须是有效 zip**（坏的报 `Did not find end of central directory signature`，先验 `zipfile.ZipFile(p)`；无效就退回上一版 docx 或省略）；命令用列表 append 构造，**不要 `cmd.insert()` 硬插**（`-o` 后必须紧跟输出名，插错报 `withBinaryFile: does not exist`）。

**④ 写进产物的数字必须先程序化统计**（章/节/表/图/字节），别凭印象——曾写"12 章 33 节"实际是 13 章 29 节。

**⑤ 交付件命名带版本号，禁同名覆盖式重发**：同一版文档在一次会话里改了又发，用同一文件名连发 2–3 次 → 用户看着两个同名 HTML 直接问"**到底是哪个？**"。
规则：更新版另存为 `<name>-v7.0.html`（主目录保留一个 `<name>.html` 作"最新滚动件"，两者内容一致），并在回复里给**指纹**（字节数 + `md5sum`）+ **一分钟自检判据**（如"附录 C 存在 / 术语表 55 行 / 图可无级缩放"三条任一成立即是终版）+ 明确"以最新一条为准，前两份删掉"。旧交付件不要靠文件名区分，靠**版本号 + 指纹**。
用户问"文件存在哪个目录" → 回**绝对路径**（`/path/to/xxx.html`）+ 可复制的 `lark-cli … --file ./x.html` 发送命令，并注明同目录哪些是现行件、哪些可清理。

**⑥ 工作目录清理纪律（重构收尾常被要求"把废弃件清理掉"）**：
- **先列清单再动手**：每条给绝对路径 + 字节数 + mtime + **判定依据**（被谁引用/被哪个脚本取代/文件尾自标"已废弃"），列完再执行——用户会明确要求"清理前先列出来"。
- **删前 grep 引用**：`grep -rl "<文件名>" .` 排除自身。实测教训：把 `_newterms.tmp` 当废弃件列入清理清单，实际它是装配脚本的**活构建输入**（`.tmp` 后缀 ≠ 一次性文件）。命中引用的先看清是"旧脚本引用"（可一并归档）还是"现行脚本引用"（保留）。
- **无 VCS 先归档**：非 git 仓库时用 `mv` 到 `_archive/<chain>/` 而非 `rm`，并告知"确认无需回溯后我可彻底删除"；用户点头后再 `rm -rf`，并把 README 里的"可回溯"表述改成"已彻底删除"（避免留下失效说明）。
- **`__pycache__`**：删的时候用 Python `shutil.rmtree(<确切路径>)` 对**精确路径**删——模式化的递归删除（`find … -exec rm -rf`）会被 agent shell 的安全硬线拒绝，白费一轮。删掉还只是暂时的：脚本互相 `import`（如装配器 import 枚举表生成器）会立刻再生。治本是装配脚本顶部加 `import sys; sys.dont_write_bytecode = True`。

细则与实测案例见 `references/deliverable-versioning.md`（再生成链与 pandoc 坑）、`references/deliverable-naming-and-cleanup.md`（命名指纹、清理清单模板与实测数字）。

## 通用转换器复用（避免复制整套 CSS）

把已调好的一次性脚本当模块加载，覆写模块级配置再调其转换函数：

```python
import importlib.util
spec = importlib.util.spec_from_file_location("conv", CONV_PATH)
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
mod.TITLE, mod.SUBTITLE, mod.MERMAID_IMGS = title, subtitle, imgs
mod.mermaid_iter = iter(imgs)        # 必须重建：模块级迭代器在 import 时已消耗
html = mod.convert(open(src, encoding="utf-8").read())
```

两个必查点：① **mermaid 迭代器要重建**，否则第二个文档起图全部走 `StopIteration` 分支；② **模板字符串的求值时机**——若 HTML 模板是模块级 f-string（import 时已求值），覆写 `TITLE` 无效，只有在 `convert()` 函数体内求值才吃得到新值（先确认再依赖）。用 argv 传 `src/out/title/subtitle` 后，一个脚本即可服务同库多份文档。

## 验证清单（交付前必做）
```python
# 1. 标签配对检查
for t in ['div','table','pre','ul','ol','h2','h3','h4','span']:
    opens == closes
# 2. TOC 锚点有效
toc_links ⊆ page_ids
# 3. 无嵌套错误
'<span class=<span' not in html
# 4. 组件计数合理（代码块/表格/callout 数量与源文档一致）
# 5. Chromium 截图确认渲染（可选，视觉模型不可用时用结构检查代替）
timeout 30 chromium --headless --disable-gpu --no-sandbox --screenshot=/tmp/plan.png --window-size=1200,900 "file:///abs/path.html"
```

补充检查项（长文档尤其必查）：

- **`<pre><code>` 数 = 源围栏对数 − mermaid/图片块数**（少了 = 有代码块被吞成段落，见陷阱 9）
- **内嵌图数**：SVG 内联时数 `<svg`（应 == 图数，且每图 `<text>` 节点 > 0、`foreignObject` == 0）；PNG 内联时数 `data:image/png;base64,`（= mermaid 块数 + 本地图片数）。少了说明有图被吞
- **小节号查重**：`collections.Counter(re.findall(r'^#{3,4} ([A-J0-9]+\.\d+)(?=\s)', md))` 无计数 > 1 的项（装配件与"被改号的基座节标题"撞号，实测一次撞 10 处：F.1×2、G.1–G.4 各×2、H.1×2）
- **反斜杠转义 == 0**（`re.findall(r'\\[*_`|]', md)`）与**表列一致性**（每个表头 `|` 数 == 分隔行 `|` 数）
- **手写 HTML 注释行不得紧贴标题**（见陷阱 14）：断言「章/附录标题锚点数 == 预期数」，TOC 有而正文没有 = 被吞
- **图题逐一比对**：抽出所有 `figcaption` 文本，与预期"图号 + 标题"清单核对——章节重排后最易错位
- **引用块段落数**：`<blockquote>` 内 `<p>` 数 = 源 `>` 行数（空 `>` 分隔行不计）；元数据块塌成一整段时该数骤降（陷阱 10）。DOCX 侧可抽查 `word/document.xml` 确认元数据各项各占一个 `<w:p>`
- **残留 ``` 计数**：仅允许出现在 JSON 字符串值内（数据内容，正常）
- **数字实测**：交付说明里的章节数/条数/字节数一律 `len(re.findall(...))` / `os.path.getsize` 实测

## 支持文件

- `references/conversion-debugging.md` — 转换调试失败案例详解（围栏断点定位、slug 不一致、高亮二次处理，含占位符实现与验证脚本）
- `references/deliverable-versioning.md` — 交付物版本与再生成（覆写前归档、无 VCS 时的恢复顺序、md→HTML→DOCX 再生成链与 pandoc 坑、交付数字实测）
- `references/deliverable-naming-and-cleanup.md` — 交付件命名与指纹（禁同名重发、"到底是哪个"的答法、绝对路径模板）、工作目录清理清单模板与实测踩点（`.tmp` 可能是活构建输入、无 VCS 归档法、`__pycache__` 再生治本）
- **配套技能 `md-diagrams`**（`~/.hermes/skills/ai-studio/md-diagrams/`）— 上文「ASCII 图块」规则的固化版实现，含 `scan.py`/`layouts.py`/`check.py`/`figlib.py`。本文档需画图时优先调它，不再手写 `gen_figures_vNNN.py`

## 交付
- HTML 单文件直接发飞书：`cd 文件目录 && lark-cli im +messages-send --user-id <open_id> --file ./xxx.html`（--file 要相对路径）
- 转换脚本一并保留在文档目录，方便下次复用

## Pitfalls
- 用户说"参考 qwen2.5 格式" = 要组件体系（toc/card/code-block/dir-tree/callout），不是随便一个 markdown 渲染
- 4000 行级文档不要手写 HTML，写转换脚本；几十行的短文档可直接手写
- 视觉模型（vision_analyze）可能不可用（API 报 unsupported model），此时用 HTML 结构检查 + Chromium 截图字节数判断渲染正常
- **结构检查+截图元数据替代法的完整可复用脚本与实测陷阱**（PNG IHDR 解析、ffmpeg 切条带、print-to-pdf 页数、锚点截图探针、execute_code f-string 撞坑）见 `references/chromium-verify-without-vision.md`
- ASCII 架构图（无 mermaid/位图的文档）单独渲染成 `.diagram` 卡片（浅蓝底+等宽+「架构图」标签），与 `.code-block`（左蓝条+语言标签）视觉区分；转换器用框线字符计数（┌│└─ 等 >2）自动判别。2026-09-21 AN12-v7（834 行、19 围栏、34 表、无 mermaid）实测全链通过
- **2026-09-23 更正（两次踩坑后的定论）：ASCII 图块既不能直接端字符画，也不能只做"程序化栅格化"。**
  - 坑 A：把 ASCII 顶替成**手绘 SVG** → 图与 ASCII 口径不一致，用户报"PNG 与 ASCII 内容不一致"。
  - 坑 B：退回 `<div class="diagram">` 文本卡片 → 用户立刻问"html 中的图为什么是字符图？之前都不是的"。
  - 坑 C：把 ASCII 逐字符转轮廓 `<path>`（技术上"矢量"了）→ 用户判"**这是你的矢量图？这么丑的效果，你认真了么**"——本质是"把字符画套了个矢量的壳"，不是作图。
  - **正解 = 走配套技能 `md-diagrams`**：`scan.py` 出清单（围栏→最近上方标题绑定，**图题只由脚本分配**）→ `layouts.py` 版面原语填 DSL（内容逐条取自 ASCII 块：ASCII 是源，图是交付形态）→ `check.py` 全量自检（XML/白底/无 foreignObject/文字越界/文字保真）。配色沿用 `gen_figures_v115.py` 那套，别另起一套视觉语言。**不要手写 `gen_figures_vNNN.py`，也不要凭行号/印象建图题清单**。
  - **必做**：ASCII 块里的「注：…」是内容，抽出来作图注（HTML `<figcaption class="fig-note">`、DOCX 楷体 19 半点灰段落），否则换图即丢内容。
  - **布局自检交给 `md-diagrams` 的 `check.py`（C4 文字越界、C5 文字保真），不要临时自写一套**：越界判断必须程序化（`tw()` 估宽 + anchor 推算 x0/x1 落在 viewBox 内），不能只靠肉眼。
  - 产出物：`figures_vNNN/fig{i}.svg` + `manifest.json`（含 viewBox 与图注），HTML 与 DOCX **共用同一目录**（DOCX 走 SVG 通道 + `rsvg-convert -w 2000` 高清 PNG 兜底，显示宽 15.5 cm ≈ 328 dpi）。
  - 图务必自带 `<rect width height fill="#ffffff"/>` 白底：透明底在 PNG 兜底/打印链路上易出问题，且会让"墨迹占比"类自检失真（透明像素 RGB=0 被当墨迹，实测得出 99% 的假信号）。

- lark-cli 发送成功时 stdout 头部有 `uploading file:` 前缀行，管道接 `json.load(sys.stdin)` 会炸——先落 `> /tmp/out 2>&1` 再解析，或 `tail -3` 肉眼确认 `\"ok\": true`
- md 源文件被修正（如补围栏）后要告知用户，保持 md 与 HTML 一致
