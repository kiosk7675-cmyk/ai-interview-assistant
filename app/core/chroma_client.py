"""ChromaDB 客户端管理器

使用本地持久化 ChromaDB 替代 Milvus，无需 Docker 环境。
数据存储在项目目录下的 chroma_db 文件夹中。
"""

from typing import Optional

import chromadb
from chromadb import PersistentClient
from loguru import logger


class ChromaClientManager:
    """ChromaDB 客户端管理器"""

    COLLECTION_NAME: str = "biz"
    VECTOR_DIM: int = 1024

    def __init__(self) -> None:
        """初始化 ChromaDB 客户端管理器"""
        self._client: Optional[PersistentClient] = None
        self._collection = None

    def connect(self) -> PersistentClient:
        """
        初始化 ChromaDB 持久化客户端

        Returns:
            PersistentClient: ChromaDB 客户端实例
        """
        if self._client is not None:
            logger.debug("ChromaDB 已连接，跳过重复 connect")
            return self._client

        try:
            # 使用持久化客户端，数据存储在本地文件
            persist_dir = "./chroma_db"
            logger.info(f"正在初始化 ChromaDB (持久化目录: {persist_dir})")

            self._client = chromadb.PersistentClient(path=persist_dir)

            # 获取或创建 collection
            self._collection = self._client.get_or_create_collection(
                name=self.COLLECTION_NAME,
                metadata={"hnsw:space": "l2"},  # 使用 L2 距离
            )

            count = self._collection.count()
            logger.info(
                f"ChromaDB 初始化成功, collection: {self.COLLECTION_NAME}, "
                f"现有文档数: {count}"
            )

            return self._client

        except Exception as e:
            logger.error(f"ChromaDB 初始化失败: {e}")
            self.close()
            raise RuntimeError(f"ChromaDB 初始化失败: {e}") from e

    def get_collection(self):
        """
        获取 collection 实例

        Returns:
            chromadb.Collection: collection 实例
        """
        if self._collection is None:
            raise RuntimeError("Collection 未初始化，请先调用 connect()")
        return self._collection

    def health_check(self) -> bool:
        """
        健康检查

        Returns:
            bool: True 表示健康，False 表示异常
        """
        try:
            if self._client is None:
                return False

            # 通过心跳检查连接
            _ = self._client.heartbeat()
            return True

        except Exception as e:
            logger.error(f"ChromaDB 健康检查失败: {e}")
            return False

    def close(self) -> None:
        """关闭连接（ChromaDB 无显式关闭操作）"""
        self._collection = None
        self._client = None
        logger.info("ChromaDB 连接已释放")

    def __enter__(self) -> "ChromaClientManager":
        """上下文管理器入口"""
        _ = self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """上下文管理器退出"""
        self.close()


# 全局单例
chroma_manager = ChromaClientManager()
