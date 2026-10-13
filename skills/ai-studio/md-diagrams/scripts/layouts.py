#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""layouts — 8 个版面原语（DSL → 内联 SVG 片段）

每个原语接收"数据 + 标题"，返回 (宽度, 高度, body)。渲染器只负责算坐标，
文字一律来自调用方传入的原文串，不生成/不改写文字。
"""
import figlib as F
from figlib import C, text, box, rrect, arrow, path, elbl, fit, tw

# ── 1. 纵向分层栈（L1–L5 / T1–T5）────────────────────────────
def stack(layers, title=None, w=1080):
    """layers: [(层名, 能力串, 包路径多行)]"""
    n = len(layers); lh = 92; gap = 34
    top = 70 if not title else 96
    h = top + n * lh + (n - 1) * gap + 36
    b = []; cx = w / 2; bw = 920; x = (w - bw) / 2
    if title:
        b.append(text(cx, 34, title, 14, C['note'], bold=True))
    for i, (name, caps, pkgs) in enumerate(layers):
        y = top + i * (lh + gap)
        fill, stroke, tc = ((C['blue_l'], C['blue'], C['blue_d']) if i % 2 == 0
                            else (C['group'], '#94a3b8', C['ink']))
        b.append(rrect(x, y, bw, lh, fill=fill, stroke=stroke, sw=1.4))
        fit('stack/name', name, 15, bw - 44)
        b.append(text(x + 22, y + 27, name, 15, tc, 'start', bold=True))
        if caps:
            fit('stack/caps', caps, 12.5, bw - 44)
            b.append(text(x + 22, y + 55, caps, 12.5, C['ink'], 'start'))
        if pkgs:
            fit('stack/pkg', pkgs, 11, bw - 44)
            b.append(text(x + 22, y + 77, pkgs, 11, C['mut'], 'start', mono=True))
        if i < n - 1:
            b.append(arrow(cx, y + lh + 3, cx, y + lh + gap - 3))
    return w, h, ''.join(b)


# ── 2. 依赖树（agent-loop → 三契约 → session → scope）──────────
def dep_tree(title=None, w=980, root=None, mids=None, sink=None, tail=None):
    root = root or ('agent-loop', '唯一包含具体循环逻辑的包', 'ctx.agentLoop')
    mids = mids or [('agent', '契约层', 'ctx.agents'), ('tools', '工具注册表', 'ctx.tools'),
                    ('system-prompt', '提示词组装', 'ctx.systemPrompt')]
    sink = sink or ('session', '唯一数据源', 'ctx.sessions')
    tail = tail or ('scope', '隔离作用域', '无 ctx key')
    b = []; cx = w / 2
    def node(cxx, y, cw, ch, t, s, ctx, fill, stroke, tc):
        x = cxx - cw / 2
        b.append(rrect(x, y, cw, ch, fill=fill, stroke=stroke))
        b.append(text(cxx, y + 22, t, 15, tc, bold=True, mono=True))
        if s: b.append(text(cxx, y + 43, s, 11.5, C['mut']))
        if ctx: b.append(text(cxx, y + 62, ctx, 11.5, C['ink'], mono=True))
    node(cx, 30, 240, 82, *root, C['blue_l'], C['blue'], C['blue_d'])
    y2 = 180; w3 = 190; gap = 40; total = 3 * w3 + 2 * gap; x0 = (w - total) / 2
    cxs = []
    for i, (t, s, ct) in enumerate(mids):
        cxx = x0 + w3 / 2 + i * (w3 + gap); cxs.append(cxx)
        node(cxx, y2, w3, 76, t, s, ct, C['group'], '#94a3b8', C['ink'])
        b.append(path(f'M{cx:.0f},112 V140 H{cxx:.0f} V{y2-2}'))
    ys = 330
    node(cx, ys, 240, 72, *sink, C['green_l'], C['green'], C['ink_green'])
    for cxx in cxs:
        b.append(path(f'M{cxx:.0f},{y2+76} V300 H{cx:.0f} V{ys-2}', color=C['mut'], marker='arm'))
    ysc = 470
    node(cx, ysc, 240, 72, *tail, C['amber_l'], C['amber'], C['ink_amber'])
    b.append(arrow(cx, ys + 72, cx, ysc - 2))
    b.append(text(cx + 66, 128, '依赖', 11, C['mut'], 'start'))
    return w, ysc + 122, ''.join(b)


# ── 3. 容器 + 注入子块（Context）─────────────────────────────
def container(title, head, rows, plugins, note=None, w=900):
    """rows: [(key, label)] 服务注入; plugins: [(名, inject 目标)]"""
    b = []; x, y, cw = 40, 30, w - 80; ch = 470
    b.append(rrect(x, y, cw, ch, fill='#fbfcfe', stroke=C['blue'], sw=1.6))
    b.append(f'<rect x="{x}" y="{y}" width="{cw}" height="46" rx="8" fill="{C["blue"]}"/>')
    b.append(text(x + 24, y + 28, head, 16, '#fff', 'start', bold=True))
    ry = y + 72
    for i, (k, v) in enumerate(rows):
        yy = ry + i * 52
        b.append(rrect(x + 30, yy, 200, 40, fill=C['blue_l'], stroke=C['blue_m']))
        b.append(text(x + 130, yy + 23, k, 13, C['blue_d'], bold=True, mono=True))
        b.append(arrow(x + 275, yy + 20, x + 330, yy + 20))
        b.append(rrect(x + 336, yy, 250, 40, fill='#fff', stroke=C['line']))
        b.append(text(x + 461, yy + 23, v, 13, C['ink']))
    ey = ry + len(rows) * 52 + 14
    b.append(rrect(x + 30, ey, cw - 60, 44, fill=C['amber_l'], stroke=C['amber']))
    b.append(text(x + cw / 2 - 30, ey + 26, '事件总线：emit / waterfall / parallel / serial',
                  13, C['ink_amber'], bold=True, mono=True))
    py = ey + 66; pw = (cw - 60 - 40) / 3
    for i, (nm, inj) in enumerate(plugins[:3]):
        px = x + 30 + i * (pw + 20)
        b.append(rrect(px, py, pw, 86, fill='#fff', stroke=C['purple'], sw=1.4))
        b.append(text(px + pw / 2, py + 24, nm, 14, C['purple'], bold=True))
        b.append(text(px + pw / 2, py + 50, 'inject:', 12, C['mut'], mono=True))
        b.append(text(px + pw / 2, py + 70, inj, 12.5, C['blue_d'], bold=True, mono=True))
    fy = py + 106
    b.append(rrect(x + 30, fy, cw - 60, 40, stroke=C['line'], dash='5 4'))
    b.append(text(x + cw / 2 - 30, fy + 24, note or 'effect() / on() 注册的副作用 → 卸载时自动撤销',
                  12.5, C['mut']))
    return w, ch + y + 10, ''.join(b)


# ── 4. 阶段流（编号步骤 / 事件块，主线箭头串联）────────────────
_TONES = {'blue': (C['blue_l'], C['blue'], C['blue_d']),
          'gray': ('#f1f5f9', '#94a3b8', C['ink']),
          'green': (C['green_l'], C['green'], C['ink_green']),
          'amber': (C['amber_l'], C['amber'], C['ink_amber']),
          'purple': (C['purple_l'], C['purple'], C['ink_purple'])}


def phaseflow(blocks, w=1060, start=None):
    """blocks: [{'head','tone','rows':[(indent,text,style)]} | {'kind':'note'|'dots',...}]"""
    b = []; cx = w / 2; bw = 860; x = (w - bw) / 2; y = 30
    if start:
        b.append(f'<rect x="{x}" y="{y}" width="{bw}" height="54" rx="8" fill="{C["blue"]}"/>')
        b.append(text(cx, y + 32, start, 14.5, '#fff', bold=True))
        b.append(arrow(cx, y + 54, cx, y + 74)); y += 74
    gap = 24
    for i, blk in enumerate(blocks):
        k = blk.get('kind')
        if k == 'dots':
            b.append(text(cx, y + 16, '⋮', 20, C['mut'], bold=True)); y += 38; continue
        if k == 'note':
            b.append(rrect(x, y, bw, 42, stroke=C['line'], dash='5 4'))
            b.append(text(cx, y + 26, blk['text'], 12.5, C['mut'])); y += 42
            if i < len(blocks) - 1:
                b.append(arrow(cx, y + 2, cx, y + gap - 2)); y += gap
            continue
        fill, stroke, tc = _TONES[blk.get('tone', 'blue')]
        head = blk.get('head'); rows = blk.get('rows', [])
        rh = (40 if head else 18) + len(rows) * 25 + 16
        b.append(rrect(x, y, bw, rh, fill='#fff', stroke=stroke, sw=1.5))
        b.append(f'<rect x="{x}" y="{y}" width="6" height="{rh}" rx="3" fill="{stroke}"/>')
        yy = y + 26
        if head:
            fit('phase/head', head, 14, bw - 44)
            b.append(text(x + 22, yy, head, 14, tc, 'start', bold=True)); yy += 28
        for ind, txt, style in rows:
            xx = x + 24 + ind * 22
            fs = 11.8 if style == 'mono' else (11.5 if style == 'sub' else 12.2)
            col = C['ink'] if style != 'sub' else C['mut']
            fit('phase/row', txt, fs, bw - 24 - ind * 22 - 12)
            b.append(text(xx, yy, txt, fs, col, 'start', mono=(style == 'mono')))
            yy += 25
        y += rh
        if i < len(blocks) - 1:
            b.append(arrow(cx, y + 2, cx, y + gap - 2)); y += gap
    return w, y + 10, ''.join(b)


# ── 5. 事件序列（seq/type 格 + Surface 投影 + shadow 框）────────
def event_seq(seqs, surface, shadow=None, log_label='Log（仅追加，包含所有事件）', w=820):
    b = []; n = len(seqs); cw = 92; gap = 10; gridw = n * cw + (n - 1) * gap
    x0 = (w - gridw) / 2; y = 70
    b.append(text(w / 2, 36, log_label, 14, C['ink'], bold=True))
    for i, (sq, tp, lab) in enumerate(seqs):
        xx = x0 + i * (cw + gap)
        sh = shadow is not None and i in shadow
        b.append(rrect(xx, y, cw, 84, fill=('#f1f5f9' if sh else C['blue_l']),
                       stroke=('#94a3b8' if sh else C['blue'])))
        b.append(text(xx + cw / 2, y + 22, str(sq), 15, C['mut'] if sh else C['blue_d'], bold=True, mono=True))
        b.append(text(xx + cw / 2, y + 46, tp, 17, C['ink'], bold=True, mono=True))
        lfs = 10.0
        while tw(lab, lfs) > cw - 8 and lfs > 7.0:
            lfs -= 0.5
        fit('seq/lab', lab, lfs, cw - 8)
        b.append(text(xx + cw / 2, y + 68, lab, lfs, C['mut']))
    sy = y + 128
    b.append(rrect(x0, sy, gridw, 64, fill='#fff', stroke=C['green'], sw=1.6))
    b.append(text(x0 + 20, sy + 24, 'Surface.nodes', 13, C['green'], 'start', bold=True))
    b.append(text(x0 + gridw / 2 + 40, sy + 38, '[' + ', '.join(map(str, surface)) + ']',
                  15, C['ink'], bold=True, mono=True))
    h = sy + 110
    if shadow:
        sx0 = x0 + min(shadow) * (cw + gap) - 5; sx1 = x0 + max(shadow) * (cw + gap) + cw + 5
        b.append(f'<rect x="{sx0}" y="{y-5}" width="{sx1-sx0}" height="94" rx="8" fill="none" '
                 f'stroke="{C["red"]}" stroke-width="2" stroke-dasharray="6 4"/>')
        b.append(text((sx0 + sx1) / 2, y - 16, '被遮蔽（shadowed）', 12, C['red'], bold=True))
        h += 8
    return w, h, ''.join(b)


# ── 7. 目录树（浅色代码卡，替代 md-to-styled-html 的 .dir-tree 组件）──
def tree_card(lines, title=None, w=780, fs=12.5, note=None):
    """lines: 原文行（含 ├└│ 缩进）。文件夹行（尾随 /）蓝色加粗，注释（# 或 ：后说明）灰色。"""
    lh = fs + 8
    top = 26 if title else 16
    h = top + len(lines) * lh + (34 if note else 14)
    x = 40
    b = [rrect(x, 14, w - 80, h, fill=C['sub'], stroke=C['line'], sw=1.2)]
    if title:
        b.append(text(x + 18, 34, title, 13, C['blue_d'], 'start', bold=True))
    y = 14 + top
    for ln in lines:
        s = ln.rstrip()
        st = s.lstrip()
        ind = len(s) - len(st)
        fit('tree', st, fs, w - 80 - 24 - ind * 0.6 * fs)
        if st.endswith('/'):
            col, bold = C['blue_d'], True
        elif st.startswith(('#', '//', '注')) or ('#' in st and st.index('#') > 0):
            col, bold = C['note'], False
        else:
            col, bold = C['ink'], False
        b.append(text(x + 18 + ind * 0.6 * fs, y, st, fs, col, 'start', mono=True, bold=bold))
        y += lh
    if note:
        b.append(text(x + 18, y + 4, note, 11.5, C['note'], 'start'))
    return w, h + 14, ''.join(b)


