# Qwen Harness MCP Server

将千问AI平台 Token Plan 的 5 个 Harness 内置工具暴露为 MCP 工具，供 Hermes Agent（或任何 MCP 客户端）调用。

## 工具列表

| MCP Tool | Harness 工具 | 能力 |
|---|---|---|
| `qwen_web_search` | web_search | 联网搜索 |
| `qwen_web_extract` | web_extractor | 网页抓取 |
| `qwen_code_interpreter` | code_interpreter | 代码解释器（云端沙箱，有网络） |
| `qwen_t2i_search` | t2i_search | 文搜图 |
| `qwen_i2i_search` | i2i_search | 图搜图 |

## 前置条件

- 千问AI平台 Token Plan（个人版或团队版）的 API Key
- 支持 Responses API 的模型：qwen3.7-max / qwen3.7-plus / qwen3.8 系列
- Python 3.10+

## 安装

```bash
cd qwen-harness-mcp
uv venv && uv pip install -r requirements.txt
# 或
pip install -r requirements.txt
```

## 配置

编辑 `config.yaml`：

```yaml
api_key: "sk-your-token-plan-key"
base_url: "https://{WorkspaceId}.cn-beijing.maas.aliyuncs.com/compatible-mode/v1"
model: "qwen3.7-plus"
```

也可通过环境变量覆盖：
- `QWEN_HARNESS_API_KEY`
- `QWEN_HARNESS_BASE_URL`
- `QWEN_HARNESS_MODEL`

## 接入 Hermes Agent

```bash
hermes mcp add qwen-harness \
  --command "uv run --directory /path/to/qwen-harness-mcp python server.py"
```

或在 `~/.hermes/config.yaml` 中手动添加：

```yaml
mcp_servers:
  qwen-harness:
    command: "uv run --directory /path/to/qwen-harness-mcp python server.py"
```

## 接入其他 MCP 客户端

任何支持 MCP stdio 协议的客户端均可接入，配置 command 为：

```
python /path/to/qwen-harness-mcp/server.py
```

## 项目结构

```
qwen-harness-mcp/
├── server.py              # MCP Server 主入口
├── client.py              # Responses API 封装（重试/超时/解析）
├── config.py              # 配置加载（env > yaml > default）
├── config.yaml            # 用户配置文件（需手动填写）
├── tools/
│   ├── __init__.py
│   ├── web_search.py      # 联网搜索
│   ├── web_extract.py     # 网页抓取
│   ├── code_interpreter.py # 代码解释器
│   ├── t2i_search.py      # 文搜图
│   └── i2i_search.py      # 图搜图
├── requirements.txt
└── README.md
```

## 技术说明

- **协议**：OpenAI Responses API（`POST /responses`），非 Chat Completions
- **传输**：MCP stdio（Hermes 按需 spawn 子进程）
- **重试**：指数退避，最多 2 次
- **图片**：自动下载到 `/tmp/qwen_harness/`，可配合 `vision_analyze` 使用
- **超时**：普通工具 60s，code_interpreter 120s

## 限制

- Token Plan 个人版禁止 API 生产自动化调用（交互式 agent 使用不受限）
- Harness 工具按抵扣系数消耗 Credits
- 仅 qwen3.7 / qwen3.8 系列支持原生工具调用
- 并发：个人版 1-2 个 Agent

## License

MIT
