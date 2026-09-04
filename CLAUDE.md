# cb-context-service — Claude Code 项目配置

Java 21 / Spring Boot 3.3 / MyBatis 后端服务，为 AgentCore 提供会话上下文、记忆、审计与 ContextBundle 组装。持久化用 MySQL，可重建向量索引存 Qdrant，对外暴露 Open API 与 Internal API。

## 文档体系

| 关键词 | 路径 | 说明 |
|--------|------|------|
| PRD | `docs/PRD/README.md` | 产品需求，子文档按模块编号 |
| TAD | `docs/TAD/README.md` | 技术架构，含 API/数据模型/SQL |
| TEST | `docs/TEST/README.md` | 测试用例，按 Batch 组织 |
| 迭代计划 | `docs/superpowers/plans/<YYYY-MM-DD>-<功能>.md` | 每功能一份，含验收标准与接口契约 |
| 技术设计 | `docs/superpowers/specs/<YYYY-MM-DD>-<功能>-design.md` | 方案变更的设计文档 |
| API 契约 | `docs/api/openapi.yaml` | Open API / Internal API 定义 |
| 数据库 | `docs/database/schema.md` | 表结构、索引 |
| 架构总览 | `docs/architecture/overview.md` | 模块划分、职责边界 |
| 集成流程 | `docs/integration/agentcore-flow.md` | 与 AgentCore 的交互时序 |

提到 PRD/TAD/TEST 时先读对应 README.md 定位子文档，再读具体内容。既有 `docs/architecture|database|api|testing|integration` 作为参考资料，PRD/TAD/TEST 为迁移期建立的索引入口。

## Superpowers 编排器（通用入口）

**`/superpowers <任务>`** — 通用入口命令，自动执行环境预检 → 风险门 → 路由 → 子技能调度。

适用于任何不确定如何路由的任务，或在开始工作前需要评估环境和风险的情况。

编排器详细定义：`.claude/agents/superpowers-orchestrator.md`

## 多 Agent 体系（接口先行 + TDD 优先）

核心 Agent（通过 slash 命令触发，主 Agent 负责编排调度）：

| Agent | 命令 | 职责 |
|-------|------|------|
| 需求拆分 | `/requirement-design` | 读 PRD/TAD/TEST → 设计摘要 + **接口签名契约** + 迭代计划 |
| 代码开发 | `/code-dev` | 基于接口签名契约 + 验收标准实现代码，**禁读测试实现** |
| TDD | `/tdd` | 基于接口签名契约设计/补全测试 + 执行测试 + 分析失败 |
| Review | `/review` | 只读审查：模块解耦、安全、可维护性 |

辅助 Agent：

| Agent | 命令 | 职责 |
|-------|------|------|
| Superpowers | `/superpowers` | 通用入口：环境预检 → 风险门 → 路由 |
| 头脑风暴 | `/brainstorm` | 多角度方案探索与对比 |
| 计划编写 | `/plan` | 编写结构化迭代/实现计划 |
| 计划执行 | `/execute` | 按计划逐步执行 |
| 系统化调试 | `/systematic-debugging` | 系统化定位 Bug 根因 |
| 回归测试 | `/regression` | 选择并执行回归测试策略 |
| Review 反馈 | `/review-feedback` | 处理 Review 报告，落实修改 |
| 完成验证 | `/verify` | 提交前代码/文档/Git 三维验证 |
| 并行开发 | `/parallel` | 调度多个子 Agent 并行工作 |
| 事故响应 | `/incident` | 生产事故分级响应 |

编排命令：`/tdd-flow <需求>` 全流程、`/bug-fix <Bug>` 修复流程、`/superpowers <任务>` 通用入口。

## 上下文隔离规则（强制）

| Agent | 可读 | 禁读 |
|-------|------|------|
| requirement-design | docs/\*, docs/superpowers/\*, src/main/java/（仅确认现有接口签名） | src/test/, *Test.java |
| code-dev | docs/PRD/\*, docs/TAD/\*, docs/superpowers/plans/\*（含接口契约）, src/main/java/, docs/TEST/\*（仅文字 TC） | **src/test/, *Test.java, *.spec.\*** |
| tdd | docs/TEST/\*, src/test/, docs/superpowers/plans/\*（含接口契约）, src/main/java/（只读） | 不改 src/main/ |
| review | 全部可读 | **不可写任何文件** |

code-dev 与 tdd 之间严格隔离：code-dev 不看测试实现，tdd 不改业务代码。两者通过**接口签名契约**协同。

## 编排流程速查

**需求变更**：① requirement-design（产出接口签名契约）→ ② tdd + code-dev（接口先行，基于契约并行/串行）→ ③ tdd 执行测试 → ④ review

**Bug 修复**：① tdd 确认复现 → ② code-dev 修复 → ③ tdd 确认修复 → ④ review

详细编排见 `.claude/workflows/tdd-orchestration.md`，文档同步见 `.claude/workflows/doc-sync.md`，风险门见 `.claude/workflows/risk-gate.md`，环境预检见 `.claude/workflows/environment-precheck.md`。

## Agent 定义与命令

- Agent 定义 = Slash 命令定义：`.claude/agents/*.md`（文件名 = 命令名，头部 `command:` 标注）
- 薄壳型命令（指向 Agent 定义）：`.claude/commands/*.md`（与 Agent 同名，仅含参数引用）
- 编排型命令（含独立编排逻辑）：`.claude/commands/tdd-flow.md`、`.claude/commands/bug-fix.md`、`.claude/commands/doc-sync.md`
- 编排规则：`.claude/workflows/*.md`

