---
name: project-agent-guide
description: cb-context-service 项目 Claude agent/skill/命令/工作流体系总览。当用户询问"项目有哪些 agent/skill""如何编排需求开发/Bug 修复""某个任务该调哪个命令"或需要新接手本项目的需求开发时使用。
---

# 项目 Claude Agent / Skill 体系使用指南

本项目没有独立的 `.claude/skills/` 历史目录 —— 它的 Claude 能力由三部分构成，均可通过 slash 命令调用：

```
.claude/agents/    # Agent 定义（14 个），文件名 = 命令名，头部 command: 标注
.claude/commands/  # slash 命令（16 个），薄壳型转发参数 / 编排型含独立编排逻辑
.claude/workflows/ # 编排规则（4 个）
```

> 本文档把三者聚合为一个可调用的 skill。调用本 skill 时，按「任务类型 → 路由到对应 Agent」的思路帮助用户。
> 详细编排规则以 `.claude/agents/README.md`（Agent 全局索引）与 `.claude/workflows/*.md` 为准。

---

## 1. 核心 Agent（4 个）—— 接口先行 + TDD 的支柱

| Agent | 命令 | 职责 | 隔离规则 |
|-------|------|------|---------|
| 需求拆分 | `/requirement-design` | 读 PRD/TAD/TEST → 设计摘要 + **接口签名契约** + 迭代计划 | 禁读 `src/test/`、`*Test.java` |
| TDD | `/tdd` | 基于接口签名契约设计/补全测试 + 执行测试 + 分析失败 | 可读 `src/main/java/`（只读），**不改 src/main/** |
| 代码开发 | `/code-dev` | 基于接口签名契约 + 验收标准实现代码 | **禁读 `src/test/`、`*Test.java`、`*.spec.*`** |
| Review | `/review` | 只读审查：模块解耦、安全、可维护性 | 全部可读，**不可写任何文件** |

## 2. 辅助 Agent（10 个）

| Agent | 命令 | 职责 |
|-------|------|------|
| Superpowers 编排器 | `/superpowers` | 通用入口：环境预检 → 风险门 → 路由 |
| 头脑风暴 | `/brainstorm` | 多角度方案探索与对比 |
| 计划编写 | `/plan` | 编写结构化实现计划（requirement-design 下游） |
| 计划执行 | `/execute` | 按计划逐步执行 + 偏差处理 |
| 系统化调试 | `/systematic-debugging` | 系统化定位 Bug 根因 |
| 回归测试 | `/regression` | 选择并执行回归测试策略 |
| Review 反馈 | `/review-feedback` | 处理 Review 报告、分类落实、形成闭环 |
| 完成验证 | `/verify` | 提交前代码/文档/Git 三维验证 |
| 并行开发 | `/parallel` | 调度多个子 Agent 并行工作 |
| 事故响应 | `/incident` | 生产事故分级响应 |

## 3. 编排命令（3 个）

| 命令 | 用途 | 通道 |
|------|------|------|
| `/tdd-flow <需求>` | 完整需求变更流程，自动串联不等待用户确认 | 快速 / 标准 / 完整 |
| `/bug-fix <Bug>` | Bug 修复流程 | 快速 / 标准 / 调试 |
| `/doc-sync <变更>` | 文档同步（引用 `.claude/workflows/doc-sync.md`） | — |

## 4. 工作流（4 个，`.claude/workflows/`）

| 工作流 | 用途 |
|--------|------|
| `tdd-orchestration.md` | 需求变更 & Bug 修复两大场景的 Agent 执行顺序 |
| `doc-sync.md` | PRD → TAD → TEST 依赖关系 + 强制检查清单 |
| `environment-precheck.md` | 环境域检查清单 |
| `risk-gate.md` | 🔴高/🟡中/🟢低三级风险分类 + 降级策略 |

## 5. Agent 协作关系图

```
用户请求 → superpowers（预检 → 风险门 → 路由）
 ├─ 新功能/需求变更 → brainstorm → tdd-flow
 │      → requirement-design（产出接口签名契约 + 迭代计划）
 │      → tdd(先行) + code-dev(后行) → tdd 执行测试
 │      → review → review-feedback → verify → 提交
 ├─ Bug/异常 → bug-fix
 │      → systematic-debugging（调试通道定位根因）
 │      → tdd 确认复现 → code-dev 修复 → tdd 验证
 │      → review → review-feedback → verify
 ├─ 生产事故 → incident（止血 → systematic-debugging → bug-fix → regression → 复盘）
 ├─ 复杂任务 → plan → execute
 ├─ 并行任务 → parallel（调度多个 code-dev/tdd）
 ├─ 回归测试 → regression
 └─ 文档同步 → doc-sync / 完成验证 → verify
```

## 6. 任务路由速查

按用户任务类型，直接推荐对应命令（**优先用 tdd-flow / bug-fix / superpowers 三个入口，不要求用户自己组合**）：

| 用户诉求 | 推荐的命令 |
|---------|-----------|
| 新功能 / 需求变更 | `/tdd-flow <需求>` 或 `/superpowers <需求>` |
| Bug / 测试失败 / 行为异常 | `/bug-fix <Bug>`；根因不明走调试通道 |
| 方案不确定、技术选型 | `/brainstorm <问题>` |
| 复杂多阶段任务 | `/plan <任务>` → `/execute <计划>` |
| 生产事故 | `/incident <现象>` |
| 提交前检查 / 文档同步 | `/verify` / `/doc-sync <变更>` |
| 多任务并行 | `/parallel <任务列表>` |
| 只想问"项目怎么组织、从哪下手" | 读本文档 + `docs/code-guide.md` |

## 7. 上下文隔离规则（强制，路由时须遵守）

| Agent | 可读 | 禁读/禁写 |
|-------|------|----------|
| requirement-design | docs/\*, docs/superpowers/\*, src/main/java/（仅确认接口签名） | src/test/, *Test.java |
| code-dev | docs/PRD/\*, docs/TAD/\*, docs/superpowers/plans/\*（含契约）, src/main/java/, docs/TEST/\*（仅文字 TC） | **src/test/, *Test.java, *.spec.\*** |
| tdd | docs/TEST/\*, src/test/, docs/superpowers/plans/\*（含契约）, src/main/java/（只读） | 不改 src/main/ |
| review | 全部可读 | **不可写任何文件** |

code-dev 与 tdd 通过**接口签名契约**协同，互不越界。

## 8. 配套技术栈速查

- 项目：Java 21 / Spring Boot 3.3 / MyBatis + MySQL/Qdrant 后端服务（见 `docs/code-guide.md`）
- 测试：`mvn test`（指定类 `mvn test -Dtest=XxxTest`）
- 编译检查：`mvn -q -DskipTests compile`
- 提交门禁：`mvn test` 0 失败 → 文档同步（doc-sync）→ 代码+文档同一 commit → `bash scripts/mark_test_passed.sh` → `git push`
- 业务代码 `src/main/java/`、测试代码 `src/test/java/`、迭代计划 `docs/superpowers/plans/`、技术设计 `docs/superpowers/specs/`

## 9. 体系来源说明

- Agent 体系源自 `open-deck-app`（Flutter）项目，已适配 Java/Maven 后端技术栈。
- 与 Claude Code **内置 skill**（dataviz、artifact-design、code-review、claude-api 等）无关，本项目不依赖内置 skill 做需求编排。
