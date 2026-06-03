# InterviewPrep - 通用面试智能辅导系统

[![Python](https://img.shields.io/badge/Python-3.13-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![LangChain](https://img.shields.io/badge/LangChain-latest-orange.svg)](https://www.langchain.com/)

## 项目简介

**InterviewPrep** 是一个基于 RAG（检索增强生成）的面试智能辅导系统，包含**面经速查对话**与**模拟面试**两大功能模块，实现简历上传 → 智能解析 → 岗位匹配 → 模拟面试 → 评分报告的端到端面试备考流程。

## 核心特性

- **面经速查** - 基于 RAG 的多轮对话，LangGraph Agent + 工具调用 + SSE 流式输出
- **模拟面试** - 简历解析 → 岗位匹配 → 逐题出题 → LLM 评分 → Markdown 报告
- **知识库丰富** - 内置 Python 核心、异步编程、FastAPI、MySQL、Redis、网络协议、系统设计等 7 大方向
- **知识库扩展** - 支持上传自定义面经、笔记（.md/.txt/.pdf），自动建立向量索引
- **LLM 幻觉检测** - 评分环节违禁词过滤 + 自动重试，防止"回答为空"等幻觉输出

## 技术栈

- **框架**: FastAPI + LangChain + LangGraph
- **LLM**: DeepSeek Chat（OpenAI 兼容接口）
- **向量库**: ChromaDB（本地持久化，无需 Docker）
- **嵌入模型**: FastEmbed（BAAI/bge-small-zh-v1.5，本地运行）
- **前端**: 纯静态 HTML/CSS/JS

## 快速开始

### 环境要求
- Python 3.11+
- DeepSeek API Key

### 安装和启动

```bash
# 1. 创建虚拟环境
python -m venv .venv
.venv\Scripts\activate

# 2. 安装依赖
pip install -e .

# 3. 配置 API Key
cp .env.example .env
# 编辑 .env 填入你的 DEEPSEEK_API_KEY

# 4. 启动服务
python -m uvicorn app.main:app --host 0.0.0.0 --port 9900
```

或双击 `start.bat` 一键启动。

### 访问服务
- **首页（面经速查）**: http://localhost:9900
- **模拟面试**: http://localhost:9900/interview
- **API 文档**: http://localhost:9900/docs

## API 接口

### 面经速查（对话 Agent）

| 功能 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 面试问答 | POST | `/api/chat` | 同步返回回答 |
| 流式问答 | POST | `/api/chat_stream` | SSE 流式输出 |
| 上传知识 | POST | `/api/upload` | 上传面经/笔记文档 |
| 清空会话 | POST | `/api/chat/clear` | 清除历史记录 |
| 会话历史 | GET | `/api/chat/session/{id}` | 查看历史对话 |
| 健康检查 | GET | `/health` | 服务状态 |

### 模拟面试

| 功能 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 上传简历 | POST | `/api/interview/resume/upload` | PDF 简历上传 |
| 解析简历 | POST | `/api/interview/resume/parse` | LLM 结构化解析 |
| 岗位匹配 | POST | `/api/interview/job/match` | 基于简历推荐岗位 |
| 开始面试 | POST | `/api/interview/start` | 生成第一题 |
| 提交回答 | POST | `/api/interview/answer` | 提交答案并生成下一题 |
| 结束面试 | POST | `/api/interview/end` | 生成评分报告 |

## 知识库结构

```
knowledge_base/
├── 01_python_core.md      # Python 核心基础（GIL、装饰器、生成器等）
├── 02_python_async.md     # 异步编程（asyncio、事件循环、FastAPI 异步）
├── 03_fastapi_web.md      # FastAPI 与 Web（请求生命周期、Pydantic、中间件）
├── 04_mysql.md            # MySQL（索引、事务、MVCC、锁、SQL 优化）
├── 05_redis.md            # Redis（数据结构、持久化、缓存策略、分布式锁）
├── 06_network_linux.md    # 网络与 Linux（TCP、HTTP、HTTPS、Docker）
└── 07_system_design.md    # 系统设计（RAG、Agent、MCP、限流、消息队列）
```

## 项目结构

```
app/
├── api/                    # API 路由层
│   ├── chat.py             # 面经速查对话接口
│   ├── interview.py        # 模拟面试接口
│   ├── file.py             # 知识库上传接口
│   └── health.py           # 健康检查
├── core/                   # 核心组件
│   ├── chroma_client.py    # ChromaDB 客户端
│   └── llm_factory.py      # LLM 配置
├── services/               # 服务层
│   ├── rag_agent_service.py       # RAG 对话 Agent（LangGraph）
│   ├── interview_service.py       # 面试全流程引擎
│   ├── resume_parser_service.py   # 简历解析
│   ├── job_match_service.py       # 岗位匹配
│   ├── vector_embedding_service.py # 向量嵌入
│   ├── vector_index_service.py    # 文档索引
│   ├── vector_search_service.py   # 向量检索
│   ├── vector_store_manager.py    # 向量存储管理
│   └── document_splitter_service.py # 文档分片
├── models/                 # 数据模型
├── tools/                  # Agent 工具
│   ├── knowledge_tool.py   # 知识检索工具
│   └── time_tool.py        # 时间工具
└── main.py                 # 应用入口
```

