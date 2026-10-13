# 正文提取策略

> 不同网站的 HTML 结构差异很大，需要分层提取策略
> 版本：v0.1
> 最后更新：2026-08-26

---

## 三级提取策略

按优先级从高到低尝试，一旦成功且内容长度达标就停止。

| 级别 | 策略 | 准确度 | 适用范围 |
|------|------|--------|----------|
| L1 | 语义标签查找 | 高 | 现代博客、文档站、CMS |
| L2 | 内容区域启发式 | 中 | 结构较规范的网站 |
| L3 | 文本密度分析 | 低 | 结构混乱的老网站 |

---

## L1：语义标签查找

### 查找顺序

1. **`<article>`** — 最理想，专门用于文章内容
2. **`<main>`** — 主内容区域，通常不含导航和侧边栏
3. **`<div role="main">`** — ARIA 角色标记的主内容

### 判断标准

- 内容长度 > 500 字符
- 包含至少一个 `<h1>` 或 `<h2>`
- 文本占比 > 30%（不是全是图片和链接）

### 已知支持的网站

| 网站 | 提取标签 | 备注 |
|------|---------|------|
| OpenAI Developers | `<article>` | 干净完整 |
| OpenAI Blog | `<article>` | 干净完整 |
| Anthropic Research | `<article>` | |
| Google DeepMind Blog | `<article>` | |
| GitHub Blog | `<article>` | |
| Medium | `<article>` | 需要处理 paywall |
| Dev.to | `<article>` | |
| Hugging Face Blog | `<article>` | |

---

## L2：内容区域启发式

当 L1 失败时，按 class/id 名称查找内容容器。

### 常见的 content 类名

```
content, main-content, post-content, article-content
entry-content, blog-content, story-content, body-content
post, article, entry, story
```

### 查找逻辑

```
1. 查找所有 div/section，检查其 class/id 是否包含上述关键词
2. 过滤掉明显不是正文的（nav, footer, sidebar, comment, header）
3. 对剩余候选，计算文本长度
4. 返回最长的那个
```

### 判断标准

- 候选数量 ≥ 1
- 最长候选文本长度 > 1000 字符
- 最长候选是第二长的 2 倍以上（避免抓到多个长度相近的区块）

### 已知需要 L2 的网站

- 部分 WordPress 主题（没有 article 标签）
- 一些老的媒体网站
- 部分 Substack 自定义主题

---

## L3：文本密度分析

当 L1 和 L2 都失败时的兜底方案。

### 算法思路

```
1. 遍历 DOM 中的所有块级元素
2. 计算每个元素的「文本密度」：
   文本字数 / (标签数量 + 链接数量)
3. 找到密度最高的连续区块
4. 向外扩展，合并相邻的高密度区块
```

### 特点

- 优点：几乎所有网站都能用
- 缺点：可能漏掉导航、广告，也可能误抓评论区
- 适用：结构非常不规范的老网站

---

## 常见问题与处理

### 问题 1：SPA / JS 渲染页面

**现象**：curl 抓到的 HTML 正文很短（< 500 字），主要内容靠 JS 渲染。

**检测方法**：
- 提取的正文长度 < 500 字符
- HTML 中有大量 `<script>` 但内容很少
- 有 `id="app"` 或类似的 React/Vue 挂载点

**处理方式**：
- 提示用户：「该页面可能是 JS 渲染的，需要浏览器方式抓取」
- 回退方案：用 Playwright/Chromium headless 渲染后再提取
- 当前脚本不内置浏览器渲染（减少依赖）

### 问题 2：分页文章

**现象**：文章分成多页，每页只有一部分内容。

**检测方法**：
- 页面有「下一页」或分页导航
- 内容明显不完整（读到一半突然结束）

**处理方式**：
- 检测是否有多页，有则全部抓取后合并
- 简单判断：查找 "next page"、"下一页"、数字分页链接

### 问题 3：Paywall / 付费墙

**现象**：只能看到文章开头，大部分内容被付费墙挡住。

**检测方法**：
- 正文很短，但页面有 "subscribe"、"会员"、"付费" 等关键词
- 有明显的 paywall 容器元素

**处理方式**：
- 诚实告知用户：该文章有付费墙，只能获取免费部分
- 不要试图绕过付费墙

### 问题 4：评论区混入

**现象**：提取的正文末尾包含了大量评论。

**检测方法**：
- 查找 "comment"、"评论"、"reply" 等关键词的区块
- 内容风格突变（从正式变成口语）

**处理方式**：
- 在候选元素中排除含 "comment" 的 class/id
- 提取时遇到评论区截断

### 问题 5：相关文章 / 推荐阅读混入

**现象**：正文末尾有"相关文章"、"推荐阅读"区块。

**处理方式**：
- 排除 class/id 含 "related"、"recommend"、"similar" 的区块
- 提取时遇到"相关文章"标题截断

---

## 清洗规则

提取到正文后，统一做以下清洗：

1. **移除脚本**：`<script>`、`<noscript>`、`<style>`
2. **移除导航**：`<nav>`、`<header>`、`<footer>`、`<aside>`
3. **移除广告**：class/id 含 "ad"、"advertisement"、"sponsor" 的区块
4. **移除分享按钮**：class 含 "share"、"social" 的区块
5. **移除 iframe**：嵌入的视频、表单等
6. **移除注释**：HTML 注释
7. **整理空白**：多余的空行压缩

---

## 图片提取

### 图片收集范围

- 正文区域内的所有 `<img>` 标签
- og:image（封面图，单独处理）

### 图片过滤

- 过滤小于 1x1 的跟踪像素
- 过滤 data URI（已经是内嵌的）
- 过滤图标类图片（宽高 < 50px）
- 过滤 SVG（排版用的，不是内容图）

### 图片下载失败处理

- 单张图片下载失败不影响整体流程
- 失败的图片保留原始 src URL（用户有网时仍能看到）
- 在日志中记录失败的图片 URL

---

## 链接修复

所有相对路径的链接和图片地址，都要补全为绝对路径：

| 原始路径 | 基准 URL | 结果 |
|---------|---------|------|
| `/images/foo.jpg` | `https://example.com/blog/post` | `https://example.com/images/foo.jpg` |
| `./bar.html` | `https://example.com/blog/post` | `https://example.com/blog/bar.html` |
| `../about/` | `https://example.com/blog/post` | `https://example.com/about/` |
| `https://other.com/x` | 任意 | 不变 |

用 `urllib.parse.urljoin` 处理，覆盖所有情况。
