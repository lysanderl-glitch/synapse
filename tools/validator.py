"""
Synapse Module & Agent Validator
Validates module.yaml files, agent cards, routing keywords, and dependencies.

Usage:
    python validator.py                          # Validate all modules
    python validator.py --module engineering      # Validate one module
    python validator.py --card modules/engineering/agents/tech_lead.md  # Validate one card

Requires: Python 3.10+, no third-party dependencies.
"""

from __future__ import annotations

import argparse
import io
import re
import sys
from pathlib import Path
from typing import Any

# Fix Windows console encoding for CJK output
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if sys.stderr.encoding and sys.stderr.encoding.lower() not in ("utf-8", "utf8"):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ---------------------------------------------------------------------------
# YAML handling — reuse from generator
# ---------------------------------------------------------------------------

try:
    import yaml as _yaml

    def load_yaml(path: str | Path) -> Any:
        with open(path, "r", encoding="utf-8") as f:
            return _yaml.safe_load(f)

except ImportError:
    # Import from sibling module
    _tools_dir = Path(__file__).resolve().parent
    sys.path.insert(0, str(_tools_dir))
    from generator import load_yaml


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SYNAPSE_ROOT = Path(__file__).resolve().parent.parent
MODULES_DIR = SYNAPSE_ROOT / "modules"

# Module Schema required fields
MODULE_REQUIRED_FIELDS = {
    "id": str,
    "name": str,
    "name_en": str,
    "version": str,
    "category": str,
    "description": str,
    "agents": list,
    "routing_keywords": dict,
}

MODULE_CATEGORIES = {"core", "business", "support", "extension"}

# Agent card required frontmatter fields
AGENT_REQUIRED_FIELDS = {
    "specialist_id": str,
    "team": str,
    "role": str,
    "role_en": str,
    "status": str,
    "type": str,
    "domains": list,
    "capabilities": list,
    "availability": str,
    "workload": str,
    "max_concurrent_tasks": int,
    "summon_keywords": list,
}

AGENT_VALID_STATUS = {"active", "probation", "inactive", "retired"}
AGENT_VALID_WORKLOAD = {"low", "medium", "high", "critical"}
AGENT_VALID_AVAILABILITY = {"available", "busy", "offline"}

# Capability quality patterns
_QUALITY_A_INDICATORS = [
    r"基于\s*.+\s*的",       # "基于 X 的 Y"
    r"(?:框架|工具|方法论|模型|矩阵|标准|协议|规范)",
    r"(?:pytest|Playwright|Docker|Kubernetes|React|Vue|FastAPI|OpenAPI)",
    r"[><=≥≤]\s*\d+",        # quantified thresholds like "> 80%"
    r"\d+\s*(?:分|%|维|步|阶段|环节|项)",  # numbered items
]

_QUALITY_C_PATTERNS = [
    r"^项目管理$",
    r"^知识沉淀$",
    r"^代码开发$",
    r"^测试$",
    r"^部署$",
    r"^.{1,6}$",  # very short descriptions (< 7 chars) are likely C-level
]


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

class ValidationIssue:
    """A single validation finding."""

    def __init__(self, level: str, path: str, message: str):
        self.level = level  # ERROR, WARNING, INFO
        self.path = path
        self.message = message

    def __str__(self):
        return f"[{self.level}] {self.path}: {self.message}"


class ValidationResult:
    """Aggregated validation results."""

    def __init__(self):
        self.issues: list[ValidationIssue] = []

    def error(self, path: str, msg: str):
        self.issues.append(ValidationIssue("ERROR", path, msg))

    def warning(self, path: str, msg: str):
        self.issues.append(ValidationIssue("WARNING", path, msg))

    def info(self, path: str, msg: str):
        self.issues.append(ValidationIssue("INFO", path, msg))

    @property
    def errors(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.level == "ERROR"]

    @property
    def warnings(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.level == "WARNING"]

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0

    def print_report(self):
        if not self.issues:
            print("  All checks passed!")
            return

        for issue in self.issues:
            marker = {"ERROR": "X", "WARNING": "!", "INFO": "i"}[issue.level]
            print(f"  [{marker}] {issue.path}: {issue.message}")

        print(f"\n  Summary: {len(self.errors)} error(s), {len(self.warnings)} warning(s)")


