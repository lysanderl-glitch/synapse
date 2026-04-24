# Synapse Core v3.0

Modular AI team orchestration framework. Build your own AI-powered organization by composing reusable modules.

## Why Synapse Forge

Synapse Core is not a thought experiment — it is extracted directly from a real production system running 44 AI agents at Janus Digital. Every harness fragment, every constraint rule, and every workflow node has been tested under daily operational load: automated intelligence pipelines, cross-team task routing, multi-level decision escalation, and continuous QA gates.

The result is a framework that reflects how AI teams actually fail in practice (constraint drift, CEO role confusion, execution chain bypasses) and how to prevent those failures through composable, auditable harness engineering.

## Architecture

```
synapse-core/
├── core/           # Framework essentials (harness fragments, core agents, hooks)
├── modules/        # Department modules (strategy, engineering, harness_ops, etc.)
├── presets/        # Quick-start templates (startup, SMB, tech_team, enterprise, etc.)
├── workspace/      # Generated instance files (populated after init)
└── tools/          # CLI utilities (init, assemble, validate)
```

## How It Works

1. **Choose a preset** or configure `synapse.yaml` manually
2. **Run `synapse init`** to assemble your CLAUDE.md from selected modules
3. **Start working** with your AI team in Claude Code

## Key Concepts

- **Harness Fragments**: CLAUDE.md is assembled from composable `.md` fragments in `core/harness/`
- **Modules**: Each department (engineering, marketing, etc.) is a self-contained module with its own agents, config, skills, and harness rules
- **Variables**: Fragments use `{{VAR_NAME}}` placeholders replaced during assembly
- **Presets**: Pre-configured module combinations for common use cases
- **CEO Guard**: P0 constraint system — prevents the AI CEO from directly executing tasks, enforcing the agent-dispatch model at the harness level

## Configuration

Edit `synapse.yaml` to set your organization details and select modules:

```yaml
organization:
  ceo_name: "YourCEO"       # Your AI CEO's name
  president_name: "YourName" # Your name (the human operator)
  org_name: "YourOrg"       # Your company/team name

modules:
  - strategy
  - engineering
  - harness_ops
  # ... add more as needed
```

## Public API Surface

The `docs/public/` directory defines the stability contract. Files listed in `docs/public/_manifest.yaml` follow SemVer; other files are internal implementation and may change without notice.

Downstream consumers (Synapse Forge, Academy, external integrations) should only reference files in the manifest.

## Status

Beta release (v3.0.0-beta). Core architecture is stable and battle-tested in production. Module library is actively expanding. Breaking changes to harness fragment schemas will be versioned.
