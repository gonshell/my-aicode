# 交付物版本与再生成（覆写前先归档 / 无 VCS 恢复 / 多形态产物）

长文档交付物通常有**多个派生形态**（md 源 → HTML → DOCX → 飞书文档），且**没有 git**。
本文件记录这一类交付链的版本纪律与实测恢复法。

## 一、铁律：覆写源文件前先归档旧版

重构 = 把新内容写回**同一个路径**。`write_file` 是整体覆盖，**先 mv 再写，一步都不省**：

```bash
# 归档命名建议：<原名>-v1-evidence-index.md（旧版仍有证据索引价值，别删）
mv AN-11-lattice-data-model.md AN-11-lattice-data-model-v1-evidence-index.md
```

### 实测事故
一个 39KB 的调研报告被直接覆写，同目录**不是 git 仓库**（`fatal: not a git repository`），
旧版内容一度只存在于会话上下文里。最终完整还原。

## 二、无 VCS 时的恢复顺序（按可用性递减）

| 优先级 | 恢复源 | 说明 |
|---|---|---|
| ① | **转换管道中间件** `_build/<x>/<x>_processed.md` | 通常只把 ```mermaid 块替换成 `![](mermaid/*.png)`，其余逐字一致。**最完整的恢复源** |
| ② | **源碎片** `.mmd` / `.docx` / 图片 | `.mmd` 可直接补回 mermaid 块；docx 内嵌图可提取 |
| ③ | **派生 HTML** 正文 | 有标签噪音，需反解析，最后手段 |

还原实现要点：用正则把图片引用换回围栏块，并**清理替换产生的多余空行**（`\n\n\n```mermaid` → `\n\n```mermaid`），
使字节/行数与原件对齐（实测 38,936B/462 行 vs 原件 38,935B/461 行）。
**还原后必须做内容抽查**：挑若干只可能出现在原件的具体字符串（章节断言、单位后缀、特有 URL、两处 mermaid 源码）逐条 `in` 校验。

### 由此推出的预防措施
- **每个 mermaid 块都落盘 `.mmd` 源码**与 PNG 并存 —— 它就是 md 的备份碎片。
- 交付链的**每一环产物都留在项目里**（`_build/<x>/` 存 processed.md + docx），不要只留最终 HTML。
- 有条件就给报告目录 `git init`；没有就靠上面三条。

## 三、多形态产物的再生成链

```
源 md ──┬─ 转换脚本（mermaid 预渲染 PNG → base64 内嵌）──> 单文件 HTML
        └─ pandoc（mermaid 块 → 相对路径图片引用）───> DOCX ──> 飞书导入
```

- **HTML**：图题/图号来自转换脚本里的 `MERMAID_IMGS` 顺序映射表 → 章节重排后**必须同步改名**。
- **DOCX**：`pandoc <processed>.md -o <x>.docx --toc --toc-depth=2 --resource-path=. --reference-doc=<上一版docx>`。
  - `--reference-doc` 文件**必须是有效 zip**（坏的报 `Did not find end of central directory signature`）；先验 `zipfile.ZipFile(p)`。
  - 无效时**退回上一版 docx 当模板**以继承样式，或省略该参数。
  - 命令用列表 append 构造，**不要 `cmd.insert()` 硬插**——`-o` 后必须紧跟输出名，插错会让 pandoc 把 reference doc 当 `-o` 的值并报 `withBinaryFile: does not exist`。
- **登记同步**：产物变了要同步更新索引（README / MANIFEST）：新增行、归档件标注、来源清单、再生成指引。
  **顺手重算索引表条目总数**（历史计数会漂移，例如标"38 条"实际已 39 条）。

## 四、交付说明里的数字

一律实测后再写：

```python
len(re.findall(r"^## ", md, re.M))      # 章数
len(re.findall(r"^### ", md, re.M))     # 节数
len(re.findall(r"^\|", md, re.M))       # 表格行数
md.count("```mermaid")                  # 图数
os.path.getsize(path)                   # 字节数
```

曾凭印象写"12 章 33 节"（实际 13 章 29 节），被自己后续核对发现并返工——**印象值不要进交付物**。
