## Engineering Module — Routing & Standards

**Route to Engineering when**: code, development, architecture, API, database, deployment, CI/CD, testing, bug, AI/ML, model, prompt.

**Code quality gates** (enforced before merge):
- Tech plan locked (`/dev-plan`) before coding starts
- Code review passed (`/dev-review`) — zero CRITICAL issues
- Tests green (`/dev-qa`) — unit coverage > 80%, E2E on critical paths
- Security scan clean — no high/critical vulnerabilities

**Dev workflow**: plan → implement → review → test → ship. No step may be skipped. `tech_lead` approves plan and review; `qa_engineer` approves test; `devops_engineer` executes deploy via `/dev-ship`.
