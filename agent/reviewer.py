"""自定义 Middleware：在最终答复交付给用户之前拦截审稿（第 9 章）。

`interrupt_on` 只能按"工具名"拦截。若暂停点不对应某个工具——例如
"模型已经写完最终答复、尚未交给用户"——就要用 Node-style Hook 直接调用底层 `interrupt()`。

`after_model` 是 Agent 图中的独立节点，因此可以作为稳定的中断边界：
- 有 tool_calls 时说明流程还没结束，直接放行
- 没有 tool_calls 说明模型正在交付最终答复，此时暂停等待人工决策

底层 `interrupt()` 的三条规则在本类中都成立：
1. 不写裸 `try/except`（会吞掉 interrupt 抛出的控制流异常）
2. `interrupt()` 之前的代码必须幂等（恢复时节点从头重放；这里只做纯函数式的消息读取）
3. 不在同一节点内动态改变 `interrupt()` 调用顺序（这里只调用一次）
"""

from typing import Any

from langchain.agents.middleware import AgentMiddleware, AgentState
from langchain.messages import AIMessage
from langgraph.runtime import Runtime
from langgraph.types import interrupt


class ReviewerGateMiddleware(AgentMiddleware):
    """交付前审稿：模型生成最终草稿后暂停，等待人工批准或退回。"""

    def after_model(
        self,
        state: AgentState,
        runtime: Runtime,
    ) -> dict[str, Any] | None:
        last_message = state["messages"][-1]
        # 仍有工具调用 → 流程未结束，放行
        if not isinstance(last_message, AIMessage) or last_message.tool_calls:
            return None

        decision = interrupt(
            {
                "type": "draft_review",
                "draft": last_message.content,
                "message": "是否批准将这份答复交付给用户？",
            }
        )

        if decision.get("approved"):
            return None

        reason = decision.get("reason") or "审批未通过"
        return {"messages": [AIMessage(content=f"[审稿未通过] {reason}")]}
