"""子 Agent 定义（第 5 章：上下文隔离 + 结构化返回）。

三个专业子 Agent 各自拥有独立上下文与最小工具集。注意三条继承边界：
- `system_prompt` 不继承主 Agent，必须独立写
- `tools` 一旦显式指定就完全替换，不是合并
- `skills` 不继承主 Agent；只有默认的 general-purpose 子 Agent 才继承

收集员使用 `response_format` 返回结构化发现，让主 Agent 收到 JSON 而非自由文本。
"""

from pydantic import BaseModel, Field

from agent.config import (
    ANALYSIS_PATH,
    FINDINGS_DIR,
    REPORT_PATH,
    RESEARCH_SKILL,
    WRITER_SKILL,
    sub_model,
)
from agent.tools import internet_search, make_write_finding


class Findings(BaseModel):
    """收集员的结构化返回：只要结论与来源，不要过程。"""

    topic: str = Field(description="结论主题")
    key_points: list[str] = Field(description="3-5 条核心发现")
    sources: list[str] = Field(description="来源 URL 列表")
    confidence: float = Field(description="对本次调研的置信度，0-1")
    gaps: str = Field(description="尚未查到、需要补充的信息缺口")


COLLECTOR_PROMPT = f"""你是资料收集员，负责把一个大问题变成可核查的原始材料。

1. 把研究问题拆成 3-5 个互补的检索角度，不要用近义词重复搜同一件事
2. 用 internet_search 逐条检索
3. 对每条有价值结论调用 write_finding，落盘到 {FINDINGS_DIR}/

纪律：只报事实、查不到就写进 gaps；key_points 每条注明来源 URL；不要回过程、不要贴大段原文。"""

ANALYST_PROMPT = f"""你是分析员，负责把原始材料提炼成可用判断。

1. 用 ls 与 read_file 读取 {FINDINGS_DIR}/ 下全部结论文件
2. 交叉比对：哪些结论互相印证、哪些存在冲突
3. 用 write_file 把整理结果写入 {ANALYSIS_PATH}

结构固定为：核心结论（3 条）→ 支撑事实（带数字）→ 分歧与不确定性 → 信息缺口。
关键事实必须带来源；无法核实的标注"待验证"；不引入材料外的新事实。返回主 Agent 的内容 500 字以内。"""

SYNTHESIZER_PROMPT = f"""你是报告撰写员，负责把分析结果组织成可直接交付的简报。

1. 读取 {ANALYSIS_PATH} 与 {FINDINGS_DIR}/ 下的支撑材料
2. 用 write_file 输出最终简报到 {REPORT_PATH}
3. 简报正文同时作为你返回给主 Agent 的内容

版式：# 标题 / ## 摘要（3-5 句）/ ## 关键发现（每条附来源）/ ## 风险与不确定性 / ## 建议下一步。
全文不超过 800 字；不重复原文；不添加未经验证的结论。"""


def build_subagents(backend) -> list[dict]:
    """三个专业子 Agent；工具集按最小权限原则裁剪。"""
    write_finding = make_write_finding(backend)
    return [
        {
            "name": "collector",
            "description": (
                "资料收集员。当任务需要多次联网检索、抓取多个来源并落盘可核查材料时使用。"
                "适合研究、调研、事实核查类子任务。"
            ),
            "system_prompt": COLLECTOR_PROMPT,
            "tools": [internet_search, write_finding],
            "skills": [RESEARCH_SKILL],
            "model": sub_model(),
            "response_format": Findings,
        },
        {
            "name": "analyst",
            "description": (
                "分析员。当落盘资料已就绪、需要交叉比对、找出分歧与信息缺口并形成结论时使用。"
                "不联网检索，只处理文件系统中已有材料；写入分析稿。"
            ),
            "system_prompt": ANALYST_PROMPT,
            "skills": [RESEARCH_SKILL, WRITER_SKILL],
            "model": sub_model(),
        },
        {
            "name": "synthesizer",
            "description": (
                "报告撰写员。当分析结论已经就绪、需要产出结构化最终简报时使用。"
                "只负责成文，不重新检索也不重新分析。"
            ),
            "system_prompt": SYNTHESIZER_PROMPT,
            "skills": [WRITER_SKILL],
            "model": sub_model(),
        },
    ]
