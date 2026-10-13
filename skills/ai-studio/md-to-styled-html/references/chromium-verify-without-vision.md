# HTML 渲染验证（vision_analyze 不可用时的替代法）

## 背景
2026-09-21 实测：`vision_analyze` 走 mimo-v2.5 后端报 `404 UnsupportedModel`（"does not support
the coding plan feature"，volcengine 侧模型不支持视觉通道），md-to-styled-html 技能早已
预警"视觉模型可能不可用（API 报 unsupported model）"。此时改用**结构检查 + 截图元数据**
组合验证，不必中断交付。

## 验证链（按序执行，全过即交付）

### 1. 结构检查（execute_code，最可靠）
对产物 HTML 逐项断言（实测脚本模式，直接可复用）：

```python
import re, hashlib, os
html = open(html_path, encoding='utf-8').read()
md   = open(md_path, encoding='utf-8').read()

# 标签配对
for t in ['div','table','pre','code','ul','ol','h2','h3','h4','blockquote']:
    o = len(re.findall(rf'<{t}[ >]', html)); c = html.count(f'</{t}>')
    assert o == c, f'{t}: {o} vs {c}'

# TOC 锚点零死链
toc_links = re.findall(r'<li><a href="#([^"]+)">', html)
page_ids  = set(re.findall(r'id="([^"]+)"', html))
assert all(x in page_ids for x in toc_links)

# 标题计数源↔产物一致（逐级）
for lv, tag in [(2,'h2'),(3,'h3'),(4,'h4')]:
    src = len(re.findall('^'+'#'*lv+r' (?!#)', md, re.M))
    dst = len(re.findall(rf'<{tag} id=', html))
    assert src == dst, f'h{lv}: {src} vs {dst}'

# 组件计数：源围栏对 == code-block + diagram
pairs = len(re.findall(r'^```', md, re.M)) // 2
assert html.count('class="code-block"') + html.count('class="diagram"') == pairs

# 表格数一致（分隔行法）
md_tables = len(re.findall(r'^\|[^\n]*\n\|[-| :]+\|', md, re.M))
assert html.count('<table>') == md_tables

# 转换器占位符不残留（高亮保护机制失效的直接证据）
assert '\x00' not in html

# 源 md 表列一致性
lines = md.split('\n')
for i in range(len(lines)-1):
    if lines[i].strip().startswith('|') and re.match(r'^\|[-| :]+\|$', lines[i+1].strip()):
        assert lines[i].count('|') == lines[i+1].count('|'), f'line {i+1}'
```

### 2. Chromium 截图元数据（判断渲染正常，不靠看图）
```bash
# 全页高截图（高度给大，如 20000，配合 virtual-time-budget 保证渲染完成）
chromium --headless --disable-gpu --no-sandbox --window-size=1200,20000 \
  --virtual-time-budget=5000 --run-all-compositor-stages-before-draw \
  --screenshot=/tmp/full.png "file:///abs/path.html"
```
读 PNG 的 IHDR（字节 16-24，`struct.unpack('>II', d[16:24])`）确认尺寸生效；
截图字节数正常范围（如 3.3MB 全页）说明有实际内容渲染——**纯空白页只有几 KB**。
再抽 4-5 个 y 偏移切条带（无 PIL 时用 `ffmpeg -vf crop=w:h:0:off`），条带字节数
100K+ 级别 = 内容真实渲染。锚点定位截图（`#5-2-字段规约`）若只有几 KB 说明该锚点
渲染异常，是可用的定位探针。

### 3. print-to-pdf 页数（内容高度 sanity check）
```bash
chromium --headless --print-to-pdf=/tmp/x.pdf --no-pdf-header-footer "file:///abs/path.html"
```
PDF 二进制里 `re.findall(rb'/Count (\d+)', d)[-1]` 取页数，长文档应有合理页数
（834 行 md → 23 页 PDF 实测）。

## 实测陷阱
- `pip install pillow` 在 PEP 668 + 无适配源环境直接失败（`No matching distribution`），
  别指望装图像库；ffmpeg 通常在，够切条带。
- execute_code 内联验证脚本注意：f-string 里的 `'#'*lv` 若写成
  `rf'^{"#"*lv} (?!#)'` 会 TypeError（str 乘 str）——先构造 pattern 变量再进 f-string。
- 带 `#anchor` 的 headless 截图对**验证锚点跳转**有用，但对整页渲染判断无意义
  （window-size 内空白区域就只有几 KB）。

## 汇报口径
交付说明里注明"视觉复核模型不可用，以结构检查+Chromium 截图字节数代替"，并
主动留口"发现局部样式问题告诉我具体位置"。用户默认接受此口径（2026-09-21 实测）。
