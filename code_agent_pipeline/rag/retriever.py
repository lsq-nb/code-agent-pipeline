"""
代码规范检索器
基于 ChromaDB 实现向量相似度检索
"""

from pathlib import Path

import chromadb


class CodeRetriever:
    """
    代码规范检索器

    使用 ChromaDB 存储和检索代码规范、项目文档、
    编码风格指南等上下文信息。
    """

    def __init__(
        self,
        collection_name: str = "code_standards",
        persist_directory: str = ".cache/chroma",
        embedder=None,
    ):
        """
        初始化检索器

        参数:
            collection_name: 向量库集合名称
            persist_directory: 持久化目录
            embedder: 嵌入服务实例（None 时使用默认）
        """
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        self.embedder = embedder
        self._client: chromadb.Client | None = None
        self._collection = None

    def get_client(self) -> chromadb.Client:
        """获取 ChromaDB 客户端"""
        if self._client is None:
            Path(self.persist_directory).mkdir(parents=True, exist_ok=True)
            self._client = chromadb.PersistentClient(
                path=self.persist_directory,
            )
        return self._client

    def get_collection(self) -> chromadb.Collection:
        """获取或创建集合"""
        if self._collection is None:
            client = self.get_client()
            self._collection = client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
        return self._collection

    def add_documents(self, documents: list[dict]) -> None:
        """
        添加文档到向量库

        参数:
            documents: 文档列表，每个文档包含:
                - id: 唯一标识
                - text: 文本内容
                - metadata: 元数据（可选）
        """
        collection = self.get_collection()
        ids = [doc["id"] for doc in documents]
        texts = [doc["text"] for doc in documents]
        metadatas = [doc.get("metadata", {}) for doc in documents]

        collection.upsert(ids=ids, documents=texts, metadatas=metadatas)

    def search(self, query: str, top_k: int = 5, filter_dict: dict | None = None) -> list[dict]:
        """
        搜索相关文档

        参数:
            query: 查询文本
            top_k: 返回条数
            filter_dict: 过滤条件

        返回:
            相关文档列表，每项包含 document 和 distance
        """
        collection = self.get_collection()
        where = filter_dict if filter_dict else None

        results = collection.query(
            query_texts=[query],
            n_results=top_k,
            where=where,
            include=["documents", "metadatas", "distances"],
        )

        documents = []
        for i in range(len(results["ids"][0])):
            documents.append(
                {
                    "id": results["ids"][0][i],
                    "document": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i],
                }
            )
        return documents

    def search_with_embedding(
        self, embedding: list[float], top_k: int = 5, filter_dict: dict | None = None
    ) -> list[dict]:
        """使用嵌入向量进行搜索"""
        collection = self.get_collection()
        where = filter_dict if filter_dict else None

        results = collection.query(
            query_embeddings=[embedding],
            n_results=top_k,
            where=where,
            include=["documents", "metadatas", "distances"],
        )

        documents = []
        for i in range(len(results["ids"][0])):
            documents.append(
                {
                    "id": results["ids"][0][i],
                    "document": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i],
                }
            )
        return documents

    def delete_collection(self) -> None:
        """删除整个集合"""
        client = self.get_client()
        try:
            client.delete_collection(self.collection_name)
        except Exception:
            pass
        self._collection = None

    def collection_count(self) -> int:
        """获取集合中文档数量"""
        return self.get_collection().count()
