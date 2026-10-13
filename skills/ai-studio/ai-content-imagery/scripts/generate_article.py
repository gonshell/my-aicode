#!/usr/bin/env python3
"""
Markdown → 文章 HTML 生成器
用于将 Markdown 格式的文章转换成美观的 HTML 页面
支持：标题、段落、列表、表格、引用、代码块、加粗、斜体、行内代码

用法：
  python3 generate_article.py input.md output.html --title "文章标题" --subtitle "副标题" --theme tech-dark

依赖：
  - 系统 Chromium（用于截图）：apt install chromium
  - 中文字体：文泉驿正黑 / Noto Sans CJK / PingFang SC
"""

import re
import html as html_mod
import argparse
import sys
import os

def md_to_html(md_text, div_table=False):
    """Markdown 转 HTML 正文（不含 head/body 包装）
    div_table=True 时表格用 flex div 布局（公众号编辑器兼容）
    """
    lines = md_text.split('\n')
    html_parts = []
    in_list = False  # False / 'ul' / 'ol'
    in_blockquote = False
    in_code = False
    
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # 代码块
        if stripped.startswith('```'):
            if in_code:
                html_parts.append('</code></pre>')
                in_code = False
            else:
                html_parts.append('<pre><code>')
                in_code = True
            i += 1
            continue
        
        if in_code:
            html_parts.append(html_mod.escape(line))
            i += 1
            continue
        
        # 引用块
        if stripped.startswith('> '):
            if not in_blockquote:
                html_parts.append('<blockquote>')
                in_blockquote = True
            content = stripped[2:]
            content = apply_inline_format(content)
            # 组件化卡片语法检测（公众号主题用）
            # > 💡 导读：xxx  → guide-card
            # > 🏆 标题：xxx  → prize-card (信息卡片)
            # > ⚠️ 标题：xxx  → warning-card
            # > ✓ 标题：xxx   → quality-card
            card_match = re.match(
                r'^<(?:strong|em)>([💡🏆⚠️⚠✅✓💎🎯📌])\s*([^：:]+)[：:]</(?:strong|em)>\s*(.*)',
                content
            )
            # 也支持不带 strong 的写法：> 💡 导读：xxx
            if not card_match:
                card_match = re.match(
                    r'^([💡🏆⚠️⚠✅✓💎🎯📌])\s*([^：:]+)[：:]\s*(.*)',
                    stripped[2:]
                )
                if card_match:
                    card_title = card_match.group(2)
                    card_body = apply_inline_format(card_match.group(3))
                else:
                    card_title = None
                    card_body = None
            else:
                card_title = card_match.group(2)
                card_body = card_match.group(3)
            
            if card_title and card_body is not None:
                emoji = card_match.group(1)
                card_type = detect_card_type(emoji)
                html_parts.append(
                    f'<div class="card card-{card_type}">'
                    f'<div class="card-title">{emoji} {card_title}</div>'
                    f'<div class="card-body">{card_body}</div>'
                    f'</div>'
                )
            # 重点卡片语法：> **要点：** / > **关键：** 开头（旧兼容）
            elif re.match(r'^<strong>(要点|关键|结论|注意)：?</strong>', content):
                content = re.sub(r'^<strong>(要点|关键|结论|注意)：?</strong>', r'<strong class="callout-label">\1</strong>', content)
                html_parts.append(f'<p class="callout">{content}</p>')
            else:
                html_parts.append(f'<p>{content}</p>')
            i += 1
            continue
        elif in_blockquote:
            html_parts.append('</blockquote>')
            in_blockquote = False
        
        # 空行
        if not stripped:
            if in_list:
                html_parts.append('</ul>' if in_list == 'ul' else '</ol>')
                in_list = False
            i += 1
            continue
        
        # 标题
        heading_match = re.match(r'^(#{1,6})\s+(.+)', stripped)
        if heading_match:
            if in_list:
                html_parts.append('</ul>' if in_list == 'ul' else '</ol>')
                in_list = False
            level = len(heading_match.group(1))
            # 跳过第一个 H1（header 已展示标题）
            if level == 1 and not html_parts:
                i += 1
                continue
            text = apply_inline_format(heading_match.group(2))
            html_parts.append(f'<h{level}>{text}</h{level}>')
            i += 1
            continue
        
        # 分隔线
        if stripped == '---':
            html_parts.append('<hr>')
            i += 1
            continue
        
        # 有序列表
        ol_match = re.match(r'^(\d+)\.\s+', stripped)
        if ol_match:
            if in_list == 'ul':
                html_parts.append('</ul>')
                in_list = False
            if not in_list:
                html_parts.append('<ol>')
                in_list = 'ol'
            text = re.sub(r'^\d+\.\s+', '', stripped)
            text = apply_inline_format(text)
            html_parts.append(f'<li>{text}</li>')
            i += 1
            continue
        
        # 无序列表（含任务列表）
        if re.match(r'^[-*]\s+', stripped):
            if in_list == 'ol':
                html_parts.append('</ol>')
                in_list = False
            if not in_list:
                html_parts.append('<ul class="task-list">')
                in_list = 'ul'
            text = re.sub(r'^[-*]\s+', '', stripped)
            # 任务列表：- [ ] 未完成 / - [x] 已完成
            task_match = re.match(r'^\[([ x])\]\s+(.+)', text)
            if task_match:
                checked = ' checked' if task_match.group(1) == 'x' else ''
                content = apply_inline_format(task_match.group(2))
                html_parts.append(f'<li class="task-item"><input type="checkbox" disabled{checked}> {content}</li>')
            else:
                text = apply_inline_format(text)
                html_parts.append(f'<li>{text}</li>')
            i += 1
            continue
        
        # 表格行
        if '|' in stripped and stripped.startswith('|') and stripped.endswith('|'):
            if in_list:
                html_parts.append('</ul>' if in_list == 'ul' else '</ol>')
                in_list = False
            table_rows = []
            while i < len(lines) and '|' in lines[i].strip() and lines[i].strip().startswith('|'):
                table_rows.append(lines[i].strip())
                i += 1
            
            if len(table_rows) >= 2:
                html_parts.append(parse_table(table_rows, div_table=div_table))
            continue
        
        # 普通段落
        if in_list:
            html_parts.append('</ul>' if in_list == 'ul' else '</ol>')
            in_list = False
        
        text = apply_inline_format(stripped)
        html_parts.append(f'<p>{text}</p>')
        i += 1
    
    if in_list:
        html_parts.append('</ul>' if in_list == 'ul' else '</ol>')
    if in_blockquote:
        html_parts.append('</blockquote>')
    if in_code:
        html_parts.append('</code></pre>')
    
    return '\n'.join(html_parts)


