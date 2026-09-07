"""
嵌入模型服务
支持 OpenAI、本地模型等多种嵌入方案
"""

import hashlib
import json
import os
from pathlib import Path
from typing import Optional

import numpy as np


class EmbeddingService:
    """
    嵌入模型服务

    支持：
    - OpenAI text-embedding-3-small/large
    - 本地 Ollama 嵌入模型
    - 内存缓存（避免重复计算）
    """

    def __init__(self, model: str = "text-embedding-3-small",
                 api_key: Optional[str] = None,
                 base_url: Optional[str] = None):
        self.model = model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL")
        self._cache: dict[str, list[float]] = {}
        self._cache_file = Path(".cache/embedding_cache.json")

    def _load_cache(self) -> None:
        """加载缓存"""
        if self._cache_file.exists():
            try:
                self._cache = json.loads(self._cache_file.read_text())
            except (json.JSONDecodeError, OSError):
                self._cache = {}

    def _save_cache(self) -> None:
        """保存缓存"""
        self._cache_file.parent.mkdir(parents=True, exist_ok=True)
        self._cache_file.write_text(json.dumps(self._cache))

    def _hash_text(self, text: str) -> str:
        """文本哈希"""
        return hashlib.md5(text.encode()).hexdigest()[:16]

    def get_embedding(self, text: str) -> list[float]:
        """
        获取文本嵌入向量

        优先使用缓存，未命中时调用 API
        """
        key = self._hash_text(text)
        if key in self._cache:
            return self._cache[key]

        if not self.api_key:
            # 无 API Key 时返回随机向量作为占位
            import random  # noqa: PLC0415
            random.seed(key)  # noqa: S311
            embedding = [random.random() for _ in range(1536)]
        elif self.base_url and "ollama" in self.base_url.lower():
            embedding = self._embed_ollama(text)
        else:
            embedding = self._embed_openai(text)

        self._cache[key] = embedding
        self._save_cache()
        return embedding

    def get_embeddings(self, texts: list[str]) -> list[list[float]]:
        """批量获取嵌入"""
        return [self.get_embedding(t) for t in texts]

    def _embed_openai(self, text: str) -> list[float]:
        """调用 OpenAI 嵌入 API"""
        try:
            from openai import OpenAI  # noqa: PLC0415 (局部导入)
            client = OpenAI(api_key=self.api_key, base_url=self.base_url)
            response = client.embeddings.create(
                model=self.model,
                input=text,
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"[RAG] 嵌入调用失败: {e}")
            return [0.0] * 1536

    def _embed_ollama(self, text: str) -> list[float]:
        """调用 Ollama 本地嵌入"""
        import requests  # noqa: PLC0415
        resp = requests.post(
            f"{self.base_url}/api/embeddings",
            json={"model": self.model, "prompt": text},
            timeout=30,
        )
        data = resp.json()
        return data.get("embedding", [0.0] * 768)
