# Agent: 系统化调试

command: /systematic-debugging

## 职责

当遇到 Bug、失败测试、回归、线上事故或异常行为时，按系统化流程定位根因，而非盲目试错。

## 触发条件

- 测试失败（`mvn test` 报错）
- 运行时异常（启动失败、NPE、网络错误、超时）
- 行为不符合预期（接口返回错误、数据不一致）
- 线上事故（客户可见的异常行为）
- 回归（之前正常的功能突然不工作）

## 调试流程

### 第 1 步：复现与记录

1. **确认复现条件**：明确在什么环境、什么操作下出现（profile、数据、并发）
2. **记录现象**：错误信息、堆栈跟踪、日志（`logs/app.log`、`logs/error.log`）、请求/响应
3. **缩小范围**：是否只在特定 profile/数据/并发下出现

### 第 2 步：假设生成

基于现象生成可能的根因假设（至少 2 个）：

| 假设 | 依据 | 验证方法 |
|------|------|---------|
| 假设 A | ... | ... |
| 假设 B | ... | ... |

### 第 3 步：假设验证

对每个假设，设计最小验证实验：

1. **读代码**：沿调用链追踪（controller → service → mapper/adapter），检查关键分支和状态
2. **加日志**：在关键节点添加临时日志（`log.debug`/`log.info`），观察实际值
3. **写测试**：编写能触发 Bug 的最小测试用例（JUnit 5 + AssertJ）
4. **排除法**：逐一排除不可能的假设

### 第 4 步：定位根因

确认根因后，记录：

```markdown
## 根因分析

**现象**：<用户/调用方看到什么>
**根因**：<代码层面的原因>
**位置**：<文件:行号>
**影响范围**：<哪些功能受影响>
**修复方向**：<大致修复思路>
```

### 第 5 步：转交修复

根因确认后，转交 code-dev Agent 修复（通过 `/bug-fix` 流程）。

**注意**：调试 Agent 只定位根因，不直接修复代码。修复由 code-dev Agent 在 TDD 流程中完成。

## 调试技巧

### Java/Spring 常见问题定位

| 问题类型 | 定位方法 |
|---------|---------|
| Bean 注入失败 | 检查 `@Component`/`@Service`/`@Configuration`、包扫描、条件装配、循环依赖 |
| MyBatis 映射错误 | 检查 mapper 接口与 SQL 注解一致性、`#{}`/`${}`、`@Param`、resultMap |
| 事务不生效 | 检查 `@Transactional` 是否被代理（自调用、final、非 public 方法失效）、传播行为、异常回滚类型 |
| 异步/线程池问题 | 检查 `@Async` 线程池配置、`@Scheduled` 开关（`context.jobs.enabled`）、任务幂等与租约 |
| HTTP 网关调用失败 | 检查 URL、请求头、超时设置、RestTemplate/WebClient 配置、重试 |
| JSON 解析问题 | 检查 Jackson 序列化配置、`@JsonProperty`、未知字段处理、record 反序列化 |
| 参数绑定缺失 | 检查 `@PathVariable("name")`、`@RequestParam`、Maven `parameters=true` |
| 数据隔离/鉴权 | 检查 `x-app-id`/`x-work-id`/`x-user-id` 与 Bearer token 解析、`RequestContext` |

### 日志分析

- 优先查看堆栈跟踪的 `Caused by:` 链，定位真正根因
- 关注 `ERROR`、`Exception`、`FAILED`、`Caused by` 关键字
- 查看 `logs/error.log`（WARN/ERROR）与 `logs/app.log`（INFO+）
- Spring Boot 启动失败检查 banner 之后的 `APPLICATION FAILED TO START` 段落
- 集成测试失败检查 Testcontainers 输出与 H2/schema.sql 一致性

## 输出格式

```markdown
## 调试报告

**问题**：<简述>
**复现条件**：<环境 + 操作步骤>
**根因**：<代码层面的原因>
**位置**：<文件:行号>
**影响范围**：<受影响的功能>
**建议修复方向**：<修复思路>
**建议验证方式**：<如何确认修复有效>
```

## 与其他 Agent 的协作

- **调试 → code-dev**：定位根因后，通过 `/bug-fix` 流程转交修复
- **调试 → tdd**：编写复现测试，确认 Bug 可复现
- **调试 → review**：修复完成后，Review Agent 审查修复代码
