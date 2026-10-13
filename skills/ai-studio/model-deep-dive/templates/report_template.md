# {model_name} 深度分析

> {one_liner}
>
> 信息来源：{source_url} | 分析日期：{date}
> 信息等级：S级（官方文档）/ A级（作者代码）/ B级（关联项目）
> 本报告：事实（默认） / ⚠️ 分析 / 💡 判断

---

## 一、项目定位

| 项目 | 说明 |
|---|---|
| 名称 | {name} |
| 作者/组织 | {author} |
| 许可协议 | {license} |
| 底座模型 | {base_model} |
| 一句话定位 | {one_liner} |

💡 判断：{position_judgment}

---

## 二、训练配置

| 配置项 | 值 | 说明 |
|---|---|---|
| 训练方法 | {method} | {method_note} |
| LoRA rank | {lora_rank} | {lora_note} |
| LoRA alpha | {lora_alpha} | |
| target_modules | {target_modules} | {target_note} |
| 学习率 | {lr} | {lr_scheduler} |
| Batch size | {batch_size} | 有效 batch: {effective_batch} |
| Epochs | {epochs} | |
| 序列长度 | {seq_len} | |
| 优化器 | {optimizer} | |
| Loss 掩码 | {loss_mask} | |
| 硬件 | {hardware} | |
| 训练时间 | {train_time} | |
| 成本估算 | {cost_est} | |
| 训练工具 | {tool} | |
| 最终 loss | {final_loss} | |

⚠️ 分析：{config_analysis}

---

## 三、数据

| 项目 | 说明 |
|---|---|
| 数据集 | {dataset_name} |
| 数据量 | {data_size} |
| 数据领域 | {data_domain} |
| 来源 | {data_source} |
| 筛选条件 | {filter_cond} |
| 处理流程 | {processing} |
| 教师模型（蒸馏） | {teacher_model} |
| 公开可复现 | {reproducible} |

⚠️ 分析：{data_analysis}

---

## 四、评估结果

### 基准成绩

| Benchmark | 底座 | 本模型 | 变化 |
|---|---|---|---|
| {bench1} | {base1} | {model1} | {delta1} |
| {bench2} | {base2} | {model2} | {delta2} |

### 和同类对比

| 模型 | {metric1} | {metric2} | 说明 |
|---|---|---|---|
| {peer1} | {p1v1} | {p1v2} | {p1note} |
| 本模型 | {mv1} | {mv2} | {mnote} |

⚠️ 分析：{eval_analysis}

---

## 五、技术设计分析

### 关键设计 1：{design1_name}

- **是什么**：{design1_desc}
- **为什么这么设计**：{design1_reason}
- **Trade-off**：{design1_tradeoff}

### 关键设计 2：{design2_name}

- **是什么**：{design2_desc}
- **为什么这么设计**：{design2_reason}
- **Trade-off**：{design2_tradeoff}

### 工程坑

| 坑 | 现象 | 解决方案 |
|---|---|---|
| {pitfall1} | {pit1_symptom} | {pit1_solution} |

💡 判断：{design_judgment}

---

## 六、局限性 & 风险

### 作者自述

{author_limits}

### ⚠️ 补充分析

{our_limits}

### 💡 潜在风险

{risks}

---

## 七、定位 & 价值

**核心贡献**：{core_contribution}

**适合场景**：
- {usecase1}
- {usecase2}

**不适合场景**：
- {not_usecase1}
- {not_usecase2}

**技术参考价值**：{ref_value}（高/中/低）

💡 综合判断：{final_judgment}

---

*报告生成时间：{datetime} | 信息基于公开文档，非实测验证*
