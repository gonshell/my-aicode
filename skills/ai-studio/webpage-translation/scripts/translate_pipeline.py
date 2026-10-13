#!/usr/bin/env python3
"""
webpage-translation 管线脚本（v2.0）

设计目标：模型只做"翻译"这一件事，其余全部脚本化，省 token。
  - extract : 抓取 + 提取 + 切块 + 自动跳过（数字单元格/参考文献/空节点）+ 图片/数学/链接保护
  - export  : 只输出"需要翻译"的节点文本（紧凑格式，控制上下文占用）
  - build   : 译文回填 + 数学恢复 + 链接恢复 + 图片 base64 嵌入 + 去双 H1 + 渲染主题

用法：
  python3 translate_pipeline.py extract <url> --workdir ./work
  python3 translate_pipeline.py export ./work [--start 0 --end 999]   # 模型读取 → 翻译
  python3 translate_pipeline.py build ./work -t translations.json -o out.html --theme tech-dark

Token 效率铁律（全局 SOUL.md）：
  1. 模型上下文只进"待译文本"，不进 HTML 噪音/调试输出/图片字节
  2. 数字单元格、参考文献、空节点由脚本自动跳过，不进模型
  3. 译文用紧凑 JSON {index: text}，回填/恢复全自动
"""
import argparse
import base64
import json
import os
import re
import ssl
import sys
import urllib.request
from urllib.parse import urljoin, urlparse

USER_AGENT = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
DEFAULT_TIMEOUT = 30
MAX_IMAGE_SIZE = 8 * 1024 * 1024

ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE

# 参考文献等保留原文的 li 区间无法通用判断，用启发式：含年份引用的 li 不翻译
# 支持 (2024) / (2024a) / (2024b) 等年份后缀
REF_LI_PATTERN = re.compile(r'^[A-Z][\w.\- ]+? \(\d{4}[a-z]?\).{20,}')

# 可翻译的节点标签
NODE_TAGS = ('h1', 'h2', 'h3', 'h4', 'p', 'li', 'figcaption', 'td', 'th')
NODE_PATTERN = re.compile(
    r'<(h[1-4]|p|li|figcaption|td|th)\b[^>]*>(.*?)</\1>', re.DOTALL)


# ─── 抓取 ───────────────────────────────────────────────
def fetch_page(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, context=ssl_ctx, timeout=DEFAULT_TIMEOUT) as resp:
        content_type = resp.headers.get("Content-Type", "")
        raw = resp.read()
        charset = "utf-8"
        if "charset=" in content_type:
            charset = content_type.split("charset=")[-1].split(";")[0].strip()
        else:
            m = re.search(rb'charset=["\']?([\w-]+)', raw[:10000])
            if m:
                charset = m.group(1).decode("ascii", errors="ignore")
        try:
            return raw.decode(charset, errors="replace")
        except (LookupError, UnicodeDecodeError):
            return raw.decode("utf-8", errors="replace")


def extract_meta(html: str, base_url: str) -> dict:
    meta = {"title": "", "description": "", "author": "", "date": "", "og_image": "", "canonical_url": base_url}
    m = re.search(r"<title[^>]*>(.*?)</title>", html, re.DOTALL | re.IGNORECASE)
    if m:
        meta["title"] = re.sub(r"<[^>]+>", "", m.group(1)).strip()
    m = re.search(r'<meta[^>]*name="description"[^>]*content="([^"]*)"', html, re.IGNORECASE)
    if not m:
        m = re.search(r'<meta[^>]*content="([^"]*)"[^>]*name="description"', html, re.IGNORECASE)
    if m:
        meta["description"] = m.group(1).strip()
    for pat in (
        r'<meta[^>]*property="og:image"[^>]*content="([^"]*)"',
        r'<meta[^>]*content="([^"]*)"[^>]*property="og:image"',
    ):
        m = re.search(pat, html, re.IGNORECASE)
        if m:
            meta["og_image"] = urljoin(base_url, m.group(1))
            break
    for pat in (
        r'<meta[^>]*property="article:published_time"[^>]*content="([^"]*)"',
        r'<meta[^>]*name="date"[^>]*content="([^"]*)"',
        r'<time[^>]*datetime="([^"]*)"',
    ):
        m = re.search(pat, html, re.IGNORECASE)
        if m:
            meta["date"] = m.group(1).strip()[:10]
            break
    return meta


