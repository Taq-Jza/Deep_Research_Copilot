
import os

from langchain_openai import ChatOpenAI

# --- 路径约定：写在一处，Agent 提示词与运行脚本共用 ---
FINDINGS_DIR = "/findings"
ANALYSIS_PATH = "/workspace/analysis.md"
REPORT_PATH = "/workspace/report.md"
MEMORY_PATH = "/memories/preferences.md"
SKILLS_ROOT = "/skills"

# 两个领域 Skill 的目录（对应 skills/ 下的子目录）
RESEARCH_SKILL = f"{SKILLS_ROOT}/deep-research/"
WRITER_SKILL = f"{SKILLS_ROOT}/report-writer/"

# --- 模型：主 Agent 与子 Agent 走不同服务商，演示"子 Agent 可用不同模型" ---
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