def detect_card_type(emoji):
    """根据 emoji 判断卡片类型，返回 CSS class 后缀"""
    mapping = {
        '💡': 'guide',
        '📌': 'guide',
        '🎯': 'guide',
        '🏆': 'prize',
        '💎': 'prize',
        '⚠️': 'warning',
        '⚠': 'warning',
        '✅': 'quality',
        '✓': 'quality',
    }
    return mapping.get(emoji, 'default')


def apply_inline_format(text):
    """应用行内格式：加粗、斜体、行内代码"""
    # 先处理行内代码（避免被其他格式影响）
    code_parts = []
    def save_code(m):
        code_parts.append(m.group(1))
        return f'__CODE_{len(code_parts)-1}__'
    text = re.sub(r'`([^`]+)`', save_code, text)
    
    # 加粗
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    # 斜体
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    
    # 恢复行内代码
    for i, code in enumerate(code_parts):
        text = text.replace(f'__CODE_{i}__', f'<code>{code}</code>')
    
    return text


def parse_table(rows, div_table=False):
    """解析 Markdown 表格。div_table=True 时用 flex div 布局（公众号兼容）"""
    # 表头
    headers = [c.strip() for c in rows[0].strip('|').split('|')]
    # 跳过分隔行
    start_idx = 2 if re.match(r'^[\s|:\-]+$', rows[1]) else 1
    body_rows = []
    for row in rows[start_idx:]:
        cells = [c.strip() for c in row.strip('|').split('|')]
        body_rows.append([apply_inline_format(c) for c in cells])
    
    if div_table:
        return build_div_table(headers, body_rows)
    
    # 原生 table
    html = ['<table>']
    html.append('<thead><tr>')
    for h in headers:
        html.append(f'<th>{apply_inline_format(h)}</th>')
    html.append('</tr></thead>')
    html.append('<tbody>')
    for row in body_rows:
        html.append('<tr>')
        for c in row:
            html.append(f'<td>{c}</td>')
        html.append('</tr>')
    html.append('</tbody></table>')
    return '\n'.join(html)


