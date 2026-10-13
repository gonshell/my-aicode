#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一次性定制转换：大型技术方案 md → qwen2.5 风格 HTML
参照 /root/workspace/modeltrain/qwen2.5_lora_finetune_plan.html 组件体系。
2026-08-28 实战验证于 qwen3.5_finetune_plan.md（3671 行 / 119 代码块 / 35 表格）。

用法：改 MD_PATH / HTML_PATH 后直接运行。CSS 建议从 qwen2.5_lora_finetune_plan.html 复制。
"""
import re
import html

MD_PATH = '/root/workspace/modeltrain/qwen3.5_finetune_plan.md'
HTML_PATH = '/root/workspace/modeltrain/qwen3.5_finetune_plan.html'

with open(MD_PATH, 'r', encoding='utf-8') as f:
    lines = f.readlines()
n = len(lines)

# ========== 工具函数 ==========
def esc(s):
    return html.escape(s, quote=False)

def inline_md(text):
    t = esc(text)
    t = re.sub(r'`([^`]+)`', r'<code class="inline-code">\1</code>', t)
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

def highlight_code(code, lang):
    """占位符保护法：先保护字符串/注释，再做关键字/函数高亮，最后还原。"""
    out = []
    if lang in ('bash', 'sh', 'shell'):
        for l in lines_to_list(code):
            l = esc(l)
            l = re.sub(r'("(?:[^"\\]|\\.)*")', r'<span class="c-str">\1</span>', l)
            l = re.sub(r'^(#.*)$', r'<span class="c-comment">\1</span>', l)
            l = re.sub(r'(\s)(#[^\s<][^<\n]*)$', r'\1<span class="c-comment">\2</span>', l)
            out.append(l)
    elif lang == 'python':
        for l in lines_to_list(code):
            l = esc(l)
            # 步骤1-2：字符串/注释 → 占位符
            string_markers, comment_markers = [], []
            def _str(m):
                string_markers.append(m.group(1)); return f'\x00S{len(string_markers)-1}\x00'
            def _cmt(m):
                comment_markers.append(m.group(1)); return f'\x00C{len(comment_markers)-1}\x00'
            l = re.sub(r'("(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\')', _str, l)
            l = re.sub(r'^(#.*)$', _cmt, l)
            l = re.sub(r'(\s)(#[^\s]*)$', lambda m: m.group(1) + _cmt(m), l)
            # 步骤3：关键字/函数
            l = re.sub(r'\b(def|class|import|from|return|if|elif|else|for|while|in|not|and|or|None|True|False|try|except|with|as|lambda|pass|break|continue|print|self|raise)\b', r'<span class="c-key">\1</span>', l)
            l = re.sub(r'\b([a-zA-Z_]\w*)(?=\()', r'<span class="c-func">\1</span>', l)
            # 步骤4：还原
            for i, s in enumerate(string_markers):
                l = l.replace(f'\x00S{i}\x00', f'<span class="c-str">{s}</span>')
            for i, s in enumerate(comment_markers):
                l = l.replace(f'\x00C{i}\x00', f'<span class="c-comment">{s}</span>')
            out.append(l)
    elif lang in ('yaml', 'yml'):
        for l in lines_to_list(code):
            l = esc(l)
            if re.match(r'^\s*#', l):
                out.append(f'<span class="c-comment">{l}</span>'); continue
            l = re.sub(r'^(\s*)([\w.-]+)(\s*:)', r'\1<span class="c-key">\2</span>\3', l)
            l = re.sub(r'(\s)(#[^\s<][^<\n]*)$', r'\1<span class="c-comment">\2</span>', l)
            out.append(l)
    elif lang in ('json', 'jsonl'):
        for l in lines_to_list(code):
            l = esc(l)
            l = re.sub(r'("(?:[^"\\]|\\.)*")(\s*:)', r'<span class="c-key">\1</span>\2', l)
            l = re.sub(r':\s*("(?:[^"\\]|\\.)*")', r': <span class="c-str">\1</span>', l)
            l = re.sub(r':\s*(\d+)', r': <span class="c-num">\1</span>', l)
            out.append(l)
    else:
        for l in lines_to_list(code):
            out.append(esc(l))
    return '\n'.join(out)

def lines_to_list(code):
    return code.split('\n')

def is_ascii_art(block):
    return sum(1 for bl in block if any(c in bl for c in '┌│└├┐┘┤─')) > 2

def render_dir_tree(block):
    out_lines = []
    for raw in block:
        l = esc(raw.rstrip('\n'))
        if not l.strip():
            out_lines.append(''); continue
        m = re.match(r'^(.*?)(\s{2,})(#.*)$', l)
        prefix, comment = l, None
        if m:
            prefix, comment = m.group(1), m.group(3)
        is_folder = '/' in prefix or prefix.rstrip().endswith('/') or re.search(r'(?:├──|└──)\s*[\w.-]+\/$', prefix)
        name_match = re.search(r'[├└]──\s*([^\s]+)\s*$', prefix)
        if name_match:
            is_folder = name_match.group(1).endswith('/')
        if prefix.strip().startswith('/') and prefix.strip().endswith('/'):
            is_folder = True
        if is_folder:
            prefix = re.sub(r'([├└]──\s*[\w.-]+/?)', r'<span class="folder">\1</span>', prefix)
            prefix = re.sub(r'^(/[\w./-]+/)', r'<span class="folder">\1</span>', prefix)
        else:
            prefix = re.sub(r'([├└]──\s*[\w.-]+(?:\.[\w]+)?)', r'<span class="file">\1</span>', prefix)
        out_lines.append(f'{prefix}<span class="comment">{comment}</span>' if comment else prefix)
    return '\n'.join(out_lines)

# ========== 围栏配对（关键：行号集合，非布尔状态机）==========
fence_idx = [i for i, l in enumerate(lines) if l.strip().startswith('```')]
if len(fence_idx) % 2 == 1:
    raise SystemExit(f"❌ 源 md 围栏为奇数个（{len(fence_idx)}），先修复 md 再转换")
fence_pairs = [(fence_idx[k], fence_idx[k+1]) for k in range(0, len(fence_idx), 2)]
fence_line_set = set(fence_idx)

# ========== TOC：扫 h2（跳过文档自带目录章节）==========
toc_items, used_ids = [], set()
def in_fence(lineno):
    return any(a <= lineno <= b for a, b in fence_pairs)
for i, l in enumerate(lines):
    if l.startswith('## ') and not in_fence(i):
        title = l[3:].strip()
        if title == '目录':
            continue
        toc_items.append((title, slugify(title, used_ids)))
used_ids.clear()

# ========== 主解析 ==========
body_parts, code_lines, code_lang = [], [], ''
table_lines, in_table = [], False
blockquote_lines, in_bq = [], False

def flush_code():
    global code_lines, code_lang
    if not code_lines:
        return
    if is_ascii_art(code_lines):
        body_parts.append(f'<pre class="dir-tree">{render_dir_tree(code_lines)}</pre>')
    else:
        body_parts.append(f'<div class="code-block"><span class="tag">{code_lang or "text"}</span>{highlight_code("\n".join(code_lines), code_lang)}</div>')
    code_lines, code_lang = [], ''

def flush_table():
    global table_lines
    if not table_lines:
        return
    rows = [[c.strip() for c in tl.strip().strip('|').split('|')] for tl in table_lines]
    filtered = [r for r in rows if not all(re.match(r'^:?-{2,}:?$', c) for c in r)]
    if not filtered:
        table_lines = []; return
    body_parts.append('<table><thead><tr>' + ''.join(f'<th>{inline_md(c)}</th>' for c in filtered[0]) + '</tr></thead><tbody>'
        + ''.join('<tr>' + ''.join(f'<td>{inline_md(c)}</td>' for c in r) + '</tr>' for r in filtered[1:])
        + '</tbody></table>')
    table_lines = []

def flush_blockquote():
    global blockquote_lines
    if not blockquote_lines:
        return
    text = ' '.join(blockquote_lines)
    cls, cls_name = 'callout', ''
    if '⚠️' in text or '风险' in text[:20]:
        cls, cls_name = 'callout callout-warn', '⚠️ 注意'
    elif '❌' in text or '不推荐' in text:
        cls, cls_name = 'callout callout-danger', '🚫 禁止'
    elif '✅' in text or '完成' in text[:30]:
        cls, cls_name = 'callout callout-success', '✅ 完成'
    elif '💡' in text or '实践建议' in text[:30]:
        cls, cls_name = 'callout', '💡 提示'
    clean = re.sub(r'^[> ]+', '', text).strip()
    clean = re.sub(r'^[⚠️❌✅💡🚫>]+\s*', '', clean).strip()
    body_parts.append(f'<div class="{cls}"><div class="callout-title">{cls_name}</div>{inline_md(clean)}</div>')
    blockquote_lines = []

i = 0
while i < n:
    l, stripped = lines[i], lines[i].strip()
    # 代码块：按 fence_pairs 精确跳转
    if i in fence_line_set:
        for a, b in fence_pairs:
            if i == a:
                code_lang = lines[i][3:].strip()
                code_lines = [lines[j].rstrip('\n') for j in range(a+1, b)]
                flush_code()
                i = b + 1
                break
            elif i == b:
                i += 1; break
        else:
            i += 1
        continue
    # 表格
    if stripped.startswith('|') and '|' in stripped[1:]:
        if not in_table:
            in_table, table_lines = True, []
        table_lines.append(stripped); i += 1; continue
    elif in_table:
        in_table = False; flush_table()
    # 引用
    if stripped.startswith('>'):
        if not in_bq:
            in_bq, blockquote_lines = True, []
        blockquote_lines.append(stripped[1:].strip()); i += 1; continue
    elif in_bq:
        in_bq = False; flush_blockquote()
    if not stripped:
        i += 1; continue
    # 标题
    if stripped.startswith('#### '):
        t, a = stripped[5:].strip(), slugify(stripped[5:].strip(), used_ids)
        body_parts.append(f'<h4 id="{a}">{inline_md(t)}</h4>'); i += 1; continue
    if stripped.startswith('### '):
        t, a = stripped[4:].strip(), slugify(stripped[4:].strip(), used_ids)
        body_parts.append(f'<h3 id="{a}">{inline_md(t)}</h3>'); i += 1; continue
    if stripped.startswith('## '):
        t = stripped[3:].strip()
        if t == '目录':  # 跳过文档自带目录（含内容）
            i += 1
            while i < n and not lines[i].strip().startswith('## '):
                i += 1
            continue
        a = slugify(t, used_ids)
        body_parts.append(f'<h2 id="{a}">{inline_md(t)}</h2>'); i += 1; continue
    if stripped.startswith('# '):
        i += 1; continue
    # 列表
    if re.match(r'^[-*]\s+', stripped):
        items = []
        while i < n and re.match(r'^[-*]\s+', lines[i].strip()):
            items.append(inline_md(re.sub(r'^[-*]\s+', '', lines[i].strip()))); i += 1
        body_parts.append('<ul>' + ''.join(f'<li>{it}</li>' for it in items) + '</ul>'); continue
    if re.match(r'^\d+\.\s+', stripped):
        items = []
        while i < n and re.match(r'^\d+\.\s+', lines[i].strip()):
            items.append(inline_md(re.sub(r'^\d+\.\s+', '', lines[i].strip()))); i += 1
        body_parts.append('<ol>' + ''.join(f'<li>{it}</li>' for it in items) + '</ol>'); continue
    if stripped in ('---', '***', '___'):
        body_parts.append('<hr>'); i += 1; continue
    # 段落
    para = []
    while i < n:
        sl = lines[i].strip()
        if not sl or sl.startswith('```') or sl.startswith('#') or sl.startswith('|') or sl.startswith('>') or re.match(r'^[-*]\s+', sl) or re.match(r'^\d+\.\s+', sl) or sl in ('---', '***', '___'):
            break
        para.append(sl); i += 1
    if para:
        body_parts.append(f'<p>{inline_md(" ".join(para))}</p>')
    i += 1

if in_table: flush_table()
if in_bq: flush_blockquote()

toc_html = '<div class="toc"><h3>📑 目录导航</h3><ol>' + ''.join(
    f'<li><a href="#{a}">{esc(t)}</a></li>' for t, a in toc_items) + '</ol></div>'

# CSS：从 qwen2.5_lora_finetune_plan.html 的 <style> 复制（组件：toc/card/code-block/dir-tree/callout/badge/steps）
CSS = '''/* 复制 qwen2.5_lora_finetune_plan.html 的 style 块 */'''

html_doc = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>技术方案</title>
<style>{CSS}</style>
</head>
<body>
<div class="container">
<header>
  <h1>技术方案</h1>
  <div class="subtitle">来源: {MD_PATH.split('/')[-1]}</div>
  <div class="meta"><span>📅 2026</span></div>
</header>
{toc_html}
{chr(10).join(body_parts)}
<div class="footer">Generated from markdown</div>
</div>
</body>
</html>'''

with open(HTML_PATH, 'w', encoding='utf-8') as f:
    f.write(html_doc)
print(f"✅ 生成完成: {HTML_PATH} ({len(html_doc):,} 字节, TOC {len(toc_items)} 条)")
