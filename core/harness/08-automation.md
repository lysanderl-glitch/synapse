<!-- Synapse Harness Fragment: 08-automation.md -->
<!-- Purpose: Automation layer - daily event chain, triggers, scheduled agents -->
<!-- Variables: {{CEO_NAME}}, {{PRESIDENT_NAME}} -->
<!-- Required: false (requires external trigger infrastructure) -->

### 自动化编排 — Harness Automation Layer

执行链不仅在对话中运行，还通过以下自动化机制持续运转（无需总裁在线）：

```
每日自动化全流程（Event Chain）：

  6:00am ── 任务自动恢复Agent
              │ 检查 active_tasks.yaml
              │ 恢复阻塞已解除的任务
              │ 续接未完成工作
              ↓
  6:15am ── SPE日历同步Agent
              │ 读取 Google Calendar + 任务状态
              │ 生成今日规划 → 更新 personal_tasks.yaml
              │ Slack 推送今日焦点给总裁
              ↓
  8:00am ── 情报日报Agent
              │ 搜索AI前沿动态
              │ 筛选实践价值内容
              │ 生成情报日报 → HTML → git push
              ↓
 10:00am ── 情报行动Agent
              │ 提取日报建议 → 专家评估 → 评审决策
              │ 执行团队执行批准项
              │ 生成行动成果报告 → HTML → git push
              ↓
 20:00pm ── SPE日终复盘Agent
              │ 对比今日计划 vs 实际执行
              │ 标记 carry-over 任务
              │ 更新周回顾数据
              ↓
  完成 ──── Slack通知总裁
```

**触发机制**（详见 `config/n8n_integration.yaml`）：
- **定时触发**：远程Agent按时间编排运行
- **事件触发**：代码变更 → 自动QA审查（webhook）
- **状态触发**：任务阻塞解除 → 自动恢复执行

**远程定时任务管理**：https://claude.ai/code/scheduled