def extract_article(html: str) -> str:
    m = re.search(r"<article[^>]*>(.*?)</article>", html, re.DOTALL | re.IGNORECASE)
    if m and len(m.group(1)) > 500:
        return m.group(1).strip()
    m = re.search(r"<main[^>]*>(.*?)</main>", html, re.DOTALL | re.IGNORECASE)
    if m and len(m.group(1)) > 1000:
        return m.group(1).strip()
    m = re.search(r"<body[^>]*>(.*?)</body>", html, re.DOTALL | re.IGNORECASE)
    if m:
        return m.group(1).strip()
    return html


def clean_content(html: str) -> str:
    for tag in ("script", "style", "noscript", "iframe", "nav", "footer", "aside"):
        html = re.sub(rf"<{tag}[^>]*>.*?</{tag}>", "", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<!--.*?-->", "", html, flags=re.DOTALL)
    html = re.sub(r"\n{3,}", "\n\n", html)
    return html.strip()


def fix_relative_links(html: str, base_url: str) -> str:
    def repl(m):
        attr, url = m.group(1), m.group(2)
        if url.startswith(("http://", "https://", "data:", "mailto:", "#", "javascript:")):
            return m.group(0)
        return f'{attr}="{urljoin(base_url, url)}"'
    html = re.sub(r'(href)="([^"]*)"', repl, html, flags=re.IGNORECASE)
    html = re.sub(r'(src)="([^"]*)"', repl, html, flags=re.IGNORECASE)
    return html


# ─── 图片 ───────────────────────────────────────────────
def download_image(url: str) -> dict | None:
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": USER_AGENT,
            "Referer": urlparse(url)._replace(path="/").geturl(),
        })
        with urllib.request.urlopen(req, context=ssl_ctx, timeout=DEFAULT_TIMEOUT) as resp:
            data = resp.read()
            if len(data) > MAX_IMAGE_SIZE:
                print(f"[WARN] image too large ({len(data)}B): {url}", file=sys.stderr)
                return None
            mime = resp.headers.get("Content-Type", "image/jpeg").split(";")[0].strip()
            return {"data_uri": f"data:{mime};base64,{base64.b64encode(data).decode('ascii')}",
                    "size_bytes": len(data), "mime_type": mime}
    except Exception as e:
        print(f"[WARN] image download failed: {url} -> {e}", file=sys.stderr)
        return None


def collect_images(html: str, base_url: str) -> list[dict]:
    images, seen = [], set()
    for m in re.finditer(r'<img[^>]*src="([^"]*)"[^>]*alt="([^"]*)"', html, re.IGNORECASE):
        abs_url = urljoin(base_url, m.group(1))
        if abs_url.startswith("data:") or abs_url in seen:
            continue
        seen.add(abs_url)
        images.append({"original_src": m.group(1), "absolute_url": abs_url, "alt": m.group(2)})
    return images


# ─── 节点切块（核心 token 效率机制）──────────────────────
def is_ref_li(text: str) -> bool:
    """参考文献条目（如 'Bai et al. (2024a) Y. Bai, ...'）→ 保留原文不翻译"""
    return bool(REF_LI_PATTERN.match(text.strip().replace("\n", " ")))


def needs_translation(text: str, tag: str, idx: int) -> tuple[bool, str]:
    t = text.strip()
    if not t:
        return False, "empty"
    if re.fullmatch(r"[\d\s/.%\-–—+×:;]+", t):
        return False, "numeric"
    if re.fullmatch(r"[\W\d]{1,3}", t):
        return False, "symbol"
    if tag == "li" and is_ref_li(t):
        return False, "reference"
    return True, ""


