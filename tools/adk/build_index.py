#!/usr/bin/env python3
"""
ADK Index Builder — builds a flat symbol index for any codebase.

Scans Python and C++ source files and writes:
  symbols.json    — symbol name → {file, line, anchor, language}
  index_meta.json — build metadata for staleness checks

Usage:
    python tools/adk/build_index.py [--root PATH] [--skip-cpp]

Environment:
    REPO_ROOT   override the root directory to scan (default: repo root of this script)
    INDEX_DIR   override the output directory (default: <root>/.claude/index)
"""

import ast
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

# tree-sitter vendored under tools/adk/vendor/ (no system install needed)
sys.path.insert(0, str(Path(__file__).parent / "vendor"))
import tree_sitter_cpp as _ts_cpp
from tree_sitter import Language as _TSLanguage, Parser as _TSParser

_CPP_LANG = _TSLanguage(_ts_cpp.language())

SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = Path(os.environ.get("REPO_ROOT", SCRIPT_DIR.parent.parent))
INDEX_DIR = Path(os.environ.get("INDEX_DIR", REPO_ROOT / ".claude" / "index"))

_SKIP_DIRS = {"build", "dist", ".git", "__pycache__", "node_modules", ".venv", "venv"}
_SKIP_PATH_FRAGMENTS = {"generated", "/build/", "\\build\\"}


def _should_skip(path: Path, root: Path) -> bool:
    rel = str(path.relative_to(root))
    if any(frag in rel for frag in _SKIP_PATH_FRAGMENTS):
        return True
    for part in path.parts:
        if part in _SKIP_DIRS:
            return True
    return False


def get_head_commit(root: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, cwd=root,
        )
        return result.stdout.strip() or "unknown"
    except Exception:
        return "unknown"


# ---------------------------------------------------------------------------
# Python symbol scan
# ---------------------------------------------------------------------------

def scan_python_symbols(root: Path) -> dict:
    symbols: dict = {}
    file_count = 0
    py_start = time.time()

    all_py_files = [
        f for f in root.rglob("*.py") if not _should_skip(f, root)
    ]
    total_py = len(all_py_files)
    print(f"  Python: {total_py} files to scan")

    for py_file in all_py_files:
        try:
            text = py_file.read_text(errors="replace")
            tree = ast.parse(text, filename=str(py_file))
        except SyntaxError:
            file_count += 1
            continue

        rel_path = str(py_file.relative_to(root))
        file_count += 1

        print(f"  Python [{file_count}/{total_py}] indexing {rel_path}")

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                name = node.name
                if name.startswith("_") and not name.startswith("__"):
                    continue
                if name not in symbols:
                    symbols[name] = {
                        "file": rel_path,
                        "line": node.lineno,
                        "anchor": name,
                        "language": "python",
                        "resolution": "static",
                    }

    py_elapsed = time.time() - py_start
    print(f"  Python: {len(symbols)} symbols from {file_count} files in {py_elapsed:.1f}s")
    return symbols


# ---------------------------------------------------------------------------
# C++ symbol scan (tree-sitter CST parser)
# ---------------------------------------------------------------------------

def _extract_cpp_nodes(node, rel_path: str, local: dict) -> None:
    """Walk a tree-sitter CST node and collect class/struct/function/namespace names."""
    t = node.type
    if t in ("class_specifier", "struct_specifier"):
        for child in node.children:
            if child.type == "type_identifier" and child.text:
                name = child.text.decode("utf-8", errors="replace")
                if len(name) > 2 and not name.startswith("_") and name not in local:
                    local[name] = {
                        "file": rel_path,
                        "line": node.start_point[0] + 1,
                        "anchor": name,
                        "language": "cpp",
                        "resolution": "static",
                    }
                break
    elif t == "function_definition":
        for child in node.children:
            if child.type == "function_declarator":
                for subchild in child.children:
                    if subchild.type == "identifier" and subchild.text:
                        name = subchild.text.decode("utf-8", errors="replace")
                        if len(name) > 2 and not name.startswith("_") and name not in local:
                            local[name] = {
                                "file": rel_path,
                                "line": node.start_point[0] + 1,
                                "anchor": name,
                                "language": "cpp",
                                "resolution": "static",
                            }
                        break
                break
    elif t == "namespace_definition":
        for child in node.children:
            if child.type == "namespace_identifier" and child.text:
                name = child.text.decode("utf-8", errors="replace")
                if len(name) > 2 and not name.startswith("_") and name not in local:
                    local[name] = {
                        "file": rel_path,
                        "line": node.start_point[0] + 1,
                        "anchor": name,
                        "language": "cpp",
                        "resolution": "static",
                    }
                break
    for child in node.children:
        _extract_cpp_nodes(child, rel_path, local)