def build_div_table(headers, body_rows):
    """用 flex div 构建表格（公众号编辑器兼容性好）"""
    col_count = len(headers)
    # 列宽分配：根据列数和内容长度简单估算
    # 第一列稍窄，后面均分
    flex_ratios = []
    for idx in range(col_count):
        if col_count == 2:
            flex_ratios = [1, 2.5]
        elif col_count == 3:
            flex_ratios = [1, 1, 1.5]
        else:
            flex_ratios = [1] * col_count
    
    html_parts = ['<div class="div-table">']
    
    # 表头行
    html_parts.append('<div class="div-table-row div-table-header">')
    for idx, h in enumerate(headers):
        flex = flex_ratios[idx] if idx < len(flex_ratios) else 1
        html_parts.append(f'<div class="div-table-cell" style="flex:{flex}">{apply_inline_format(h)}</div>')
    html_parts.append('</div>')
    
    # 数据行
    for i, row in enumerate(body_rows):
        bg_class = ' div-table-row-alt' if i % 2 == 1 else ''
        html_parts.append(f'<div class="div-table-row{bg_class}">')
        for idx, cell in enumerate(row):
            flex = flex_ratios[idx] if idx < len(flex_ratios) else 1
            html_parts.append(f'<div class="div-table-cell" style="flex:{flex}">{cell}</div>')
        html_parts.append('</div>')
    
    html_parts.append('</div>')
    return '\n'.join(html_parts)