# ---------------------------------------------------------------------------
# Module Schema Validation
# ---------------------------------------------------------------------------

def validate_module(module_id: str, result: ValidationResult | None = None) -> ValidationResult:
    """Validate a module.yaml against the schema."""
    if result is None:
        result = ValidationResult()

    mod_path = MODULES_DIR / module_id / "module.yaml"
    path_str = str(mod_path.relative_to(SYNAPSE_ROOT))

    if not mod_path.exists():
        result.error(path_str, "module.yaml not found")
        return result

    try:
        raw = load_yaml(mod_path)
    except Exception as e:
        result.error(path_str, f"YAML parse error: {e}")
        return result

    if not isinstance(raw, dict):
        result.error(path_str, "Root must be a YAML mapping")
        return result

    # Extract module block (may be nested under 'module' key)
    mod = raw.get("module", raw)
    if not isinstance(mod, dict):
        result.error(path_str, "'module' must be a mapping")
        return result

    # --- Required fields ---
    for field, expected_type in MODULE_REQUIRED_FIELDS.items():
        val = mod.get(field)
        if val is None:
            result.error(path_str, f"Missing required field: {field}")
        elif not isinstance(val, expected_type):
            result.error(path_str, f"Field '{field}' must be {expected_type.__name__}, got {type(val).__name__}")

    # --- ID format ---
    mod_id_val = mod.get("id", "")
    if mod_id_val and not re.match(r"^[a-z][a-z0-9_]{1,30}$", str(mod_id_val)):
        result.error(path_str, f"Module ID '{mod_id_val}' must match ^[a-z][a-z0-9_]{{1,30}}$")

    # Cross-check: ID in YAML matches directory name
    if mod_id_val and str(mod_id_val) != module_id:
        result.warning(path_str, f"Module ID '{mod_id_val}' does not match directory name '{module_id}'")

    # --- Version format ---
    version = mod.get("version", "")
    if version and not re.match(r"^\d+\.\d+\.\d+$", str(version)):
        result.error(path_str, f"Version '{version}' must be semantic (X.Y.Z)")

    # --- Category ---
    category = mod.get("category", "")
    if category and str(category) not in MODULE_CATEGORIES:
        result.error(path_str, f"Category '{category}' must be one of {MODULE_CATEGORIES}")

    # --- Agents ---
    agents = mod.get("agents", [])
    if isinstance(agents, list):
        seen_ids: set[str] = set()
        for i, agent in enumerate(agents):
            if isinstance(agent, dict):
                sid = agent.get("specialist_id", "")
                if not sid:
                    result.error(path_str, f"Agent [{i}] missing specialist_id")
                elif sid in seen_ids:
                    result.error(path_str, f"Duplicate agent specialist_id: {sid}")
                else:
                    seen_ids.add(sid)

                # Check agent ID format
                if sid and not re.match(r"^[a-z][a-z0-9_]{1,40}$", str(sid)):
                    result.error(path_str, f"Agent ID '{sid}' must match ^[a-z][a-z0-9_]{{1,40}}$")

                # Check required agent sub-fields
                for af in ("role", "role_en", "card_path", "description"):
                    if not agent.get(af):
                        result.error(path_str, f"Agent '{sid}' missing field: {af}")

                # Check card file exists
                card_path_val = agent.get("card_path", "")
                if card_path_val:
                    full_card = MODULES_DIR / module_id / card_path_val
                    if not full_card.exists():
                        result.error(path_str, f"Agent '{sid}' card not found: {card_path_val}")

                # required must be boolean
                req = agent.get("required")
                if req is not None and not isinstance(req, bool):
                    result.warning(path_str, f"Agent '{sid}' field 'required' should be boolean")

            elif isinstance(agent, str):
                result.warning(path_str, f"Agent [{i}] '{agent}' is a bare string — should be a dict with specialist_id/role/card_path")

    # --- Routing keywords ---
    keywords = mod.get("routing_keywords", {})
    if isinstance(keywords, dict):
        effective_agents = list(agents or [])
        regions = mod.get("regions", {})
        active_regions = mod.get("active_regions", [])

        if regions and not isinstance(regions, dict):
            result.warning(path_str, "regions should be a mapping")
            regions = {}

        if active_regions and not isinstance(active_regions, list):
            result.warning(path_str, "active_regions should be a list")
            active_regions = []

        for rk in (active_regions or []):
            if rk not in (regions or {}):
                result.warning(path_str, f"active_regions includes unknown region '{rk}'")
                continue
            region = (regions or {}).get(rk, {}) or {}
            region_agents = region.get("agents", []) or []
            if not isinstance(region_agents, list):
                continue
            effective_agents.extend(region_agents)

        agent_ids_in_module = set()
        for a in (effective_agents or []):
            if isinstance(a, dict):
                agent_ids_in_module.add(a.get("specialist_id", ""))
                card_path_val = a.get("card_path", "")
                sid = a.get("specialist_id", "")
                if card_path_val:
                    full_card = MODULES_DIR / module_id / card_path_val
                    if not full_card.exists():
                        result.error(path_str, f"Agent '{sid}' card not found: {card_path_val}")
            elif isinstance(a, str):
                agent_ids_in_module.add(a)

        for kw, targets in keywords.items():
            if isinstance(targets, list):
                for t in targets:
                    if t not in agent_ids_in_module:
                        result.warning(path_str, f"Routing keyword '{kw}' targets unknown agent '{t}'")
            elif isinstance(targets, str):
                if targets not in agent_ids_in_module:
                    result.warning(path_str, f"Routing keyword '{kw}' targets unknown agent '{targets}'")

    # --- Skills ---
    skills = mod.get("skills", [])
    if isinstance(skills, list):
        for skill in skills:
            if isinstance(skill, dict):
                skill_path_val = skill.get("path", "")
                if skill_path_val:
                    full_skill = MODULES_DIR / module_id / skill_path_val
                    if not full_skill.exists():
                        result.info(path_str, f"Skill file not found (may be created later): {skill_path_val}")

    # --- Harness fragment ---
    frag = mod.get("harness_fragment", "")
    if frag:
        frag_path = MODULES_DIR / module_id / frag
        if not frag_path.exists():
            result.error(path_str, f"Harness fragment not found: {frag}")
        else:
            # Check token limit (rough estimate: 1 token ~= 4 chars for English, ~= 2 chars for CJK)
            content = frag_path.read_text(encoding="utf-8")
            # Conservative estimate: split by whitespace + CJK chars
            cjk_count = len(re.findall(r"[\u4e00-\u9fff]", content))
            word_count = len(content.split())
            estimated_tokens = word_count + cjk_count
            if estimated_tokens > 300:
                result.warning(
                    str(frag_path.relative_to(SYNAPSE_ROOT)),
                    f"Harness fragment exceeds 300 token limit (estimated ~{estimated_tokens} tokens)"
                )

    # --- Dependencies ---
    deps = mod.get("dependencies", {})
    if isinstance(deps, dict):
        for dep_id in (deps.get("required", []) or []):
            dep_mod_path = MODULES_DIR / dep_id / "module.yaml"
            if not dep_mod_path.exists():
                result.error(path_str, f"Required dependency '{dep_id}' module not found")
        for dep_id in (deps.get("recommended", []) or []):
            dep_mod_path = MODULES_DIR / dep_id / "module.yaml"
            if not dep_mod_path.exists():
                result.info(path_str, f"Recommended dependency '{dep_id}' module not found")

    return result


