"""向量存储管理器 - 封装 ChromaDB VectorStore 操作"""

import time
import uuid
from typing import List

from langchain_chroma import Chroma
from langchain_core.documents import Document
from loguru import logger

from app.services.vector_embedding_service import vector_embedding_service
from app.core.chroma_client import chroma_manager


# 统一使用 biz collection
COLLECTION_NAME = "biz"


class VectorStoreManager:
    """向量存储管理器（ChromaDB 版）"""

    def __init__(self):
        """初始化向量存储管理器"""
        self.vector_store = None
        self.collection_name = COLLECTION_NAME
        self._initialize_vector_store()

    def _initialize_vector_store(self):
        """初始化 ChromaDB VectorStore"""
        try:
            # 初始化 ChromaDB 客户端
            chroma_client = chroma_manager.connect()

            # 创建 LangChain Chroma VectorStore
            self.vector_store = Chroma(
                client=chroma_client,
                collection_name=self.collection_name,
                embedding_function=vector_embedding_service,
            )

            logger.info(
                f"ChromaDB VectorStore 初始化成功, "
                f"collection: {self.collection_name}"
            )

        except Exception as e:
            logger.error(f"VectorStore 初始化失败: {e}")
            raise

    def add_documents(self, documents: List[Document]) -> List[str]:
        """
        批量添加文档到向量存储（自动批量向量化）

        Args:
            documents: 文档列表

        Returns:
            List[str]: 文档 ID 列表
        """
        try:
            start_time = time.time()

            # 为每个文档生成唯一 id
            ids = [str(uuid.uuid4()) for _ in documents]

            # LangChain Chroma 的 add_documents 会自动调用 embedding_function
            result_ids = self.vector_store.add_documents(documents, ids=ids)

            elapsed = time.time() - start_time
            logger.info(
                f"批量添加 {len(documents)} 个文档到 VectorStore 完成, "
                f"耗时: {elapsed:.2f}秒, 平均: {elapsed/len(documents):.2f}秒/个"
            )
            return result_ids
        except Exception as e:
            logger.error(f"添加文档失败: {e}")
            raise

    def delete_by_source(self, file_path: str) -> int:
        """
        删除指定文件的所有文档

        Args:
            file_path: 文件路径

        Returns:
            int: 删除的文档数量
        """
        try:
            # 使用 ChromaDB 原生 collection 按 where 条件删除
            collection = chroma_manager.get_collection()
            # 先查询符合条件的文档数量
            existing = collection.get(where={"_source": file_path})
            existing_ids = existing.get("ids", []) if existing else []

            if existing_ids:
                collection.delete(ids=existing_ids)
                deleted_count = len(existing_ids)
                logger.info(
                    f"删除文件旧数据: {file_path}, 删除数量: {deleted_count}"
                )
                return deleted_count

            return 0

        except Exception as e:
            logger.warning(f"删除旧数据失败 (可能是首次索引): {e}")
            return 0

    def get_vector_store(self) -> Chroma:
        """
        获取 VectorStore 实例

        Returns:
            Chroma: VectorStore 实例
        """
        return self.vector_store

    def similarity_search(self, query: str, k: int = 3) -> List[Document]:
        """
        相似度搜索

        Args:
            query: 查询文本
            k: 返回结果数量

        Returns:
            List[Document]: 相关文档列表
        """
        try:
            docs = self.vector_store.similarity_search(query, k=k)
            logger.debug(f"相似度搜索完成: query='{query}', 结果数={len(docs)}")
            return docs
        except Exception as e:
            logger.error(f"相似度搜索失败: {e}")
            return []


# 全局单例
vector_store_manager = VectorStoreManager()
