# 洞察台（Insight Desk）

用 Deep Agents 搭一个「研究协作 Agent」：把一句模糊的调研诉求，跑成一份带来源、可复核的团队简报。

项目对应课程 **第 3–9 章**，把其中 **六项能力** 组装到同一个 Agent 上，而不是六个互不相干的例子。

---

## 一、能力映射

| # | 能力 | 章节 | 在本项目中的落点 |
|---|---|---|---|
| 1 | 虚拟文件系统 + 上下文管理 | 第 3 章 | `CompositeBackend`：`/findings`、`/workspace` 是主/子 Agent 共享的草稿区；`/memories`、`/skills` 路由到持久化 Store |
| 2 | 任务规划 | 第 4 章 | `middleware=[TodoListMiddleware()]`，v0.7 起需显式加入 |
| 3 | 子 Agent 与上下文隔离 | 第 5 章 | `collector` / `analyst` / `synthesizer` 三个专业子 Agent，各自独立上下文与工具集 |
| 4 | 结构化子 Agent 返回 | 第 5 章 | `collector` 用 `response_format=Findings` 返回 JSON 而非自由文本 |
| 5 | 长期记忆 | 第 8 章 | `memory=["/memories/preferences.md"]` + `StoreBackend` 按用户隔离，跨线程加载 |
| 6 | Human-in-the-Loop | 第 9 章 | 两层：`interrupt_on` 拦外发工具；自定义 `ReviewerGateMiddleware` 在交付前审稿 |

**Skills（第 7 章）** 作为第 4 项能力的载体一并接入：`skills/deep-research` 与 `skills/report-writer` 通过 Store 注入，用 `FilesystemPermission` 设为只读。

---

## 二、它实际做什么

```
用户：调研 deepagents 0.7 的异步子 Agent 适合什么场景、有哪些限制
        │
        ├─ 主 Agent 读 /skills/*/SKILL.md，用 write_todos 制定计划
        │
        ├─ task(collector)    联网检索 → write_finding 落盘 /findings/*.md
        ├─ task(analyst)      读 /findings → 交叉比对 → 写 /workspace/analysis.md
        ├─ task(synthesizer)  读 /workspace/analysis.md → 写 /workspace/report.md
        │
        ├─ 主 Agent read_file 复核 report.md
        └─ send_brief  ← 被人工审批拦下，批准/改参/拒绝后才执行
```

关键点：三个子 Agent 的中间过程（十几次检索、多个文件读写）**不会进入主 Agent 的上下文**，
主 Agent 只收到各自 400–500 字的摘要；原文留在共享文件系统里，需要时可 `read_file` 回查。

---

## 三、目录结构

```
Task8_Deep_Research_Copilot/
├── main.py                     # 运行脚本：四幕演示，可单幕运行
├── agent/
│   ├── config.py               # 路径约定 + 模型工厂（主/子走不同服务商）
│   ├── tools.py                # 三个共享工具：internet_search / write_finding / send_brief
│   ├── subagents.py            # 三个专业子 Agent + 结构化返回 schema
│   ├── reviewer.py             # 自定义 Middleware：交付前审稿（底层 interrupt()）
│   └── copilot.py              # 装配层：把六项能力拼成一个 Agent
├── skills/
│   ├── deep-research/SKILL.md  # 检索流程、落盘规范、引用格式
│   ├── report-writer/SKILL.md  # 统一版式、字数上限、来源标注
│   └── shared/                 # 预留团队级 Skills（last-wins 覆盖）
├── requirements.txt
└── .env                        # 不提交（见 .gitignore）
```

---

## 四、运行

```bash
# 依赖
pip install -r requirements.txt

# 全部四幕（约 15 分钟，第 1 幕最耗时）
python main.py

# 单幕
python main.py 1     # 完整研究工作流（规划 + 委派 + 共享文件系统 + Skills）
python main.py 2     # 长期记忆跨线程
python main.py 3     # 投递审批（interrupt_on）
python main.py 4     # 交付前审稿（自定义 Middleware + interrupt()）

# 切到真人交互审批（第 3、4 幕）
python main.py 3 --interactive
```

`.env` 需要：

| 变量 | 用途 |
|---|---|
| `MODEL_NAME` / `DEEPSEEK_URL` / `DEEPSEEK_API_KEY` | 主 Agent 模型 |
| `SUB_MODEL_NAME` / `SILICONFLOW_URL` / `SILICONFLOW_API_KEY` | 子 Agent 模型（演示「不同子 Agent 用不同模型」） |
| `TAVILY_API_KEY` | `internet_search` |
| `LANGSMITH_TRACING` / `LANGSMITH_API_KEY` | 可选，开启 trace |

