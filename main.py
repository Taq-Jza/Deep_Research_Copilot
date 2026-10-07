"""Insight Desk运行脚本。

四项演示各自独立，可以单独跑：

    python main.py               # 全部（默认）
    python main.py 1             # 只跑第 1 幕：完整研究工作流
    python main.py 2             # 只跑第 2 幕：长期记忆跨线程
    python main.py 3             # 只跑第 3 幕：投递审批（HITL）
    python main.py 4             # 只跑第 4 幕：交付前审稿（自定义 Middleware）

加 `--interactive` 可切到真人交互审批。
"""

import os
import sys
import uuid

from dotenv import load_dotenv

load_dotenv()

from langgraph.types import Command

from agent.config import ANALYSIS_PATH, FINDINGS_DIR, MEMORY_PATH, REPORT_PATH
from agent.copilot import build_agent

USER_ID = "user-123"

RESEARCH_TASK = (
    "调研一下 deepagents 0.7 的异步子 Agent （Async SubAgent）适合什么场景、"
    "有哪些已知限制，给团队一个是否引入的初步判断。"
)


# --------------------------------------------------------------------------- #
# 输出辅助
# --------------------------------------------------------------------------- #
def title(text: str) -> None:
    print(f"\n{'=' * 72}\n{text}\n{'=' * 72}")


def step(text: str) -> None:
    print(f"\n--- {text} ---")


def show_todos(todos) -> None:
    """打印任务清单，直观呈现规划轨迹。"""
    if not todos:
        print("(本次未创建任务清单)")
        return
    icon = {"completed": "[x]", "in_progress": "[>]", "pending": "[ ]"}
    for item in todos:
        print(f"  {icon.get(item['status'], '[?]')} {item['content']}")


def last_reply(result) -> str:
    """取最终自然语言回复。

    兼容两种返回形态：普通 invoke 返回 dict，`version="v2"` / 中断恢复返回 GraphOutput
    （消息在 `.value` 里）。
    """
    messages = getattr(result, "value", result).get("messages", [])
    for message in reversed(messages):
        if type(message).__name__ == "AIMessage" and not message.tool_calls:
            return message.content
    return "(无最终回复)"


# --------------------------------------------------------------------------- #
# 第 1 幕：规划 + 委派 + 共享文件系统 + Skills
# --------------------------------------------------------------------------- #
def _iter_updates(chunk):
    """把 stream(updates, subgraphs=True) 的 chunk 摊平成 (节点名, 更新字典) 序列。

    开启 subgraphs 后每条 chunk 可能是 `(namespace, update)` 元组（子图/子 Agent 更新）
    或 `{node: update}` 字典（主图更新），这里递归摊平两种形态。
    """
    if isinstance(chunk, tuple):
        for item in chunk:
            yield from _iter_updates(item)
    elif isinstance(chunk, dict):
        for node, update in chunk.items():
            if isinstance(update, dict) and {"messages", "todos", "files"} & update.keys():
                yield node, update
            else:
                yield from _iter_updates(update)


def trace(agent, payload: dict, config: dict) -> dict:
    """流式跑一遍 Agent，边跑边打印工具调用轨迹，最后返回完整状态。"""
    for chunk in agent.stream(payload, config=config, stream_mode="updates", subgraphs=True):
        for node, update in _iter_updates(chunk):
            for message in update.get("messages") or []:
                for call in getattr(message, "tool_calls", None) or []:
                    args = call["args"]
                    detail = next(
                        (v for k in ("description", "file_path", "query", "subject", "channel")
                         if (v := args.get(k))),
                        "",
                    )
                    print(f"  [{node}] {call['name']}: {str(detail)[:76]}")
            if update.get("todos"):
                print(f"  [{node}] todos 已更新")
    return agent.get_state(config).values


