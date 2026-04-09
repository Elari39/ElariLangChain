# AI Agent Model

基于 LangChain/LangGraph 的 AI 助手代理，支持多种工具和模型提供商。

## 功能特性

- **多模型支持**: OpenAI、DeepSeek、MiniMax 等 OpenAI 兼容接口
- **对话记忆**: 基于 LangGraph 的 InMemorySaver 实现会话持久化
- **丰富工具**: 网络搜索、天气查询、网页抓取、图片搜索、文件读取等

## 环境要求

- Python 3.10+
- API Key (MiniMax / DeepSeek / OpenAI)

## 安装步骤

```bash
pip install -r requirements.txt
```

## 配置说明

在项目根目录创建 `.env` 文件：

```env
# MiniMax 配置
MINIMAX_API_KEY=your_api_key
MINIMAX_BASE_URL=https://api.minimax.chat/v1
MINIMAX_MODEL=your_model_name

# DeepSeek 配置
DEEPSEEK_API_KEY=your_api_key

# OpenAI 配置
OPENAI_API_KEY=your_api_key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_CHAT_MODEL=gpt-4

# SerpAPI (用于网络搜索)
SERPAPI_API_KEY=your_api_key
```

## 使用方法

### 运行交互式对话

```bash
python agent.py
```

### 代码调用示例

```python
from agent_factory import build_agent, build_config, build_runtime_context

# 创建 Agent
agent = build_agent()

# 构建上下文和配置
context = build_runtime_context(user_id="user_1")
config = build_config(thread_id="session_1")

# 同步调用
result = agent.invoke(
    {"messages": [{"role": "user", "content": "你好"}]},
    context=context,
    config=config,
)

# 流式调用
for chunk in agent.stream(
    {"messages": [{"role": "user", "content": "你好"}]},
    context=context,
    config=config,
):
    print(chunk)
```

## 工具列表

| 工具 | 说明 |
|------|------|
| `get_weather` | 查询城市天气 |
| `web_search` | 网络实时信息搜索 |
| `fetch_webpage` | 抓取网页正文文本 |
| `read_local_file` | 读取 `./post` 目录下的本地文件 |
| `get_mossia_pixiv_image` | 从 Pixiv 获取图片信息 |
| `get_mossia_x_image` | 从 X (Twitter) 获取图片信息 |
| `save_image_from_url` | 保存图片到本地 `./img` 目录 |
| `arxiv` | 搜索 arxiv 学术论文 |
| `wikipedia` | 搜索维基百科 |
| `python_repl` | 执行 Python 代码 |

## 项目结构

```
.
├── model.py           # 模型配置
├── agent_factory.py   # Agent 构建工厂
├── agent_tools.py     # 工具定义
├── agent.py           # 入口和交互逻辑
└── .env               # 环境变量配置
```
