"""qwen_code_interpreter - 代码解释器工具"""

import json
import config
from client import call_harness


def code_interpreter(code: str, language: str = "python", instruction: str = "") -> str:
    """Execute code in Qwen's cloud sandbox via code_interpreter harness tool.

    The sandbox has network access (unlike local execute_code).

    Args:
        code: The code to execute.
        language: Programming language (default: python).
        instruction: Optional additional instruction for the interpreter.

    Returns:
        JSON string with execution output.
    """
    if instruction:
        input_text = (
            f"请使用代码解释器执行以下 {language} 代码，{instruction}：\n"
            f"```{language}\n{code}\n```"
        )
    else:
        input_text = (
            f"请使用代码解释器执行以下 {language} 代码并返回完整输出：\n"
            f"```{language}\n{code}\n```"
        )

    result = call_harness(
        input_text,
        ["code_interpreter"],
        timeout=config.CODE_TIMEOUT,
    )

    if result.get("error"):
        return json.dumps({"error": result["error"]}, ensure_ascii=False)

    return json.dumps({
        "language": language,
        "output": result["text"],
        "tool_details": result["tool_outputs"],
        "usage": result["usage"],
    }, ensure_ascii=False)
