"""洞察台（Insight Desk）—— 集中放置路径约定与模型工厂。

Demo 的能力映射（参考课程第 3-9 章）：

| 能力 | 章节 | 落点 |
|---|---|---|
| 虚拟文件系统 | 第 3 章 | `/findings` 与 `/workspace` 共享落盘，`READ_LIMIT` 演示分片读取 |
| 任务规划 | 第 4 章 | `TodoListMiddleware` 注入 `write_todos` |
| 子 Agent | 第 5 章 | collector / analyst / synthesizer 三专业子 Agent |
| Skills | 第 7 章 | `/skills/deep-research`、`/skills/report-writer` |
| 长期记忆 | 第 8 章 | `/memories/preferences.md` 跨线程加载 |
| HITL | 第 9 章 | `send_brief` 审批 + 自定义 `ReviewerGateMiddleware` |
"""

import os

from langchain_openai import ChatOpenAI

# --- 路径约定：写在一处，Agent 提示词与运行脚本共用 ---
FINDINGS_DIR = "/findings"
WORKSPACE_DIR = "/workspace"
ANALYSIS_PATH = f"{WORKSPACE_DIR}/analysis.md"
REPORT_PATH = f"{WORKSPACE_DIR}/report.md"
MEMORY_PATH = "/memories/preferences.md"
SKILLS_ROOT = "/skills"

# --- 模型 ---
# 主 Agent 与子 Agent 走不同服务商，用于演示"子 Agent 可用不同模型"
MAIN_MODEL_NAME = os.getenv("MODEL_NAME", "deepseek-chat")
MAIN_BASE_URL = os.getenv("DEEPSEEK_URL", "https://api.deepseek.com/v1")
SUB_MODEL_NAME = os.getenv("SUB_MODEL_NAME", "deepseek-ai/DeepSeek-V3.2")
SUB_BASE_URL = os.getenv("SILICONFLOW_URL", "https://api.siliconflow.cn/v1")


def main_model() -> ChatOpenAI:
    return ChatOpenAI(
        model=MAIN_MODEL_NAME,
        api_key=os.environ["DEEPSEEK_API_KEY"],
        base_url=MAIN_BASE_URL,
        max_retries=4,
        timeout=120,
    )


def sub_model() -> ChatOpenAI:
    return ChatOpenAI(
        model=SUB_MODEL_NAME,
        api_key=os.environ["SILICONFLOW_API_KEY"],
        base_url=SUB_BASE_URL,
        # 免费额度有流控，失败时线性退避重试，避免整轮演示被打断
        max_retries=6,
        timeout=120,
    )
