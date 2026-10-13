# Kino - 企业级智能知识库

> K = Knowledge 知识 · I = Intelligence 智能 · N = Navigation 导航 · O = Organization 组织

基于 Matt Pocock 技能体系的企业级 AI 知识库产品研发。

## 关于 Kino 这个名字

Kino 有两层含义：
1. **词源本义**：在德语、俄语、斯拉夫语系中意为"电影院"，承载光影、叙事、流动的意象
2. **产品含义**：
   - **K**nowledge - 知识（产品核心）
   - **I**ntelligence - 智能（AI 语义理解）
   - **N**avigation - 导航（知识检索、发现）
   - **O**rganization - 组织（面向企业，以及知识的结构化组织）

也可理解为 **Knowledge IN / Knowledge OUT**——对应知识库的两个核心动作：知识沉淀入库，知识检索输出。

## 目录结构

```
kino/
├── docs/
│   ├── agents/           ← Matt Pocock 技能配置
│   ├── product/          ← 产品文档
│   │   ├── prd/          ← to-spec 输出的规格文档
│   │   ├── research/     ← 调研产出
│   │   └── domain-model/ ← 领域模型
│   └── engineering/      ← 技术文档
│       ├── adr/          ← 架构决策记录
│       └── architecture/ ← 架构设计
├── .scratch/             ← to-tickets 输出的本地工单（临时，不提交 Git）
└── README.md
```

## 当前阶段

- [x] 项目结构初始化
- [x] 技能环境配置
- [x] 产品命名确认
- [ ] 领域建模 (domain-modeling)
- [ ] 需求拷问 (grill-me)
- [ ] 规格生成 (to-spec)
- [ ] 工单拆解 (to-tickets)
- [ ] 实现 (implement)
- [ ] 代码评审 (code-review)
