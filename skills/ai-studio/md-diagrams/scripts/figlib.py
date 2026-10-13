#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""figlib — 内联 SVG 图元助手（继承 ai-studio 既有 gen_figures_vNNN.py 约定）

约定（勿改，改了要与 md-to-styled-html 同步）：
  配色 #e8eefc/#1a56db/#1e3a8a 主色 + #f8faff/#93b4f5 次级 + #6b7280 旁注
  语义色 #16a34a 绿 / #dc2626 红 / #d97706 琥珀 / #7c3aed 紫
  SVG 根带 role="img"、font-family；**必须含白底 rect**（PNG 兜底/打印/墨迹自检需要）
  宽度自检：所有文字经 tw() 估宽，超框写入 WARNS（生成期即报，不做事后补）

用法：
  import figlib as F
  body = F.box(...) + F.arrow(...) + F.elbl(...)
  svg = F.wrap(w, h, body)
  F.report()   # 打印宽度自检结果
"""
import html

FF = "'PingFang SC','Microsoft YaHei','Noto Sans CJK SC',sans-serif"
MONO = "'SF Mono','JetBrains Mono',Consolas,monospace"

C = dict(
    blue_d='#1e3a8a', blue='#1a56db', blue_l='#e8eefc', blue_m='#93b4f5', sub='#f8faff',
    ink='#1e293b', mut='#64748b', note='#6b7280', line='#cbd5e1', bg='#ffffff', group='#f8fafc',
    green='#16a34a', green_l='#f0fdf4', red='#dc2626', red_l='#fef2f2',
    amber='#d97706', amber_l='#fef3c7', purple='#7c3aed', purple_l='#ede9fe',
    ink_green='#065f46', ink_amber='#92400e', ink_purple='#5b21b6',
)
WARNS = []


def esc(t):
    return html.escape(str(t), quote=True)


def tw(t, fs):
    """估宽：CJK/全宽按 fs，其余按 0.58*fs（与既有 gen_figures 一致）"""
    w = 0.0
    for c in str(t):
        o = ord(c)
        full = (0x2E80 <= o <= 0x9FFF or 0x3000 <= o <= 0x303F
                or 0xFF00 <= o <= 0xFFEF or c in '←→↕⇒⊑—…├└│┌┐┘┤┬┴┼▼▲◀▶')
        w += fs if full else 0.58 * fs
    return w


def fit(tag, t, fs, avail):
    w = tw(t, fs)
    if w > avail:
        WARNS.append(f'{tag}: "{t}" 估宽{w:.0f} > 可用{avail:.0f}')
    return w


def report():
    if WARNS:
        print('宽度自检：%d 处告警' % len(WARNS))
        for w in WARNS:
            print('  !', w)
    else:
        print('宽度自检：全部通过 ✅')
    return not WARNS


def text(x, y, t, fs=12, fill=None, anchor='middle', bold=False, mono=False, italic=False):
    fill = fill or C['ink']
    fam = f' font-family="{MONO}"' if mono else ''
    w = ' font-weight="600"' if bold else ''
    s = ' font-style="italic"' if italic else ''
    return (f'<text x="{x}" y="{y+fs*0.35:.1f}" font-size="{fs}" fill="{fill}" '
            f'text-anchor="{anchor}"{fam}{w}{s}>{esc(t)}</text>')


def box(x, y, w, h, lines, fs=13, fill=None, stroke=None, dash=False, bold=True, rx=8):
    fill = fill or C['blue_l']; stroke = stroke or C['blue']
    d = ' stroke-dasharray="6 4"' if dash else ''
    s = (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" '
         f'stroke="{stroke}"{d}/>')
    n = len(lines)
    for i, t in enumerate(lines):
        ty = y + h / 2 + (i - (n - 1) / 2) * (fs + 4) - fs * 0.35
        f = fs if (i == 0 or n == 1) else fs - 1
        fit(f'box@({x:.0f},{y:.0f})', t, f, w - 12)
        s += text(x + w / 2, ty, t, f, C['blue_d'], bold=(bold and i == 0))
    return s


def rrect(x, y, w, h, fill=None, stroke=None, sw=1.2, rx=8, dash=None):
    fill = fill if fill is not None else C['bg']
    stroke = stroke or C['line']
    d = f' stroke-dasharray="{dash}"' if dash else ''
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="{sw}"{d}/>')


def arrow(x1, y1, x2, y2, dash=False, color=None, marker='ar'):
    color = color or C['blue']
    d = ' stroke-dasharray="6 4"' if dash else ''
    return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" '
            f'stroke-width="1.5"{d} marker-end="url(#{marker})"/>')


def path(dstr, dash=False, both=False, color=None, marker='ar'):
    color = color or C['blue']
    d = ' stroke-dasharray="6 4"' if dash else ''
    m2 = f' marker-end="url(#{marker})"'
    m1 = f' marker-start="url(#{marker})"' if both else ''
    return f'<path d="{dstr}" fill="none" stroke="{color}" stroke-width="1.5"{d}{m1}{m2}/>'


def elbl(x, y, t, fs=11, fill=None, anchor='middle', italic=False, mono=False):
    fit('elbl', t, fs, 920)
    return text(x, y, t, fs, fill or C['mut'], anchor, italic=italic, mono=mono)


def chip(x, y, t, fs=10.5, fill=None, stroke=None, tcol=None, pad=13, h=22):
    """小标签胶囊（图例/角标）。返回 (svg, width)"""
    fill = fill or C['blue_l']; stroke = stroke or C['blue_m']; tcol = tcol or C['blue_d']
    w = tw(t, fs) + 2 * pad
    s = (f'<rect x="{x}" y="{y}" width="{w:.0f}" height="{h}" rx="{h/2}" fill="{fill}" '
         f'stroke="{stroke}"/>')
    s += text(x + w / 2, y + (h - fs) / 2 - 1, t, fs, tcol, bold=True)
    return s, w


DEFS = (
    '<defs>'
    '<marker id="ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7.5" markerHeight="7.5" '
    f'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{C["blue"]}"/></marker>'
    '<marker id="arg" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7.5" markerHeight="7.5" '
    f'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{C["green"]}"/></marker>'
    '<marker id="arm" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7.5" markerHeight="7.5" '
    f'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{C["mut"]}"/></marker>'
    '<marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7.5" markerHeight="7.5" '
    f'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{C["red"]}"/></marker>'
    '</defs>')


def wrap(w, h, body):
    """SVG 根：白底 + viewBox + role=img + font-family。白底 rect 必须在最底层。"""
    bg = f'<rect x="0" y="0" width="{w}" height="{h}" fill="{C["bg"]}"/>'
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
            f'width="{w}" height="{h}" style="font-family:{FF}" role="img" '
            f'aria-label="diagram">\n{DEFS}\n{bg}\n{body}\n</svg>\n')


def save(path, w, h, body):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(wrap(w, h, body))
    import os
    return os.path.getsize(path)
