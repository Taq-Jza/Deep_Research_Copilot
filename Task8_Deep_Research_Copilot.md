# 洞察台（Insight Desk）运行演示记录

> 本文档是 `Task8_Deep_Research_Copilot` 的**完整运行演示记录**，收录四幕演示的真实终端输出、
> 关键观测点与断言结果。所有输出均为实际运行采集，未做美化。

- 运行环境：Windows / 中文系统；`.venv`（Python 3.12.10）
- 运行命令：`PYTHONUTF8=1 python main.py`（全量四幕，一次跑完）
- 主 Agent 模型：`deepseek-chat`（DeepSeek）
- 子 Agent 模型：`deepseek-ai/DeepSeek-V3.2`（硅基流动）
- 检索工具：Tavily

---

## 一、启动信息

每次运行先打印一次就绪信息，确认路径约定无误：

```
洞察台已就绪 | 记忆路径 /memories/preferences.md | 落盘目录 /findings
分析与简报路径 /workspace/analysis.md / /workspace/report.md
```

---

## 二、第 1 幕 · 完整研究工作流（第 3/4/5/7 章）

### 输入

```
调研一下 deepagents 0.7 的异步子 Agent（Async SubAgent）适合什么场景、
有哪些已知限制，给团队一个是否引入的初步判断。
```

### 实时轨迹（主 Agent + 全部子 Agent 的工具调用）

用 `stream(..., stream_mode="updates", subgraphs=True)` 摊平 `(namespace, update)` 与 `{node: update}`
两种 chunk 形态后逐条打印。下面是本次完整运行的真实轨迹：

```
--- 实时轨迹（主 Agent 与子 Agent 的全部工具调用） ---
  [model] write_todos: 
  [model] read_file: /skills/deep-research/SKILL.md                              ← 加载领域 Skill
  [model] read_file: /skills/report-writer/SKILL.md
  [tools] todos 已更新
  [model] task: 研究任务：调研 LangChain / LangGraph 生态中 deepagents 0.7 版本的…  ← 委派 collector
  [model] ls: 
  [model] internet_search: deepagents 0.7 async subagent release notes changelog
  [model] internet_search: "async subagents" deepagents 0.7 architecture LangSmith Deployment
  [model] internet_search: deepagents async subagents tutorial use case example blog
  [model] internet_search: deepagents async subagents issues bugs limitations concurrent state manageme
  [model] internet_search: async subagents implementation mechanism spawn timeout cancellation streamin
  [model] read_file: /docs/langchain-5e9cc07a.mintlify.app/oss/python/releases/changelog
  [model] internet_search: "AsyncSubAgent" python deepagents 0.7 implementation
  [model] internet_search: deepagents 0.7 vs 0.5 async subagents differences update
  [model] read_file: /docs/langchain.com/oss/python/deepagents/async-subagents
  [model] write_finding:                                                        ← 逐条落盘 /findings/
  [model] write_finding: 
  [model] write_finding: 
  [model] write_finding: 
  [model] internet_search: deepagents async subagents concurrency limit token cost timeout
  [model] write_finding: 
  [model] ls: 
  [model] write_finding: 
  [model] ls: 
  [model] read_file: /findings/20261006T174842Z-deepagents-0-7异步子Agent支持后台非阻塞并发任务.md
  …（读完全部 finding）
  [model] Findings:                                                             ← 返回结构化 JSON 给主 Agent
  [model] ls: 
  [model] internet_search: deepagents 0.7 release notes async subagent
  [model] internet_search: Deep Agents v0.7 changelog migration notes
  [model] internet_search: langchain deepagents async subagents documentation limitations
  [model] write_finding: （×5）
  [model] write_todos: 
  [tools] todos 已更新
  [model] task: 分析任务：基于 /findings/ 目录下已落盘的调研材料…                    ← 委派 analyst
  [model] ls: 
  [model] read_file: /findings/…（11 个）
  [model] write_file: /workspace/analysis.md                                    ← 产出分析稿
  [model] read_file: /workspace/analysis.md
  [model] write_todos: 
  [tools] todos 已更新
  [model] task: 撰写任务：读取 /workspace/analysis.md…按 report-writer 版式产出…    ← 委派 synthesizer
  [model] read_file: /workspace/analysis.md
  [model] read_file: /findings/…（4 个）
  [model] write_file: /workspace/report.md                                      ← 产出最终简报
  [model] read_file: /workspace/report.md                                       ← 主 Agent 复核
  [model] write_todos: 
  [tools] todos 已更新
  [model] send_brief: DeepAgents 异步子 Agent 引入评估简报                        ← 高风险外发，被闸门拦下
```

