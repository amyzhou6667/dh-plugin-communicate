# 文档同步规范（Claude Code 适配版）

当任意文档发生变更或设计结论与现有文档不一致时，检查并同步相关文档。

## 文档依赖关系

```
PRD (docs/PRD/) → TAD (docs/TAD/) → TEST (docs/TEST/)
     ↓                 ↓                  ↓
 用户旅程/功能     API/数据模型/SQL      验收/接口/集成测试
```

## 同步触发条件

| 变更源 | 需检查/同步 |
|--------|------------|
| PRD 功能模块/用户故事 | TAD（API/服务划分）、TEST（验收范围/Batch） |
| PRD 信息架构/实体 | TAD（数据模型/序列化）、TEST（数据验证） |
| TAD API 接口 | TEST（接口测试/TC）、PRD（若接口限制产品能力）、`docs/api/openapi.yaml` |
| TAD 数据模型/SQL schema | TEST（边界用例）、PRD（若影响信息架构）、`docs/database/schema.md` |
| TEST 新增/修改用例 | PRD（验收标准）、TAD（若用例体现新接口） |
| **代码变更（新类/新模块/接口修改/SQL/行为变更）** | **TAD + TEST + 迭代计划（见下方强制检查）** |

## 代码变更后强制检查（优先级最高）

代码写完、测试通过后立即执行，**不可跳过**：

```
□ 引入了新类 / 新模块 / 新文件？
    → 更新 TAD 对应子文档，在 docs/TAD/README.md「最近补充」追加一行

□ 修改了接口、数据模型或 SQL 存储结构？
    → 更新 TAD 对应子文档 + docs/api/openapi.yaml + docs/database/schema.md

□ 改变了某个功能的行为或边界？
    → 更新 TEST 对应 Batch，必要时更新 PRD

□ Bug Fix 升级为方案变更（引入新架构）？
    → 视同功能迭代，新建 docs/superpowers/plans/<日期>-<功能>.md
      + docs/superpowers/specs/<日期>-<功能>-design.md
```

**判断原则**：修了一个 Bug，但解法引入了新的类、模块或存储机制，就是方案变更，不能以「只是 Bug Fix」为由跳过文档。

**执行时机**：文档同步不是独立步骤，是 `git commit` 的组成部分。
正确顺序：`mvn test` → 文档同步 → `git add 代码+文档` → `git commit`（同一个 commit）。
禁止先 commit 代码、后补文档的两次提交模式。

> 历史教训（参考项目 3 次）：每次都是「代码提交 → 用户追问 → 补文档」。
> 根因：文档被视为独立后续步骤，而非 commit 必要组成。
> 唯一有效的修复：文档和代码必须在同一个 commit 中出现。

## 同步流程

1. **确定变更源**：PRD、TAD、TEST 还是代码
2. **读取相关文档**：先读各 README.md 定位子文档，再读具体内容
3. **差异分析**：术语不一致、结构不一致、测试遗漏、流程/时序不一致
4. **按依赖顺序更新**：
   - PRD 变更 → 更新 PRD → 更新 TAD → 更新 TEST
   - TAD 变更 → 更新 TAD → 检查 PRD 反向更新 → 更新 TEST
   - TEST 变更 → 更新 TEST → 反哺 PRD/TAD（如发现遗漏）
   - 代码变更 → 按上方强制检查清单同步
5. **产出变更说明表**

## 检查清单

- [ ] PRD 功能模块与 TAD 服务/API 对应正确
- [ ] PRD 信息架构与 TAD 数据模型对应
- [ ] PRD 验收标准与 TEST 用例对应
- [ ] TAD API 与 TEST 接口测试/TC 对应
- [ ] `docs/api/openapi.yaml` 与代码 Controller 一致
- [ ] `docs/database/schema.md` 与 `db/migration/V1__init_schema.sql` 一致
- [ ] 术语在 PRD/TAD/TEST 中一致
- [ ] 代码变更已触发上方强制检查，文档已同步
