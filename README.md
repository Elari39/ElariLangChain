# AI Agent Model

基于 LangChain 与 LangGraph 的命令行 AI Agent 项目，主入口为 `agent.py`。项目支持会话记忆、流式输出和工具调用，适合用来搭建可扩展的本地智能助手。

## 功能概览

- 基于 LangChain `create_agent` 组织模型、上下文和工具调用
- 基于 LangGraph 的 `InMemoryStore` 与 `InMemorySaver` 保存会话状态
- 支持流式输出，适合命令行持续对话
- 内置网络搜索、天气查询、网页抓取、本地文件读取、图片信息获取与图片保存能力
- 已接入结构化 Pixiv 图源工具，支持随机获取与条件筛选

## 环境要求

- Python 3.10 及以上
- 可用的模型接口配置
- 可选的 SerpAPI Key，用于网络实时搜索

## 安装

```bash
pip install -r requirements.txt
```

## 环境变量配置

在项目根目录创建 `.env` 文件，建议至少配置以下变量：

```env
# 当前 agent_factory.py 默认使用的模型配置
MINIMAX_API_KEY=your_api_key
MINIMAX_BASE_URL=https://api.minimax.chat/v1
MINIMAX_MODEL=your_model_name

# 网络搜索工具使用
SERPAPI_API_KEY=your_serpapi_key
```

如果你需要在其他脚本或后续扩展中切换模型，也可以补充这些可选变量：

```env
# OpenAI 兼容模型
OPENAI_API_KEY=your_openai_api_key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_CHAT_MODEL=gpt-4o-mini

# DeepSeek
DEEPSEEK_API_KEY=your_deepseek_api_key
```

## 快速开始

### 运行命令行 Agent

```bash
python agent.py
```

运行后会进入交互式命令行会话。

- 第一行会显示 `请输入您的问题：`
- 如果你的输入需要换行，继续输入即可，后续提示符为 `... `
- 连续输入两个空行后，本轮内容会被提交给 Agent
- 按 `Ctrl+C` 可以退出程序

### Python 调用示例

```python
from agent_factory import build_agent, build_config, build_runtime_context

agent = build_agent()
context = build_runtime_context(user_id="user_1")
config = build_config(thread_id="session_1")

result = agent.invoke(
    {"messages": [{"role": "user", "content": "你好，请介绍一下你能做什么"}]},
    context=context,
    config=config,
)

print(result["messages"][-1].content)
```

如果你希望使用流式输出：

```python
for chunk in agent.stream(
    {"messages": [{"role": "user", "content": "帮我查一下今天的天气"}]},
    context=context,
    config=config,
):
    print(chunk)
```

## 工具能力

### 通用工具

| 工具名 | 说明 |
| --- | --- |
| `get_weather` | 查询指定城市天气 |
| `web_search` | 搜索网络实时信息 |
| `fetch_webpage` | 抓取网页正文文本 |
| `read_local_file` | 读取 `./post` 目录下的本地文件 |

### 图片工具

| 工具名 | 说明 |
| --- | --- |
| `get_mossia_pixiv_image` | 从 Mossia Pixiv 图源获取图片信息，支持结构化筛选与随机获取 |
| `save_image_from_url` | 将图片保存到本地 `./img` 目录 |

`get_mossia_pixiv_image` 已不是旧的 JSON 字符串入参形式，而是结构化工具。它支持的主要筛选字段包括：

- `num`
- `pid`
- `uid`
- `author`
- `proxy`
- `aiType`
- `r18Type`
- `dateAfter`
- `dateBefore`
- `sizeList`
- `imageSizeType`

工具返回的是整理后的图片元数据，包含作品基本信息、标签列表和按尺寸组织的图片链接，不会自动下载图片。

### 学术与知识工具

| 工具名 | 说明 |
| --- | --- |
| `arxiv` | 搜索 arXiv 学术论文 |
| `wikipedia` | 搜索 Wikipedia 内容 |

### Python 执行工具

| 工具名 | 说明 |
| --- | --- |
| `python_repl` | 在受控环境中执行 Python 代码 |

## 项目结构

```text
.
├── agent.py                 # 命令行主入口，负责读取输入并输出结果
├── agent_factory.py         # 构建 Agent、上下文与线程配置
├── agent_tools.py           # 注册并组合项目实际使用的工具
├── mossia_pixiv_tool.py     # 结构化 Pixiv 工具实现、参数校验与响应整理
├── model.py                 # 预定义的模型初始化示例
├── tests/
│   └── test_mossia_pixiv_tool.py  # Pixiv 工具的单元测试
├── post/                    # 允许读取的本地文本目录
├── img/                     # 默认图片保存目录
├── requirements.txt         # Python 依赖列表
└── .env                     # 本地环境变量配置
```

## 核心接口

`agent_factory.py` 对外暴露的主要接口如下：

- `build_agent()`：创建可调用的 LangChain Agent
- `build_runtime_context(user_id: str)`：构建运行时上下文
- `build_config(thread_id: str)`：构建会话线程配置

如果你希望在其他脚本中集成当前 Agent，建议直接复用这三个接口。

## 测试与验证

当前仓库已包含 Pixiv 工具的单元测试：

- `tests/test_mossia_pixiv_tool.py`

推荐验证命令：

```bash
python -m unittest discover -s tests -v
```

该命令主要覆盖以下内容：

- Pixiv 工具参数构造
- GET / POST 请求分支
- 响应字段整理
- 错误处理与结构化工具 schema

## 注意事项

- `read_local_file` 仅允许访问 `./post` 目录下的文件
- `save_image_from_url` 默认将图片写入 `./img` 目录
- `get_mossia_pixiv_image` 只返回图片信息和链接，不会自动下载图片
- 当前 `agent_factory.py` 默认读取 MiniMax 相关环境变量作为主模型配置
- `model.py` 中提供了其他模型初始化示例，但不是命令行入口的主调用路径