### 任务清单（第 4 章：`write_todos`）

```
--- 任务清单（第 4 章：write_todos） ---
  [x] 检索 deepagents 0.7 Async SubAgent 相关资料，落盘到 /findings/
  [x] 分析资料，产出 /workspace/analysis.md
  [x] 撰写简报 /workspace/report.md
  [x] 复核 report.md 与 analysis 结论一致性
  [>] 投递简报（触发人工审批）
```

清单在过程中被多次更新（轨迹里出现 4 次 `todos 已更新`），且**在上下文被压缩后依然保留**——
这是第 4 章强调的 `todos` 状态字段特性。

### 虚拟文件系统产物（第 3 章：共享落盘）

```
--- 虚拟文件系统产物（第 3 章：共享落盘） ---
  /findings/20261006T174842Z-deepagents-0-7异步子Agent支持后台非阻塞并发任务.md  (550 字符)
  /findings/20261006T174854Z-异步子Agent具有mid-flight更新与取消能力-支持任务状态跟踪.md  (478 字符)
  /findings/20261006T174913Z-异步子Agent已有生产级别应用案例和开发实践反馈.md  (568 字符)
  /findings/20261006T174927Z-异步子Agent使用需谨慎状态管理和错误处理-有最佳实践规范.md  (515 字符)
  /findings/20261006T175004Z-异步子Agent的流式输出和并发机制未在0-7版本中明确详细说明.md  (460 字符)
  /findings/20261006T175021Z-异步子Agent与同步子Agent适用场景对比清晰.md  (339 字符)
  /findings/20261006T175223Z-Async-SubAgent-依赖远程-Agent-Protocol-部署环境-.md  (425 字符)
  /findings/20261006T175223Z-Async-SubAgent-实际引入于-v0-5-v0-7-的变更是-harn.md  (722 字符)
  /findings/20261006T175223Z-Async-与-inline-subagent-的取舍-非阻塞与可控性换运维复杂.md  (476 字符)
  /findings/20261006T175223Z-版本成熟度风险-pre-1-0-阶段-minor-升级可含破坏性变更.md  (412 字符)
  /findings/20261006T175223Z-量化边界缺失-并发上限-超时-取消传播-token-成本均无官方文档.md  (466 字符)
  /workspace/analysis.md  (3980 字符)
  /workspace/report.md  (1804 字符)
```

### 断言与结论

```
--- 最终回复 ---
  （末步停在 send_brief 审批点，无最终回复；审批演示见第 3 幕）

--- 断言 ---
  [OK] 共享文件系统共 13 个文件，其中落盘结论 11 条
```

> **说明**：本幕末尾 `send_brief` 撞上第 9 章的审稿闸门而暂停，因此**不产生最终自然语言回复**
> （演示脚本已显式提示这一点）。投递审批链路在第 3 幕单独完整演示。

**验证到的能力：**

