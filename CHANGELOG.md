# Synapse Core Changelog

## v2.1.0 (2026-04-17)

### Added — New Module: harness-ops Agents (P0 Gap Closure)

- `evolution_engine` — 体系进化引擎，添加至 harness_ops 模块
  - SemVer 版本管理、结构化 Gap 分析（P0/P1/P2 矩阵）、AI Agent 设计模式追踪、版本迁移工程
- `capability_architect` — 能力架构师，添加至 harness_ops 模块
  - A/B/C 三级质量审计、Jaccard 重叠检测（>30% 阈值）、入职审批流程、Conway's Law 组织优化

### Added — P1 Gap Closure: New Agents

- `ai_visual_creator` — AI视觉创作师，添加至 content 模块
  - Midjourney/DALL-E/SD Prompt 工程（A/B 测试驱动）、品牌一致性生产（--sref/--cref/LoRA）、场景化叙事视觉设计、Prompt 模板库管理
- `publishing_ops` — 发布运营专家，添加至 content 模块
  - GitHub Actions CI/CD 自动化、Pandoc+Puppeteer 格式转换管线、Lighthouse CI 质量门禁（≥90 才发布）、发布调度管理
- `sales_enablement` — 销售赋能专家，添加至 marketing 模块
  - JTBD 价值主张提炼、销售物料体系（One-pager/Deck/案例/ROI计算器）、MEDDIC Playbook 设计、竞品战场卡

### Confirmed Present — P0 Agents Already in synapse-core

以下 P0 缺口经核查已存在于 synapse-core，无需补充：
- `relation_discovery` — strategy 模块（知识图谱/Jaccard/PageRank/Louvain，A级）
- `ai_tech_researcher` — strategy 模块（三维评估框架/Harness 模式提取/情报卡片，A级）
- `visual_designer` — content 模块（品牌规范/Tailwind/ECharts/Midjourney，A级）

### Confirmed Present — Degraded Agents Already Upgraded in synapse-core

以下 P1 降级问题经核查已在 synapse-core 修复，无需补充：
- `frontend_engineer` — 已含 7 维度设计审计 (WCAG 2.1 AA / Lighthouse / Playwright)
- `backend_engineer` — 已含 SQL 安全自审（参数化查询/TOCTOU/N+1）+ 并发安全编码（乐观锁/原子操作）
- `qa_engineer` — 已含 STRIDE 六维度威胁建模（Spoofing/Tampering/Repudiation/InfoDisclosure/DoS/EoP）
- `training_designer` — 已含 ADDIE/Bloom/Kirkpatrick 完整方法论，A级

### Added — Canonical CLAUDE.md

- 新建 `CLAUDE.md`（约 180 行，从 541 行参考版精简）
  - 三层架构标记（LAYER 1: IDENTITY / LAYER 2: CORE HARNESS / LAYER 3: INSTANCE CONFIG）
  - 前置加载 CEO 执行禁区 P0 约束（文件最前部）
  - 合并重复说明，消除冗余（违规模式表格化，路由表格化）
  - 升级协议引用外部文档（`docs/upgrade-protocol.md`）
  - HR Schema 引用外部文档（`obs/03-process-knowledge/agent-hr-management-system.md`）

### Added — Instance Management

- `synapse-instance.yaml` — 实例绑定模板
  - 三层标记锚点配置、模块列表（含/排注释）、锁定文件保护
  - framework 版本追踪字段，支持 auto_update 开关

### Changed — harness_ops module.yaml

- 新增 `evolution_engine` 和 `capability_architect` Agent 注册
- 新增对应路由关键词（版本管理/Gap分析/能力审计/入职审批等）

### Changed — VERSION

- `2.0.0-alpha.1` → `2.1.0`（minor 版本 bump：新模块/新 Agent 批量接入）

---

## v2.0.0-alpha.1 (2026-04-10)

- 初始化 synapse-core v2.0 模块化架构
- 11 个模块，38 个 Agent
- 相比 v1.0 新增：Product / Legal / Finance / Data / Customer Success 5 个模块
- harness 碎片化工程（9 片段可组合拼装）
- 5 个部署预设（startup / smb / tech_team / content_creator / enterprise）
