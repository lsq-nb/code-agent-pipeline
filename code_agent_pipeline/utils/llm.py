"""
LLM 工厂函数
创建和获取 LLM 实例
"""

from typing import Optional

from ..config import get_config


def create_llm(model: Optional[str] = None, temperature: Optional[float] = None):
    """
    创建 LLM 实例

    根据配置自动选择提供商和模型
    """
    config = get_config()
    model = model or config.llm.model
    temp = temperature if temperature is not None else config.llm.temperature

    provider = config.llm.provider.lower()

    if provider == "openai":
        from langchain_openai import ChatOpenAI  # noqa: PLC0415
        return ChatOpenAI(
            model=model,
            temperature=temp,
            api_key=config.llm.api_key,
            base_url=config.llm.base_url,
        )
    elif provider == "anthropic":
        from langchain_anthropic import ChatAnthropic  # noqa: PLC0415
        return ChatAnthropic(
            model=model,
            temperature=temp,
        )
    else:
        # 默认使用 OpenAI 兼容接口
        from langchain_openai import ChatOpenAI  # noqa: PLC0415
        return ChatOpenAI(
            model=model,
            temperature=temp,
            api_key=config.llm.api_key or "dummy",
            base_url=config.llm.base_url or "http://localhost:8000/v1",
        )


def get_llm():
    """获取全局 LLM 实例（缓存）"""
    return create_llm()
