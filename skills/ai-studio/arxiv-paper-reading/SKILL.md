---
name: arxiv-paper-reading
description: "把 arXiv 论文读成可用的纯文本：HTML 全文提取 + 章节定位 + 表格交叉验证。"
tags: [research, arxiv, paper, html2text, deep-research]
---

# arXiv 论文阅读（全文提取 → 结构化精读）

触发：深度技术博客/技术报告/文献调研需要读 arXiv 论文全文时（tech-blog-production、deep-research-report 的素材环节）。目标是把论文变成可核对、可引用的素材，而不是"看过摘要"。

## 核心工作流

1. **取 HTML 全文，不碰 PDF/abs 页**：arXiv 为大部分新论文提供 HTML 版（`https://arxiv.org/html/{paper_id}`），curl 直抓 + stdlib html2text 转纯文本，一步拿到完整正文（实测约 2000 行，含表格）：

```bash
curl -sL --max-time 90 -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0" \
  "https://arxiv.org/html/{paper_id}" -o /tmp/paper.html
python3 html2text.py /tmp/paper.html > /tmp/paper.txt   # 纯 stdlib HTMLParser 版即可
```

2. **先定位章节结构，再按需精读**：2000+ 行不要整读。

```bash
grep -n -E "^(Abstract|1 |2 |3 |[0-9]+\.[0-9]+ )" /tmp/paper.txt | head -80
```

标准阅读顺序：Abstract → Introduction（贡献点）→ Methodology（架构）→ Experiments（主结果）→ Analysis/消融 → Limitations → Related Work。用 read_file 按行段读，而不是一次读完。

3. **现成素材优先**：
- Limitations 节 = "反方视角/局限"章节的现成素材，作者自己列的限制比外部批评更准确、更省检索。
- Related Work = "竞品对比/同类方法"的现成素材，能省一轮搜索。
- Abstract 里的一句话贡献点 = 文章核心论点的候选。

## 关键坑：表格提取必错位

html2text 把论文表格转成文本后，**表头/行列经常错位**（列对不齐、表头串行、Avg 列含义丢失）。处理规则：

- **数字必须用论文正文交叉验证，绝不照抄提取结果**。
- 实测案例：WikiSkill 消融表（Table 3）提取后 5 行 × 4 基准 + Avg 全部串位；靠正文 "from 48.7% to 63.7% (+15.0)" 与 "reduces ... from 63.7% to 60.9%" 重建出正确的四配置消融表。
- 引用任何表格数字前，逐一与正文出现的数字核对；正文没出现的数字，标注"从图表读取，约"。

## 归属与边界

- 本技能负责"读论文"；"页面被拦的兜底抓取"（curl 绕过工具级拦截、Wayback、archive.today）见 `web-fetch-fallbacks` / `blocked-page-recovery`，两者有重叠、由 curator 合并。
- 提取用 html2text 脚本与 `web-fetch-fallbacks` 中内联的 stdlib 脚本同一份。
