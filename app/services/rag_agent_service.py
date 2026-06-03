"""RAG Agent 服务 - 基于 LangGraph 的智能代理

使用 DeepSeek Chat（通过 OpenAI 兼容接口调用），
支持流式输出、工具调用和 RAG 知识库检索。
"""

from typing import Annotated, Any, AsyncGenerator, Dict, Sequence

from langchain.agents import create_agent
from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    RemoveMessage,
    SystemMessage,
)
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.message import REMOVE_ALL_MESSAGES, add_messages
from loguru import logger
from typing_extensions import TypedDict

from app.config import config
from app.tools import get_current_time, retrieve_knowledge
from app.agent.mcp_client import get_mcp_client_with_retry


class AgentState(TypedDict):
    """Agent 状态"""
    messages: Annotated[Sequence[BaseMessage], add_messages]


def trim_messages_middleware(state: AgentState) -> dict[str, Any] | None:
    """
    修剪消息历史，只保留最近的几条消息以适应上下文窗口

    策略：
    - 保留第一条系统消息（System Message）
    - 保留最近的 6 条消息（3 轮对话）
    - 当消息少于等于 7 条时，不做修剪

    Args:
        state: Agent 状态

    Returns:
        包含修剪后消息的字典，如果无需修剪则返回 None
    """
    messages = state["messages"]

    # 如果消息数量较少，无需修剪
    if len(messages) <= 7:
        return None

    # 提取第一条系统消息
    first_msg = messages[0]

    # 保留最近的 6 条消息（确保包含完整的对话轮次）
    recent_messages = messages[-6:] if len(messages) % 2 == 0 else messages[-7:]

    # 构建新的消息列表
    new_messages = [first_msg] + list(recent_messages)

    logger.debug(f"修剪消息历史: {len(messages)} -> {len(new_messages)} 条")

    return {
        "messages": [
            RemoveMessage(id=REMOVE_ALL_MESSAGES),
            *new_messages
        ]
    }


