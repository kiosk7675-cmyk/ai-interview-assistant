"""向量嵌入服务模块 - 使用本地 FastEmbed 模型

无需外部 API，模型文件本地缓存，离线可用。
"""

import os
from typing import List

from langchain_core.embeddings import Embeddings
from loguru import logger

# 设置 HuggingFace 镜像加速下载（中国大陆网络优化）
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"


class LocalEmbeddings(Embeddings):
    """基于 FastEmbed 的本地嵌入模型

    使用 BAAI/bge-small-zh-v1.5 中文嵌入模型，
    模型文件自动缓存到 ./embed_cache 目录。
    """

    def __init__(self, model_name: str = "BAAI/bge-small-zh-v1.5"):
        """
        初始化本地嵌入模型

        Args:
            model_name: 嵌入模型名称，默认中文小型模型
        """
        from fastembed import TextEmbedding

        self.model_name = model_name
        self.cache_dir = "./embed_cache"
        self._model = TextEmbedding(
            model_name=model_name,
            cache_dir=self.cache_dir,
        )

        logger.info(
            f"本地嵌入模型初始化完成 - "
            f"模型: {model_name}, 缓存目录: {self.cache_dir}"
        )

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        批量嵌入文档列表

        Args:
            texts: 文本列表

        Returns:
            List[List[float]]: 嵌入向量列表
        """
        if not texts:
            return []

        try:
            logger.info(f"批量嵌入 {len(texts)} 个文档 (本地模型)")

            # fastembed 返回生成器
            embeddings = list(self._model.embed(texts))
            result = [vec.tolist() for vec in embeddings]

            logger.debug(f"批量嵌入完成, 维度: {len(result[0])}")
            return result

        except Exception as e:
            logger.error(f"批量嵌入失败: {e}")
            raise RuntimeError(f"批量嵌入失败: {e}") from e

    def embed_query(self, text: str) -> List[float]:
        """
        嵌入单个查询文本

        Args:
            text: 查询文本

        Returns:
            List[float]: 嵌入向量
        """
        if not text or not text.strip():
            raise ValueError("查询文本不能为空")

        try:
            logger.debug(f"嵌入查询 (本地模型), 长度: {len(text)} 字符")

            embeddings = list(self._model.embed([text]))
            vec = embeddings[0].tolist()

            logger.debug(f"查询嵌入完成, 维度: {len(vec)}")
            return vec

        except Exception as e:
            logger.error(f"查询嵌入失败: {e}")
            raise RuntimeError(f"查询嵌入失败: {e}") from e


# 全局单例
vector_embedding_service = LocalEmbeddings()
