## Harness Ops Module — Routing & Change Management

**Route to Harness Ops when**: harness configuration, CLAUDE.md, module.yaml, assembly-order, fragment, template variables, execution chain config, constraint system, CEO Guard scripts, validator, generator, hr_base.py, automation pipeline prompts.

**Change management gates** (enforced before any Harness config merges):
- Impact analysis completed by `harness_qa` — scope of affected templates/configs documented
- Fragment token count verified <= 300 per fragment
- Routing keywords conflict-free across all active modules
- Module schema compliance validated (required fields + capability grade >= B)
- Variable substitution verified — zero `{{xxx}}` residuals in output

**Harness Ops workflow**: design change → `harness_engineer` implements → `harness_qa` validates (mandatory, no skip) → deliver. Code changes by `ai_systems_dev` follow engineering `/dev-review` before merge. `harness_qa` approval is the quality gate for all configuration deliverables.
