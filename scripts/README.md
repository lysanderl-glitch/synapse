# synapse Scripts

## frontmatter_lint.py
Validates frontmatter of `docs/public/**/*.md` against the 12-field spec.

Ref: `docs/public/methodology/content-frontmatter-spec.md`

### Usage
- `python scripts/frontmatter_lint.py` — warning mode (default)
- `python scripts/frontmatter_lint.py --strict` — strict mode (exits 1 on errors; auto-switches on 2026-07-23)
- `python scripts/frontmatter_lint.py --json` — JSON output (for CI / tooling)
- `python scripts/frontmatter_lint.py --path docs/public/methodology` — scan a subpath

### Requirements
- Python 3.8+
- PyYAML (optional; falls back to a simple key-value parser)

### Exit codes
- `0` — warning mode always; strict mode with no errors
- `1` — strict mode with at least one error
- `2` — path not found

### Cutover
Warning -> strict mode auto-flips on `2026-07-23` (90-day grace from first introduction).
After that date, CI should run without `--strict` and still fail on errors.
