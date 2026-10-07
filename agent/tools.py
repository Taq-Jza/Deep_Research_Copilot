"""洞察台（Insight Desk）的三个共享工具。

覆盖"检索 → 落盘 → 外发"链路：
- `internet_search`  主 Agent 与 collector 共用的联网检索
- `write_finding`    子 Agent 专用；通过闭包把落盘根目录钉在共享文件系统上
- `send_brief`       高风险外发工具，由 HITL 拦截审批
"""

import json
import re
from datetime import datetime, timezone

from langchain.tools import tool
from tavily import TavilyClient

from agent.config import FINDINGS_DIR

_tavily = TavilyClient()


@tool
def internet_search(query: str, max_results: int = 4) -> str:
    """联网检索，返回标题、URL 与正文摘要，用于收集资料。"""
    response = _tavily.search(query, max_results=max_results)
    blocks = [
        f"[{index}] {item['title']}\n    URL: {item['url']}\n"
        f"    摘要: {(item.get('content') or '').strip()[:400]}"
        for index, item in enumerate(response.get("results", []), start=1)
    ]
    return "\n".join(blocks) or "没有检索到结果。"


def make_write_finding(store) -> object:
    """构造把结论写进共享虚拟文件系统的落盘工具。

    子 Agent 与主 Agent 共用同一个后端，但只有拿到这个工具的身份才能写 /findings/，
    避免子 Agent 把文件散落到任意路径。
    """

    @tool
    def write_finding(topic: str, summary: str, sources: str) -> str:
        """把一条调研结论落盘到 /findings/，供后续阶段读取。

        Args:
            topic: 结论主题，会转成文件名。
            summary: 结论正文，建议 200 字以内。
            sources: 来源 URL，多个用换行分隔。
        """
        slug = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "-", topic).strip("-")[:40] or "finding"
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        path = f"{FINDINGS_DIR}/{stamp}-{slug}.md"
        payload = json.dumps(
            {"topic": topic, "summary": summary, "sources": sources.splitlines()},
            ensure_ascii=False,
            indent=2,
        )
        store.write(path, payload)
        return f"已落盘到 {path}（{len(payload)} 字节）"

    return write_finding


@tool
def send_brief(channel: str, subject: str, body: str) -> str:
    """把最终简报投递到指定渠道（demo 中为模拟投递，不产生真实外发）。"""
    return f"简报已投递到 {channel}｜主题：{subject}｜正文 {len(body)} 字。"