class RagAgentService:
    """RAG Agent 服务 - 使用 LangGraph + ChatQwen 原生集成"""

    def __init__(self, streaming: bool = True):
        """初始化 RAG Agent 服务

        Args:
            streaming: 是否启用流式输出，默认为 True
        """
        self.model_name = config.rag_model
        self.streaming = streaming
        self.system_prompt = self._build_system_prompt()


        # DeepSeek Chat（通过 OpenAI 兼容接口）
        self.model = ChatOpenAI(
            model="deepseek-chat",
            api_key=config.dashscope_api_key,
            base_url=config.dashscope_api_base or "https://api.deepseek.com/v1",
            temperature=0.7,
            streaming=streaming,
        )

        # 定义基础工具
        self.tools = [retrieve_knowledge, get_current_time]

        # MCP 客户端（延迟初始化，使用全局管理）
        self.mcp_tools: list = []

        # 创建内存检查点（用于会话管理）
        self.checkpointer = MemorySaver()

        # Agent 初始化（会在异步方法中完成）
        self.agent = None
        self._agent_initialized = False

        logger.info(f"RAG Agent 服务初始化完成 (DeepSeek Chat), model={self.model_name}, streaming={streaming}")

    async def _initialize_agent(self):
        """异步初始化 Agent（MCP 工具可选，连接失败则仅使用内置工具）"""
        if self._agent_initialized:
            return

        # 尝试加载 MCP 工具（可选，连接失败不中断）
        mcp_tools_loaded = []
        try:
            mcp_client = await get_mcp_client_with_retry()
            mcp_tools_loaded = await mcp_client.get_tools()
            logger.info(f"成功加载 {len(mcp_tools_loaded)} 个 MCP 工具")
        except Exception as e:
            logger.warning(f"MCP 工具加载失败（可选功能，继续运行）: {e}")

        # 将 MCP 工具添加到实例变量中
        self.mcp_tools = mcp_tools_loaded

        # 合并所有工具
        all_tools = self.tools + self.mcp_tools

        self.agent = create_agent(
            self.model,
            tools=all_tools,
            checkpointer=self.checkpointer,
        )

        self._agent_initialized = True


        if all_tools:
            tool_names = [tool.name if hasattr(tool, "name") else str(tool) for tool in all_tools]
            logger.info(f"可用工具列表: {', '.join(tool_names)}")

    def _build_system_prompt(self) -> str:
        """
        构建系统提示词

        Returns:
            str: 系统提示词
        """
        from textwrap import dedent

        return dedent("""
            你是一个专业的面试辅导助手，覆盖Java后端、Python后端、软件测试等多个技术方向，帮助用户准备技术面试。

            核心能力:
            1. 基于知识库回答技术问题，提供准确、深度的解析
            2. 对概念进行横向对比（如synchronized vs Lock、pytest vs unittest），帮助理解异同
            3. 结合实际项目经验给出最佳实践建议
            4. 模拟面试场景，自动追问考察深度理解

            回答风格:
            - 先给出简洁的结论（1-2句话）
            - 再展开详细原理和底层实现
            - 结合实际场景说明为什么如此设计
            - 最后可补充常见面试追问点

            工作原则:
            - 基于知识库回答，不编造信息
            - 遇到知识库没有的内容，诚实告知并基于自身知识回答
            - 鼓励用户深入思考，而非直接背诵八股文
        """).strip()

    async def query(
        self,
        question: str,
        session_id: str,
    ) -> str:
        """
        非流式处理用户问题（一次性返回完整答案）

        Args:
            question: 用户问题
            session_id: 会话ID（作为 thread_id）

        Returns:
            str: 完整答案
        """
        try:
            await self._initialize_agent()

            logger.info(f"[会话 {session_id}] RAG Agent 收到查询（非流式）: {question}")

            # 构建消息列表（系统提示 + 用户问题）
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=question)
            ]

            # 构建 Agent 输入
            agent_input = {"messages": messages}

            # 配置 thread_id（用于会话持久化）
            config_dict = {
                "configurable": {
                    "thread_id": session_id
                }
            }

            result = await self.agent.ainvoke(
                input=agent_input,
                config=config_dict,
            )

            # 提取最终答案
            messages_result = result.get("messages", [])
            if messages_result:
                last_message = messages_result[-1]
                answer = last_message.content if hasattr(last_message, 'content') else str(last_message)

                # 记录工具调用
                if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                    tool_names = [tc.get("name", "unknown") for tc in last_message.tool_calls]
                    logger.info(f"[会话 {session_id}] Agent 调用了工具: {tool_names}")

                logger.info(f"[会话 {session_id}] RAG Agent 查询完成（非流式）")
                return answer

            logger.warning(f"[会话 {session_id}] Agent 返回结果为空")
            return ""

        except Exception as e:
            logger.error(f"[会话 {session_id}] RAG Agent 查询失败（非流式）: {e}")
            raise

    async def query_stream(
        self,
        question: str,
        session_id: str,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        流式处理用户问题（逐步返回答案片段）

        Args:
            question: 用户问题
            session_id: 会话ID（作为 thread_id）

        Yields:
            Dict[str, Any]: 包含流式数据的字典
                - type: "content" | "tool_call" | "complete" | "error"
                - data: 具体内容
        """
        try:
            await self._initialize_agent()

            logger.info(f"[会话 {session_id}] RAG Agent 收到查询（流式）: {question}")

            # 构建消息列表（系统提示 + 用户问题）
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=question)
            ]

            # 构建 Agent 输入
            agent_input = {"messages": messages}

            # 配置 thread_id（用于会话持久化）
            config_dict = {
                "configurable": {
                    "thread_id": session_id
                }
            }

            async for token, metadata in self.agent.astream(
                input=agent_input,
                config=config_dict,
                stream_mode="messages",
            ):
                node_name = metadata.get('langgraph_node', 'unknown') if isinstance(metadata, dict) else 'unknown'
                message_type = type(token).__name__

                if message_type in ("AIMessage", "AIMessageChunk"):
                    # 优先从 content_blocks 中提取（部分模型/版本）
                    content_blocks = getattr(token, 'content_blocks', None)
                    if content_blocks and isinstance(content_blocks, list):
                        for block in content_blocks:
                            if isinstance(block, dict) and block.get('type') == 'text':
                                text_content = block.get('text', '')
                                if text_content:
                                    yield {
                                        "type": "content",
                                        "data": text_content,
                                        "node": node_name
                                    }
                    else:
                        # 兜底：直接从 token.content 取字符串（DeepSeek/OpenAI 兼容接口标准路径）
                        raw_content = getattr(token, 'content', '')
                        if isinstance(raw_content, str) and raw_content:
                            yield {
                                "type": "content",
                                "data": raw_content,
                                "node": node_name
                            }
                        elif isinstance(raw_content, list):
                            # content 也可能是 list of dicts (e.g. Anthropic format)
                            for block in raw_content:
                                if isinstance(block, dict) and block.get('type') == 'text':
                                    text_content = block.get('text', '')
                                    if text_content:
                                        yield {
                                            "type": "content",
                                            "data": text_content,
                                            "node": node_name
                                        }

            logger.info(f"[会话 {session_id}] RAG Agent 查询完成（流式）")
            yield {"type": "complete"}

        except Exception as e:
            logger.error(f"[会话 {session_id}] RAG Agent 查询失败（流式）: {e}")
            yield {
                "type": "error",
                "data": str(e)
            }
            raise

    def get_session_history(self, session_id: str) -> list:
        """
        获取会话历史（从 MemorySaver checkpointer 中读取）

        Args:
            session_id: 会话ID（即 thread_id）

        Returns:
            list: 消息历史列表 [{"role": "user|assistant", "content": "...", "timestamp": "..."}]
        """
        try:
            # 使用 checkpointer 的 get 方法获取最新的检查点
            config = {"configurable": {"thread_id": session_id}}
            
            # 获取该 thread 的最新检查点
            checkpoint_tuple = self.checkpointer.get(config)
            
            if not checkpoint_tuple:
                logger.info(f"获取会话历史: {session_id}, 消息数量: 0")
                return []
            
            # checkpoint_tuple 可能是命名元组或普通元组，安全地提取 checkpoint
            # 通常第一个元素是 checkpoint 数据
            if hasattr(checkpoint_tuple, 'checkpoint'):
                checkpoint_data = checkpoint_tuple.checkpoint  # type: ignore
            else:
                # 如果是普通元组，第一个元素是 checkpoint
                checkpoint_data = checkpoint_tuple[0] if checkpoint_tuple else {}
            
            # 从检查点中提取消息
            messages = checkpoint_data.get("channel_values", {}).get("messages", [])
            
            # 转换为前端需要的格式
            history = []
            for msg in messages:
                # 跳过系统消息
                if isinstance(msg, SystemMessage):
                    continue
                    
                role = "user" if isinstance(msg, HumanMessage) else "assistant"
                content = msg.content if hasattr(msg, 'content') else str(msg)
                
                # 提取时间戳（如果有的话）
                timestamp = getattr(msg, 'timestamp', None)
                if timestamp:
                    history.append({
                        "role": role,
                        "content": content,
                        "timestamp": timestamp
                    })
                else:
                    from datetime import datetime
                    history.append({
                        "role": role,
                        "content": content,
                        "timestamp": datetime.now().isoformat()
                    })
            
            logger.info(f"获取会话历史: {session_id}, 消息数量: {len(history)}")
            return history
            
        except Exception as e:
            logger.error(f"获取会话历史失败: {session_id}, 错误: {e}")
            return []

    def clear_session(self, session_id: str) -> bool:
        """
        清空会话历史（从 MemorySaver checkpointer 中删除）

        Args:
            session_id: 会话ID（即 thread_id）

        Returns:
            bool: 是否成功
        """
        try:
            # 使用 checkpointer 的 delete_thread 方法删除该 thread 的所有检查点
            self.checkpointer.delete_thread(session_id)
            
            logger.info(f"已清除会话历史: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"清空会话历史失败: {session_id}, 错误: {e}")
            return False

    async def cleanup(self):
        """清理资源"""
        try:
            logger.info("清理 RAG Agent 服务资源...")
            # MCP 客户端由全局管理器统一管理，无需手动清理
            logger.info("RAG Agent 服务资源已清理")
        except Exception as e:
            logger.error(f"清理资源失败: {e}")


# 全局单例 - 启用流式输出
rag_agent_service = RagAgentService(streaming=True)
