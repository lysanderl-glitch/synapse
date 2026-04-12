# Synapse Core v2.0

Modular AI team orchestration framework. Build your own AI-powered organization by composing reusable modules.

## Architecture

```
synapse-core/
├── core/           # Framework essentials (harness fragments, core agents, hooks)
├── modules/        # Department modules (strategy, engineering, product, etc.)
├── presets/        # Quick-start templates (startup, SMB, enterprise, etc.)
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

## Configuration

Edit `synapse.yaml` to set your organization details and select modules:

```yaml
organization:
  ceo_name: "YourCEO"
  president_name: "YourName"
  org_name: "YourOrg"

modules:
  - strategy
  - engineering
  # ... add more as needed
```

## Status

This is an alpha release (v2.0.0-alpha.1) validating the modular architecture approach.