# ---------------------------------------------------------------------------
# Agent Card Validation
# ---------------------------------------------------------------------------

def _parse_frontmatter(content: str) -> tuple[dict | None, str]:
    """Parse YAML frontmatter from a Markdown file."""
    if not content.startswith("---"):
        return None, content
    end = content.find("---", 3)
    if end == -1:
        return None, content
    fm_text = content[3:end].strip()

    # Try to parse the frontmatter as YAML
    try:
        import yaml as _y
        fm = _y.safe_load(fm_text)
    except ImportError:
        # Minimal inline parse
        fm = {}
        current_key = None
        current_list: list[str] | None = None

        for line in fm_text.split("\n"):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if stripped.startswith("- ") and current_key and current_list is not None:
                val = stripped[2:].strip().strip('"').strip("'")
                current_list.append(val)
                fm[current_key] = current_list
                continue

            if ":" in stripped:
                colon = stripped.index(":")
                key = stripped[:colon].strip()
                val_str = stripped[colon + 1:].strip()

                if current_key and current_list is not None:
                    fm[current_key] = current_list

                if val_str == "" or val_str == "[]":
                    current_key = key
                    current_list = []
                else:
                    current_key = None
                    current_list = None
                    val_str = val_str.strip('"').strip("'")
                    if val_str.lower() == "true":
                        fm[key] = True
                    elif val_str.lower() == "false":
                        fm[key] = False
                    else:
                        try:
                            fm[key] = int(val_str)
                        except ValueError:
                            fm[key] = val_str

        if current_key and current_list is not None:
            fm[current_key] = current_list
    except Exception:
        return None, content

    body = content[end + 3:].strip()
    return fm, body


