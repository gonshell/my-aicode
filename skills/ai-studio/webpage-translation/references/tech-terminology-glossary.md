# 技术术语对照表

> AI/LLM 领域常用技术术语的标准译法 + 一句话解释
> 版本：v0.1
> 最后更新：2026-08-26

---

## 使用方法

1. 翻译时遇到术语，先查表，用表里的译法
2. 首次出现时：「中文名（英文原名）—— 一句话解释」
3. 后文直接用中文名
4. 表里没有的，根据上下文自行判断，首次出现加解释

---

## 核心概念

| 英文 | 中文 | 一句话解释 |
|------|------|-----------|
| LLM / Large Language Model | 大语言模型 | 基于海量文本训练的神经网络，能理解和生成自然语言 |
| Agent | 智能体 / Agent | 能自主规划、调用工具、执行任务的 AI 系统 |
| Harness | 框架 / 运行时 | 包裹在模型外围的执行系统，管理工具调用和上下文 |
| Agent loop | Agent 循环 | Agent 反复执行「思考→行动→观察」的迭代过程 |
| Prompt | 提示词 | 给 AI 模型的输入指令或问题 |
| Context | 上下文 | 模型在生成回复时能参考的所有历史信息 |
| Context window | 上下文窗口 | 模型一次能处理的最大 token 数量 |
| Token | Token / 词元 | 模型处理文本的基本单位，约等于 0.7 个中文汉字 |
| Inference | 推理 | 模型根据输入生成输出的过程（区别于训练） |
| Training | 训练 | 用大量数据让模型学习参数的过程 |
| Fine-tuning | 微调 | 在预训练模型基础上用特定数据进一步训练 |
| RAG / Retrieval-Augmented Generation | 检索增强生成 | 先检索相关文档再生成回答的技术 |

## 对齐与安全

| 英文 | 中文 | 一句话解释 |
|------|------|-----------|
| RLHF | 基于人类反馈的强化学习 | 用人类偏好数据训练奖励模型来对齐 AI 行为 |
| Alignment | 对齐 | 让 AI 行为符合人类价值观和意图的过程 |
| Safety | 安全 | 防止 AI 产生有害输出的技术和措施 |
| Guardrails | 护栏 / 安全边界 | 限制 AI 行为范围的机制 |
| Jailbreak | 越狱 / 绕过 | 通过特殊提示让 AI 突破安全限制 |

## 架构与技术

| 英文 | 中文 | 一句话解释 |
|------|------|-----------|
| Transformer | Transformer | 基于自注意力机制的深度学习架构，是 LLM 的基础 |
| Attention | 注意力机制 | 让模型在处理每个词时关注其他相关词的机制 |
| MoE / Mixture of Experts | 混合专家模型 | 由多个子模型组成，每次只激活部分的架构 |
| Multimodal | 多模态 | 能同时处理文本、图像、音频等多种输入的模型 |
| Embedding | 嵌入 / 向量 | 将文本等数据转换为高维向量表示 |
| Vector database | 向量数据库 | 专门存储和检索向量嵌入的数据库 |

## 工具与平台

| 英文 | 中文 | 一句话解释 |
|------|------|-----------|
| MCP / Model Context Protocol | 模型上下文协议 | OpenAI 推出的 AI 工具接入标准协议 |
| Sandbox | 沙箱 | 隔离的安全执行环境，防止 AI 操作影响系统 |
| SDK / Software Development Kit | 软件开发工具包 | 供开发者集成某项功能的代码库和工具 |
| API / Application Programming Interface | 应用程序接口 | 不同软件之间交互的接口 |
| CLI / Command Line Interface | 命令行界面 | 通过命令行操作的工具界面 |
| IDE / Integrated Development Environment | 集成开发环境 | 编写代码的综合工具（如 VS Code） |
| CI / Continuous Integration | 持续集成 | 代码提交后自动构建和测试的流程 |

## 产品名（不翻译，直接用）

以下产品名/公司名**直接保留英文**，不翻译：
- OpenAI, Anthropic, Google DeepMind, Meta
- GPT-4, GPT-5, GPT-5.6 Sol, Codex, Sora
- Claude, Gemini, Llama, Mistral
- GitHub, GitLab, VS Code, JetBrains
- Hugging Face, LangChain, LlamaIndex
- ARC-AGI, MMLU, GSM8K（基准测试名）

## 常见动词短语

| 英文 | 推荐译法 | 说明 |
|------|---------|------|
| power | 驱动 / 为……提供动力 | "Codex powers the app" → 「Codex 为这个应用提供动力」 |
| leverage | 利用 / 借助 | 不要翻成「杠杆」 |
| deploy | 部署 | 技术领域通用译法 |
| iterate | 迭代 | 产品/开发语境 |
| ship | 发布 / 上线 | 产品发布 |
| roll out | 推出 / 逐步上线 | 功能或产品的推出 |
| scale | 扩展 / 规模化 | 规模扩张 |
| integrate | 集成 / 整合 | 技术集成 |
| streamline | 简化 / 优化流程 | 流程优化 |
| address | 解决 / 应对 | 解决问题 |

---

## 补充说明

- 本表是「建议译法」，不是绝对标准。如果上下文有更合适的译法，可以调整
- 但同一篇文章内必须保持一致
- 遇到表中没有的术语，建议查一下业界通用译法（可参考机器之心、量子位等中文科技媒体的用法）
