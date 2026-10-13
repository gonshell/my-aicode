# JSON 输出可靠性与容错解析

## 降低格式失败率

### Prompt 设计

- **规则简短**：4-5 条以内，一行一条
- **示例放最后**：格式示例放在 prompt 末尾
- **不要长约束**：长约束 prompt 反而降低格式遵循率（实测解析失败率从 6% 升到 30%）
- **失败重试追加一句**："只输出 JSON，不要其他任何文字。"

### 输出格式

**推荐数组格式**：
```json
[{"question": "...", "answer": "..."}]
```

**推荐单对象格式**：
```json
{"fact_accuracy": 4.5, "reason": "..."}
```

## 三层容错解析

```python
def extract_json_array(text):
    # 1. 直接解析
    try:
        return json.loads(text.strip())
    except Exception:
        pass
    # 2. 截取首尾括号
    s, e = text.find("["), text.rfind("]")
    if s != -1 and e > s:
        try:
            return json.loads(text[s:e+1])
        except Exception:
            pass
    # 3. 逐行提取对象
    results = []
    for line in text.split("\n"):
        line = line.strip().strip(",")
        if line.startswith("{") and line.endswith("}"):
            try:
                obj = json.loads(line)
                if isinstance(obj, dict):
                    results.append(obj)
            except Exception:
                continue
    return results or None
```

单对象解析同理，换 `{`/`}`。

## 常见失败模式

| 模式 | 原因 | 处理 |
|------|------|------|
| JSON 前后有解释文字 | 模型"先说两句再输出" | 截取首尾括号（第2层） |
| 数组变成单对象 | 模型觉得"只有一条就不用数组" | 兼容单对象 → 转数组 |
| 引号不匹配 / 转义错 | 中文引号 / 未转义 | 宽松正则兜底 |
| 完全空返回 | max_tokens 截断 / 模型空返回 | 提 max_tokens + 重试 |
| 末尾被截断 | max_tokens 不够 | 提 max_tokens（1024→1536 通常解决） |

## 批量生成的 JSON 可靠性工程

1. **批次内容错**：单条解析失败不算整批失败，收集成功的，失败的单独重试
2. **失败分级**：解析失败的条目进 fail.json，与空返回、超时分开统计
3. **重试升级**：正常失败 → 追加强制输出 prompt 重试 → 单发 + max_tokens=4096 + 降温度
4. **模板兜底**：对约束类/格式固定的任务，返回格式错时直接用模板生成（零幻觉），不要反复重试 LLM