def act1_research_workflow(agent) -> None:
    title("第 1 幕 · 完整研究工作流")
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}

    step("实时轨迹（主 Agent 与子 Agent 的全部工具调用）")
    # 主 Agent 末尾会调用 send_brief，它在第 1 幕里会触发人工审批；
    # 第 1 幕只验证"规划 + 委派 + 落盘"，因此这里把审批交给第 3 幕单独演示。
    result = trace(agent, {"messages": [{"role": "user", "content": RESEARCH_TASK}]}, config)

    step("任务清单（write_todos）")
    show_todos(result.get("todos"))

    step("虚拟文件系统产物（共享落盘）")
    files = result.get("files") or {}
    for path in sorted(files):
        print(f"  {path}  ({len(files[path]['content'])} 字符)")

    step("最终回复")
    # 本幕末尾会调用 send_brief（高风险外发），它在审稿闸门处暂停，
    # 因此这里通常拿不到最终自然语言回复——审批链路留给第 3 幕单独演示。
    messages = result.get("messages") or []
    has_reply = any(type(m).__name__ == "AIMessage" and not m.tool_calls for m in messages)
    print(last_reply(result) if has_reply else "  （末步停在 send_brief 审批点，无最终回复；审批演示见第 3 幕）")

    step("断言")
    assert files, "未产生任何文件，说明子 Agent 没有落盘"
    findings = [p for p in files if p.startswith(FINDINGS_DIR)]
    print(f"  [OK] 共享文件系统共 {len(files)} 个文件，其中落盘结论 {len(findings)} 条")


# --------------------------------------------------------------------------- #
# 第 2 幕：长期记忆跨线程
# --------------------------------------------------------------------------- #
def act2_long_term_memory(agent, store, user_id: str) -> None:
    title("第 2 幕 · 长期记忆跨线程")

    step("对话 1：写入偏好（新 thread）")
    agent.invoke(
        {"messages": [{"role": "user", "content": "记住我的偏好：简报里所有数字都要标注统计口径。"}]},
        config={"configurable": {"thread_id": str(uuid.uuid4())}},
    )
    saved = store.get((user_id, "memories"), "/preferences.md")
    assert saved is not None, "偏好文件未写入 Store"
    print(saved.value["content"].strip())

    step("核对写入结果（只看工具是否真的写成功）")
    assert "统计口径" in saved.value["content"], "偏好未按约定写入，请检查 trace"
    print("  [OK] 新偏好已并入 /memories/preferences.md，旧偏好未被覆盖")

    step("对话 2：全新 thread，验证记忆是否跨线程生效")
    result = agent.invoke(
        {"messages": [{"role": "user", "content": "用一句话说明你会怎么遵守我的偏好。"}]},
        config={"configurable": {"thread_id": str(uuid.uuid4())}},
    )
    print(last_reply(result))

    step("断言")
    # 模型复述偏好时会用同义表述，因此只锚定一个稳定特征词：
    # "统计" 来自对话 1 新写入的偏好，是"跨线程读到新内容"的直接证据。
    reply = last_reply(result)
    assert "统计" in reply, (
        f"新线程未读到新偏好，记忆未跨线程生效：{reply[:200]}"
    )
    print("  [OK] 两个 thread_id 不同，偏好仍从 Store 加载到系统提示词")


# --------------------------------------------------------------------------- #
# 第 3 幕：投递审批（interrupt_on）
# --------------------------------------------------------------------------- #
def _ask_reviewer(interactive: bool) -> dict:
    """审稿决策。

    非交互模式默认"退回"，这样能稳定演示"草稿被拦下、流程没有直接交付"。
    """
    if not interactive:
        return {"approved": False, "reason": "退回：请在摘要中先给出一句话结论，再展开依据。"}
    verdict = input("是否批准交付？[y]批准 / [n]退回：").strip().lower()
    if verdict == "y":
        return {"approved": True}
    return {"approved": False, "reason": input("  退回理由：").strip() or "审批未通过"}


def _decide_interactively(value) -> list[dict]:
    """让真人在终端逐条审批。"""
    decisions: list[dict] = []
    for request in value["action_requests"]:
        args = request.get("arguments", request.get("args", {}))
        print(f"\n待审批工具：{request['name']}")
        for key, item in args.items():
            print(f"    {key}: {str(item)[:120]}")
        choice = input("选择 [a]批准 / [e]改渠道 / [r]拒绝：").strip().lower()
        if choice == "e":
            channel = input(f"  新渠道（当前 {args.get('channel')}）：").strip() or args["channel"]
            decisions.append(
                {
                    "type": "edit",
                    "edited_action": {"name": request["name"], "args": {**args, "channel": channel}},
                }
            )
        elif choice == "r":
            reason = input("  拒绝原因（会反馈给 Agent）：").strip()
            decisions.append({"type": "reject", "message": reason or "用户拒绝了本次投递。"})
        else:
            decisions.append({"type": "approve"})
    return decisions


