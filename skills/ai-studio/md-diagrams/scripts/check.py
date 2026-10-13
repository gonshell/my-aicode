#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check — SVG 全量程序化自检（零 token；视觉抽检只留 2–3 张做美学）

用法:
  python3 check.py <figdir> [--manifest manifest.json] [--md source.md]

检查项:
  C1 XML 合法 + 有 viewBox
  C2 白底 rect 存在且覆盖全幅（PNG 兜底/打印/墨迹自检需要）
  C3 无 foreignObject（标签必须是真 <text>，否则部分查看器不渲染文字）
  C4 文字不越界：每个 <text> 按 figlib.tw 估宽 + anchor 推算，落在 viewBox 内
  C5 文字保真：源 ASCII 块里的标识符（事件名/函数名/路径/字段）在 SVG 中逐字命中
     （中文说明可压缩，标识符不许改：这是防「张冠李戴」的直接判据）

退出码 0 = 全过；1 = 有硬伤。
"""
import os, re, sys, json, glob, argparse
import xml.etree.ElementTree as ET
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import figlib as F

SVGNS = '{http://www.w3.org/2000/svg}'
# 标识符：允许字母数字 _ . / : - （覆盖 turn/start, ctx.tools, mcp__github__x, a/b.tsx）
IDENT = re.compile(r'[A-Za-z_][A-Za-z0-9_]{1,}(?:[./:_-][A-Za-z0-9_]+)*')
# 太常见的英文词不算标识符（避免噪声）
STOP = {'the', 'and', 'for', 'with', 'from', 'true', 'false', 'null', 'none', 'type', 'name', 'key'}


def parse(p):
    tree = ET.parse(p)
    root = tree.getroot()
    vb = root.get('viewBox')
    if not vb:
        return None, None
    x0, y0, W, H = (float(x) for x in vb.split())
    return root, (x0, y0, W, H)


def texts(root):
    out = []
    for t in root.iter(SVGNS + 'text'):
        s = ''.join(t.itertext())
        if not s.strip():
            continue
        x = float(t.get('x', 0)); y = float(t.get('y', 0))
        fs = float(t.get('font-size', 12))
        anchor = t.get('text-anchor', 'start')
        w = F.tw(s, fs)
        x0 = x - w / 2 if anchor == 'middle' else (x - w if anchor == 'end' else x)
        out.append((x0, x0 + w, y - fs, y + fs * 0.35, s))
    return out


def check_svg(p):
    issues = []
    try:
        root, dim = parse(p)
    except ET.ParseError as e:
        return ['C1 XML 非法: %s' % e]
    if dim is None:
        return ['C1 缺 viewBox']
    minx, miny, W, H = dim
    xmax, ymax = minx + W, miny + H
    raw = open(p, encoding='utf-8').read()
    # C2 白底：接受三种形态
    #   (a) svg 根 style 含 background-color: white
    #   (b) 全幅 rect（数值或 100%）fill 为白
    #   (c) <rect fill="white"> 覆盖 viewBox
    root_style = (root.get('style') or '').lower().replace(' ', '')
    has_bg = ('background-color:white' in root_style or 'background-color:#fff' in root_style
              or 'background:white' in root_style)
    for r in root.iter(SVGNS + 'rect'):
        fill = (r.get('fill') or '').lower()
        rst = (r.get('style') or '').lower().replace(' ', '')
        white_fill = fill in ('#fff', '#ffffff', 'white') or 'fill:white' in rst or 'fill:#fff' in rst
        if not white_fill:
            continue
        wv, hv = (r.get('width') or '0'), (r.get('height') or '0')
        try:
            wnum = float(wv); hnum = float(hv)
        except ValueError:
            wnum = W if wv.strip() == '100%' else 0
            hnum = H if hv.strip() == '100%' else 0
        if wnum >= W - 1 and hnum >= H - 1:
            has_bg = True
    if not has_bg:
        issues.append('C2 缺白底（svg 根 background-color 或全幅 fill=#fff rect）')
    # C3 foreignObject
    if root.find('.//' + SVGNS + 'foreignObject') is not None:
        issues.append('C3 含 foreignObject（标签非真 text）')
    # C4 越界
    for tx0, tx1, ty0, ty1, s in texts(root):
        if tx0 < minx - 1 or tx1 > xmax + 1:
            issues.append(f'C4 文字横向越界 [{tx0:.0f},{tx1:.0f}] / 视窗[{minx:.0f},{xmax:.0f}]: {s[:40]}')
        if ty1 < miny - 1 or ty0 > ymax + 1:
            issues.append(f'C4 文字纵向越界: {s[:40]}')
    return issues


def coverage(svg_text, src_block):
    """返回缺失的标识符列表"""
    idents = []
    for m in IDENT.finditer(src_block):
        tok = m.group(0)
        if tok.lower() in STOP or len(tok) < 4:
            continue
        if tok not in idents:
            idents.append(tok)
    missing = [t for t in idents if t not in svg_text]
    return missing, len(idents)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('figdir')
    ap.add_argument('--manifest')
    ap.add_argument('--md')
    a = ap.parse_args()

    svgs = sorted(glob.glob(os.path.join(a.figdir, '*.svg')))
    if not svgs:
        print('未找到 SVG'); sys.exit(1)

    bad = 0
    src_blocks = {}
    if a.md and a.manifest and os.path.exists(a.manifest):
        lines = open(a.md, encoding='utf-8').read().splitlines()
        man = json.load(open(a.manifest, encoding='utf-8'))
        for e in man:
            fo = e.get('fence_open')
            if not fo:
                continue
            # 抓围栏体
            body, on = [], False
            for i, ln in enumerate(lines):
                if i + 1 == fo:
                    on = True; continue
                if on:
                    if ln.strip().startswith('```'):
                        break
                    body.append(ln)
            src_blocks[e.get('file', '')] = '\n'.join(body)

    print(f'自检 {len(svgs)} 个 SVG\n')
    for p in svgs:
        name = os.path.basename(p)
        iss = check_svg(p)
        missing = []
        if name in src_blocks:
            root, _ = parse(p)
            svg_text = ' '.join(t for *_, t in texts(root))
            missing, total = coverage(svg_text, src_blocks[name])
            if missing:
                iss.append('C5 文字保真缺失 %d/%d: %s' % (len(missing), total, ', '.join(missing[:6])))
        if iss:
            bad += 1
            print(f'✗ {name}')
            for i in iss:
                print('    ', i)
        else:
            print(f'✓ {name}')
    print(f'\n通过 {len(svgs)-bad}/{len(svgs)}')
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
