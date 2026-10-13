#!/usr/bin/env python3
"""
AI 资讯素材采集脚本
用途：抓取 L1/L2 信息源的最新内容，提取活料（数字/原话/细节）
适用：ai-content-production 技能的素材驱动流程第一步

用法：
    python3 fetch-ai-materials.py              # 抓取所有 L1 源
    python3 fetch-ai-materials.py --deep 3     # 抓取 + 深入前 3 篇（抓原文提取活料）
    python3 fetch-ai-materials.py --source simon  # 只抓 Simon Willison

依赖：curl（系统自带），无 Python 第三方依赖
"""

import subprocess
import xml.etree.ElementTree as ET
import re
import html
import sys
import json

# ── 信息源配置 ──────────────────────────────────────────
# L1 每日必扫
L1_SOURCES = {
    "量子位": {
        "url": "https://www.qbitai.com/feed",
        "type": "rss",
        "lang": "zh",
        "desc": "中文日常热点，AI 行业新闻"
    },
    "Simon Willison": {
        "url": "https://simonwillison.net/atom/everything/",
        "type": "atom",
        "lang": "en",
        "desc": "工具实测，技术向，一手经验"
    },
    "TechCrunch AI": {
        "url": "https://techcrunch.com/category/artificial-intelligence/feed/",
        "type": "rss",
        "lang": "en",
        "desc": "AI 创业融资、深度报道"
    },
    "The Rundown AI": {
        "url": "https://www.therundown.ai/feed",
        "type": "rss",
        "lang": "en",
        "desc": "每日策展，商业向，摘要精炼"
    },
    "Hugging Face Blog": {
        "url": "https://huggingface.co/blog/feed.xml",
        "type": "atom",
        "lang": "en",
        "desc": "技术博客，周更，模型/框架发布"
    },
}

# L2 按需深读（触发式抓取）
L2_SOURCES = {
    "Ars Technica AI": {
        "url": "https://arstechnica.com/ai/feed/",
        "type": "rss",
        "lang": "en",
        "desc": "深度技术分析"
    },
    "VentureBeat AI": {
        "url": "https://venturebeat.com/category/ai/feed/",
        "type": "rss",
        "lang": "en",
        "desc": "商业+技术交叉"
    },
    "The Verge AI": {
        "url": "https://www.theverge.com/ai-artificial-intelligence/rss",
        "type": "rss",
        "lang": "en",
        "desc": "消费科技视角"
    },
}

USER_AGENT = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) "
              "AppleWebKit/537.36 (KHTML, like Gecko) "
              "Chrome/126.0.0.0 Safari/537.36")


def fetch_rss(url, source_type, limit=8):
    """抓取 RSS/Atom feed，返回条目列表"""
    try:
        r = subprocess.run(
            ["curl", "-sL", "--max-time", "15",
             "-A", USER_AGENT, url],
            capture_output=True, text=True, timeout=20
        )
        if r.returncode != 0 or not r.stdout.strip():
            return []

        root = ET.fromstring(r.stdout)

        if source_type == "rss":
            items = root.findall('.//item')
            results = []
            for item in items[:limit]:
                title = item.findtext('title', '').strip()
                link = item.findtext('link', '').strip()
                desc = item.findtext('description', '').strip()[:300]
                date = item.findtext('pubDate', '').strip()
                results.append({
                    'title': title, 'link': link,
                    'desc': desc, 'date': date
                })
        elif source_type == "atom":
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            items = root.findall('.//atom:entry', ns)
            results = []
            for item in items[:limit]:
                title_el = item.find('atom:title', ns)
                title = title_el.text.strip() if title_el is not None else ''
                link_el = item.find('atom:link', ns)
                link = link_el.get('href', '') if link_el is not None else ''
                summary_el = item.find('atom:summary', ns) or item.find('atom:content', ns)
                desc = (summary_el.text or '')[:300].strip() if summary_el is not None else ''
                updated_el = item.find('atom:updated', ns)
                date = updated_el.text.strip() if updated_el is not None else ''
                results.append({
                    'title': title, 'link': link,
                    'desc': desc, 'date': date
                })

        # 清理 HTML 标签
        for item in results:
            desc = item['desc']
            desc = re.sub(r'<[^>]+>', ' ', desc)
            desc = html.unescape(desc)
            desc = re.sub(r'\s+', ' ', desc).strip()
            item['desc'] = desc

        return results
    except Exception as e:
        return []


