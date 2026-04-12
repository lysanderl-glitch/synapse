## Data Module — Routing & Standards

**Route to Data when**: data, analytics, metrics, KPI, dashboard, BI, report, ETL, data warehouse, cohort, funnel, retention, visualization.

**Data workflow**: question → metric mapping → data sourcing → analysis → visualization → insight delivery. `data_analyst` owns analysis; `data_engineer` owns pipelines; `bi_specialist` owns dashboards.

**Quality gates**:
- New metrics require definition in metric dictionary (owner/formula/data source/refresh cadence)
- Data pipeline changes validated by Great Expectations checks before promotion
- BI dashboards reviewed for metric accuracy before stakeholder release

**Escalation**: `data_analyst` resolves metric definition disputes with business owners. Data infrastructure architecture decisions are L3 (Lysander + expert review). No L4 items unless involving external data vendor contracts.
