## Compliance Module — Harness Fragment

### Routing Rules
Compliance tasks route through `compliance_lead` as coordinator. Region-specific queries route directly to activated regional specialists based on `routing_keywords` in module.yaml.

### Region Plugin Protocol
Only regions listed in `active_regions` are loaded at startup. To activate a region:
1. Add region key to `active_regions` in module.yaml (e.g., `["china", "uae"]`)
2. Regional agent cards are loaded on next session init
3. Routing keywords for regional specialists become active

Core agents (`compliance_lead`, `data_protection_officer`, `compliance_auditor`) are always available regardless of `active_regions`.

### Cross-Module Coordination
- **Legal overlap**: `compliance_lead` coordinates with `legal_counsel` on regulatory interpretation; compliance owns implementation, legal owns interpretation
- **Data protection**: `data_protection_officer` is the single DPO across all regions; regional specialists handle jurisdiction-specific requirements under DPO guidance
- **Audit**: `compliance_auditor` may request evidence from any team; teams must respond within the audit window

### Compliance Escalation
- Routine compliance queries: L1 auto-route to matching specialist
- Multi-jurisdiction issues: L2 compliance_lead coordination
- Regulatory enforcement actions or material non-compliance: L3 Lysander decision
- External regulatory filings or penalties > AED 100k: L4 president approval
