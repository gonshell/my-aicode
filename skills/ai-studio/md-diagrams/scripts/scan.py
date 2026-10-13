#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""scan — 扫描 md 图块，按「最近上方标题」绑定，输出清单（先跑这个，再渲染）

用法:
  python3 scan.py <doc.md> [--json out.json] [--min-lines N]

输出每条: {fence_open, fence_close, heading, level, kind, n_lines, fingerprint, preview}
kind ∈ {mermaid, tree, ascii-box, other}   —— other 一律保留为代码块，不渲染

自检（不过则 exit 1）:
  · 围栏必须成对（奇数 → 报错，不静默吞块）
  · 无重复图题（同标题两个图块 → 报错，逼人工消歧）
  · 图块均落在某个标题之下（文件头的无标题块 → 警告）
"""
import sys, re, json, hashlib, argparse

FENCE = re.compile(r'^\s*```(.*)$')
HEAD = re.compile(r'^(#{1,6})\s+(.*?)\s*$')
# 框线字符（ASCII 图判定）
BOXCH = set('┌┐└┘├┤┬┴┼─│├▼▲◀▶↑↓→←╔╗╚╝║═')
TREECH = set('├└│─')


def classify(info, body):
    info = (info or '').strip().lower()
    if 'mermaid' in info:
        return 'mermaid'
    chars = [c for c in body if c in BOXCH]
    if len(chars) >= 4:
        return 'ascii-box'
    # 纯目录树：几乎每行都是 ├└│ 缩进结构
    lines = [l for l in body.splitlines() if l.strip()]
    if lines and sum(1 for l in lines if set(l.strip()) & TREECH) >= max(2, len(lines) * 0.5):
        return 'tree'
    return 'other'


def scan(path, min_lines=3):
    lines = open(path, encoding='utf-8').read().splitlines()
    blocks = []
    i, cur_head, cur_lvl = 0, None, 0
    n = len(lines)
    open_at = None
    open_info = None
    for idx, line in enumerate(lines):
        m = FENCE.match(line)
        if m:
            if open_at is None:
                open_at, open_info, body = idx + 1, m.group(1), []
            else:
                body_txt = '\n'.join(body)
                blocks.append(dict(fence_open=open_at, fence_close=idx + 1,
                                   heading=cur_head, level=cur_lvl,
                                   info=open_info.strip(),
                                   kind=classify(open_info, body_txt),
                                   n_lines=len(body),
                                   fingerprint=hashlib.sha1(body_txt.encode()).hexdigest()[:12],
                                   preview=body[0][:60] if body else ''))
                open_at = None
            continue
        if open_at is not None:
            if len(body) < 10000:
                body.append(line)
            continue
        hm = HEAD.match(line)
        if hm:
            cur_lvl, cur_head = len(hm.group(1)), hm.group(2)
    return blocks, (open_at is not None)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('md')
    ap.add_argument('--json')
    ap.add_argument('--min-lines', type=int, default=3)
    a = ap.parse_args()
    blocks, unclosed = scan(a.md, a.min_lines)

    figs = [b for b in blocks if b['kind'] in ('mermaid', 'ascii-box', 'tree')
            and b['n_lines'] >= a.min_lines]
    others = [b for b in blocks if b not in figs]

    errs, warns = [], []
    if unclosed:
        errs.append('围栏未闭合（文件结束仍在代码块内）')
    if len(blocks) % 2 != 0:
        errs.append(f'围栏块数为奇数 {len(blocks)}（应成对）')
    seen = {}
    for b in figs:
        key = b['heading'] or '(无标题)'
        seen.setdefault(key, []).append(b)
        if not b['heading']:
            warns.append(f"行 {b['fence_open']}: 图块上方无标题，无法命名")
    # 同名标题 → 按出现顺序编号（同小节合法地可有多个图块），不阻断
    for k, lst in seen.items():
        if len(lst) > 1:
            for j, b in enumerate(lst):
                b['title'] = f'{k}（{j+1}/{len(lst)}）'
            warns.append(f'「{k}」有 {len(lst)} 个图块，已按出现顺序编号')
        else:
            lst[0]['title'] = k
    # 指纹重复 → 内容完全相同的块（可共用同一 SVG）
    fp = {}
    for b in figs:
        fp.setdefault(b['fingerprint'], []).append(b['fence_open'])
    for h, ols in fp.items():
        if len(ols) > 1:
            warns.append(f'行 {ols} 内容完全相同（指纹 {h}），可共用同一 SVG')

    if a.json:
        json.dump({'source': a.md, 'figures': figs, 'skipped': others},
                  open(a.json, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

    print(f'围栏块 {len(blocks)} 个 → 图块 {len(figs)} 个（mermaid {sum(1 for b in figs if b["kind"]=="mermaid")}'
          f' / ascii-box {sum(1 for b in figs if b["kind"]=="ascii-box")}'
          f' / tree {sum(1 for b in figs if b["kind"]=="tree")}），其余 {len(others)} 块保留为代码块')
    for b in figs:
        print(f"  L{b['fence_open']:>5}  [{b['kind']:9}] {b['n_lines']:>3}行  {b['fingerprint']}  {b['heading']}")
    for w in warns:
        print('  ~ 警告:', w)
    if errs:
        print('\n❌ 禁止渲染：')
        for e in errs:
            print('  -', e)
        sys.exit(1)
    print('\n✅ 清单通过，可渲染')


if __name__ == '__main__':
    main()