DELIVERY_PROMPT = (
    "把下面这条已经定稿的简报投递给团队，直接调用 send_brief，不要再检索、不要改动内容：\n"
    "主题：本周研究进展\n"
    "正文：本周完成 3 项调研，均已归档；其中 2 项结论明确、1 项仍需补充数据。"
)


def act3_delivery_approval(agent, interactive: bool) -> None:
    title("第 3 幕 · 投递审批（interrupt_on）")
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}

    step("发起投递请求（内容已定稿，只差外发这一步）")
    result = agent.invoke(
        {"messages": [{"role": "user", "content": DELIVERY_PROMPT}]},
        config=config,
        version="v2",
    )

    # 交付前审稿与工具审批可能交替出现，逐层处理直到没有中断
    while result.interrupts:
        value = result.interrupts[0].value

        if value.get("type") == "draft_review":
            print("\n[审稿] 模型草稿：", str(value["draft"])[:180].replace("\n", " "))
            decision = _ask_reviewer(interactive)
            result = agent.invoke(
                Command(resume=decision), config=config, version="v2"
            )
            continue

        step(f"命中人工审批：{len(value['action_requests'])} 个待批工具")
        for request in value["action_requests"]:
            args = request.get("arguments", request.get("args", {}))
            print(f"  工具 {request['name']} 参数：{args}")
        print(f"  可选项：{value['review_configs'][0]['allowed_decisions']}")

        if interactive:
            decisions = _decide_interactively(value)
        else:
            # 非交互模式演示 edit：审批人把渠道改成 team-channel
            decisions = [
                {
                    "type": "edit",
                    "edited_action": {
                        "name": "send_brief",
                        "args": {
                            "channel": "team-channel",
                            "subject": "本周研究进展",
                            "body": "本周完成 3 项调研，均已归档；其中 2 项结论明确、1 项仍需补充数据。",
                        },
                    },
                }
            ]
        print("\n  决策：", decisions)
        result = agent.invoke(Command(resume={"decisions": decisions}), config=config, version="v2")

    step("最终回复")
    print(last_reply(result))
    print("\n  [OK] send_brief 被拦截后才执行；恢复时使用了 edit 改写后的渠道参数")


# --------------------------------------------------------------------------- #
# 第 4 幕：交付前审稿（自定义 Middleware + interrupt()）
# --------------------------------------------------------------------------- #
def act4_review_gate(agent, interactive: bool) -> None:
    title("第 4 幕 · 交付前审稿（自定义 Middleware + interrupt()）")
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}

    step("提一个简单问题，观察模型交付前被拦下")
    result = agent.invoke(
        {"messages": [{"role": "user", "content": "用一句话说明 Async SubAgent 的核心价值。"}]},
        config=config,
        version="v2",
    )

    assert result.interrupts, "未被审稿中间件拦截，请检查 ReviewerGateMiddleware"
    draft = result.interrupts[0].value["draft"]
    print("  草稿：", str(draft)[:160].replace("\n", " "))

    decision = _ask_reviewer(interactive)
    step("审稿结论")
    print("  已批准交付" if decision["approved"] else f"  已退回：{decision['reason']}")

    result = agent.invoke(Command(resume=decision), config=config, version="v2")
    step("最终回复")
    print(last_reply(result))
    print("\n  [OK] 暂停点不对应任何工具，靠 Node-style Hook 里的 interrupt() 实现")


# --------------------------------------------------------------------------- #
# 入口
# --------------------------------------------------------------------------- #
def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    interactive = "--interactive" in sys.argv
    selected = args[0] if args else "all"

    agent, store, _ = build_agent(user_id=USER_ID)

    print(f"洞察台已就绪 | 记忆路径 {MEMORY_PATH} | 落盘目录 {FINDINGS_DIR}")
    print(f"分析与简报路径 {ANALYSIS_PATH} / {REPORT_PATH}")

    if selected in ("all", "1"):
        act1_research_workflow(agent)
    if selected in ("all", "2"):
        act2_long_term_memory(agent, store, USER_ID)
    if selected in ("all", "3"):
        act3_delivery_approval(agent, interactive)
    if selected in ("all", "4"):
        act4_review_gate(agent, interactive)

    title("演示完成")


if __name__ == "__main__":
    main()
