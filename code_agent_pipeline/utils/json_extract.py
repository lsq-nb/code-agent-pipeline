"""
LLM 输出 JSON 提取工具
各节点统一从这里提取最外层 JSON 对象，容忍裸 JSON、markdown 围栏、
前导说明文字、字符串内含嵌套大括号与真实换行等多种 LLM 输出形态。
"""

import re


def extract_json(raw: str) -> dict | None:
    """从 LLM 输出中提取最外层 JSON 对象；失败返回 None。

    策略：
    1. 若有 ```json 围栏，优先取围栏内内容（但配平时仍用全量文本兜底）。
    2. 用括号配平切出最外层 {...}，容忍 JSON 前后多余文字。
    3. 若字符串字面量内含真实换行等非法字符，转义后再解析一次。
    """
    if not raw:
        return None

    # 剥掉 markdown 围栏（若存在）
    fence = re.search(r"```(?:json)?\s*(\{.*\})\s*```", raw, re.DOTALL)
    base = fence.group(1) if fence else raw

    candidates = [base]
    stripped = base.lstrip()
    if not stripped.startswith("{"):
        candidates.append(base[base.find("{") :])

    for cand in candidates:
        start = cand.find("{")
        if start < 0:
            continue
        block = _take_outermost_object(cand[start:])
        if block is None:
            continue
        try:
            import json  # noqa: PLC0415

            return json.loads(block)
        except (ValueError, json.JSONDecodeError):
            fixed = _escape_raw_newlines_in_strings(block)
            if fixed != block:
                try:
                    import json  # noqa: PLC0415

                    return json.loads(fixed)
                except (ValueError, json.JSONDecodeError):
                    continue
    return None


def _take_outermost_object(text: str) -> str | None:
    """按括号配平切出最外层 {...}；未配平则返回 None。"""
    depth = 0
    in_str = False
    esc = False
    for i, ch in enumerate(text):
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
        else:
            if ch == '"':
                in_str = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return text[: i + 1]
    return None


def _escape_raw_newlines_in_strings(text: str) -> str:
    """把 JSON 字符串字面量内的真实换行/制表符转成 \\n / \\t。"""
    out: list[str] = []
    in_str = False
    esc = False
    for ch in text:
        if in_str:
            if esc:
                out.append(ch)
                esc = False
            elif ch == "\\":
                out.append(ch)
                esc = True
            elif ch == '"':
                in_str = False
                out.append(ch)
            elif ch == "\n":
                out.append("\\n")
            elif ch == "\t":
                out.append("\\t")
            else:
                out.append(ch)
        else:
            if ch == '"':
                in_str = True
            out.append(ch)
    return "".join(out)
