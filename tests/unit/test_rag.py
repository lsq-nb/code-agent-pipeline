"""
RAG 模块测试
"""

from unittest.mock import MagicMock, patch

import pytest

from code_agent_pipeline.rag.embedder import EmbeddingService
from code_agent_pipeline.rag.indexer import CodeIndexer
from code_agent_pipeline.rag.retriever import CodeRetriever


def _mock_openai_embedding(value: int = 1):
    """构造一个返回确定性向量的 OpenAI embeddings mock。

    让 embedding 测试不依赖真实 LLM 服务，既快又可复现。
    返回的 embedding 是长度 4 的确定性向量，便于断言。
    """
    fake_client = MagicMock()
    fake_response = MagicMock()
    fake_response.data = [MagicMock(embedding=[float(value)] * 4)]
    fake_client.embeddings.create.return_value = fake_response
    return fake_client


class TestEmbeddingService:
    """嵌入服务测试（mock OpenAI 客户端，避免真实网络调用）"""

    def test_get_embedding(self):
        with patch("openai.OpenAI") as mock_cls:
            mock_cls.return_value = _mock_openai_embedding(1)
            service = EmbeddingService(api_key="test-key")
            embedding = service.get_embedding("hello world")
            assert isinstance(embedding, list)
            assert len(embedding) > 0

    def test_get_embeddings_batch(self):
        with patch("openai.OpenAI") as mock_cls:
            mock_cls.return_value = _mock_openai_embedding(2)
            service = EmbeddingService(api_key="test-key")
            embeddings = service.get_embeddings(["text1", "text2"])
            assert len(embeddings) == 2

    def test_cache(self):
        with patch("openai.OpenAI") as mock_cls:
            mock_cls.return_value = _mock_openai_embedding(3)
            service = EmbeddingService(api_key="test-key")
            e1 = service.get_embedding("same text")
            e2 = service.get_embedding("same text")
            assert e1 == e2
            # 缓存命中后不应再次调用 OpenAI
            assert mock_cls.return_value.embeddings.create.call_count == 1


class TestCodeRetriever:
    """检索器测试"""

    def test_init(self):
        retriever = CodeRetriever(collection_name="test")
        assert retriever.collection_name == "test"

    @pytest.mark.xfail(reason="ChromaDB Rust panic on this environment")
    def test_collection_count_empty(self):
        retriever = CodeRetriever(collection_name="te")
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
        test_file.write_text(
            'def hello():\n    """这是一个文档字符串"""\n    # 这是一行注释\n    pass\n',
            encoding="utf-8",
        )
        extracted = indexer._extract_comments_and_docs(test_file)
        assert len(extracted) > 0