> **编码**：中文 Windows（默认 cp936/GBK）下建议设 `PYTHONUTF8=1` 再运行，避免第三方库用裸 `open()` 读 UTF-8 文件时报 `UnicodeDecodeError`。

---

## 五、四幕演示说明

### 第 1 幕 · 完整研究工作流

覆盖第 3/4/5/7 章。用 `stream(..., subgraphs=True)` 实时打印主 Agent 与子 Agent 的**全部工具调用**，
结束后打印 `todos` 轨迹与虚拟文件系统产物清单。断言：共享文件系统必须产生文件（否则说明委派或落盘没生效）。

### 第 2 幕 · 长期记忆跨线程

覆盖第 8 章。对话 1 让 Agent 记住新偏好 → 从 **Store 核对真实写入结果**（不能只看模型回复"已记住"）
→ 对话 2 用**全新 `thread_id`** 验证偏好仍从 Store 加载到系统提示词。断言：新线程回复中必须出现新偏好。

### 第 3 幕 · 投递审批

覆盖第 9 章 `interrupt_on`。用一条已定稿内容请求投递，因此流程必然走到 `send_brief`。
非交互模式演示 `edit`：审批人把渠道从 `team` 改成 `team-channel`，恢复后使用的是改写后的参数。
`--interactive` 可切到真人逐条 `approve / edit / reject`。

### 第 4 幕 · 交付前审稿

覆盖第 9 章底层 `interrupt()`。暂停点**不对应任何工具**——是"模型已写完最终答复、尚未交付"这一刻。
这只能靠自定义 Middleware 的 Node-style Hook 实现，`interrupt_on` 表达不了。

---

## 六、两个值得注意的实现细节

### 1. 记忆文件名：namespace 必须与预填路径一致

`memory=` 的加载链路是 `before_agent → backend.download_files()`，一旦 namespace 与
`store.put()` 时不一致，框架**不会报错**，只会静默加载不到内容——表现为"Agent 完全不知道偏好"。

本项目的 `memory_namespace()` 是记忆读写路径上**唯一的事实来源**，且 `build_agent()` 会把
`DEFAULT_USER_ID` 同步给兜底分支：

```python
def memory_namespace(runtime):
    if runtime is not None and getattr(runtime, "server_info", None) and runtime.server_info.user:
        return (runtime.server_info.user.identity, "memories")
    user_id = getattr(getattr(runtime, "context", None), "user_id", None)
    return (user_id or DEFAULT_USER_ID, "memories")   # 本地 invoke() 时 context 为 None
```

> **踩坑记录**：本地 `invoke()` 不传 `context=` 时，`runtime.context` 就是 `None`。
> 早期版本直接 `getattr(runtime.context, "user_id", "local-user")`，导致运行期 namespace 变成
> `("local-user", "memories")`，而文件预填在 `("user-123", "memories")` —— 记忆永远加载不到。
> 排查方式是给 `memory_namespace` 加个探针，打印真实返回值，而不是只看预填的 key。

### 2. `write_finding` 为什么直接调 backend，而不是返回路径让模型再写

子 Agent 的落盘工具是 `make_write_finding(backend)`：**闭包里持有同一个 backend 实例，直接
`backend.write(path, payload)`**。

这样做的原因：让模型"先返回路径、再自己调 `write_file`"是两步、会失败的模式；闭包绑定后端后，
子 Agent 只拿到一个工具，落盘路径与共享文件系统天然一致（主 Agent 用 `read_file` 能直接读到）。

---

## 七、已知边界

- **检索质量**：`internet_search` 走 Tavily，返回的是标题 + 摘要，不抓全文。要更深的内容需另加 `fetch_page`。
- **Store 是内存态**：`InMemoryStore` 进程重启即丢。生产应换 `PostgresStore`（第 8 章）。
- **Checkpointer 是内存态**：`InMemorySaver` 同理；跨进程恢复中断需要持久化 Checkpointer。
- **`interrupt()` 的重放语义**：恢复时节点从头重放，`interrupt()` 之前的副作用必须幂等（第 9 章规则 2）。
  `ReviewerGateMiddleware` 的 `after_model` 里只做消息读取，因此是安全的。
- **模型流控**：硅基流动免费额度会返回 429。`sub_model()` 设了 `max_retries=6` 做线性退避。