## 项目约定

- 构建工具：Maven（`mvn`），无 mvnw wrapper
- **JDK 版本**：项目要求 Java 21（`pom.xml: java.version=21`）。本机默认 `mvn` 可能走更高版本 JDK，运行前需固定为 21：
  - macOS：`export JAVA_HOME=$(/usr/libexec/java_home -v 21)`
  - 或写入 shell profile（`~/.zshrc`）持久化
  - `scripts/mark_test_passed.sh` 已内置 JDK 21 自动探测，无需手动设置
- 测试：`mvn test`（指定类 `mvn test -Dtest=XxxTest`，指定方法 `-Dtest=XxxTest#methodName`）
- 编译检查：`mvn -q -DskipTests compile`
- 自定义 settings.xml：通过环境变量 `MAVEN_SETTINGS` 注入（`mark_test_passed.sh` 会自动加 `-s`），不写死用户路径
- 持久化：MyBatis mapper 接口 + SQL 注解；schema 手动维护在 `src/main/resources/db/migration/V1__init_schema.sql`（Flyway 已禁用）
- 分层：controller → service → mapper/adapter，遵循 `shared/` 下的统一响应、异常、分页、日志约定
- API 面：Open API `/api/v1/**`（Bearer token）、Internal API `/internal/v1/**`（`x-app-id`/`x-work-id`/`x-user-id`）
- 配置 profile：`application-local.yml`（本地）、`application-test.yml`（测试部署）
- 始终使用汉语回复

## 测试门控（强制，不可跳过）

**`mvn test` 必须 0 失败才能提交和推送。不允许"容忍已有失败"。**

- 如果存在非本次引入的失败用例，**必须先修复旧失败**（可合并到当前 commit），然后再提交
- **推送前工作流**：
  1. `bash scripts/mark_test_passed.sh`（内部执行 `mvn test`，全部通过后自动写入标记，无需单独再跑 `mvn test`）
  2. `git push`（`pre-push` hook 自动验证标记与当前 HEAD 匹配）
- hook 安装：`bash scripts/install_hooks.sh`（新 clone 后执行一次）
- 标记机制：`mark_test_passed.sh` 在测试全部通过后将 HEAD commit hash 写入 `.git/.test_passed`；`pre-push` hook 校验该标记与当前 HEAD 一致，不一致或缺失则阻止推送
- 紧急跳过：`git push --no-verify`（仅紧急情况，需在 commit message 中说明原因）

> 历史教训（参考项目）：曾因"容忍无关失败"导致破窗效应，失败用例长期未修复。
> 根本原因：把"本次改动无新增失败"等同于"测试通过"。
> 唯一有效规则：**0 失败 = 通过，>0 失败 = 不通过，无例外。**

## 代码变更完成后强制文档检查（不可跳过）

**文档同步与 `git commit` 是同一个动作，不是两个步骤。**
每次准备提交时，按以下顺序执行，缺一不可：

```
① mvn test（必须 0 失败，有旧失败则先修复）
② 文档同步（见 .claude/workflows/doc-sync.md，有一项为「是」则必须先同步文档）
③ git add + git commit（文档和代码一起提交，同一个 commit）
```

**强制检查清单**（详见 `.claude/workflows/doc-sync.md`）：

| 检查项 | 若为「是」→ 必须同步的目标 |
|--------|--------------------------|
| 引入了新类 / 新模块 / 新文件？ | TAD 对应子文档 + `docs/TAD/README.md`「最近补充」末尾追加 |
| 修改了接口、数据模型或 SQL 存储结构？ | TAD 对应子文档 + `docs/api/openapi.yaml` + `docs/database/schema.md` |
| 改变了某个功能的行为或边界？ | TEST 对应 Batch；必要时更新 PRD |
| 是独立功能迭代或 Bug Fix 升级为方案变更？ | 新建/追加 `docs/superpowers/plans/<日期>-<功能>.md` + 对应 `specs/` 设计 |

**适用于所有流程（`/tdd-flow`、`/plan`、手动实现），无例外。**

> 历史教训（参考项目 3 次）：已发生 3 次「代码提交后补文档」的失误。
> 根本原因：把文档当作独立后续步骤，而非 commit 的组成部分。
> 唯一有效的修复：文档和代码必须在同一个 commit 中出现。

## 工程文件整理规则

当用户提到"工程文件整理"、"临时文件整理"时：

1. **删除临时性文档**：开发过程中的临时文件、预览文件、临时计划
2. **归档总结性文档**：已完成功能的实现总结归档
3. **代码清理**：删除调试日志（`System.out`/`e.printStackTrace()`），清理过时注释
4. **更新 README**：确保文档索引准确

## 配置 Profile 与运行模式

重大功能变更必须在测试阶段覆盖关键 profile 组合：

| profile | 验证重点 |
|---------|---------|
| local（H2 内存库） | 基础逻辑校验、单测、边界条件 |
| test（docker-compose + 真实依赖） | MySQL/Qdrant/网关连通性、集成测试、配置验证 |
| production | 生产配置验证、权限拦截、鉴权、稳定性 |

## 需求与功能开发核心规程

**Documents First**：严禁在未更新技术规格说明前直接修改核心逻辑。

1. **方案先行**：PRD 更新 → TAD 更新 → TEST 更新
2. **实现**：基于迭代计划验收标准实现（接口签名契约先行）
3. **回归验证**：local / test / production profile
4. **交付**：代码 + 文档同一 commit 提交
