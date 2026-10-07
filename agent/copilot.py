"""洞察台（Insight Desk）主 Agent 装配层。

一个 Agent 上叠加六项能力，对应关系见 README 的能力映射表：

    规划(TodoList) + 委派(SubAgents) + 共享文件系统(CompositeBackend)
    + 领域知识(Skills) + 跨线程记忆(Memory) + 人工审批(HITL)
"""

import pathlib

from deepagents import FilesystemPermission, create_deep_agent
from deepagents.backends import CompositeBackend, StateBackend, StoreBackend
from deepagents.backends.utils import create_file_data
from langchain.agents.middleware import TodoListMiddleware
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore

from agent.config import MEMORY_PATH, SKILLS_ROOT, main_model
from agent.reviewer import ReviewerGateMiddleware
from agent.subagents import build_subagents
from agent.tools import internet_search, make_write_finding, send_brief

# Skills 库是 Agent 级的，命名空间固定；记忆是用户级的，按 user_id 隔离
SKILLS_NAMESPACE = ("insight-desk", "skills")
SKILLS_DIR = pathlib.Path(__file__).resolve().parent.parent / "skills"

DEFAULT_PREFERENCES = """# 用户偏好
- 报告语言：中文
- 关键事实必须附来源链接
- 结论先行，避免铺垫
"""

MAIN_SYSTEM_PROMPT = f"""你是"洞察台"的主协调者，负责把模糊的研究诉求变成可交付简报。

标准工作流：
1. 先用 write_todos 制定计划（检索 → 分析 → 成文 → 投递），并随进展更新状态
2. 把资料收集委派给 collector，它会把原始结论落盘到 /findings/
3. 把结论提炼委派给 analyst，产出 /workspace/analysis.md
4. 把简报撰写委派给 synthesizer，产出 /workspace/report.md
5. 自己用 read_file 复核 report.md 与分析结论是否一致
6. 用 send_brief 投递简报（此步会触发人工审批）

工作纪律：
- 简单单步问答直接回答，不要启动整个流程，也不要创建 todo
- 委派时把"研究问题 + 期望产出路径 + 字数上限"写清楚，不要让子 Agent 猜
- 子 Agent 返回的是摘要，细节在文件里；需要细节自己 read_file，不要重复委派
- 面向用户只汇报结论与产物路径，不要复述工具调用过程
- 用户明确要求记住偏好时，先读取 {MEMORY_PATH} 再追加；写入成功后才确认"""

# 低风险只读放行；受保护路径（组织策略、Skill 库）一律禁止写入
PERMISSIONS = [
    FilesystemPermission(operations=["write"], paths=["/policies/**"], mode="deny"),
    FilesystemPermission(operations=["write"], paths=[f"{SKILLS_ROOT}/**"], mode="deny"),
]

# 高风险外发工具：可审批、可改参、可拒绝；只读与常规写入直接放行
INTERRUPT_ON = {
    "send_brief": {"allowed_decisions": ["approve", "edit", "reject"]},
    "read_file": False,
    "ls": False,
    "glob": False,
    "grep": False,
    "write_file": False,
    "edit_file": False,
}


def memory_namespace(runtime) -> tuple[str, ...]:
    """用户级记忆隔离。

    本地 `invoke()` 时 `runtime.context` 为 None（没有传 context=），
    因此回落到由 `build_agent()` 注入的 `DEFAULT_USER_ID`；部署到
    LangGraph Server 后自动按登录身份或显式传入的 context 隔离。

    ⚠️ 这个函数是记忆读写路径上唯一的事实来源：Store 预填、`memory=` 加载、
    Agent 的 write_file 三条路径都必须落到同一个 namespace，否则会出现
    "提示词里没有记忆、写入又写到了别处" 的静默失败。
    """
    if runtime is not None and getattr(runtime, "server_info", None) and runtime.server_info.user:
        return (runtime.server_info.user.identity, "memories")
    user_id = getattr(getattr(runtime, "context", None), "user_id", None)
    return (user_id or DEFAULT_USER_ID, "memories")


DEFAULT_USER_ID = "user-123"


def load_skill_files() -> dict[str, str]:
    """扫描 skills/*/SKILL.md，返回 {skill 名: 内容}。"""
    return {
        path.parent.name: path.read_text(encoding="utf-8")
        for path in sorted(SKILLS_DIR.glob("*/SKILL.md"))
    }


def build_store(user_id: str = DEFAULT_USER_ID) -> InMemoryStore:
    """预置长期记忆与 Skills。

    CompositeBackend 会剥掉路由前缀 `/skills/`，因此 Store key 必须写成
    `/deep-research/SKILL.md`。写成 `/skills/deep-research/SKILL.md` 会被补回一次前缀，
    最终暴露成错误的 `/skills/skills/deep-research/SKILL.md` —— 这是第 8 章明确的易错点。
    """
    store = InMemoryStore()
    store.put((user_id, "memories"), "/preferences.md", create_file_data(DEFAULT_PREFERENCES))
    for name, content in load_skill_files().items():
        store.put(SKILLS_NAMESPACE, f"/{name}/SKILL.md", create_file_data(content))
    return store


def build_agent(user_id: str = DEFAULT_USER_ID, checkpointer=None, store=None):
    """创建洞察台 Agent。

    Returns:
        (agent, store, checkpointer) —— store 供运行脚本核对记忆写入结果。
    """
    global DEFAULT_USER_ID
    DEFAULT_USER_ID = user_id  # 让 memory_namespace 的兜底值与预填 namespace 一致

    store = store or build_store(user_id)
    checkpointer = checkpointer or InMemorySaver()

    backend = CompositeBackend(
        default=StateBackend(),
        routes={
            "/memories/": StoreBackend(namespace=memory_namespace),
            f"{SKILLS_ROOT}/": StoreBackend(namespace=lambda _rt: SKILLS_NAMESPACE),
        },
    )

    agent = create_deep_agent(
        model=main_model(),
        # write_finding 绑定共享后端，子 Agent 与主 Agent 看到同一份文件
        tools=[internet_search, make_write_finding(backend), send_brief],
        backend=backend,
        checkpointer=checkpointer,
        store=store,
        memory=[MEMORY_PATH],
        skills=[f"{SKILLS_ROOT}/"],
        permissions=PERMISSIONS,
        subagents=build_subagents(backend),
        interrupt_on=INTERRUPT_ON,
        middleware=[
            TodoListMiddleware(),  # 第 4 章：v0.7 起规划能力需显式加入
            ReviewerGateMiddleware(),  # 第 9 章：交付前审稿
        ],
        system_prompt=MAIN_SYSTEM_PROMPT,
    )
    return agent, store, checkpointer