def grade_capability(cap: str) -> str:
    """Grade a capability description: A, B, or C."""
    # C-level: very short or generic
    for pattern in _QUALITY_C_PATTERNS:
        if re.match(pattern, cap.strip()):
            return "C"

    # A-level: has framework references + quantified outputs
    a_score = 0
    for pattern in _QUALITY_A_INDICATORS:
        if re.search(pattern, cap):
            a_score += 1
    if a_score >= 3:
        return "A"
    if a_score >= 1:
        return "B"

    # Default: B if longer than 20 chars, C otherwise
    return "B" if len(cap.strip()) > 20 else "C"


def validate_agent_card(card_path: str | Path, result: ValidationResult | None = None) -> ValidationResult:
    """Validate an agent card file."""
    if result is None:
        result = ValidationResult()

    card_path = Path(card_path)
    try:
        path_str = str(card_path.relative_to(SYNAPSE_ROOT))
    except ValueError:
        path_str = str(card_path)

    if not card_path.exists():
        result.error(path_str, "Card file not found")
        return result

    content = card_path.read_text(encoding="utf-8")

    # Parse frontmatter
    fm, body = _parse_frontmatter(content)
    if fm is None:
        result.error(path_str, "No YAML frontmatter found (must start with ---)")
        return result

    # Check required fields
    for field, expected_type in AGENT_REQUIRED_FIELDS.items():
        val = fm.get(field)
        if val is None:
            result.error(path_str, f"Missing required frontmatter field: {field}")
        elif not isinstance(val, expected_type):
            result.error(path_str, f"Field '{field}' must be {expected_type.__name__}, got {type(val).__name__}")

    # Specialist ID format
    sid = fm.get("specialist_id", "")
    if sid and not re.match(r"^[a-z][a-z0-9_]{1,40}$", str(sid)):
        result.error(path_str, f"specialist_id '{sid}' must match ^[a-z][a-z0-9_]{{1,40}}$")

    # Status validation
    status = fm.get("status", "")
    if status and str(status) not in AGENT_VALID_STATUS:
        result.error(path_str, f"Invalid status '{status}', must be one of {AGENT_VALID_STATUS}")

    # Workload validation
    workload = fm.get("workload", "")
    if workload and str(workload) not in AGENT_VALID_WORKLOAD:
        result.warning(path_str, f"Unusual workload value '{workload}', expected one of {AGENT_VALID_WORKLOAD}")

    # Availability validation
    avail = fm.get("availability", "")
    if avail and str(avail) not in AGENT_VALID_AVAILABILITY:
        result.warning(path_str, f"Unusual availability '{avail}', expected one of {AGENT_VALID_AVAILABILITY}")

    # Domains check
    domains = fm.get("domains", [])
    if isinstance(domains, list):
        if len(domains) < 2:
            result.warning(path_str, "Agent should have at least 2 domains")
        for d in domains:
            if isinstance(d, str) and len(d.strip()) < 5:
                result.warning(path_str, f"Domain '{d}' is too short — be more specific")

    # Capabilities quality check
    capabilities = fm.get("capabilities", [])
    if isinstance(capabilities, list):
        if len(capabilities) < 3:
            result.warning(path_str, "Agent should have at least 3 capabilities")

        c_count = 0
        for cap in capabilities:
            if not isinstance(cap, str):
                continue
            grade = grade_capability(cap)
            if grade == "C":
                result.error(path_str, f"C-level capability (unacceptable): \"{cap[:60]}...\"")
                c_count += 1
            elif grade == "B":
                result.info(path_str, f"B-level capability (acceptable, A preferred): \"{cap[:60]}...\"")

        if c_count > 0:
            result.error(path_str, f"{c_count} capability(ies) at C-level — must be B or above")

    # Summon keywords check
    keywords = fm.get("summon_keywords", [])
    if isinstance(keywords, list) and len(keywords) < 2:
        result.warning(path_str, "Agent should have at least 2 summon_keywords")

    # Body section checks
    required_sections = ["角色定义", "核心职责", "协作方式", "边界约束", "产出标准"]
    for section in required_sections:
        if section not in body:
            result.warning(path_str, f"Card body missing recommended section: {section}")

    return result


