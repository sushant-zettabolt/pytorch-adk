#!/usr/bin/env python3
"""
Stage 1 — Parse pybind11 boundaries between Python and C++.

Produces boundary_table.json mapping Python call sites → C++ targets.
Uses static pattern matching on binding files (tree-sitter optional).

Requires real PyTorch source. Exits with error if PYTORCH_ROOT has no source.

Usage:
    PYTORCH_ROOT=/path/to/pytorch python tools/adk/parse_boundaries.py

Outputs written to: .claude/index/boundary_table.json, unresolved_edges.json
"""

import json
import os
import re
import sys
from pathlib import Path


PYTORCH_ROOT = Path(os.environ.get("PYTORCH_ROOT", "."))
OUTPUT_DIR = Path(os.environ.get("INDEX_DIR", ".claude/index"))

PYBIND_PATTERNS = [
    re.compile(r'm\.def\(\s*"([^"]+)"\s*,\s*[&]?(\w+(?:::\w+)*)'),
    re.compile(r'\.def\(\s*"([^"]+)"\s*,\s*[&]?(\w+(?:::\w+)*)'),
]

TORCH_CALL_PATTERN = re.compile(r'torch\.(\w+(?:\.\w+)*)\s*\(')


def find_binding_files(root: Path) -> list[Path]:
    binding_files = []
    # NOTE: generated files ARE included for boundary parsing — they contain the actual
    # pybind11 bindings. The "don't cite generated files" rule applies only to SKILL.md
    # citation sources, not to boundary table parsing.
    skip_patterns = ["python_variable_methods"]
    for pattern in ["torch/csrc/**/*.cpp", "torch/csrc/**/*.h"]:
        for p in root.glob(pattern):
            if not any(sp in str(p) for sp in skip_patterns):
                binding_files.append(p)
    return binding_files


def parse_pybind_file(filepath: Path) -> list[dict]:
    entries = []
    try:
        text = filepath.read_text(errors="replace")
        for pattern in PYBIND_PATTERNS:
            for match in pattern.finditer(text):
                if len(match.groups()) >= 2:
                    entries.append({
                        "python_name": match.group(1),
                        "cpp_target": match.group(2),
                        "resolution": "static",
                        "confidence": 1.0,
                        "binding_file": str(filepath.relative_to(PYTORCH_ROOT)),
                    })
    except Exception as e:
        print(f"  Warning: could not parse {filepath}: {e}", file=sys.stderr)
    return entries


def parse_native_functions_yaml(root: Path) -> dict[str, str]:
    yaml_path = root / "aten/src/ATen/native/native_functions.yaml"
    if not yaml_path.exists():
        return {}
    mappings = {}
    try:
        text = yaml_path.read_text()
        current_func = None
        in_dispatch = False
        for line in text.splitlines():
            func_match = re.match(r"- func:\s+(\w+)\(", line)
            if func_match:
                current_func = func_match.group(1)
                in_dispatch = False
                continue
            if "dispatch:" in line:
                in_dispatch = True
                continue
            if in_dispatch and current_func:
                dispatch_match = re.match(r"\s+\w+:\s+(\w+)", line)
                if dispatch_match:
                    mappings[f"torch.{current_func}"] = f"at::native::{dispatch_match.group(1)}"
                elif not line.startswith(" ") and line.strip():
                    in_dispatch = False
    except Exception as e:
        print(f"  Warning: could not parse native_functions.yaml: {e}", file=sys.stderr)
    return mappings


def collect_unresolved(boundary_table: dict) -> list[dict]:
    unresolved = []
    py_dir = PYTORCH_ROOT / "torch"
    if not py_dir.exists():
        return unresolved
    for py_file in py_dir.rglob("*.py"):
        if "generated" in str(py_file):
            continue
        try:
            text = py_file.read_text(errors="replace")
            for match in TORCH_CALL_PATTERN.finditer(text):
                call_site = f"torch.{match.group(1)}"
                if call_site not in boundary_table:
                    lineno = text[: match.start()].count("\n") + 1
                    unresolved.append({
                        "python_call_site": call_site,
                        "source_file": str(py_file.relative_to(PYTORCH_ROOT)),
                        "line": lineno,
                        "context": text.splitlines()[max(0, lineno - 2): lineno + 2],
                    })
        except Exception:
            pass
    seen = set()
    deduped = []
    for item in unresolved:
        if item["python_call_site"] not in seen:
            seen.add(item["python_call_site"])
            deduped.append(item)
    return deduped


def main():
    print("Stage 1 — parse_boundaries.py")
    print(f"  PyTorch root: {PYTORCH_ROOT.resolve()}")

    binding_files = find_binding_files(PYTORCH_ROOT)
    if not binding_files:
        print("ERROR: No PyTorch source found at PYTORCH_ROOT.", file=sys.stderr)
        print("  Set PYTORCH_ROOT to a real PyTorch checkout and re-run.", file=sys.stderr)
        return 1

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    boundary_table: dict = {}
    print(f"  Found {len(binding_files)} binding files")
    for bf in binding_files:
        for e in parse_pybind_file(bf):
            key = f"torch.{e['python_name']}"
            if key not in boundary_table:
                boundary_table[key] = e

    yaml_mappings = parse_native_functions_yaml(PYTORCH_ROOT)
    print(f"  Found {len(yaml_mappings)} entries in native_functions.yaml")
    for py_name, cpp_target in yaml_mappings.items():
        if py_name not in boundary_table:
            boundary_table[py_name] = {
                "cpp_target": cpp_target,
                "resolution": "static",
                "confidence": 0.9,
                "binding_file": "aten/src/ATen/native/native_functions.yaml",
            }

    out_boundary = OUTPUT_DIR / "boundary_table.json"
    with open(out_boundary, "w") as f:
        json.dump({
            "_meta": {
                "note": "Python→C++ boundary table. Generated — do not edit.",
                "format": "python_call_site -> {cpp_target, resolution, confidence, binding_file}",
            },
            **boundary_table,
        }, f, indent=2)
    print(f"  Written: {out_boundary} ({len(boundary_table)} entries)")

    unresolved = collect_unresolved(boundary_table)
    total = len(boundary_table) + len(unresolved)
    unresolved_pct = (len(unresolved) / total * 100) if total > 0 else 0.0

    out_unresolved = OUTPUT_DIR / "unresolved_edges.json"
    with open(out_unresolved, "w") as f:
        json.dump({
            "_meta": {
                "unresolved_count": len(unresolved),
                "total_call_sites": total,
                "unresolved_pct": round(unresolved_pct, 1),
            },
            "unresolved": unresolved,
        }, f, indent=2)
    print(f"  Written: {out_unresolved} ({len(unresolved)} unresolved, {unresolved_pct:.1f}%)")

    gate_pass = unresolved_pct < 25.0
    print(f"  Gate: unresolved < 25% → {'PASS' if gate_pass else 'FAIL'} ({unresolved_pct:.1f}%)")
    return 0 if gate_pass else 1


if __name__ == "__main__":
    sys.exit(main())