# ── 6. 分栏对照 / 公式（列卡）────────────────────────────────
def columns(headline, cols, w=None, ch=300, fs_head=13.5, fs_item=12):
    """cols: [(标题, 配色key, [条目...])]。w=None 时按内容自动定宽（一次算对，不事后补）。"""
    n = len(cols); gap = 16
    need = []
    for t, _tone, items in cols:
        need.append(max(tw(t, fs_head), max((tw(it, fs_item) for it in items), default=0)) + 34)
    if w is None:
        w = int(sum(need) + (n - 1) * gap + 80)
    else:  # 给定宽则按需等比分配
        avail = w - 80 - (n - 1) * gap
        need = [avail * x / sum(need) for x in need]
    b = []
    fit('col/headline', headline, 17, w - 90)
    b.append(f'<rect x="40" y="24" width="{w-80}" height="56" rx="8" fill="{C["blue"]}"/>')
    b.append(text(w / 2, 56, headline, 17, '#fff', bold=True, mono=True))
    x0 = 40; y = 120
    for i, (t, tone, items) in enumerate(cols):
        _f, st, tc = _TONES[tone]
        bw = need[i]; xx = x0 + sum(need[:i]) + i * gap
        b.append(rrect(xx, y, bw, ch, fill=_f, stroke=st, sw=1.5))
        fit('col/title', t, fs_head, bw - 24)
        b.append(text(xx + bw / 2, y + 28, t, fs_head, tc, bold=True))
        for j, it in enumerate(items):
            if not it:
                continue
            fit('col/item', it, fs_item, bw - 30)
            b.append(text(xx + 16, y + 62 + j * 26,
                          ('· ' + it) if not it.startswith((' ', '+', 'D')) else it,
                          fs_item, C['ink'], 'start'))
    return w, y + ch + 36, ''.join(b)