# ---------------------------------------------------------------------------
# Cross-Module Validation
# ---------------------------------------------------------------------------

def validate_routing_conflicts(result: ValidationResult | None = None) -> ValidationResult:
    """Detect routing keyword conflicts across all modules."""
    if result is None:
        result = ValidationResult()

    # Collect all routing keywords from all modules
    keyword_map: dict[str, list[tuple[str, list[str]]]] = {}  # keyword -> [(module_id, [agent_ids])]

    for mod_dir in MODULES_DIR.iterdir():
        if not mod_dir.is_dir():
            continue
        mod_yaml = mod_dir / "module.yaml"
        if not mod_yaml.exists():
            continue

        try:
            raw = load_yaml(mod_yaml)
        except Exception:
            continue

        mod = raw.get("module", raw) if isinstance(raw, dict) else {}
        if not isinstance(mod, dict):
            continue

        mod_id = mod.get("id", mod_dir.name)
        keywords = mod.get("routing_keywords", {})
        if not isinstance(keywords, dict):
            continue

        for kw, targets in keywords.items():
            target_list = targets if isinstance(targets, list) else [targets]
            if kw not in keyword_map:
                keyword_map[kw] = []
            keyword_map[kw].append((mod_id, target_list))

    # Detect conflicts: same keyword in different modules
    for kw, sources in keyword_map.items():
        module_ids = list(set(src[0] for src in sources))
        if len(module_ids) > 1:
            modules_str = ", ".join(module_ids)
            result.warning(
                "routing",
                f"Keyword '{kw}' routes to agents in multiple modules: {modules_str}. "
                f"Consider resolving to avoid ambiguous routing."
            )

    return result


def validate_global_agent_uniqueness(result: ValidationResult | None = None) -> ValidationResult:
    """Ensure all specialist_id values are globally unique across modules."""
    if result is None:
        result = ValidationResult()

    seen: dict[str, str] = {}  # specialist_id -> module_id

    for mod_dir in MODULES_DIR.iterdir():
        if not mod_dir.is_dir():
            continue
        mod_yaml = mod_dir / "module.yaml"
        if not mod_yaml.exists():
            continue

        try:
            raw = load_yaml(mod_yaml)
        except Exception:
            continue

        mod = raw.get("module", raw) if isinstance(raw, dict) else {}
        if not isinstance(mod, dict):
            continue

        mod_id = mod.get("id", mod_dir.name)
        agents = list(mod.get("agents", []) or [])

        regions = mod.get("regions", {}) or {}
        active_regions = mod.get("active_regions", []) or []
        if isinstance(regions, dict) and isinstance(active_regions, list):
            for rk in active_regions:
                region = regions.get(rk) or {}
                region_agents = region.get("agents", []) or []
                if isinstance(region_agents, list):
                    agents.extend(region_agents)
        if not isinstance(agents, list):
            continue

        for agent in agents:
            if isinstance(agent, dict):
                sid = agent.get("specialist_id", "")
            elif isinstance(agent, str):
                sid = agent
            else:
                continue

            if sid in seen:
                result.error(
                    f"modules/{mod_id}/module.yaml",
                    f"Duplicate specialist_id '{sid}' — already defined in module '{seen[sid]}'"
                )
            else:
                seen[sid] = mod_id

    return result