THEMES = {
    "tech-dark": {
        "name": "科技深蓝",
        "bg": "linear-gradient(180deg, #0f172a 0%, #1e293b 100%)",
        "text": "#f1f5f9",
        "text-secondary": "#94a3b8",
        "accent": "#3b82f6",
        "accent-light": "#60a5fa",
        "border": "rgba(59, 130, 246, 0.2)",
        "blockquote-bg": "rgba(59, 130, 246, 0.1)",
        "blockquote-border": "#3b82f6",
        "code-bg": "rgba(0, 0, 0, 0.3)",
        "table-border": "rgba(148, 163, 184, 0.2)",
        "table-header": "rgba(59, 130, 246, 0.2)",
    },
    "light-minimal": {
        "name": "简约白底",
        "bg": "#ffffff",
        "text": "#1f2937",
        "text-secondary": "#6b7280",
        "accent": "#2563eb",
        "accent-light": "#3b82f6",
        "border": "#e5e7eb",
        "blockquote-bg": "#f3f4f6",
        "blockquote-border": "#2563eb",
        "code-bg": "#f3f4f6",
        "table-border": "#e5e7eb",
        "table-header": "#f9fafb",
    },
    "warm-dark": {
        "name": "暖色暗夜",
        "bg": "linear-gradient(180deg, #1c1917 0%, #292524 100%)",
        "text": "#fafaf9",
        "text-secondary": "#a8a29e",
        "accent": "#f97316",
        "accent-light": "#fb923c",
        "border": "rgba(249, 115, 22, 0.2)",
        "blockquote-bg": "rgba(249, 115, 22, 0.1)",
        "blockquote-border": "#f97316",
        "code-bg": "rgba(0, 0, 0, 0.3)",
        "table-border": "rgba(168, 162, 158, 0.2)",
        "table-header": "rgba(249, 115, 22, 0.15)",
    },
    "toutiao-dark": {
        "name": "头条深色",
        "desc": "适合手机端信息流阅读，段落间距大，引用块醒目，节奏轻快",
        "bg": "#0f172a",
        "text": "#e2e8f0",
        "text-secondary": "#64748b",
        "accent": "#3b82f6",
        "accent-light": "#60a5fa",
        "border": "rgba(59, 130, 246, 0.15)",
        "blockquote-bg": "rgba(59, 130, 246, 0.15)",
        "blockquote-border": "#3b82f6",
        "code-bg": "rgba(0, 0, 0, 0.3)",
        "table-border": "rgba(148, 163, 184, 0.15)",
        "table-header": "rgba(59, 130, 246, 0.15)",
        "layout": {
            "content_width": "680px",
            "body_font_size": "16px",
            "line_height": "1.9",
            "paragraph_margin": "24px",
            "h2_font_size": "22px",
            "h2_margin_top": "40px",
            "h2_border_left": "3px",
            "header_padding_bottom": "28px",
            "header_margin_bottom": "36px",
            "blockquote_border_left": "4px",
            "blockquote_padding": "18px 22px",
            "container_padding": "40px 24px 60px",
            "title_font_size": "26px",
        },
    },
    "plain": {
        "name": "朴素发布版",
        "desc": "白底黑字，无装饰，复制粘贴到各平台后台不走样。适合头条/公众号正文发布。",
        "bg": "#ffffff",
        "text": "#1a1a1a",
        "text-secondary": "#666666",
        "accent": "#1a1a1a",
        "accent-light": "#333333",
        "border": "#e5e5e5",
        "blockquote-bg": "#f9f9f9",
        "blockquote-border": "#d4d4d4",
        "code-bg": "#f5f5f5",
        "table-border": "#e5e5e5",
        "table-header": "#f9f9f9",
        "layout": {
            "content_width": "100%",
            "body_font_size": "17px",
            "line_height": "1.8",
            "paragraph_margin": "20px",
            "h2_font_size": "22px",
            "h2_margin_top": "36px",
            "h2_border_left": "0px",
            "header_padding_bottom": "20px",
            "header_margin_bottom": "28px",
            "blockquote_border_left": "3px",
            "blockquote_padding": "12px 16px",
            "container_padding": "30px 24px 50px",
            "title_font_size": "26px",
        },
    },
    "wechat-light": {
        "name": "微信公众号",
        "desc": "浅色白底+微信绿，适合手机端公众号阅读。首行缩进、卡片组件、div 表格（公众号编辑器兼容）。",
        "bg": "#ffffff",
        "text": "#333333",
        "text-secondary": "#999999",
        "accent": "#07c160",
        "accent-light": "#0f766e",
        "accent-warm": "#f59e0b",
        "accent-info": "#0ea5e9",
        "border": "#eeeeee",
        "blockquote-bg": "#f0fdf4",
        "blockquote-border": "#07c160",
        "code-bg": "#f1f5f9",
        "code-text": "#e11d48",
        "table-border": "#e2e8f0",
        "table-header": "#f1f5f9",
        "layout": {
            "content_width": "677px",
            "body_font_size": "16px",
            "line_height": "2",
            "paragraph_margin": "16px",
            "paragraph_text_indent": "2em",
            "h2_font_size": "20px",
            "h2_margin_top": "36px",
            "h2_border_left": "4px",
            "h3_style": "dashed",
            "header_padding_bottom": "30px",
            "header_margin_bottom": "32px",
            "blockquote_border_left": "4px",
            "blockquote_padding": "14px 18px",
            "container_padding": "0 20px 40px",
            "title_font_size": "24px",
            "hero_tag": True,
            "guide_card": True,
            "toc_card": True,
            "quality_note": True,
            "div_table": True,
        },
    },
}