def _scan_one_cpp_file(cpp_file: Path, root: Path) -> tuple[str, dict, str | None]:
    """Parse one C++ file with tree-sitter. Safe to call from worker threads."""
    rel_path = str(cpp_file.relative_to(root))
    local: dict = {}
    try:
        source = cpp_file.read_bytes()
        parser = _TSParser(_CPP_LANG)
        tree = parser.parse(source)
        _extract_cpp_nodes(tree.root_node, rel_path, local)
    except Exception as exc:
        return rel_path, local, str(exc)
    return rel_path, local, None


def scan_cpp_symbols(root: Path) -> dict:
    symbols: dict = {}

    # Collect C++ files
    cpp_files: list[Path] = []
    for ext in ("*.h", "*.hpp", "*.cpp", "*.cc", "*.cxx"):
        for f in root.rglob(ext):
            if not _should_skip(f, root):
                cpp_files.append(f)

    if not cpp_files:
        print("  C++: no source files found")
        return symbols

    total_cpp = len(cpp_files)
    workers = os.cpu_count() or 4
    print(f"  C++: tree-sitter parsing {total_cpp} files using {workers} threads")

    ts_start = time.time()

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(_scan_one_cpp_file, f, root) for f in cpp_files]

        for file_idx, future in enumerate(futures, 1):
            rel_path, file_symbols, warning = future.result()

            print(f"  C++ [{file_idx}/{total_cpp}] indexing {rel_path}")

            if warning is not None:
                print(f"  C++ WARNING: {rel_path} ({warning})")

            for name, entry in file_symbols.items():
                if name not in symbols:
                    symbols[name] = entry

    ts_elapsed = time.time() - ts_start
    print(f"  C++: {len(symbols)} symbols via tree-sitter in {ts_elapsed:.1f}s")
    return symbols


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    skip_cpp = "--skip-cpp" in sys.argv
    root = REPO_ROOT
    for i, arg in enumerate(sys.argv[1:], 1):
        if arg == "--root" and i < len(sys.argv):
            root = Path(sys.argv[i + 1])

    print("=" * 60)
    print("ADK Index Builder")
    print(f"  Root:      {root.resolve()}")
    print(f"  Index dir: {INDEX_DIR.resolve()}")
    print("=" * 60)

    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    start_time = time.time()
    head_commit = get_head_commit(root)
    print(f"  HEAD: {head_commit}")

    # Scan Python
    print("\nScanning Python symbols...")
    py_symbols = scan_python_symbols(root)

    # Scan C++
    cpp_symbols: dict = {}
    if not skip_cpp:
        print("\nScanning C++ symbols...")
        cpp_symbols = scan_cpp_symbols(root)
    else:
        print("\nC++ scan skipped (--skip-cpp)")

    # Merge: Python wins on name collision (more specific)
    merged = {**cpp_symbols, **py_symbols}

    # Write symbols.json
    output = {
        "_meta": {
            "built_at_commit": head_commit,
            "format": "symbol_name -> {file, line, anchor, language, resolution}",
            "note": "Run python tools/adk/build_index.py to rebuild",
        },
        **merged,
    }
    symbols_path = INDEX_DIR / "symbols.json"
    with open(symbols_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nWritten: symbols.json ({len(merged)} symbols)")

    # Write index_meta.json
    elapsed = time.time() - start_time
    meta = {
        "built_at_commit": head_commit,
        "built_at_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "index_version": "3.0",
        "build_seconds": round(elapsed, 1),
        "python_symbols": len(py_symbols),
        "cpp_symbols": len(cpp_symbols),
        "total_symbols": len(merged),
        "status": "built",
        "note": "Navigation agents must check built_at_commit == HEAD before using index",
    }
    with open(INDEX_DIR / "index_meta.json", "w") as f:
        json.dump(meta, f, indent=2)
    print(f"Written: index_meta.json (built at {head_commit[:8]} in {elapsed:.1f}s)")

    print("\n" + "=" * 60)
    print(f"Done — {len(merged)} symbols indexed")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
