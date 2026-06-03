"""向量检索服务模块 - ChromaDB 版"""

from typing import Any, Dict, List

from loguru import logger

from app.core.chroma_client import chroma_manager
from app.services.vector_embedding_service import vector_embedding_service


class SearchResult:
    """搜索结果类"""

    def __init__(
        self,
        id: str,
        content: str,
        score: float,
        metadata: Dict[str, Any],
    ):
        self.id = id
        self.content = content
        self.score = score
        self.metadata = metadata

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "content": self.content,
            "score": self.score,
            "metadata": self.metadata,
        }


class VectorSearchService:
    """向量检索服务 - 负责从 ChromaDB 中搜索相似向量"""

    def __init__(self):
        """初始化向量检索服务"""
        logger.info("向量检索服务初始化完成 (ChromaDB)")

    def search_similar_documents(
        self, query: str, top_k: int = 3
    ) -> List[SearchResult]:
        """
        搜索相似文档

        Args:
            query: 查询文本
            top_k: 返回最相似的K个结果

        Returns:
            List[SearchResult]: 搜索结果列表

        Raises:
            RuntimeError: 搜索失败时抛出
        """
        try:
            logger.info(
                f"开始搜索相似文档, 查询: {query}, topK: {top_k}"
            )

            # 1. 将查询文本向量化
            query_vector = vector_embedding_service.embed_query(query)
            logger.debug(f"查询向量生成成功, 维度: {len(query_vector)}")

            # 2. 获取 collection
            collection = chroma_manager.get_collection()

            # 3. 执行搜索
            results = collection.query(
                query_embeddings=[query_vector],
                n_results=top_k,
                include=["documents", "metadatas", "distances"],
            )

            # 4. 解析搜索结果
            search_results = []
            if results["ids"]:
                for i in range(len(results["ids"][0])):
                    doc_id = results["ids"][0][i]
                    content = results["documents"][0][i] if results["documents"] else ""
                    distance = results["distances"][0][i] if results["distances"] else 0.0
                    metadata = results["metadatas"][0][i] if results["metadatas"] else {}

                    result = SearchResult(
                        id=doc_id,
                        content=content,
                        score=distance,  # L2 距离，越小越相似
                        metadata=metadata,
                    )
                    search_results.append(result)

            logger.info(
                f"搜索完成, 找到 {len(search_results)} 个相似文档"
            )
            return search_results

        except Exception as e:
            logger.error(f"搜索相似文档失败: {e}")
            raise RuntimeError(f"搜索失败: {e}") from e


# 全局单例
vector_search_service = VectorSearchService()
