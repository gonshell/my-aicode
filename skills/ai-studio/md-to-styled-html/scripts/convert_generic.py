#!/usr/bin/env python3
"""通用 md → 自包含 HTML 转换器（md-to-styled-html 技能支持脚本）

用法:
    python3 convert_generic.py 输入.md "文档标题" 输出.html ["副标题"]

特点:
- 纯 stdlib, 零依赖
- 自带内联暗色 CSS (GitHub-dark 风格), 不依赖任何基准 HTML 存在
- 自动生成 h2 目录导航 (带锚点)
- 支持围栏代码块 / 表格 / 引用块 / 有序无序列表 / 行内 md
- 围栏奇数个时自动截断最后一个 (容错, 不报错退出)

注意: 要 qwen2.5 组件体系风格 (callout/dir-tree/代码高亮) 时, 改用
scripts/convert_plan.py 的克隆法, 见 SKILL.md。
"""
import re
import html as html_mod
import sys
import os

# 浅色主题（白底 + 深蓝强调，用户默认偏好）

CSS_LIGHT = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body { background: #f5f7fa; color: #1f2328; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.7; font-size: 15px; }
.container { max-width: 900px; margin: 24px auto; padding: 40px 48px 80px; background: #ffffff; border-radius: 12px; box-shadow: 0 1px 4px rgba(0,0,0,0.08); }
h1 { color: #1a56db; font-size: 28px; font-weight: 700; margin-bottom: 8px; }
h2 { color: #1a56db; font-size: 22px; font-weight: 600; margin-top: 36px; margin-bottom: 16px; padding-bottom: 8px; border-bottom: 1px solid #e5e7eb; }
h3 { color: #1e429f; font-size: 18px; font-weight: 600; margin-top: 24px; margin-bottom: 12px; }
h4 { color: #1e429f; font-size: 16px; font-weight: 600; margin-top: 18px; margin-bottom: 10px; }
p { margin-bottom: 14px; }
ul, ol { margin-bottom: 14px; padding-left: 24px; }
li { margin-bottom: 6px; }
table { border-collapse: collapse; width: 100%; margin: 16px 0; font-size: 14px; }
th, td { border: 1px solid #e5e7eb; padding: 8px 12px; text-align: left; }
th { background: #f0f4ff; color: #1a56db; font-weight: 600; }
tr:nth-child(even) { background: #f9fafb; }
code { background: #f0f4ff; color: #b34700; padding: 2px 6px; border-radius: 4px; font-family: 'SF Mono', Consolas, monospace; font-size: 13px; }
pre { background: #f8f9fb; border: 1px solid #e5e7eb; border-radius: 6px; padding: 14px; overflow-x: auto; margin: 14px 0; }
pre code { background: none; padding: 0; color: #1f2328; }
blockquote { border-left: 4px solid #1a56db; background: #f0f4ff; padding: 12px 18px; margin: 14px 0; border-radius: 0 6px 6px 0; }
a { color: #1a56db; text-decoration: none; }
a:hover { text-decoration: underline; }
strong { color: #111827; font-weight: 600; }
hr { border: none; border-top: 1px solid #e5e7eb; margin: 24px 0; }
.subtitle { color: #6b7280; font-size: 15px; margin-bottom: 20px; }
.header-meta { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 24px; }
.header-meta span { background: #f0f4ff; border: 1px solid #dbe3f0; padding: 4px 12px; border-radius: 20px; font-size: 13px; color: #6b7280; }
.toc { background: #f8f9fb; border: 1px solid #e5e7eb; border-radius: 8px; padding: 18px 24px; margin: 24px 0 32px; }
.toc h3 { color: #1a56db; margin-top: 0; margin-bottom: 12px; font-size: 16px; }
.toc ol { margin: 0; padding-left: 20px; }
.toc li { margin-bottom: 4px; }
.toc a { color: #4b5563; }
.toc a:hover { color: #1a56db; }
.footer { text-align: center; color: #9ca3af; font-size: 13px; margin-top: 48px; padding-top: 24px; border-top: 1px solid #f3f4f6; }
"""

CSS = CSS_LIGHT

def esc(s):
    return html_mod.escape(s, quote=False)

def inline_md(text):
    t = esc(text)
    t = re.sub(r'`([^`]+)`', r'<code>\1</code>', t)
    t = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', t)
    t = re.sub(r'(?<!\*)\*([^*\n]+)\*(?!\*)', r'<em>\1</em>', t)
    t = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" target="_blank">\1</a>', t)
    return t

def slugify(text, used):
    s = re.sub(r'[#*`>|]', '', text).strip()
    s = re.sub(r'[^\w\u4e00-\u9fff-]', '-', s)
    s = re.sub(r'-+', '-', s).strip('-')
    if not s:
        s = 'section'
    base = s[:50]
    s = base
    k = 2
    while s in used:
        s = f"{base}-{k}"
        k += 1
    used.add(s)
    return s

def convert(md_text, title, subtitle=""):
    lines = md_text.split('\n')
    n = len(lines)

    fence_idx = [i for i, l in enumerate(lines) if l.strip().startswith('```')]
    if len(fence_idx) % 2 == 1:
        fence_idx = fence_idx[:-1]
    fence_pairs = [(fence_idx[k], fence_idx[k + 1]) for k in range(0, len(fence_idx), 2)]
    fence_set = set(fence_idx)

    def in_fence(ln):
        for a, b in fence_pairs:
            if a <= ln <= b:
                return True
        return False

    toc, used_ids = [], set()
    for i, l in enumerate(lines):
        if l.startswith('## ') and not in_fence(i):
            t = l[3:].strip()
            toc.append((t, slugify(t, used_ids)))
    used_ids.clear()

    body = []
    table_buf, in_tbl = [], False
    bq_buf, in_bq = [], False

    def flush_code(start, end):
        code_lines = [lines[j].rstrip('\n') for j in range(start + 1, end)]
        body.append(f'<pre><code>{esc(chr(10).join(code_lines))}</code></pre>')

    def flush_table():
        if not table_buf:
            return
        rows = [[c.strip() for c in t.strip().strip('|').split('|')] for t in table_buf]
        flt = [r for r in rows if not all(re.match(r'^:?-{2,}:?$', c) for c in r)]
        if not flt:
            table_buf.clear()
            return
        hdr = '<tr>' + ''.join(f'<th>{inline_md(c)}</th>' for c in flt[0]) + '</tr>'
        bdy = ''.join('<tr>' + ''.join(f'<td>{inline_md(c)}</td>' for c in r) + '</tr>' for r in flt[1:])
        body.append(f'<table><thead>{hdr}</thead><tbody>{bdy}</tbody></table>')
        table_buf.clear()

    def flush_bq():
        if not bq_buf:
            return
        text = ' '.join(bq_buf)
        body.append(f'<blockquote>{inline_md(text)}</blockquote>')
        bq_buf.clear()

    i = 0
    while i < n:
        l, s = lines[i], lines[i].strip()
        if i in fence_set:
            for a, b in fence_pairs:
                if i == a:
                    flush_code(a, b)
                    i = b + 1
                    break
            continue
        if s.startswith('|') and '|' in s[1:]:
            if not in_tbl:
                in_tbl, table_buf = True, table_buf
            table_buf.append(s)
            i += 1
            continue
        elif in_tbl:
            in_tbl = False
            flush_table()
        if s.startswith('>'):
            if not in_bq:
                in_bq, bq_buf = True, bq_buf
            bq_buf.append(s[1:].strip())
            i += 1
            continue
        elif in_bq:
            in_bq = False
            flush_bq()
        if not s:
            i += 1
            continue
        if s.startswith('#### '):
            t = s[5:].strip()
            a = slugify(t, used_ids)
            body.append(f'<h4 id="{a}">{inline_md(t)}</h4>')
            i += 1
            continue
        if s.startswith('### '):
            t = s[4:].strip()
            a = slugify(t, used_ids)
            body.append(f'<h3 id="{a}">{inline_md(t)}</h3>')
            i += 1
            continue
        if s.startswith('## '):
            t = s[3:].strip()
            a = slugify(t, used_ids)
            body.append(f'<h2 id="{a}">{inline_md(t)}</h2>')
            i += 1
            continue
        if s.startswith('# '):
            i += 1
            continue
        if re.match(r'^[-*]\s+', s):
            items = []
            while i < n and re.match(r'^[-*]\s+', lines[i].strip()):
                items.append(inline_md(re.sub(r'^[-*]\s+', '', lines[i].strip())))
                i += 1
            body.append('<ul>' + ''.join(f'<li>{it}</li>' for it in items) + '</ul>')
            continue
        if re.match(r'^\d+\.\s+', s):
            items = []
            while i < n and re.match(r'^\d+\.\s+', lines[i].strip()):
                items.append(inline_md(re.sub(r'^\d+\.\s+', '', lines[i].strip())))
                i += 1
            body.append('<ol>' + ''.join(f'<li>{it}</li>' for it in items) + '</ol>')
            continue
        if s in ('---', '***', '___'):
            body.append('<hr>')
            i += 1
            continue
        para = []
        while i < n:
            sl = lines[i].strip()
            if not sl or sl.startswith('```') or sl.startswith('#') or sl.startswith('|') or sl.startswith('>') \
               or re.match(r'^[-*]\s+', sl) or re.match(r'^\d+\.\s+', sl) or sl in ('---', '***', '___'):
                break
            para.append(sl)
            i += 1
        if para:
            body.append(f'<p>{inline_md(" ".join(para))}</p>')
        i += 1

    if in_tbl:
        flush_table()
    if in_bq:
        flush_bq()

    toc_html = '<div class="toc"><h3>📑 目录</h3><ol>' + ''.join(
        f'<li><a href="#{a}">{esc(t)}</a></li>' for t, a in toc) + '</ol></div>'
    meta_html = '<div class="header-meta"><span>🔬 深度分析</span><span>📅 2026</span></div>'
    subtitle_html = f'<p class="subtitle">{esc(subtitle)}</p>' if subtitle else ''

    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title)}</title>
<style>{CSS}</style>
</head>
<body>
<div class="container">
  <h1>{esc(title)}</h1>
  {subtitle_html}
  {meta_html}
  {toc_html}
  {chr(10).join(body)}
  <div class="footer">基于公开信息的技术分析</div>
</div>
</body>
</html>'''


if __name__ == '__main__':
    if len(sys.argv) < 4:
        print("Usage: convert_generic.py <input.md> <title> <output.html> [subtitle]")
        sys.exit(1)
    md_path, title, out_path = sys.argv[1], sys.argv[2], sys.argv[3]
    subtitle = sys.argv[4] if len(sys.argv) > 4 else ""
    with open(md_path, encoding='utf-8') as f:
        md_text = f.read()
    html_text = convert(md_text, title, subtitle)
    out_dir = os.path.dirname(out_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html_text)
    print(f"✅ {out_path}  ({len(html_text):,} bytes)")