| 能力 | 证据 |
|---|---|
| 第 3 章 虚拟文件系统 | 子 Agent 落盘 11 个 `/findings/*.md`，主 Agent 用 `read_file` 复核到 `report.md` / `analysis.md` |
| 第 4 章 任务规划 | `write_todos` 生成 5 项清单，状态从 `pending → in_progress → completed` 多次推进 |
| 第 5 章 子 Agent | 三次 `task(...)` 委派（collector / analyst / synthesizer），上下文隔离 |
| 第 5 章 结构化返回 | `[model] Findings:` 说明 collector 用 `response_format` 返回了结构化对象 |
| 第 7 章 Skills | 主 Agent 与子 Agent 都 `read_file /skills/*/SKILL.md`，说明 Skill 被渐进式加载 |

---

## 三、第 2 幕 · 长期记忆跨线程（第 8 章）

### 对话 1：写入新偏好（新 thread）

```
--- 对话 1：写入偏好（新 thread） ---
# 用户偏好
- 报告语言：中文
- 关键事实必须附来源链接
- 结论先行，避免铺垫
- 简报中所有数字必须标注统计口径（数据来源、统计时点/区间、统计范围与方法）
```

Agent 没有覆盖原有偏好，而是**先读原文件再追加**，把新偏好并入记忆文件。

### 核对写入结果（从 Store 直接读取，不信任模型自述）

```
--- 核对写入结果（只看工具是否真的写成功） ---
  [OK] 新偏好已并入 /memories/preferences.md，旧偏好未被覆盖
```

### 对话 2：全新 `thread_id` 验证跨线程生效

```
--- 对话 2：全新 thread，验证记忆是否跨线程生效 ---
我会先读取 /memories/preferences.md，按其中四条偏好执行每份简报：
中文撰写、关键事实附来源链接、结论先行、所有数字标注统计口径（来源／时点区间／范围与方法）。
```

### 断言与结论

```
--- 断言 ---
  [OK] 两个 thread_id 不同，偏好仍从 Store 加载到系统提示词
```

**验证到的能力（第 8 章）：**

- 两次 `invoke()` 使用**完全不同的 `thread_id`**，但第二次仍读到了第一次写入的偏好
- 证明记忆不是靠对话历史携带，而是靠 `memory=["/memories/preferences.md"]`
  在 `before_agent` 阶段从 `StoreBackend` 加载进系统提示词
- 断言只锚定新偏好引入的特征词「统计」，避免模型同义复述导致误判

> **踩坑记录**：本地 `invoke()` 不传 `context=` 时 `runtime.context` 为 `None`，
> 早期版本使运行期 namespace 变成 `("local-user", "memories")`，而预填在 `("user-123", "memories")`，
> 框架不报错、只是静默加载不到记忆。修复后 `memory_namespace()` 成为唯一事实来源。详见 README 第六节。

---

## 四、第 3 幕 · 投递审批（第 9 章：`interrupt_on`）

### 输入（内容已定稿，流程必然走到 `send_brief`）

```
把下面这条已经定稿的简报投递给团队，直接调用 send_brief，不要再检索、不要改动内容：
主题：本周研究进展
正文：本周完成 3 项调研，均已归档；其中 2 项结论明确、1 项仍需补充数据。
```

### 命中人工审批

```
--- 发起投递请求（内容已定稿，只差外发这一步） ---

--- 命中人工审批：1 个待批工具 ---
  工具 send_brief 参数：{'channel': '团队', 'subject': '本周研究进展',
                        'body': '本周完成 3 项调研，均已归档；其中 2 项结论明确、1 项仍需补充数据。'}
  可选项：['approve', 'edit', 'reject']
```

### 审批人选择 `edit`：把渠道从「团队」改成 `team-channel`

```
  决策： [{'type': 'edit', 'edited_action': {'name': 'send_brief',
          'args': {'channel': 'team-channel', 'subject': '本周研究进展', 'body': '…'}}}]
```

恢复执行（`Command(resume={"decisions": decisions})`）后，工具使用的是**改写后的参数**。

### 恢复后撞上第二层闸门（交付前审稿）

