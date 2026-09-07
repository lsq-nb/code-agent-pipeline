"""
输入验证工具
"""

import re


def validate_requirement(requirement: str) -> tuple[bool, str]:
    """
    验证需求描述

    返回:
        (是否有效, 错误信息)
    """
    if not requirement or not requirement.strip():
        return False, "需求描述不能为空"

    if len(requirement.strip()) < 10:
        return False, "需求描述至少需要 10 个字符"

    if len(requirement.strip()) > 5000:
        return False, "需求描述不能超过 5000 个字符"

    return True, ""


def validate_code_output(code: str, language: str) -> tuple[bool, list[str]]:
    """
    验证生成的代码

    返回:
        (是否有效, 问题列表)
    """
    issues = []

    if not code or not code.strip():
        issues.append("代码内容为空")
        return False, issues

    if language == "python":
        # Python 基本检查
        if "import" not in code and len(code) > 100:
            issues.append("建议添加模块导入")
        # 检查语法基本合法性
        try:
            compile(code, "<generated>", "exec")
        except SyntaxError as e:
            issues.append(f"语法错误: {e.msg} (行 {e.lineno})")

    return len(issues) == 0, issues


def sanitize_input(text: str, max_length: int = 10000) -> str:
    """清理输入文本"""
    # 移除危险字符
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)
    return text[:max_length]