def extract_nodes(content_html: str) -> list[dict]:
    """保护 math → 切块 → 标记 need/skip 理由 → 提取链接映射"""
    # 保护 math
    maths: list[str] = []
    def protect(m):
        maths.append(m.group(0))
        return f"@@MATH{len(maths)-1}@@"
    html = re.sub(r"<math.*?</math>", protect, content_html, flags=re.DOTALL)

    nodes = []
    for m in NODE_PATTERN.finditer(html):
        tag, inner = m.group(1), m.group(2)
        text = re.sub(r"<[^>]+>", "", inner).strip()
        if not text:
            continue
        need, reason = needs_translation(text, tag, len(nodes))
        # 链接映射：节点内 <a href>text</a>
        links = [{"text": re.sub(r"<[^>]+>", "", a.group(2)).strip(),
                  "href": a.group(1)}
                 for a in re.finditer(r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', inner, re.DOTALL)]
        nodes.append({
            "tag": tag,
            "text": text,
            "html": inner,
            "need": need,
            "skip_reason": reason if not need else "",
            "has_math": "@@MATH" in inner,
            "links": links,
        })
    return nodes, maths


# ─── extract 子命令 ─────────────────────────────────────
def cmd_extract(url: str, workdir: str):
    os.makedirs(workdir, exist_ok=True)
    print(f"[1/6] fetch: {url}")
    html = fetch_page(url)
    print(f"      raw HTML: {len(html):,} bytes")

    meta = extract_meta(html, url)
    print(f"      title: {meta['title'][:60]}")

    content = clean_content(fix_relative_links(extract_article(html), url))
    if len(content) < 500:
        print("[WARN] short content - SPA/WAF? need browser rendering", file=sys.stderr)

    nodes, maths = extract_nodes(content)
    need_count = sum(1 for n in nodes if n["need"])
    print(f"[2/6] nodes: {len(nodes)} total, {need_count} need translation, {len(maths)} maths protected")

    # 下载图片（只存 data_uri，不写进 content）
    images = collect_images(content, url)
    print(f"[3/6] images: {len(images)} found, downloading...")
    for img in images:
        res = download_image(img["absolute_url"])
        img["data_uri"] = res["data_uri"] if res else ""

    # og:image
    og = ""
    if meta["og_image"]:
        res = download_image(meta["og_image"])
        og = res["data_uri"] if res else ""

    data = {
        "source_url": url,
        "meta": meta,
        "og_image_b64": og,
        "content_html": content,     # 原始（含 @@MATHn@@ 占位）
        "nodes": nodes,
        "maths": maths,
        "images": images,
        "image_count": sum(1 for i in images if i["data_uri"]),
        "image_total": len(images),
    }
    with open(os.path.join(workdir, "page.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print(f"[4/6] saved workdir: {workdir}/page.json")


# ─── export 子命令（模型读取待译文本）───────────────────
def cmd_export(workdir: str, start: int, end: int):
    data = json.load(open(os.path.join(workdir, "page.json"), encoding="utf-8"))
    nodes = data["nodes"]
    shown = 0
    for i, n in enumerate(nodes):
        if not n["need"]:
            continue
        if not (start <= i < end):
            continue
        shown += 1
        t = n["text"].replace("\n", " ")
        print(f"[{i:04d}] {n['tag']:10s} {len(n['text']):5d} | {t}")
    print(f"\n--- exported {shown} nodes (of {sum(1 for n in nodes if n['need'])} needing translation) ---")


# ─── build 子命令（回填 + 恢复 + 渲染）──────────────────
def cmd_build(workdir: str, translations_path: str, output: str, theme: str, title: str | None):
    data = json.load(open(os.path.join(workdir, "page.json"), encoding="utf-8"))
    trans = json.load(open(translations_path, encoding="utf-8"))
    nodes = data["nodes"]
    maths = data["maths"]
    images = {i["original_src"]: i["data_uri"] for i in data["images"] if i["data_uri"]}
    images.update({i["absolute_url"]: i["data_uri"] for i in data["images"] if i["data_uri"]})

    def restore_math(t):
        return re.sub(r"@@MATH(\d+)@@", lambda m: maths[int(m.group(1))], t)

    # 回填节点
    html = data["content_html"]
    idx = 0
    def repl(m):
        nonlocal idx
        tag, inner = m.group(1), m.group(2)
        text = re.sub(r"<[^>]+>", "", inner).strip()
        if not text:
            return m.group(0)
        node_idx = idx
        idx += 1
        node = nodes[node_idx]
        if not node["need"]:
            return m.group(0)
        key = str(node_idx)
        if key not in trans or not trans[key]:
            print(f"[WARN] missing translation for node {key} ({tag})", file=sys.stderr)
            return m.group(0)
        tr = restore_math(trans[key])
        # 链接恢复：若节点原文有 <a> 且译文文本匹配链接文本，包回 <a>
        # 安全规则：跳过短文本/纯数字链接（如 "2"→#S4.T2），避免误伤译文；
        # 按文本长度降序处理，防止短链接文本污染长链接的 href。
        for link in sorted(node["links"], key=lambda l: -len(l["text"])):
            lt = link["text"].strip()
            if len(lt) < 4 or re.fullmatch(r"[\d\s/.\-]+", lt):
                continue
            if lt in tr:
                tr = tr.replace(lt,
                                f'<a href="{link["href"]}" target="_blank" rel="noopener">{lt}</a>')
        return f"<{tag}>{tr}</{tag}>"

    html = NODE_PATTERN.sub(repl, html)

    # 图片嵌入
    for orig, uri in images.items():
        html = html.replace(f'src="{orig}"', f'src="{uri}"')

    # 去双 H1：正文第一个 h1 与模板标题重复
    html = re.sub(r"<h1[^>]*>.*?</h1>", "", html, count=1, flags=re.DOTALL)

    # 渲染
    final_title = title or data["meta"].get("title", "")
    domain = urlparse(data["source_url"]).netloc
    meta_parts = []
    if data["meta"].get("author"):
        meta_parts.append(f"作者：{data['meta']['author']}")
    if data["meta"].get("date"):
        meta_parts.append(f"日期：{data['meta']['date']}")
    cover = f'<div class="cover"><img src="{data["og_image_b64"]}" alt="封面图"></div>' if data["og_image_b64"] else ""

    template = TECH_DARK if theme == "tech-dark" else CLEAN
    out = template
    out = out.replace("__TITLE__", final_title)
    out = out.replace("__DESCRIPTION__", data["meta"].get("description", ""))
    out = out.replace("__SOURCE_URL__", data["source_url"])
    out = out.replace("__SOURCE_DOMAIN__", domain)
    out = out.replace("__META_LINE__", " · ".join(meta_parts))
    out = out.replace("__COVER__", cover)
    out = out.replace("__CONTENT__", html)

    with open(output, "w", encoding="utf-8") as f:
        f.write(out)
    print(f"built: {output} ({os.path.getsize(output):,} bytes)")


# ─── 模板（与 translate_page.py 一致，避免引入）──────────
CLEAN = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<meta name="description" content="__DESCRIPTION__">
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC','Hiragino Sans GB','Microsoft YaHei',sans-serif;background:#fff;color:#1a1a1a;line-height:1.75;font-size:17px}
.header{position:sticky;top:0;width:100%;height:56px;z-index:50;background:#fff;border-bottom:1px solid #e5e5e5;display:flex;align-items:center;padding:0 24px}
.header .src{font-size:13px;color:#888}
.header .src a{color:#10a37f;text-decoration:none;border-bottom:1px solid rgba(16,163,127,.3)}
.container{max-width:720px;margin:0 auto;padding:48px 20px 96px}
h1{font-size:36px;font-weight:700;line-height:1.25;margin-bottom:16px;letter-spacing:-.02em}
.meta{color:#888;font-size:14px;margin-bottom:24px}
.cover{margin:0 0 32px;border-radius:8px;overflow:hidden;border:1px solid #e5e5e5}
.cover img{width:100%;display:block}
h2{font-size:26px;font-weight:700;margin-top:40px;margin-bottom:16px;line-height:1.35;letter-spacing:-.01em}
h3{font-size:20px;font-weight:600;margin-top:28px;margin-bottom:12px}
p{margin-bottom:18px;color:#2a2a2a}
a{color:#10a37f;text-decoration:none;border-bottom:1px solid rgba(16,163,127,.3)}
ul,ol{margin-bottom:20px;padding-left:28px}
li{margin-bottom:8px;color:#2a2a2a}
figure{margin:28px 0}
figure img{width:100%;border-radius:8px;border:1px solid #e5e5e5;background:#fff;padding:12px}
figcaption{margin-top:10px;text-align:center;font-size:13px;color:#666}
blockquote{margin:20px 0;padding:12px 20px;border-left:4px solid #10a37f;background:#f0fdf8;color:#374151;font-style:italic}
code{font-family:'SFMono-Regular',Consolas,'Liberation Mono',Menlo,monospace;font-size:.9em;background:#f3f4f6;padding:2px 6px;border-radius:4px;color:#dc2626}
pre{background:#1f2937;color:#e5e7eb;padding:16px 20px;border-radius:8px;overflow-x:auto;margin:20px 0;font-size:14px;line-height:1.6}
pre code{background:none;padding:0;color:inherit;font-size:inherit}
strong{font-weight:600}
hr{border:none;border-top:1px solid #e5e5e5;margin:32px 0}
table{width:100%;border-collapse:collapse;margin:20px 0;font-size:15px}
th,td{padding:10px 14px;text-align:left;border-bottom:1px solid #e5e5e5}
th{background:#f9fafb;font-weight:600}
.term-note{background:#fffbeb;border:1px solid #fde68a;border-radius:6px;padding:10px 14px;margin:12px 0;font-size:14px;color:#92400e}
.footer-note{margin-top:56px;padding-top:24px;border-top:1px solid #e5e5e5;font-size:13px;color:#999;line-height:1.6}
.footer-note p{margin-bottom:8px;color:#999}
@media (max-width:640px){h1{font-size:28px}h2{font-size:22px}.container{padding:24px 16px 64px}body{font-size:16px}}
</style>
</head>
<body>
<header class="header"><div class="src">原文：<a href="__SOURCE_URL__" target="_blank" rel="noopener">__SOURCE_DOMAIN__</a></div></header>
<main class="container">
__COVER__
<h1>__TITLE__</h1>
<div class="meta">__META_LINE__</div>
<article>
__CONTENT__
</article>
<div class="footer-note">
<p><strong>关于翻译</strong>：本文为外文页面的中文翻译，图片内容保持原文未翻译。翻译仅供参考，请以<a href="__SOURCE_URL__" target="_blank" rel="noopener">英文原文</a>为准。</p>
<p>来源：<a href="__SOURCE_URL__" target="_blank" rel="noopener">__SOURCE_URL__</a></p>
</div>
</main>
</body>
</html>"""

TECH_DARK = CLEAN.replace(
    "body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC','Hiragino Sans GB','Microsoft YaHei',sans-serif;background:#fff;color:#1a1a1a;line-height:1.75;font-size:17px}",
    "body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC','Hiragino Sans GB','Microsoft YaHei',sans-serif;background:linear-gradient(180deg,#0f172a 0%,#1e293b 100%);color:#e2e8f0;line-height:1.75;font-size:17px;min-height:100vh}"
).replace(
    "h1{font-size:36px;font-weight:700;line-height:1.25;margin-bottom:16px;letter-spacing:-.02em}",
    "h1{font-size:36px;font-weight:700;line-height:1.25;margin-bottom:16px;letter-spacing:-.02em;color:#f1f5f9}"
).replace(
    "h2{font-size:26px;font-weight:700;margin-top:40px;margin-bottom:16px;line-height:1.35;letter-spacing:-.01em}",
    "h2{font-size:26px;font-weight:700;margin-top:40px;margin-bottom:16px;line-height:1.35;letter-spacing:-.01em;color:#f1f5f9}"
).replace(
    "h3{font-size:20px;font-weight:600;margin-top:28px;margin-bottom:12px}",
    "h3{font-size:20px;font-weight:600;margin-top:28px;margin-bottom:12px;color:#f1f5f9}"
).replace(
    "p{margin-bottom:18px;color:#2a2a2a}", "p{margin-bottom:18px;color:#cbd5e1}"
).replace(
    "a{color:#10a37f;text-decoration:none;border-bottom:1px solid rgba(16,163,127,.3)}",
    "a{color:#34d399;text-decoration:none;border-bottom:1px solid rgba(52,211,153,.3)}"
).replace(
    "li{margin-bottom:8px;color:#2a2a2a}", "li{margin-bottom:8px;color:#cbd5e1}"
).replace(
    "li p{margin-bottom:6px}", "li p{margin-bottom:6px;color:#cbd5e1}"
).replace(
    "figure img{width:100%;border-radius:8px;border:1px solid #e5e5e5;background:#fff;padding:12px}",
    "figure img{width:100%;border-radius:8px;border:1px solid #334155;background:#0f172a;padding:12px}"
).replace(
    "figcaption{margin-top:10px;text-align:center;font-size:13px;color:#666}",
    "figcaption{margin-top:10px;text-align:center;font-size:13px;color:#64748b}"
).replace(
    "blockquote{margin:20px 0;padding:12px 20px;border-left:4px solid #10a37f;background:#f0fdf8;color:#374151;font-style:italic}",
    "blockquote{margin:20px 0;padding:12px 20px;border-left:4px solid #34d399;background:rgba(52,211,153,.08);color:#a7f3d0;font-style:italic}"
).replace(
    "code{font-family:'SFMono-Regular',Consolas,'Liberation Mono',Menlo,monospace;font-size:.9em;background:#f3f4f6;padding:2px 6px;border-radius:4px;color:#dc2626}",
    "code{font-family:'SFMono-Regular',Consolas,'Liberation Mono',Menlo,monospace;font-size:.9em;background:#1e293b;padding:2px 6px;border-radius:4px;color:#fbbf24}"
).replace(
    "pre{background:#1f2937;color:#e5e7eb;padding:16px 20px;border-radius:8px;overflow-x:auto;margin:20px 0;font-size:14px;line-height:1.6}",
    "pre{background:#0f172a;color:#e2e8f0;padding:16px 20px;border-radius:8px;overflow-x:auto;margin:20px 0;font-size:14px;line-height:1.6;border:1px solid #334155}"
).replace(
    "th{background:#f9fafb;font-weight:600}", "th{background:#1e293b;font-weight:600;color:#f1f5f9}"
).replace(
    "th,td{padding:10px 14px;text-align:left;border-bottom:1px solid #e5e5e5}",
    "th,td{padding:10px 14px;text-align:left;border-bottom:1px solid #334155}"
).replace(
    ".header{position:sticky;top:0;width:100%;height:56px;z-index:50;background:#fff;border-bottom:1px solid #e5e5e5;display:flex;align-items:center;padding:0 24px}",
    ".header{position:sticky;top:0;width:100%;height:56px;z-index:50;background:rgba(15,23,42,.9);backdrop-filter:blur(10px);border-bottom:1px solid #334155;display:flex;align-items:center;padding:0 24px}"
).replace(
    ".header .src{font-size:13px;color:#888}", ".header .src{font-size:13px;color:#94a3b8}"
).replace(
    ".header .src a{color:#10a37f;text-decoration:none;border-bottom:1px solid rgba(16,163,127,.3)}",
    ".header .src a{color:#34d399;text-decoration:none;border-bottom:1px solid rgba(52,211,153,.3)}"
).replace(
    ".container{max-width:720px;margin:0 auto;padding:48px 20px 96px}",
    ".container{max-width:720px;margin:0 auto;padding:48px 20px 96px}"
).replace(
    ".meta{color:#888;font-size:14px;margin-bottom:24px}", ".meta{color:#64748b;font-size:14px;margin-bottom:24px}"
).replace(
    ".cover{margin:0 0 32px;border-radius:8px;overflow:hidden;border:1px solid #e5e5e5}",
    ".cover{margin:0 0 32px;border-radius:12px;overflow:hidden;border:1px solid #334155;box-shadow:0 4px 24px rgba(0,0,0,.3)}"
).replace(
    ".footer-note{margin-top:56px;padding-top:24px;border-top:1px solid #e5e5e5;font-size:13px;color:#999;line-height:1.6}",
    ".footer-note{margin-top:56px;padding-top:24px;border-top:1px solid #334155;font-size:13px;color:#64748b;line-height:1.6}"
).replace(
    ".footer-note p{margin-bottom:8px;color:#999}", ".footer-note p{margin-bottom:8px;color:#64748b}"
).replace(
    "hr{border:none;border-top:1px solid #e5e5e5;margin:32px 0}",
    "hr{border:none;border-top:1px solid #334155;margin:32px 0}"
).replace(
    "strong{font-weight:600}", "strong{font-weight:600;color:#f1f5f9}"
).replace(
    "table{width:100%;border-collapse:collapse;margin:20px 0;font-size:15px}",
    "table{width:100%;border-collapse:collapse;margin:20px 0;font-size:15px}"
).replace(
    "th,td{padding:10px 14px;text-align:left;border-bottom:1px solid #334155}",
    "th,td{padding:10px 14px;text-align:left;border-bottom:1px solid #334155}"
)


# ─── CLI ────────────────────────────────────────────────
def main():
    p = argparse.ArgumentParser(description="Webpage Translation Pipeline v2.0")
    sub = p.add_subparsers(dest="cmd", required=True)

    ex = sub.add_parser("extract", help="抓取+提取+切块，生成 workdir")
    ex.add_argument("url")
    ex.add_argument("--workdir", default="work")

    ep = sub.add_parser("export", help="输出待译节点文本（模型读取）")
    ep.add_argument("workdir", default="work")
    ep.add_argument("--start", type=int, default=0)
    ep.add_argument("--end", type=int, default=10**9)

    bd = sub.add_parser("build", help="译文回填+恢复+渲染")
    bd.add_argument("workdir", default="work")
    bd.add_argument("-t", "--translations", required=True)
    bd.add_argument("-o", "--output", default="translated.html")
    bd.add_argument("--theme", choices=["clean", "tech-dark"], default="clean")
    bd.add_argument("--title", default=None)

    args = p.parse_args()
    if args.cmd == "extract":
        cmd_extract(args.url, args.workdir)
    elif args.cmd == "export":
        cmd_export(args.workdir, args.start, args.end)
    elif args.cmd == "build":
        cmd_build(args.workdir, args.translations, args.output, args.theme, args.title)


if __name__ == "__main__":
    main()