def validate_dependency_integrity(result: ValidationResult | None = None) -> ValidationResult:
    """Verify all declared module dependencies exist."""
    if result is None:
        result = ValidationResult()

    available_modules: set[str] = set()
    for mod_dir in MODULES_DIR.iterdir():
        if mod_dir.is_dir() and (mod_dir / "module.yaml").exists():
            available_modules.add(mod_dir.name)

    for mod_dir in MODULES_DIR.iterdir():
        if not mod_dir.is_dir():
            continue
        mod_yaml = mod_dir / "module.yaml"
        if not mod_yaml.exists():
            continue

        try:
            raw = load_yaml(mod_yaml)
        except Exception:
            continue

        mod = raw.get("module", raw) if isinstance(raw, dict) else {}
        if not isinstance(mod, dict):
            continue

        mod_id = mod.get("id", mod_dir.name)
        deps = mod.get("dependencies", {})
        if not isinstance(deps, dict):
            continue

        for dep_id in (deps.get("required", []) or []):
            if dep_id not in available_modules:
                result.error(
                    f"modules/{mod_id}/module.yaml",
                    f"Required dependency '{dep_id}' does not exist as a module"
                )

        for dep_id in (deps.get("recommended", []) or []):
            if dep_id not in available_modules:
                result.info(
                    f"modules/{mod_id}/module.yaml",
                    f"Recommended dependency '{dep_id}' does not exist as a module"
                )

    return result


# ---------------------------------------------------------------------------
# Full Validation
# ---------------------------------------------------------------------------

def validate_all(module_id: str | None = None) -> ValidationResult:
    """
    Run all validations.
    If module_id is specified, validate only that module.
    Otherwise, validate all modules + cross-module checks.
    """
    result = ValidationResult()

    if module_id:
        # Single module
        print(f"[Validator] Checking module: {module_id}")
        validate_module(module_id, result)

        # Validate all agent cards in this module
        agents_dir = MODULES_DIR / module_id / "agents"
        if agents_dir.exists():
            for card_file in sorted(agents_dir.glob("*.md")):
                validate_agent_card(card_file, result)
    else:
        # All modules
        print("[Validator] Checking all modules...")
        for mod_dir in sorted(MODULES_DIR.iterdir()):
            if not mod_dir.is_dir():
                continue
            if not (mod_dir / "module.yaml").exists():
                result.info(str(mod_dir.name), "Directory exists but no module.yaml — skipping")
                continue

            print(f"  Checking module: {mod_dir.name}")
            validate_module(mod_dir.name, result)

            # Validate agent cards
            agents_dir = mod_dir / "agents"
            if agents_dir.exists():
                for card_file in sorted(agents_dir.glob("*.md")):
                    validate_agent_card(card_file, result)

        # Cross-module validations
        print("  Checking cross-module uniqueness...")
        validate_global_agent_uniqueness(result)

        print("  Checking routing conflicts...")
        validate_routing_conflicts(result)

        print("  Checking dependency integrity...")
        validate_dependency_integrity(result)

    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Synapse Module & Agent Validator"
    )
    parser.add_argument(
        "--module", "-m",
        default=None,
        help="Validate a specific module by ID (e.g. 'engineering')"
    )
    parser.add_argument(
        "--card", "-c",
        default=None,
        help="Validate a specific agent card file path"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as errors"
    )

    args = parser.parse_args()

    if args.card:
        # Single card validation
        print(f"[Validator] Checking card: {args.card}")
        result = validate_agent_card(args.card)
    else:
        # Module or full validation
        result = validate_all(args.module)

    # Print report
    print("\n--- Validation Report ---")
    result.print_report()

    # Exit code
    if args.strict and result.warnings:
        print(f"\n  STRICT MODE: {len(result.warnings)} warning(s) treated as errors")
        sys.exit(1)
    elif not result.is_valid:
        sys.exit(1)
    else:
        print("\n  PASSED")
        sys.exit(0)


if __name__ == "__main__":
    main()
