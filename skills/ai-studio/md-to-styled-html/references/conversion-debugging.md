# 转换调试失败案例详解（来自 qwen3.5_finetune_plan.md 实际转换）

## 案例 1：围栏未闭合导致 TOC 丢失（最严重）

**症状**：文档有 13 个 `##` 章节，转换后 TOC 只有 6-7 条；后面的标题全部消失。

**根因**：源 md 中某个 yaml 代码块**缺闭合围栏**——作者把闭合的 ` ``` ` 误写成了 ` ```json `（或丢失一行）。围栏总数=119（奇数），配对算法从断点开始错位，后续所有 `## 六、` 等标题被当成"代码块内部"跳过。

**定位方法**：
1. 统计围栏数：`fence_idx = [i for i, l in enumerate(lines) if l.strip().startswith('```')]`，奇数即有问题
2. 打印每对围栏的起止行和语言标注，找出"语言标注不匹配"或"块内包含标题"的异常块
3. 打印异常块附近 ±30 行内容，确认缺的是闭合行
4. **修 md 文件**（插入缺失的 ` ``` `），不是修脚本

**关键注意**：JSON/JSONL 数据里 `value` 字段常包含 ```python 代码示例字符串——这些是**内容不是围栏**。只匹配 `l.strip().startswith('```')` 的行（JSON 行以 `{` 开头，天然不匹配）。但行内含 ``` 的 JSON 字符串可能干扰"找断点"的判断，要打印原始行确认。

## 案例 2：文档自带目录链接失效

**症状**：页面出现 59 个失效锚点（`href="#一项目概述"` 找不到对应 `id`）。

**根因**：源 md 开头有 `## 目录` 章节，里面的 markdown 链接锚点格式（`#一项目概述`，无连字符）与正文标题生成的 slug（`一-项目概述`，有连字符）不一致。

**处理**：转换时检测到标题为"目录"时，**整章跳过**（含内容直到下一个 `##`），用自动生成的 `<div class="toc">` 替代。

## 案例 3：语法高亮二次处理产生嵌套错误

**症状**：代码块输出 `<span class=<span class="c-str">"c-comment"</span>>` 之类的嵌套破损。

**根因**：高亮是分步正则替换。先替换注释插入 `<span class="c-comment">`，后一步字符串替换又把 span 属性里的 `"c-comment"` 当字符串再次包裹；python 的关键字替换把 `<span class="...">` 里的 `class` 当关键字包裹。

**修复（占位符方案）**：
```python
# 步骤1：字符串 → 占位符
string_markers = []
def _str_repl(m):
    idx = len(string_markers)
    string_markers.append(m.group(1))
    return f'\x00S{idx}\x00'
l = re.sub(r'("(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\')', _str_repl, l)

# 步骤2：注释 → 占位符
comment_markers = []
def _comment_repl(m):
    idx = len(comment_markers)
    comment_markers.append(m.group(1))
    return f'\x00C{idx}\x00'
l = re.sub(r'^(#.*)$', _comment_repl, l)
l = re.sub(r'(\s)(#[^\s]*)$', lambda m: m.group(1) + _comment_repl(m), l)

# 步骤3：对纯代码做关键字/函数高亮（此时无 HTML 干扰）
l = re.sub(r'\b(def|class|import|...)\b', r'<span class="c-key">\1</span>', l)
l = re.sub(r'\b([a-zA-Z_]\w*)(?=\()', r'<span class="c-func">\1</span>', l)

# 步骤4：还原
for idx, s in enumerate(string_markers):
    l = l.replace(f'\x00S{idx}\x00', f'<span class="c-str">{s}</span>')
for idx, s in enumerate(comment_markers):
    l = l.replace(f'\x00C{idx}\x00', f'<span class="c-comment">{s}</span>')
```

**顺序原则**：字符串 → 注释 → 关键字/函数 → 还原。bash 无关键字替换，但字符串也须先于注释（避免注释正则 `#[^"]*` 匹配 span 的引号）。

## 验证检查清单（生成后必跑）

```python
import re
content = open(html_path, encoding='utf-8').read()

# 1. 标签配对
for t in ['div', 'table', 'pre', 'ul', 'ol', 'h2', 'h3', 'h4', 'span']:
    opens = len(re.findall(rf'<{t}[ >]', content))
    closes = len(re.findall(rf'</{t}>', content))
    assert opens == closes, f"{t}: {opens}/{closes}"

# 2. TOC 锚点有效性
toc_start = content.find('<div class="toc">')
toc_end = content.find('</div>', toc_start) + 10
toc_links = re.findall(r'href="#([^"]+)"', content[toc_start:toc_end])
all_ids = set(re.findall(r'id="([^"]+)"', content))
assert all(l in all_ids for l in toc_links)

# 3. 嵌套错误
assert '<span class=<span' not in content
```
