"""
Synapse Configuration Generator
Assembles CLAUDE.md and organization.yaml from modular definitions.

Usage:
    python generator.py --config synapse.yaml --modules core,engineering,strategy
    python generator.py --config synapse.yaml --preset startup
    python generator.py --config synapse.yaml  (uses modules from config)

Requires: Python 3.10+, no third-party dependencies.
Uses built-in yaml if available, falls back to a minimal YAML parser.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import re
import shutil
import sys
from pathlib import Path
from typing import Any

# Fix Windows console encoding for CJK output
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if sys.stderr.encoding and sys.stderr.encoding.lower() not in ("utf-8", "utf8"):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ---------------------------------------------------------------------------
# YAML handling — prefer PyYAML but fall back to a minimal safe parser
# ---------------------------------------------------------------------------

try:
    import yaml as _yaml

    def load_yaml(path: str | Path) -> Any:
        with open(path, "r", encoding="utf-8") as f:
            return _yaml.safe_load(f)

    def dump_yaml(data: Any) -> str:
        return _yaml.dump(data, allow_unicode=True, default_flow_style=False, sort_keys=False)

except ImportError:
    # Minimal YAML-subset parser (handles the config files in this project)
    def _parse_yaml_value(val: str) -> Any:
        val = val.strip()
        if val == "" or val == "~" or val.lower() == "null":
            return None
        if val.lower() == "true":
            return True
        if val.lower() == "false":
            return False
        if val.startswith('"') and val.endswith('"'):
            return val[1:-1]
        if val.startswith("'") and val.endswith("'"):
            return val[1:-1]
        try:
            return int(val)
        except ValueError:
            pass
        try:
            return float(val)
        except ValueError:
            pass
        return val

    def load_yaml(path: str | Path) -> Any:
        """Minimal YAML loader — supports flat/nested dicts, lists, scalars."""
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        return _parse_lines(lines, 0, 0)[0]

    def _indent(line: str) -> int:
        return len(line) - len(line.lstrip())

    def _parse_lines(lines: list[str], start: int, base_indent: int) -> tuple[Any, int]:
        result: dict[str, Any] = {}
        i = start
        while i < len(lines):
            raw = lines[i]
            stripped = raw.strip()
            # skip blanks, comments
            if not stripped or stripped.startswith("#"):
                i += 1
                continue
            ind = _indent(raw)
            if ind < base_indent:
                break
            if ind > base_indent and not result:
                # unexpected deeper indent at start
                i += 1
                continue
            if ind > base_indent:
                break
            # list item at current level
            if stripped.startswith("- "):
                # collect list
                lst: list[Any] = []
                while i < len(lines):
                    raw2 = lines[i]
                    s2 = raw2.strip()
                    if not s2 or s2.startswith("#"):
                        i += 1
                        continue
                    ind2 = _indent(raw2)
                    if ind2 < base_indent:
                        break
                    if ind2 == base_indent and s2.startswith("- "):
                        item_val = s2[2:].strip()
                        if ":" in item_val and not item_val.startswith('"'):
                            # inline dict in list
                            sub, i = _parse_mapping_from_list(lines, i, ind2)
                            lst.append(sub)
                        else:
                            lst.append(_parse_yaml_value(item_val))
                            i += 1
                    elif ind2 > base_indent:
                        # nested content under last list item
                        sub, i = _parse_lines(lines, i, ind2)
                        if lst and isinstance(lst[-1], str):
                            # replace last string with dict
                            lst[-1] = sub
                        else:
                            lst.append(sub)
                    else:
                        break
                return lst, i
            # key: value
            if ":" in stripped:
                colon_pos = stripped.index(":")
                key = stripped[:colon_pos].strip().strip("-").strip()
                val_part = stripped[colon_pos + 1:].strip()
                if val_part.startswith("#"):
                    val_part = ""
                # check for inline comment
                for q in ('"', "'"):
                    if q in val_part:
                        break
                else:
                    if "#" in val_part:
                        val_part = val_part[:val_part.index("#")].strip()
                if val_part:
                    result[key] = _parse_yaml_value(val_part)
                    i += 1
                else:
                    # value on next lines (nested)
                    i += 1
                    if i < len(lines):
                        next_stripped = lines[i].strip()
                        next_ind = _indent(lines[i]) if next_stripped else base_indent
                        if next_stripped and next_ind > base_indent:
                            child, i = _parse_lines(lines, i, next_ind)
                            result[key] = child
                        else:
                            result[key] = None
                    else:
                        result[key] = None
            else:
                i += 1
        return result, i

    def _parse_mapping_from_list(lines: list[str], start: int, base_indent: int) -> tuple[dict, int]:
        """Parse a mapping that starts as a list item (- key: val)."""
        mapping: dict[str, Any] = {}
        raw = lines[start]
        stripped = raw.strip()
        # first line: "- key: val"
        content = stripped[2:]  # remove "- "
        colon_pos = content.index(":")
        key = content[:colon_pos].strip()
        val = content[colon_pos + 1:].strip()
        mapping[key] = _parse_yaml_value(val) if val else None
        i = start + 1
        child_indent = base_indent + 2
        while i < len(lines):
            raw2 = lines[i]
            s2 = raw2.strip()
            if not s2 or s2.startswith("#"):
                i += 1
                continue
            ind2 = _indent(raw2)
            if ind2 < child_indent:
                break
            if ":" in s2:
                cp = s2.index(":")
                k = s2[:cp].strip()
                v = s2[cp + 1:].strip()
                if v:
                    mapping[k] = _parse_yaml_value(v)
                    i += 1
                else:
                    i += 1
                    if i < len(lines) and _indent(lines[i]) > ind2:
                        child, i = _parse_lines(lines, i, _indent(lines[i]))
                        mapping[k] = child
                    else:
                        mapping[k] = None
            else:
                i += 1
        return mapping, i

    def dump_yaml(data: Any, indent: int = 0) -> str:
        """Minimal YAML serializer."""
        prefix = "  " * indent
        if isinstance(data, dict):
            parts = []
            for k, v in data.items():
                if isinstance(v, (dict, list)):
                    parts.append(f"{prefix}{k}:")
                    parts.append(dump_yaml(v, indent + 1))
                elif v is None:
                    parts.append(f"{prefix}{k}:")
                elif isinstance(v, bool):
                    parts.append(f"{prefix}{k}: {'true' if v else 'false'}")
                elif isinstance(v, str):
                    if any(c in v for c in (":", "#", "'", '"', "\n", "[", "]", "{", "}")):
                        parts.append(f'{prefix}{k}: "{v}"')
                    else:
                        parts.append(f"{prefix}{k}: {v}")
                else:
                    parts.append(f"{prefix}{k}: {v}")
            return "\n".join(parts)
        elif isinstance(data, list):
            parts = []
            for item in data:
                if isinstance(item, dict):
                    first = True
                    for k, v in item.items():
                        if first:
                            if isinstance(v, (dict, list)):
                                parts.append(f"{prefix}- {k}:")
                                parts.append(dump_yaml(v, indent + 2))
                            else:
                                val_str = f'"{v}"' if isinstance(v, str) and any(c in v for c in ":#") else v
                                parts.append(f"{prefix}- {k}: {val_str}")
                            first = False
                        else:
                            if isinstance(v, (dict, list)):
                                parts.append(f"{prefix}  {k}:")
                                parts.append(dump_yaml(v, indent + 2))
                            else:
                                val_str = f'"{v}"' if isinstance(v, str) and any(c in v for c in ":#") else v
                                parts.append(f"{prefix}  {k}: {val_str}")
                else:
                    parts.append(f"{prefix}- {item}")
            return "\n".join(parts)
        else:
            return f"{prefix}{data}"


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SYNAPSE_ROOT = Path(__file__).resolve().parent.parent
CORE_HARNESS = SYNAPSE_ROOT / "core" / "harness"
MODULES_DIR = SYNAPSE_ROOT / "modules"
PRESETS_DIR = SYNAPSE_ROOT / "presets"
WORKSPACE_DIR = SYNAPSE_ROOT / "workspace"


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------

class SynapseGenerator:
    """Assembles a complete Synapse workspace from modular definitions."""

    def __init__(self, user_config_path: str | Path):
        """Load user configuration from synapse.yaml."""
        self.config_path = Path(user_config_path).resolve()
        self.config = load_yaml(self.config_path)
        self.errors: list[str] = []

        # Extract user identity settings
        org = self.config.get("organization", {}) or {}
        self.ceo_name: str = org.get("ceo_name", "Lysander")
        self.president_name: str = org.get("president_name", "YourName")
        self.org_name: str = org.get("org_name", "YourOrg")

        # Settings
        settings = self.config.get("settings", {}) or {}
        self.upgrade_url: str = settings.get("upgrade_url", "")

        # Features
        features = self.config.get("features", {}) or {}
        self.feature_spe: bool = bool(features.get("spe", False))
        self.feature_automation: bool = bool(features.get("automation", False))

    # ------------------------------------------------------------------
    # Module loading
    # ------------------------------------------------------------------

    def _resolve_module_ids(self) -> list[str]:
        """Determine which modules to enable from config or preset."""
        preset_name = self.config.get("preset")
        if preset_name:
            preset_path = PRESETS_DIR / f"{preset_name}.yaml"
            if preset_path.exists():
                preset = load_yaml(preset_path)
                p = preset.get("preset", {}) or {}
                modules = p.get("modules", []) or []
                # Also apply preset feature flags
                feat = p.get("features", {}) or {}
                if feat.get("spe") is not None:
                    self.feature_spe = bool(feat["spe"])
                if feat.get("automation") is not None:
                    self.feature_automation = bool(feat["automation"])
                return list(modules)
            else:
                self.errors.append(f"Preset '{preset_name}' not found at {preset_path}")
                return []
        return list(self.config.get("modules", []) or [])

    def load_modules(self, selected_module_ids: list[str] | None = None) -> list[dict]:
        """Load module.yaml for each selected module."""
        if selected_module_ids is None:
            selected_module_ids = self._resolve_module_ids()

        # Always ensure 'core' is included
        if "core" not in selected_module_ids:
            selected_module_ids = ["core"] + list(selected_module_ids)

        modules: list[dict] = []
        for mid in selected_module_ids:
            mod_path = MODULES_DIR / mid / "module.yaml"
            if not mod_path.exists():
                self.errors.append(f"Module '{mid}' not found: {mod_path}")
                continue
            data = load_yaml(mod_path)
            mod = data.get("module", data) if isinstance(data, dict) else data
            # Ensure the id is set
            if isinstance(mod, dict) and "id" not in mod:
                mod["id"] = mid
            if isinstance(mod, dict):
                self._apply_regions(mod, mid)
            modules.append(mod)
        return modules

    def _apply_regions(self, mod: dict, module_id: str) -> None:
        regions = mod.get("regions") or {}
        active = mod.get("active_regions") or []
        if not isinstance(regions, dict) or not isinstance(active, list) or not active:
            return
        agents = list(mod.get("agents") or [])
        seen = set()
        for a in agents:
            if isinstance(a, dict) and a.get("specialist_id"):
                seen.add(a.get("specialist_id"))
            elif isinstance(a, str) and a:
                seen.add(a)
        for region_key in active:
            region = regions.get(region_key) or {}
            region_agents = region.get("agents") or []
            if not isinstance(region_agents, list):
                continue
            for ra in region_agents:
                if not isinstance(ra, dict):
                    continue
                sid = str(ra.get("specialist_id", "")).strip()
                if not sid or sid in seen:
                    continue
                agents.append(ra)
                seen.add(sid)
        mod["agents"] = agents

    def resolve_dependencies(self, modules: list[dict]) -> list[dict]:
        """
        Resolve module dependencies.
        Ensures 'core' is always first and all required dependencies are present.
        """
        loaded_ids = {m.get("id", "") for m in modules}
        to_add: list[str] = []

        for mod in modules:
            deps = mod.get("dependencies", {}) or {}
            required = deps.get("required", []) or []
            for dep_id in required:
                if dep_id not in loaded_ids and dep_id not in to_add:
                    to_add.append(dep_id)

        # Load missing dependencies
        for dep_id in to_add:
            dep_path = MODULES_DIR / dep_id / "module.yaml"
            if dep_path.exists():
                data = load_yaml(dep_path)
                dep_mod = data.get("module", data) if isinstance(data, dict) else data
                if isinstance(dep_mod, dict) and "id" not in dep_mod:
                    dep_mod["id"] = dep_id
                modules.append(dep_mod)
                loaded_ids.add(dep_id)
            else:
                self.errors.append(f"Dependency '{dep_id}' not found: {dep_path}")

        # Sort: core first, then alphabetical
        core_modules = [m for m in modules if m.get("id") == "core"]
        other_modules = sorted(
            [m for m in modules if m.get("id") != "core"],
            key=lambda m: m.get("id", "")
        )
        return core_modules + other_modules

    # ------------------------------------------------------------------
    # CLAUDE.md assembly
    # ------------------------------------------------------------------

    def _load_assembly_order(self) -> list[dict]:
        """Load the harness assembly order definition."""
        order_path = CORE_HARNESS / "assembly-order.yaml"
        if not order_path.exists():
            self.errors.append(f"Assembly order not found: {order_path}")
            return []
        data = load_yaml(order_path)
        return data.get("assembly", []) or []

    def _apply_variables(self, content: str, modules: list[dict]) -> str:
        """Replace template variables in content."""
        # Calculate team count
        team_count = 0
        team_names: list[str] = []
        for mod in modules:
            agents = mod.get("agents", []) or []
            team_count += len(agents)
            mod_name = mod.get("name", mod.get("name_en", mod.get("id", "")))
            if mod.get("id") != "core":
                team_names.append(mod_name)

        # Build routing block
        routing_lines: list[str] = []
        for mod in modules:
            mod_id = mod.get("id", "")
            mod_name = mod.get("name_en", mod_id)
            keywords = mod.get("routing_keywords", {}) or {}
            if keywords:
                keyword_list = ", ".join(keywords.keys()) if isinstance(keywords, dict) else str(keywords)
                routing_lines.append(f"        ├─ {mod_name} → {keyword_list}")
        routing_block = "\n".join(routing_lines) if routing_lines else "        (no routing rules defined)"

        # Team list for header
        team_list_str = " / ".join(team_names) if team_names else "（请启用业务模块）"

        replacements = {
            "{{CEO_NAME}}": self.ceo_name,
            "{{PRESIDENT_NAME}}": self.president_name,
            "{{ORG_NAME}}": self.org_name,
            "{{TEAM_COUNT}}": str(team_count),
            "{{TEAM_LIST}}": team_list_str,
            "{{TEAM_ROUTING}}": routing_block,
            "{{UPGRADE_URL}}": self.upgrade_url,
        }

        for var, val in replacements.items():
            content = content.replace(var, val)

        return content

    def _collect_module_fragments(self, modules: list[dict]) -> str:
        """Collect harness fragments from all non-core modules."""
        fragments: list[str] = []
        for mod in modules:
            mod_id = mod.get("id", "")
            if mod_id == "core":
                continue
            frag_rel = mod.get("harness_fragment", "")
            if not frag_rel:
                continue
            frag_path = MODULES_DIR / mod_id / frag_rel
            if frag_path.exists():
                content = frag_path.read_text(encoding="utf-8")
                fragments.append(f"<!-- Module Fragment: {mod_id} -->\n{content}")
            else:
                self.errors.append(f"Harness fragment not found for module '{mod_id}': {frag_path}")
        return "\n\n".join(fragments)

    def assemble_claude_md(self, modules: list[dict]) -> str:
        """
        Assemble CLAUDE.md:
        1. Read core harness fragments in assembly order
        2. Inject module fragments after the workflow section
        3. Apply variable substitution
        4. Return the complete CLAUDE.md content
        """
        assembly_order = self._load_assembly_order()
        sections: list[str] = []

        # Determine module injection point
        injection_file = "03-workflow.md"  # default from assembly-order.yaml

        for entry in assembly_order:
            filename = entry.get("file", "")
            required = entry.get("required", True)
            feature_flag = entry.get("feature_flag", "")

            # Check feature flags for optional sections
            if feature_flag:
                if feature_flag == "spe" and not self.feature_spe:
                    continue
                if feature_flag == "automation" and not self.feature_automation:
                    continue

            frag_path = CORE_HARNESS / filename
            if not frag_path.exists():
                if required:
                    self.errors.append(f"Required harness fragment missing: {frag_path}")
                continue

            content = frag_path.read_text(encoding="utf-8")
            sections.append(content)

            # Inject module fragments after the injection point
            if filename == injection_file:
                module_fragments = self._collect_module_fragments(modules)
                if module_fragments:
                    sections.append(
                        f"\n<!-- === Module-Specific Harness Fragments === -->\n\n{module_fragments}\n"
                    )

        full_content = "\n\n".join(sections)
        full_content = self._apply_variables(full_content, modules)
        return full_content

    # ------------------------------------------------------------------
    # organization.yaml assembly
    # ------------------------------------------------------------------

    def assemble_organization(self, modules: list[dict]) -> dict:
        """
        Assemble organization.yaml:
        1. Collect all agents from all modules
        2. Build routing keyword map
        3. Generate team structure
        """
        teams: list[dict] = []
        all_routing: dict[str, list[str]] = {}

        for mod in modules:
            mod_id = mod.get("id", "")
            mod_name = mod.get("name", "")
            mod_name_en = mod.get("name_en", "")

            agents = mod.get("agents", []) or []
            agent_list: list[dict] = []
            for agent in agents:
                if isinstance(agent, dict):
                    agent_list.append({
                        "specialist_id": agent.get("specialist_id", ""),
                        "role": agent.get("role", ""),
                        "role_en": agent.get("role_en", ""),
                        "required": agent.get("required", True),
                    })
                elif isinstance(agent, str):
                    agent_list.append({
                        "specialist_id": agent,
                        "role": agent,
                        "role_en": agent,
                        "required": True,
                    })

            team_entry = {
                "id": mod_id,
                "name": mod_name,
                "name_en": mod_name_en,
                "agents": agent_list,
            }
            teams.append(team_entry)

            # Merge routing keywords
            agent_ids_in_module = {a.get("specialist_id", "") for a in agent_list if a.get("specialist_id")}

            keywords = mod.get("routing_keywords", {}) or {}
            if isinstance(keywords, dict):
                for kw, agent_ids in keywords.items():
                    agent_id_list = agent_ids if isinstance(agent_ids, list) else [agent_ids]
                    filtered = [aid for aid in agent_id_list if aid in agent_ids_in_module]
                    targets = [f"{mod_id}.{aid}" for aid in filtered]
                    if not targets:
                        continue
                    if kw in all_routing:
                        all_routing[kw].extend(targets)
                    else:
                        all_routing[kw] = targets

        org = {
            "organization": {
                "ceo_name": self.ceo_name,
                "president_name": self.president_name,
                "org_name": self.org_name,
                "total_agents": sum(len(t.get("agents", [])) for t in teams),
                "teams": teams,
                "routing": all_routing,
            }
        }
        return org

    # ------------------------------------------------------------------
    # Agent cards & Skills collection
    # ------------------------------------------------------------------

    def collect_agent_cards(self, modules: list[dict]) -> list[tuple[str, str]]:
        """
        Collect all agent card files from selected modules.
        Returns list of (relative_target_path, file_content) tuples.
        """
        cards: list[tuple[str, str]] = []
        for mod in modules:
            mod_id = mod.get("id", "")
            agents = mod.get("agents", []) or []
            for agent in agents:
                if isinstance(agent, dict):
                    card_rel = agent.get("card_path", "")
                    specialist_id = agent.get("specialist_id", "")
                else:
                    card_rel = f"agents/{agent}.md"
                    specialist_id = agent

                card_path = MODULES_DIR / mod_id / card_rel
                if card_path.exists():
                    content = card_path.read_text(encoding="utf-8")
                    # Apply variable substitution to cards
                    content = content.replace("{{CEO_NAME}}", self.ceo_name)
                    content = content.replace("{{ORG_NAME}}", self.org_name)
                    target = f"obs/01-team-knowledge/HR/personnel/{specialist_id}.md"
                    cards.append((target, content))
                else:
                    self.errors.append(f"Agent card not found: {card_path}")
        return cards

    def collect_skills(self, modules: list[dict]) -> list[tuple[str, str]]:
        """
        Collect all skill files from selected modules.
        Returns list of (relative_target_path, file_content) tuples.
        """
        skills: list[tuple[str, str]] = []
        for mod in modules:
            mod_id = mod.get("id", "")
            mod_skills = mod.get("skills", []) or []
            for skill in mod_skills:
                if isinstance(skill, dict):
                    skill_id = skill.get("id", "")
                    skill_rel = skill.get("path", "")
                else:
                    skill_id = skill
                    skill_rel = f"skills/{skill}.md"

                skill_path = MODULES_DIR / mod_id / skill_rel
                if skill_path.exists():
                    content = skill_path.read_text(encoding="utf-8")
                    target = f".claude/skills/{skill_id}.md"
                    skills.append((target, content))
                # Skills may not exist yet during initial setup — not an error
        return skills

    # ------------------------------------------------------------------
    # Settings generation
    # ------------------------------------------------------------------

    def _generate_settings(self, modules: list[dict]) -> dict:
        """Generate .claude/settings.json for the workspace."""
        # Collect all skill IDs to register as allowed tools
        skill_ids = []
        for mod in modules:
            for skill in (mod.get("skills", []) or []):
                if isinstance(skill, dict):
                    skill_ids.append(skill.get("id", ""))
                else:
                    skill_ids.append(skill)

        settings = {
            "permissions": {
                "allow": [
                    "Bash(read:*)",
                    "Read(*)",
                    "Glob(*)",
                    "Grep(*)",
                ],
                "deny": []
            },
            "synapse": {
                "version": "2.0.0",
                "ceo_name": self.ceo_name,
                "modules_enabled": [m.get("id", "") for m in modules],
                "skills_registered": skill_ids,
                "features": {
                    "spe": self.feature_spe,
                    "automation": self.feature_automation,
                }
            }
        }
        return settings

    # ------------------------------------------------------------------
    # Full generation
    # ------------------------------------------------------------------

    def generate(self, selected_module_ids: list[str] | None = None) -> bool:
        """
        Full generation workflow:
        1. Load and resolve modules
        2. Assemble CLAUDE.md
        3. Assemble organization.yaml
        4. Copy agent cards
        5. Copy skills
        6. Generate settings.json
        7. Validate results
        Returns True if successful (no errors).
        """
        print(f"[Synapse Generator] Starting generation...")
        print(f"  Config: {self.config_path}")
        print(f"  CEO: {self.ceo_name} | President: {self.president_name} | Org: {self.org_name}")

        # 1. Load modules
        modules = self.load_modules(selected_module_ids)
        if not modules:
            self.errors.append("No modules loaded. Aborting.")
            self._print_errors()
            return False

        # 2. Resolve dependencies
        modules = self.resolve_dependencies(modules)
        module_ids = [m.get("id", "?") for m in modules]
        print(f"  Modules: {', '.join(module_ids)}")
        print(f"  Features: SPE={'on' if self.feature_spe else 'off'}, "
              f"Automation={'on' if self.feature_automation else 'off'}")

        # 3. Assemble CLAUDE.md
        print("\n[1/5] Assembling CLAUDE.md ...")
        claude_md = self.assemble_claude_md(modules)
        out_claude = WORKSPACE_DIR / "CLAUDE.md"
        out_claude.parent.mkdir(parents=True, exist_ok=True)
        out_claude.write_text(claude_md, encoding="utf-8")
        print(f"  -> {out_claude} ({len(claude_md)} chars)")

        # 4. Assemble organization.yaml
        print("[2/5] Assembling organization.yaml ...")
        org = self.assemble_organization(modules)
        out_org = WORKSPACE_DIR / "config" / "organization.yaml"
        out_org.parent.mkdir(parents=True, exist_ok=True)
        org_content = dump_yaml(org)
        out_org.write_text(org_content, encoding="utf-8")
        print(f"  -> {out_org}")

        # 5. Copy agent cards
        print("[3/5] Copying agent cards ...")
        cards = self.collect_agent_cards(modules)
        for rel_path, content in cards:
            target = WORKSPACE_DIR / rel_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        print(f"  -> {len(cards)} cards copied")

        # 6. Copy skills
        print("[4/5] Copying skills ...")
        skills = self.collect_skills(modules)
        for rel_path, content in skills:
            target = WORKSPACE_DIR / rel_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        print(f"  -> {len(skills)} skills copied")

        # 7. Generate settings.json
        print("[5/5] Generating settings.json ...")
        settings = self._generate_settings(modules)
        out_settings = WORKSPACE_DIR / ".claude" / "settings.json"
        out_settings.parent.mkdir(parents=True, exist_ok=True)
        out_settings.write_text(
            json.dumps(settings, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
        print(f"  -> {out_settings}")

        # 8. Report
        print(f"\n[Synapse Generator] Generation complete!")
        total_agents = sum(len(m.get("agents", [])) for m in modules)
        print(f"  Total agents: {total_agents}")
        print(f"  Output: {WORKSPACE_DIR}")

        if self.errors:
            self._print_errors()
            return False

        print("  Status: SUCCESS (0 errors)")
        return True

    def validate(self) -> list[str]:
        """Validate the generated workspace for completeness."""
        issues: list[str] = []

        # Check CLAUDE.md exists
        claude_path = WORKSPACE_DIR / "CLAUDE.md"
        if not claude_path.exists():
            issues.append("CLAUDE.md not found in workspace")
        else:
            content = claude_path.read_text(encoding="utf-8")
            # Check no unresolved variables
            unresolved = re.findall(r"\{\{[A-Z_]+\}\}", content)
            if unresolved:
                issues.append(f"Unresolved variables in CLAUDE.md: {unresolved}")
            # Check key sections exist
            if "CEO 执行禁区" not in content:
                issues.append("CLAUDE.md missing CEO constraints section")
            if "标准执行链" not in content:
                issues.append("CLAUDE.md missing execution chain section")
            if "决策体系" not in content:
                issues.append("CLAUDE.md missing decision system section")

        # Check organization.yaml
        org_path = WORKSPACE_DIR / "config" / "organization.yaml"
        if not org_path.exists():
            issues.append("organization.yaml not found in workspace")

        # Check settings.json
        settings_path = WORKSPACE_DIR / ".claude" / "settings.json"
        if not settings_path.exists():
            issues.append("settings.json not found in workspace")
        else:
            try:
                with open(settings_path, encoding="utf-8") as f:
                    json.load(f)
            except json.JSONDecodeError as e:
                issues.append(f"settings.json is invalid JSON: {e}")

        # Check at least some agent cards exist
        personnel_dir = WORKSPACE_DIR / "obs" / "01-team-knowledge" / "HR" / "personnel"
        if personnel_dir.exists():
            cards = list(personnel_dir.glob("*.md"))
            if not cards:
                issues.append("No agent cards found in personnel directory")
        else:
            issues.append("Personnel directory not found in workspace")

        return issues

    def _print_errors(self):
        if self.errors:
            print(f"\n[WARNING] {len(self.errors)} error(s) during generation:")
            for err in self.errors:
                print(f"  - {err}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Synapse Configuration Generator — assemble CLAUDE.md from modules"
    )
    parser.add_argument(
        "--config", "-c",
        default=str(SYNAPSE_ROOT / "synapse.yaml"),
        help="Path to synapse.yaml config file (default: synapse-core/synapse.yaml)"
    )
    parser.add_argument(
        "--modules", "-m",
        default=None,
        help="Comma-separated module IDs to enable (overrides config file)"
    )
    parser.add_argument(
        "--preset", "-p",
        default=None,
        help="Preset name to use (overrides modules list)"
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate existing workspace, don't regenerate"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be generated without writing files"
    )

    args = parser.parse_args()

    # Initialize generator
    gen = SynapseGenerator(args.config)

    # Handle preset override
    if args.preset:
        gen.config["preset"] = args.preset

    # Validate only mode
    if args.validate_only:
        print("[Synapse Validator] Checking workspace...")
        issues = gen.validate()
        if issues:
            print(f"\n  {len(issues)} issue(s) found:")
            for issue in issues:
                print(f"    - {issue}")
            sys.exit(1)
        else:
            print("  All checks passed!")
            sys.exit(0)

    # Determine modules
    selected = None
    if args.modules:
        selected = [m.strip() for m in args.modules.split(",")]

    # Dry run
    if args.dry_run:
        modules = gen.load_modules(selected)
        modules = gen.resolve_dependencies(modules)
        print("[Dry Run] Would generate with modules:")
        for m in modules:
            agents = m.get("agents", [])
            agent_count = len(agents) if isinstance(agents, list) else 0
            print(f"  - {m.get('id', '?')} ({m.get('name_en', '?')}) — {agent_count} agents")
        print(f"\nTotal agents: {sum(len(m.get('agents', [])) for m in modules)}")
        print(f"SPE: {'on' if gen.feature_spe else 'off'}")
        print(f"Automation: {'on' if gen.feature_automation else 'off'}")
        sys.exit(0)

    # Generate
    success = gen.generate(selected)
    if not success:
        sys.exit(1)

    # Post-generation validation
    issues = gen.validate()
    if issues:
        print(f"\n[Post-Validation] {len(issues)} issue(s):")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("\n[Post-Validation] All checks passed!")


if __name__ == "__main__":
    main()
