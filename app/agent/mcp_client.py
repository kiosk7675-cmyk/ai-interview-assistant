"""MCP Client - 可选模块，连接失败不中断主流程"""
from loguru import logger


class DummyMCPClient:
    """占位 MCP 客户端，提供空方法避免上游代码报错"""

    async def get_tools(self):
        return []


async def get_mcp_client_with_retry() -> DummyMCPClient:
    """返回占位客户端（MCP 功能已禁用）"""
    logger.info("MCP 功能未启用，使用空客户端")
    return DummyMCPClient()
