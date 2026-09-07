"""
状态序列化/反序列化工具
"""

import json
from datetime import datetime
from typing import Any, Optional

from ..models import PipelineState, PipelineStage, TaskStatus


def serialize_state(state: PipelineState) -> str:
    """将 PipelineState 序列化为 JSON 字符串"""
    return state.model_dump_json(indent=2, exclude_none=True)


def deserialize_state(data: str) -> PipelineState:
    """从 JSON 字符串反序列化为 PipelineState"""
    parsed = json.loads(data)
    # 处理枚举字段
    if "current_stage" in parsed and isinstance(parsed["current_stage"], str):
        parsed["current_stage"] = PipelineStage(parsed["current_stage"])
    if "status" in parsed and isinstance(parsed["status"], str):
        parsed["status"] = TaskStatus(parsed["status"])
    return PipelineState(**parsed)


def save_state(state: PipelineState, path: str) -> None:
    """保存状态到文件"""
    import json as _json  # noqa: PLC0415
    with open(path, "w", encoding="utf-8") as f:
        f.write(serialize_state(state))


def load_state(path: str) -> PipelineState:
    """从文件加载状态"""
    import json as _json  # noqa: PLC0415
    with open(path, "r", encoding="utf-8") as f:
        return deserialize_state(f.read())
