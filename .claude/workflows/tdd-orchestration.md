# TDD 流程编排（Claude Code 适配版）

定义需求变更与 Bug 修复两种场景下，各 Agent 的执行顺序与职责。

---

## 核心原则：接口先行

> **接口签名契约**是 TDD Agent 和 Code-dev Agent 的共同输入。
> requirement-design 阶段产出接口签名契约（方法签名、参数类型、返回类型、异常声明），
> TDD Agent 基于契约编写测试，Code-dev Agent 基于契约编写实现。
> 两者可真正并行，且隔离规则可严格执行。

---

## 场景 1：需求变更

### 阶段 1：需求拆分（串行）

调用 requirement-design Agent（`.claude/agents/requirement-design.md`）：
1. 接收用户需求
2. 读取 `docs/PRD/`、`docs/TAD/`、`docs/TEST/` 相关章节
3. 产出设计摘要 + **接口签名契约** + 迭代计划
4. 写入 `docs/superpowers/plans/<YYYY-MM-DD>-<功能名>.md`（契约作为计划必要组成部分）

### 阶段 2：TDD + 代码开发（按迭代，可并行执行）

> **接口先行模式**：两者均基于阶段 1 产出的接口签名契约独立工作。
> - TDD Agent 基于契约编写测试（如果实现尚未完成，测试编译失败是预期行为）
> - Code-dev Agent 基于契约编写实现（禁读测试实现）
> - 两者可并行执行（使用 Workflow 工具的 `parallel()`/`pipeline()` 模式）
> - 如无法并行，则 TDD 先行、Code-dev 后行（串行执行）

对每个迭代：
- **TDD Agent**：基于接口签名契约 + 验收标准，生成 `docs/TEST/` TC + `src/test/java/` 可执行测试
- **Code-dev Agent**：基于接口签名契约 + PRD/TAD/验收标准实现；**禁读测试实现**

### 阶段 3：TDD 执行测试（串行）

- 执行该迭代测试（`mvn test` 或 `mvn test -Dtest=XxxTest`）
- 失败 → code-dev 修复 → 重跑
- 通过 → 进入阶段 4

### 阶段 4：Review + 反馈处理（串行，每迭代一次）

- Review Agent 对本迭代代码 diff 做审查，产出报告
- Review-feedback Agent 分类处理审查报告（必须修改/建议修改/可以保留）
- 有「必须修改」项 → code-dev 落实修改 → TDD 复测

---

## 场景 2：Bug 修复

> 完整流程定义见 `.claude/commands/bug-fix.md`（含快速/标准/调试三通道选择）。
> 以下为精简概要。

1. **通道选择**：根据根因明确程度和改动范围，选择快速修复 / 标准修复 / 调试修复
2. **调试修复通道**：先调用 systematic-debugging Agent 定位根因
3. **TDD Agent**：执行测试确认 Bug 复现
4. **Code-dev Agent**：修复实现（禁读测试；如涉及接口变更，产出精简契约）
5. **TDD Agent**：确认修复
6. **Review Agent**：审查修复代码
7. **Review-feedback Agent**：分类处理审查报告（必须修改/建议修改/可以保留）
8. **完成**：文档同步 + 代码提交（同一 commit）

---

## 上下文隔离

| Agent | 可读 | 禁读/禁写 |
|-------|------|----------|
| requirement-design | docs/\*, docs/superpowers/\*, src/main/java/（仅确认现有接口签名） | src/test/, *Test.java |
| code-dev | docs/PRD/\*, docs/TAD/\*, docs/superpowers/plans/\*（含接口契约）, src/main/java/, docs/TEST/\*（仅文字 TC） | **src/test/, *Test.java, *.spec.\*** |
| tdd | docs/TEST/\*, src/test/, docs/superpowers/plans/\*（含接口契约）, src/main/java/（只读） | 不改 src/main/ |
| review | 全部可读 | **不可写任何文件** |