def build_toc(body_html):
    """从 H2 标题生成目录导航 HTML"""
    toc_items = []
    for m in re.finditer(r'<h2[^>]*>(.*?)</h2>', body_html):
        text = re.sub(r'<[^>]+>', '', m.group(1))
        toc_items.append(f'<li>{html_mod.escape(text)}</li>')
    if not toc_items:
        return ''
    items_html = '\n'.join(toc_items)
    return f'''<nav class="toc">
  <div class="toc-title">目录</div>
  <ul>{items_html}</ul>
</nav>'''


def wrap_article(content_html, title, subtitle="", theme="tech-dark"):
    """包装成完整的 HTML 页面"""
    t = THEMES.get(theme, THEMES["tech-dark"])
    toc_html = build_toc(content_html)

    # 布局参数：有 layout 配置就用主题的，没有就用默认值（兼容旧主题）
    layout = t.get("layout", {})
    L = {
        "content_width": layout.get("content_width", "760px"),
        "body_font_size": layout.get("body_font_size", "17px"),
        "line_height": layout.get("line_height", "1.8"),
        "paragraph_margin": layout.get("paragraph_margin", "20px"),
        "paragraph_text_indent": layout.get("paragraph_text_indent", "0"),
        "h2_font_size": layout.get("h2_font_size", "24px"),
        "h2_margin_top": layout.get("h2_margin_top", "48px"),
        "h2_border_left": layout.get("h2_border_left", "4px"),
        "h3_style": layout.get("h3_style", "none"),
        "header_padding_bottom": layout.get("header_padding_bottom", "40px"),
        "header_margin_bottom": layout.get("header_margin_bottom", "50px"),
        "blockquote_border_left": layout.get("blockquote_border_left", "4px"),
        "blockquote_padding": layout.get("blockquote_padding", "16px 24px"),
        "container_padding": layout.get("container_padding", "60px 40px 80px"),
        "title_font_size": layout.get("title_font_size", "32px"),
        "hero_tag": layout.get("hero_tag", False),
        "guide_card": layout.get("guide_card", False),
        "toc_card": layout.get("toc_card", False),
        "quality_note": layout.get("quality_note", False),
        "div_table": layout.get("div_table", False),
    }
    
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html_mod.escape(title)}</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  
  body {{
    font-family: "PingFang SC", "Microsoft YaHei", "Noto Sans CJK SC", "WenQuanYi Zen Hei", sans-serif;
    background: {t["bg"]};
    color: {t["text"]};
    line-height: {L["line_height"]};
    min-height: 100vh;
    -webkit-font-smoothing: antialiased;
  }}
  
  .article-container {{
    max-width: {L["content_width"]};
    margin: 0 auto;
    padding: {L["container_padding"]};
  }}
  
  .article-header {{
    margin-bottom: {L["header_margin_bottom"]};
    padding-bottom: {L["header_padding_bottom"]};
    border-bottom: 1px solid {t["border"]};
  }}
  
  .article-header h1 {{
    font-size: {L["title_font_size"]};
    font-weight: 800;
    line-height: 1.4;
    margin-bottom: 16px;
    background: linear-gradient(135deg, {t["accent-light"]}, {t["accent"]});
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }}
  
  .article-meta {{
    font-size: 14px;
    color: {t["text-secondary"]};
    display: flex;
    gap: 20px;
    flex-wrap: wrap;
  }}
  
  .article-meta span::before {{
    content: "·";
    margin-right: 8px;
    color: {t["accent"]};
  }}
  
  .article-meta span:first-child::before {{
    content: "";
    margin: 0;
  }}
  
  /* 目录导航 */
  .toc {{
    background: {t["blockquote-bg"]};
    border: 1px solid {t["border"]};
    border-radius: 12px;
    padding: 24px 28px;
    margin-bottom: 48px;
  }}
  
  .toc-title {{
    font-size: 15px;
    font-weight: 700;
    color: {t["accent-light"]};
    margin-bottom: 12px;
    letter-spacing: 0.5px;
  }}
  
  .toc ul {{
    list-style: none;
    padding: 0;
    margin: 0;
  }}
  
  .toc li {{
    padding: 6px 0;
    color: {t["text-secondary"]};
    font-size: 15px;
    border-bottom: 1px dashed {t["border"]};
  }}
  
  .toc li:last-child {{
    border-bottom: none;
  }}
  
  .toc li:hover {{
    color: {t["accent-light"]};
  }}
  
  .article-body {{
    font-size: {L["body_font_size"]};
  }}
  
  .article-body h1 {{
    font-size: 28px;
    font-weight: 800;
    margin-top: 48px;
    margin-bottom: 24px;
    line-height: 1.4;
  }}
  
  .article-body h2 {{
    font-size: {L["h2_font_size"]};
    font-weight: 700;
    margin-top: {L["h2_margin_top"]};
    margin-bottom: 20px;
    padding-left: 16px;
    border-left: {L["h2_border_left"]} solid {t["accent"]};
    line-height: 1.4;
  }}
  
  .article-body h3 {{
    font-size: 20px;
    font-weight: 700;
    margin-top: 36px;
    margin-bottom: 16px;
    color: {t["accent-light"]};
  }}
  
  /* H3 虚线底部分隔（公众号主题用） */
  .article-body h3 {{
    padding-bottom: {('6px' if L["h3_style"] == "dashed" else '0')};
    border-bottom: {('1px dashed ' + t["border"]) if L["h3_style"] == "dashed" else 'none'};
  }}
  
  .article-body h4 {{
    font-size: 18px;
    font-weight: 600;
    margin-top: 28px;
    margin-bottom: 12px;
  }}
  
  .article-body p {{
    margin-bottom: {L["paragraph_margin"]};
    color: {t["text"]};
    text-indent: {L["paragraph_text_indent"]};
  }}
  
  .article-body strong {{
    color: {t["accent-light"]};
    font-weight: 700;
  }}
  
  .article-body em {{
    color: {t["text-secondary"]};
    font-style: normal;
  }}
  
  .article-body code {{
    background: {t["code-bg"]};
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 0.9em;
    font-family: "SF Mono", "Fira Code", Consolas, monospace;
    color: {t["accent-light"]};
  }}
  
  .article-body pre {{
    background: {t["code-bg"]};
    padding: 20px;
    border-radius: 8px;
    overflow-x: auto;
    margin: 20px 0;
  }}
  
  .article-body pre code {{
    padding: 0;
    background: none;
    font-size: 14px;
    line-height: 1.6;
  }}
  
  .article-body blockquote {{
    background: {t["blockquote-bg"]};
    border-left: {L["blockquote_border_left"]} solid {t["blockquote-border"]};
    padding: {L["blockquote_padding"]};
    margin: 24px 0;
    border-radius: 0 8px 8px 0;
  }}
  
  .article-body blockquote p {{
    margin-bottom: 12px;
    color: {t["text"]};
  }}
  
  .article-body blockquote p:last-child {{
    margin-bottom: 0;
  }}
  
  /* 重点卡片样式 */
  .article-body p.callout {{
    background: {t["blockquote-bg"]};
    border-left: 4px solid {t["accent"]};
    padding: 16px 24px;
    margin: 24px 0;
    border-radius: 0 8px 8px 0;
    font-weight: 500;
  }}
  
  .article-body p.callout .callout-label {{
    color: {t["accent-light"]};
    margin-right: 4px;
  }}
  
  .article-body ul, .article-body ol {{
    margin: 20px 0;
    padding-left: 24px;
  }}
  
  .article-body li {{
    margin-bottom: 10px;
  }}
  
  .article-body ul li::marker {{
    color: {t["accent"]};
  }}
  
  .article-body ol li::marker {{
    color: {t["accent"]};
    font-weight: 700;
  }}

  /* 任务列表 */
  .article-body ul.task-list {{
    list-style: none;
    padding-left: 0;
  }}

  .article-body .task-item {{
    display: flex;
    align-items: flex-start;
    gap: 10px;
    margin-bottom: 10px;
  }}

  .article-body .task-item input[type="checkbox"] {{
    margin-top: 5px;
    flex-shrink: 0;
    width: 16px;
    height: 16px;
    accent-color: {t["accent"]};
  }}

  .article-body table {{
    width: 100%;
    border-collapse: collapse;
    margin: 24px 0;
    font-size: 15px;
  }}
  
  .article-body th {{
    background: {t["table-header"]};
    padding: 12px 16px;
    text-align: left;
    font-weight: 700;
    border-bottom: 2px solid {t["border"]};
    color: {t["accent-light"]};
  }}
  
  .article-body td {{
    padding: 12px 16px;
    border-bottom: 1px solid {t["table-border"]};
    color: {t["text"]};
  }}
  
  .article-body tr:hover td {{
    background: rgba(59, 130, 246, 0.05);
  }}
  
  .article-body hr {{
    border: none;
    height: 1px;
    background: {t["border"]};
    margin: 40px 0;
  }}
  
  /* === 组件化卡片样式（公众号主题用）=== */
  .card {{
    border-radius: 8px;
    padding: 16px 20px;
    margin: 20px 0;
    line-height: 1.8;
  }}
  
  .card-title {{
    font-size: 14px;
    font-weight: 600;
    margin-bottom: 8px;
    letter-spacing: 0.3px;
  }}
  
  .card-body {{
    font-size: 15px;
    color: {t["text"]};
  }}
  
  .card-guide {{
    background: {t["blockquote-bg"]};
    border-left: 4px solid {t["accent"]};
    border-radius: 0 8px 8px 0;
  }}
  
  .card-guide .card-title {{
    color: {t["accent"]};
  }}
  
  .card-prize {{
    background: linear-gradient(135deg, rgba(7,193,96,0.06), rgba(14,165,233,0.06));
    border: 1px solid {t["border"]};
  }}
  
  .card-prize .card-title {{
    color: {t["accent"]};
    font-size: 16px;
  }}
  
  .card-warning {{
    background: #fffbeb;
    border: 1px solid #fde68a;
    border-left: 4px solid #f59e0b;
    border-radius: 0 8px 8px 0;
  }}
  
  .card-warning .card-title {{
    color: #d97706;
  }}
  
  .card-warning .card-body {{
    color: #78350f;
  }}
  
  .card-quality {{
    background: #f0fdf4;
    border: 1px solid #bbf7d0;
  }}
  
  .card-quality .card-title {{
    color: #059669;
  }}
  
  .card-quality .card-body {{
    color: #166534;
    font-size: 13.5px;
  }}
  
  .card-default {{
    background: {t["blockquote-bg"]};
    border: 1px solid {t["border"]};
  }}
  
  /* === Div 表格（公众号兼容）=== */
  .div-table {{
    margin: 18px 0 24px;
    font-size: 14px;
    border-radius: 6px;
    overflow: hidden;
  }}
  
  .div-table-row {{
    display: flex;
    border-left: 1px solid {t["table-border"]};
    border-right: 1px solid {t["table-border"]};
    border-bottom: 1px solid {t["table-border"]};
  }}
  
  .div-table-header {{
    background: {t["table-header"]};
    font-weight: 600;
    color: {t["text-secondary"]};
    font-size: 13px;
    letter-spacing: 0.3px;
    border-top: 1px solid {t["table-border"]};
  }}
  
  .div-table-row-alt {{
    background: #fafafa;
  }}
  
  .div-table-cell {{
    padding: 10px 12px;
    line-height: 1.6;
    color: {t["text"]};
    word-break: break-word;
  }}
  
  .div-table-header .div-table-cell {{
    color: {t["text-secondary"]};
  }}
  
  .article-body > p:first-of-type {{
    font-size: 19px;
    line-height: 1.9;
    color: {t["text"]};
  }}
  
  @media (max-width: 640px) {{
    .article-container {{
      padding: 30px 20px 50px;
    }}
    .article-header h1 {{
      font-size: 26px;
    }}
    .article-body {{
      font-size: 16px;
    }}
    .article-body h2 {{
      font-size: 20px;
    }}
    .article-body h3 {{
      font-size: 18px;
    }}
  }}