```
[审稿] 模型草稿： 已投递到 team-channel（主题：本周研究进展，正文 37 字），内容按原稿发送，未做任何改动。

--- 最终回复 ---
[审稿未通过] 退回：请在摘要中先给出一句话结论，再展开依据。

  [OK] send_brief 被拦截后才执行；恢复时使用了 edit 改写后的渠道参数
```

**验证到的能力（第 9 章）：**

- `interrupt_on={"send_brief": {"allowed_decisions": ["approve", "edit", "reject"]}}`
  确实在工具执行**之前**暂停，返回 `action_requests` 与 `review_configs`
- `edit` 决策通过 `edited_action`（固定用 `args` 字段、且必须带 `name`）改写了渠道参数
- 恢复后进入**第二层**中断（自定义 Middleware 的审稿闸门），两层闸门可交替出现并被循环处理

> 另经交互模式确认：两处闸门都选批准时，`send_brief` 正常执行，
> 最终回复为「已按原文投递到 team 渠道」。

---

## 五、第 4 幕 · 交付前审稿（第 9 章：自定义 Middleware + `interrupt()`）

### 输入

```
用一句话说明 Async SubAgent 的核心价值。
```

### 暂停点不对应任何工具

```
--- 提一个简单问题，观察模型交付前被拦下 ---
  草稿： Async SubAgent 的核心价值在于：让主 Agent 把耗时的子任务（如多轮检索、长文写作）
        异步派发出去并行执行，主流程无需阻塞等待即可继续处理其他工作，
        从而在保持上下文精简的同时显著提升整体吞吐与响应速度。

--- 审稿结论 ---
  已退回：退回：请在摘要中先给出一句话结论，再展开依据。

--- 最终回复 ---
[审稿未通过] 退回：请在摘要中先给出一句话结论，再展开依据。

  [OK] 暂停点不对应任何工具，靠 Node-style Hook 里的 interrupt() 实现
```

**验证到的能力（第 9 章）：**

- 暂停点**不对应任何工具**——是"模型已生成最终答复、尚未交给用户"这一刻，
  `interrupt_on` 表达不了这种中断，必须用自定义 Middleware 的 `after_model` Hook 直接 `interrupt()`
- `after_model` 是图中的独立节点，可作为稳定的中断边界
- 退回后 `ReviewerGateMiddleware` 注入 `[审稿未通过]` 消息取代原草稿，流程没有直接交付

---

## 六、验证结论汇总

| 幕 | 覆盖章节 | 断言结果 | 核心证据 |
|---|---|---|---|
| 第 1 幕 | 3 / 4 / 5 / 7 | ✅ 13 个文件，11 条落盘结论 | 三次子 Agent 委派、`write_todos` 推进、Skills 被加载 |
| 第 2 幕 | 8 | ✅ 跨线程读到新偏好 | 不同 `thread_id` 仍加载 `/memories/preferences.md` |
| 第 3 幕 | 9 | ✅ `edit` 改写渠道后执行 | `send_brief` 被拦 → 改参 → 两层闸门交替恢复 |
| 第 4 幕 | 9 | ✅ 无工具中断被触发 | `after_model` 中 `interrupt()` 拦下最终草稿 |

**六项能力全部经真实运行验证通过。** 四幕的断言均为程序化断言（`assert`），
任何一环失效都会直接抛错终止，而不是靠人工肉眼确认。

---

## 附：运行耗时参考

| 幕 | 耗时 | 说明 |
|---|---|---|
| 第 1 幕 | 约 12–15 分钟 | 最耗时；含十余次联网检索与 3 次子 Agent 委派 |
| 第 2 幕 | 约 30 秒 | 两次 `invoke()` |
| 第 3 幕 | 约 10 秒 | 两层中断恢复 |
| 第 4 幕 | 约 10 秒 | 一次中断恢复 |

瓶颈在联网检索与子 Agent 调用的串行等待；子 Agent 走硅基流动免费额度时偶发 429 流控，
`sub_model()` 设了 `max_retries=6` 做线性退避，不影响整体演示。
