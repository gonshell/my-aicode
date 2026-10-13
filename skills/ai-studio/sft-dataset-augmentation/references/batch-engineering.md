# LLM 批量生成工程细节

垂域 SFT 数据增强场景下的批量生成工程实践。

## 基础架构

```
worker 函数 → 单条请求处理 → run_batch 批调度 → 每批落盘
```

## 关键参数（经验值）

| 参数 | 默认值 | 说明 |
|------|--------|------|
| batch_size | 40 | 每批提交数量 |
| concurrency | 3 | 并发数。DeepSeek 并发 8 触发限流+退避，从 3 起步 |
| max_retries | 3 | 普通重试次数 |
| aggressive_retries | 5 | 顽固条目升级重试次数 |
| 空 content 退避 | 0.4s | 模型空返回时的重试间隔（短，因为是瞬时失败） |
| 429/5xx 退避 | 指数退避 | 服务端压力时的重试间隔 |

## 断点续跑三件套

1. **done 进度文件**：输入 id 集合，与结果文件分离
2. **results 文件**：成功输出，append 模式
3. **fail.json**：失败条目，便于 rerun

一输入多输出时，进度用输入 id 计，不用输出行数。

## 空 content 处理

DeepSeek v4-flash 对短请求空返回率极高（3 次 2 次空）。

- 空串 → 退避 0.4s 快速重试
- 空返回不一定是模型问题，可能是 max_tokens 截断（finish_reason=length）
- 诊断：单发请求看 finish_reason
- 解决：max_tokens 从 1024 提到 1536（长问题需 2048+）
- 降温度是辅助手段（高温度先写铺垫语，耗 token 加大截断概率）

## JSON 容错（三层递进）

```python
def extract_json_array(text):
    # 1. 直接解析
    try: return json.loads(text.strip())
    except: pass
    # 2. 截取首尾括号
    s, e = text.find("["), text.rfind("]")
    if s != -1 and e > s:
        try: return json.loads(text[s:e+1])
        except: pass
    # 3. 逐行提取对象
    results = []
    for line in text.split("\n"):
        line = line.strip().strip(",")
        if line.startswith("{") and line.endswith("}"):
            try:
                obj = json.loads(line)
                if isinstance(obj, dict): results.append(obj)
            except: continue
    return results or None
```

降低格式失败的技巧：
- prompt 简短，规则 ≤5 条，一行一条
- 格式示例放最后
- 失败重试时追加一句"只输出JSON数组，不要其他文字"
- 长约束 prompt 反而降低格式遵循率（实测 6%→30%）

## 失败分类与升级阶梯

| 失败类型 | 特征 | 处理 |
|----------|------|------|
| 空 content（截断） | 多次重试同位置失败，长问题多发 | 提 max_tokens 到 1536/2048 |
| 空 content（瞬时） | 偶发，重试即好 | 0.4s 快速重试 |
| 401 Unauthorized | 全败，单发也败 | key 失效，切备用 key |
| 429 限流 | 大量失败，带 retry-after | 指数退避，降并发 |
| 5xx 服务端 | 偶发 | 指数退避 |
| JSON 解析失败 | 返回有内容但格式错 | 三层容错 + 重试时加强制输出 |
| 内容校验失败 | 事实/格式不合要求 | 模板兜底 > 反复重试 LLM |

## 诊断隔离法

- 批量全败 + 单发成功 → 查封装代码（索引/进度/解析）
- 单发也失败且无 4xx → 怀疑服务端故障窗口，恢复后重跑，勿先改代码
- 失败集中在某类任务 → 该类 prompt 有问题，不是整体问题

## worker 必须透传错误类型

吞异常只返回 None = 大面积失败无法诊断。
worker 返回 `(idx, text, err_type)`，批次结束按类型 Counter 打印分布 + 前 5 条样例。一次打印区分 key 失效、限流、模型空返回三类故障。

## 分批调用的索引陷阱

chat_batch 的 results 按传入 idx 定位且每次调用重建。分批循环里若传全局 idx，第二批就 IndexError。
**批内用局部索引**（enumerate(chunk)），zip 回写时对齐。

## 补跑也要断点续跑

失败补跑必须走 run_batch（每批落盘），不能直跑 chat_batch——chat_batch 全跑完才落盘，中断全丢。
aggressive 重试也走同一路径，只在 prompt/参数上调整。