</style>
</head>
<body>
  <div class="article-container">
    <header class="article-header">
      <h1>{html_mod.escape(title)}</h1>
      {f'<div class="article-meta"><span>{html_mod.escape(subtitle)}</span></div>' if subtitle else ''}
    </header>
    {toc_html}
    <article class="article-body">
      {content_html}
    </article>
  </div>
</body>
</html>'''


def md_to_png(html_path, png_path, width=760, full_page=True):
    """用 Chromium headless 将 HTML 渲染成 PNG 长图"""
    import subprocess
    
    cmd = [
        "chromium",
        "--headless",
        "--disable-gpu",
        "--no-sandbox",
        f"--screenshot={png_path}",
        f"--window-size={width},1200",
        f"file://{os.path.abspath(html_path)}",
    ]
    
    if full_page:
        # Chromium headless 模式下 --screenshot 默认只截首屏
        # 需要用 --virtual-time-budget 等待加载，然后用 --full-page
        cmd.insert(2, "--full-page")
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        print(f"  截图失败: {result.stderr}", file=sys.stderr)
        return False
    return os.path.exists(png_path)


def main():
    parser = argparse.ArgumentParser(description='Markdown 文章 → HTML / PNG 生成器')
    parser.add_argument('input', help='输入 Markdown 文件路径')
    parser.add_argument('output', help='输出 HTML 文件路径')
    parser.add_argument('--title', help='文章标题（默认从 MD 中提取第一个 # 标题）')
    parser.add_argument('--subtitle', default='', help='副标题/元信息')
    parser.add_argument('--theme', default='tech-dark', 
                       choices=list(THEMES.keys()),
                       help=f'主题色（可选：{", ".join(THEMES.keys())}）')
    parser.add_argument('--png', action='store_true', help='同时生成 PNG 长图')
    parser.add_argument('--png-width', type=int, default=760, help='PNG 宽度（像素）')
    
    args = parser.parse_args()
    
    # 读取 Markdown
    with open(args.input, 'r', encoding='utf-8') as f:
        md_text = f.read()
    
    # 提取标题
    title = args.title
    if not title:
        for line in md_text.split('\n'):
            if line.startswith('# '):
                title = line[2:].strip()
                break
    if not title:
        title = os.path.basename(args.input)
    
    # 转换
    theme_config = THEMES.get(args.theme, THEMES["tech-dark"])
    div_table = theme_config.get("layout", {}).get("div_table", False)
    body_html = md_to_html(md_text, div_table=div_table)
    full_html = wrap_article(body_html, title, args.subtitle, args.theme)
    
    # 写入 HTML
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(full_html)
    
    print(f"✅ HTML 已生成: {args.output}")
    print(f"   标题: {title}")
    print(f"   主题: {THEMES[args.theme]['name']}")
    
    # 生成 PNG
    if args.png:
        png_path = os.path.splitext(args.output)[0] + '.png'
        print(f"\n生成 PNG 长图中...")
        if md_to_png(args.output, png_path, args.png_width):
            size_kb = os.path.getsize(png_path) / 1024
            print(f"✅ PNG 已生成: {png_path} ({size_kb:.0f} KB)")
        else:
            print("❌ PNG 生成失败")


if __name__ == '__main__':
    main()
