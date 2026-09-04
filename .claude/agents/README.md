# Agent 体系全局索引

## Agent 列表（14 个）

### 核心 Agent（4 个）

| Agent | 文件 | 命令 | 职责 |
|-------|------|------|------|
| 需求拆分 | `requirement-design.md` | `/requirement-design` | 读 PRD/TAD/TEST → 设计摘要 + 接口签名契约 + 迭代计划 |
| TDD | `tdd.md` | `/tdd` | 基于接口签名契约设计/补全测试 + 执行测试 + 分析失败 |
| 代码开发 | `code-dev.md` | `/code-dev` | 基于接口签名契约 + 验收标准实现代码，禁读测试实现 |
| Review | `review.md` | `/review` | 只读审查：模块解耦、安全、可维护性 |

### 辅助 Agent（10 个）

| Agent | 文件 | 命令 | 职责 |
|-------|------|------|------|
| Superpowers 编排器 | `superpowers-orchestrator.md` | `/superpowers` | 通用入口：环境预检 → 风险门 → 路由 |
| Review 反馈 | `review-feedback.md` | `/review-feedback` | 处理 Review 报告：理解 → 分类 → 落实 → 回复 |
| 完成验证 | `verify.md` | `/verify` | 提交前代码/文档/Git 三维验证 |
| 计划编写 | `plan.md` | `/plan` | 编写结构化迭代/实现计划（requirement-design 下游） |
| 计划执行 | `execute.md` | `/execute` | 按计划逐步执行 + 偏差处理 |
| 头脑风暴 | `brainstorm.md` | `/brainstorm` | 多角度方案探索与对比 |
| 系统化调试 | `systematic-debugging.md` | `/systematic-debugging` | 系统化定位 Bug 根因 |
| 回归测试 | `regression.md` | `/regression` | 选择并执行回归测试策略 |
| 并行开发 | `parallel.md` | `/parallel` | 调度多个子 Agent 并行工作 |
| 事故响应 | `incident.md` | `/incident` | 生产事故分级响应 |

## 编排命令（3 个）

| 命令 | 文件 | 用途 |
|------|------|------|
| `/tdd-flow <需求>` | `.claude/commands/tdd-flow.md` | 完整需求变更流程（快速/标准/完整通道） |
| `/bug-fix <Bug>` | `.claude/commands/bug-fix.md` | Bug 修复流程（快速/标准/调试通道） |
| `/doc-sync <变更>` | `.claude/commands/doc-sync.md` | 文档同步（引用 `.claude/workflows/doc-sync.md`） |

## 工作流（4 个）

| 工作流 | 文件 | 用途 |
|--------|------|------|
| TDD 编排 | `.claude/workflows/tdd-orchestration.md` | 需求变更 & Bug 修复两大场景的 Agent 执行顺序 |
| 文档同步 | `.claude/workflows/doc-sync.md` | PRD → TAD → TEST 依赖关系 + 强制检查清单 |
| 环境预检 | `.claude/workflows/environment-precheck.md` | 环境域检查清单 |
| 风险门 | `.claude/workflows/risk-gate.md` | 🔴高/🟡中/🟢低 三级风险分类 + 降级策略 |

## Agent 协作关系图

```
用户请求
    │
    ▼
superpowers（环境预检 → 风险门 → 路由）
    │
    ├── 新功能/需求变更 ──→ brainstorm → tdd-flow
    │                                    │
    │                                    ▼
    │                           requirement-design
    │                              │（产出接口签名契约 + 迭代计划）
    │                              ▼
    │                           tdd(先行) → code-dev(后行)
    │                              │
    │                           tdd 执行测试
    │                              │
    │                           review → review-feedback
    │                              │
    │                           verify → 提交
    │
    ├── Bug/异常 ──→ bug-fix（快速/标准/调试通道）
    │                    │
    │              systematic-debugging（调试通道）
    │                    │
    │              tdd 确认 → code-dev 修复 → tdd 验证
    │                    │
    │              review → review-feedback → verify
    │
    ├── 生产事故 ──→ incident
    │                    │
    │              止血 → systematic-debugging → bug-fix → regression → 复盘
    │
    ├── 复杂任务 ──→ plan → execute
    │
    ├── 并行任务 ──→ parallel（调度多个 code-dev/tdd）
    │
    ├── 回归测试 ──→ regression
    │
    ├── 文档同步 ──→ doc-sync
    │
    └── 完成验证 ──→ verify
```

## 上下文隔离规则（强制）

| Agent | 可读 | 禁读/禁写 |
|-------|------|----------|
| requirement-design | docs/\*, docs/superpowers/\*, src/main/java/（仅确认现有接口签名） | src/test/, *Test.java |
| code-dev | docs/PRD/\*, docs/TAD/\*, docs/superpowers/plans/\*（含接口契约）, src/main/java/, docs/TEST/\*（仅文字 TC） | **src/test/, *Test.java, *.spec.\*** |
| tdd | docs/TEST/\*, src/test/, docs/superpowers/plans/\*（含接口契约）, src/main/java/（只读） | 不改 src/main/ |
| review | 全部可读 | **不可写任何文件** |

## 技术栈

本项目为 Java 21 + Spring Boot 3.3 + MyBatis + MySQL/Qdrant 后端服务：
- 测试命令：`mvn test`（指定类 `mvn test -Dtest=XxxTest`）
- 编译检查：`mvn -q -DskipTests compile`
- 业务代码：`src/main/java/`
- 测试代码：`src/test/java/`
- 迭代计划：`docs/superpowers/plans/`
- 技术设计：`docs/superpowers/specs/`

> 体系源自 `open-deck-app`（Flutter）项目，已适配 Java/Maven 后端技术栈。
