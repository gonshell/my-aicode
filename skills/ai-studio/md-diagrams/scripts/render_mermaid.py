#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""render_mermaid — mermaid 围栏 → 高清 SVG（mmdc 封装）

用法:
  python3 render_mermaid.py <in.mmd> <out.svg> [--bg white]

约定（与 md-to-styled-html 陷阱 13 一致）:
  · 输出 SVG（非 PNG）——PNG 默认仅 784px，放大必虚
  · htmlLabels=false —— 否则标签是 <foreignObject><div>，<text> 节点数=0，部分查看器不渲染
  · 依赖 node/npx + chromium；缺失则返回非 0，调用方降级为代码块
"""
import os, sys, json, shutil, subprocess, tempfile

CHROME_CANDIDATES = ['/usr/bin/chromium', '/usr/bin/chromium-browser',
                     '/usr/bin/google-chrome', shutil.which('chromium')]
NODE_BIN = '/root/.hermes/node/bin'


def find_chrome():
    for c in CHROME_CANDIDATES:
        if c and os.path.exists(c):
            return c
    return None


def render(inp, out, bg='white'):
    env = dict(os.environ)
    if os.path.isdir(NODE_BIN):
        env['PATH'] = NODE_BIN + os.pathsep + env.get('PATH', '')
    chrome = find_chrome()
    if not chrome or not shutil.which('npx', path=env['PATH']):
        print('mermaid 依赖缺失（npx/chromium），请降级为代码块', file=sys.stderr)
        return 2
    tmp = tempfile.mkdtemp()
    cfg = os.path.join(tmp, 'mmd.json')
    pptr = os.path.join(tmp, 'puppeteer.json')
    json.dump({'theme': 'neutral', 'htmlLabels': False, 'flowchart': {'htmlLabels': False},
               'securityLevel': 'loose', 'themeVariables': {'fontFamily': 'PingFang SC, Microsoft YaHei, Noto Sans CJK SC, sans-serif'}},
              open(cfg, 'w'))
    json.dump({'executablePath': chrome, 'args': ['--no-sandbox', '--disable-gpu']}, open(pptr, 'w'))
    cmd = ['npx', '-y', '@mermaid-js/mermaid-cli@latest', '-i', inp, '-o', out,
           '-c', cfg, '-p', pptr, '-b', bg]
    r = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=180)
    if r.returncode != 0 or not os.path.exists(out):
        print(r.stdout[-800:], r.stderr[-800:], file=sys.stderr)
        return 1
    size = os.path.getsize(out)
    print(f'OK {out} ({size:,} B)')
    return 0


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(2)
    sys.exit(render(sys.argv[1], sys.argv[2]))
