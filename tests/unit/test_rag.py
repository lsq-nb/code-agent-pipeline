"""
RAG 模块测试
"""

import pytest

from code_agent_pipeline.rag.retriever import CodeRetriever
from code_agent_pipeline.rag.indexer import CodeIndexer
from code_agent_pipeline.rag.embedder import EmbeddingService


class TestEmbeddingService:
    """嵌入服务测试"""

    def test_get_embedding(self):
        service = EmbeddingService(api_key="test-key")
        embedding = service.get_embedding("hello world")
        assert isinstance(embedding, list)
        assert len(embedding) > 0

    def test_get_embeddings_batch(self):
        service = EmbeddingService(api_key="test-key")
        embeddings = service.get_embeddings(["text1", "text2"])
        assert len(embeddings) == 2

    def test_cache(self):
        service = EmbeddingService(api_key="test-key")
        e1 = service.get_embedding("same text")
        e2 = service.get_embedding("same text")
        assert e1 == e2


class TestCodeRetriever:
    """检索器测试"""

    def test_init(self):
        retriever = CodeRetriever(collection_name="test")
        assert retriever.collection_name == "test"

    def test_collection_count_empty(self):
        retriever = CodeRetriever(collection_name="test_empty")
        count = retriever.collection_count()
        assert count == 0


class TestCodeIndexer:
    """索引器测试"""

    def test_chunk_text(self):
        indexer = CodeIndexer(chunk_size=50, chunk_overlap=10)
        text = "word " * 100
        chunks = indexer._chunk_text(text)
        assert len(chunks) > 1
        for chunk in chunks:
            assert len(chunk) <= 60  # 允许少量超额

    def test_chunk_text_short(self):
        indexer = CodeIndexer(chunk_size=50, chunk_overlap=10)
        text = "short text"
        chunks = indexer._chunk_text(text)
        assert len(chunks) <= 1

    def test_extract_comments(self, tmp_path):
        indexer = CodeIndexer()
        # 创建测试 Python 文件
        test_file = tmp_path / "test.py"
        test_file.write_text('''
def hello():
    """这是一个文档字符串"""
    # 这是一行注释
    pass
''')
        extracted = indexer._extract_comments_and_docs(test_file)
        assert "文档字符串" in extracted or "注释" in extracted