def fetch_article(url, max_chars=5000):
    """
    抓取文章全文，提取纯文本内容。
    处理 Cloudflare/WAF: 用 curl + 真实 UA + 无 JS 回退。
    返回: (status, content)
        status: 'ok' / 'error' / 'truncated'
    """
    try:
        r = subprocess.run(
            ["curl", "-sL", "--max-time", "25",
             "-A", USER_AGENT, url],
            capture_output=True, text=True, timeout=30
        )
        h = r.stdout

        # 提取 article 内容区域
        m = re.search(r'<article[^>]*>(.*?)</article>', h, re.DOTALL | re.IGNORECASE)
        article = m.group(1) if m else h

        # 移除 script/style/noscript/svg
        for tag in ['script', 'style', 'noscript', 'svg', 'nav', 'header', 'footer', 'aside']:
            article = re.sub(f'<{tag}[^>]*>.*?</{tag}>', ' ', article, flags=re.DOTALL | re.IGNORECASE)

        # 块级元素转行
        for tag in ['p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'br', 'tr', 'blockquote', 'pre']:
            article = re.sub(f'<{tag}[^>]*>', '\n', article, flags=re.IGNORECASE)

        # 移除剩余标签
        article = re.sub(r'<[^>]+>', '', article)
        article = html.unescape(article)

        # 清理空白
        article = re.sub(r'\n{3,}', '\n\n', article)
        article = re.sub(r'[ \t]+', ' ', article)
        lines = [l.strip() for l in article.split('\n')]
        article = '\n'.join(l for l in lines if l)

        if not article.strip():
            return ('error', 'Empty content after extraction')

        if len(article) > max_chars:
            return ('truncated', article[:max_chars] + "\n\n[...截断...]")

        return ('ok', article)
    except Exception as e:
        return ('error', str(e))


def extract_living_material(article_text):
    """
    从文章文本中提取"活料"——具体数字、原话、关键细节。
    返回一个 dict 或列表。
    """
    materials = []

    # 找数字（百分比、金额、数量等）
    number_patterns = [
        r'(\d+[\.\d]*%?)',           # 百分比/数字
        r'(\$[\d,]+\.?\d*\s*(?:万|亿|million|billion)?)',  # 美元金额
        r'(\d+[\.\d]*\s*万)',         # 万
        r'(\d+[\.\d]*\s*亿)',         # 亿
    ]

    # 找引号内的原话
    quote_pattern = r'[""]([^""]{10,})[""]'

    lines = article_text.split('\n')
    numbers_found = []
    quotes_found = []

    for line in lines:
        # 找数字
        for pat in number_patterns:
            nums = re.findall(pat, line)
            numbers_found.extend(nums)
        # 找原话
        quotes = re.findall(quote_pattern, line)
        quotes_found.extend(quotes)

    return {
        'numbers': list(set(numbers_found))[:10],
        'quotes': list(set(quotes_found))[:5],
        'total_chars': len(article_text),
    }


def display_sources(sources, label, limit=8):
    """显示一批来源的 RSS 条目"""
    for name, cfg in sources.items():
        print(f"\n{'='*60}")
        print(f"【{name}】{cfg['desc']} ({cfg['lang']})")
        print(f"  {cfg['url']}")
        print('='*60)

        items = fetch_rss(cfg['url'], cfg['type'], limit)
        if not items:
            print("  ❌ 抓取失败或无条目")
            continue

        for i, item in enumerate(items):
            print(f"\n  [{i+1}] {item['title']}")
            print(f"      时间: {item['date']}")
            desc = item['desc'][:200]
            if desc:
                print(f"      摘要: {desc}")
            print(f"      链接: {item['link']}")


def deep_dive(items, count=3):
    """深入抓取指定条目的原文并提取活料"""
    for i, item in enumerate(items[:count]):
        if not item['link']:
            continue
        print(f"\n{'─'*60}")
        print(f"  深度挖掘 [{i+1}]: {item['title']}")
        print(f"  链接: {item['link']}")
        print(f"{'─'*60}")

        status, content = fetch_article(item['link'])
        if status == 'error':
            print(f"  ❌ 抓取失败: {content}")
            continue

        print(f"  📄 状态: {status} ({len(content)} 字符)")
        materials = extract_living_material(content)
        if materials['numbers']:
            print(f"  🔢 发现数字: {', '.join(materials['numbers'][:5])}")
        if materials['quotes']:
            for q in materials['quotes'][:3]:
                print(f"  💬 原话: \"{q}\"")

        # 显示前 1000 字预览
        print(f"\n  --- 正文预览 ---")
        print(content[:1000])
        print(f"  ... (共 {len(content)} 字符)")


def main():
    # 解析参数
    deep_count = 0
    source_filter = None

    args = sys.argv[1:]
    for i, arg in enumerate(args):
        if arg == '--deep' and i + 1 < len(args):
            deep_count = int(args[i + 1])
        elif arg == '--source' and i + 1 < len(args):
            source_filter = args[i + 1]

    print("=" * 60)
    print("  AI 资讯素材采集器")
    print("=" * 60)

    # 抓取 L1 源
    print("\n\n📡 L1 每日必扫源")
    if source_filter:
        filtered = {k: v for k, v in L1_SOURCES.items()
                    if source_filter.lower() in k.lower() or source_filter.lower() in v['url']}
        display_sources(filtered, "L1")
    else:
        display_sources(L1_SOURCES, "L1")

    # 抓取 L2 源（快速预览）
    print("\n\n📡 L2 按需深读源")
    display_sources(L2_SOURCES, "L2", limit=3)

    # 深度挖掘
    if deep_count > 0:
        # 收集所有 L1 条目
        all_items = []
        for name, cfg in L1_SOURCES.items():
            items = fetch_rss(cfg['url'], cfg['type'], deep_count)
            all_items.extend(items[:2])

        if all_items:
            print(f"\n\n🔍 深度挖掘前 {deep_count} 篇")
            deep_dive(all_items, deep_count)

    print("\n\n✅ 完成")


if __name__ == '__main__':
    main()