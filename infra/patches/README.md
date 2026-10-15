# 本地补丁存档（infra/patches）

对第三方代码（hermes-agent 核心、hermes 插件）的本地修改，一律以补丁形式登记在此。
原则：**能配置解决就不打补丁。补丁是负债——每次上游升级都要还。**

## 目录结构

```
infra/patches/
├── README.md              # 本文件：规则与规程
├── REGISTRY.yaml          # 补丁清单（机器可读，脚本读写它）
├── bin/
│   ├── pr-submit          # 把一条补丁提为上游 PR
│   └── pr-status          # 核查所有 active 补丁的 PR 状态
├── hermes-agent/          # 对 hermes 核心本体的补丁
│   └── NNNN-<slug>-<base_version>.patch
└── hermes-plugins/
    └── <plugin-name>/     # 对某个插件的补丁
        ├── NNNN-<slug>-<base_version>.patch
        └── NNNN-<slug>-<base_version>.test.py   # 与补丁同序号的自包含验证脚本
```

被改对象分两类目录：`hermes-agent/`（核心，装在 /usr/local/lib/hermes-agent）
和 `hermes-plugins/<name>/`（~/.hermes/plugins 下的 git 克隆）。其它第三方代码以后
按归属再开同级目录。

## 命名规则

- 补丁文件：`NNNN-<slug>-<base_version>.patch`
  - `NNNN`：同一目标内的应用顺序，与 git format-patch 编号一致；0001、0002……
  - `slug`：改动内容，全小写连字符（zh-extract-patterns、fix-sentence-split）
  - `base_version`：补丁基于的上游版本（v0.6.1）。文件名直接回答"打在哪个版本"
- 验证脚本：与补丁同序号，扩展名 `.test.py`，必须自包含（临时目录建库，不写真实数据，
  不依赖 /root/.hermes/cache/scratch 等会话级路径）
- 补丁 id（REGISTRY 内）：`<target短名>-NNNN`，如 `holographic-0001`，跨版本稳定；
  文件名序号会随重排变化，id 是人和脚本引用补丁的稳定标识
- **状态不进文件名、不进目录名**。active/merged 只写在 REGISTRY 字段里；文件名是
  稳定标识，改名会让所有引用和 git 历史断裂

## 补丁文件的产生

补丁必须是 `git format-patch` 产物（带提交信息，可 `git am` 重放），不手写裸 diff。

工作方式：在被改代码自己的 git 仓库里建长期分支 `local-patches`，基线为上游 release tag，
每个逻辑改动一个 commit，提交信息以 `local-patch NNNN:` 开头，并在代码注释中留下
`Local patch NNNN:` 锚点（升级后 grep 锚点即可确认补丁是否还在）。

```
cd ~/.hermes/plugins/<name>
git switch -c local-patches          # 基于当前 release commit
# 改动、提交（每个逻辑改动一个 commit）
git format-patch <base_commit> -o <临时目录>
# 复制到本存档目录并按命名规则改名
```

一个改动如果将来可能单独提 PR（例如一个 bugfix + 一个特性），从一开始就拆成两个补丁。

## 登记规程（新补丁落地时）

1. 确认没有配置层面的解法
2. 在目标仓库 local-patches 分支上改代码、写自包含验证脚本、先跑出通过结果
3. format-patch 导出，按命名规则放入本目录，验证脚本同目录
4. REGISTRY.yaml 增加一条记录（字段见该文件内注释），status: active
5. fact_store 加一条**指针**事实（不重复机制和实现细节）：补丁 id + 本目录路径 +
   "升级覆盖后按 REGISTRY 重放"，entities 挂被改工具名
6. 提交 my-aicode

## 升级后核查 SOP（每次 hermes update / plugins update 之后）

1. `git -C <目标仓库> status` 确认分支与工作区状态；注意 hermes 可能做 detached HEAD
   精确版本 checkout 而不是分支 pull，先看清 HEAD 形态再操作
2. 对 REGISTRY 中每个 status: active 且 target 匹配的补丁：
   grep `Local patch NNNN` 锚点 → 不在则补丁已丢
3. 丢失则重放：在目标仓库 `git am <补丁文件>`（或对新版分支 rebase local-patches）；
   冲突手工解决，更新补丁文件与 base_version/base_commit
4. 跑该补丁的 `.test.py`，exit 0 才算恢复
5. `bin/pr-status` 核查已提 PR 是否合并；合并则走退役流程

## 上游 PR 流程

通用流程在此（具体分支名/PR 要点在 REGISTRY 条目内）：

1. `bin/pr-submit <patch-id>`：读 REGISTRY → 准备 /root/workspace/forks/<repo>
   工作副本（不存在则 clone 个人 fork 并挂 upstream remote）→ 建分支 → git am →
   push → 用 gh 开 PR → 回写 upstream_pr / pr_status
2. 前置条件：`gh auth login` 一次（gh 未登录时脚本退化为只 push 并打印 compare URL，
   浏览器手动开 PR）
3. PR 工作副本在 /root/workspace/forks/（易失、可重克隆），**不放进 my-aicode**
   （嵌套 git 仓库）；PR 的永久记录是 REGISTRY 里的 upstream_pr URL
4. PR 状态值：not-proposed / draft / open / merged / closed（被关未合并）
5. 已提 PR 期间本地补丁与 local-patches 分支**不删**；只有 pr_status=merged 才退役

## 退役

- 上游合并：status 改 merged-upstream、填 upstream_pr；从 local-patches 删除对应
  commit；补丁文件**原地保留**作历史档案；fact_store 指针事实 supersede
- 被上游拒绝且不再追：status=abandoned 并记录原因；确认本地是否回退
- 新补丁取代旧补丁：旧的 status=superseded，字段写明被谁取代

## 脚本

- `bin/pr-submit <patch-id>` — 提交上游 PR（见上）
- `bin/pr-status [patch-id]` — 查 PR 状态，merged 的提示退役；建议升级 SOP 后跑一次
