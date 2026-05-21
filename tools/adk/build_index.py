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
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

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
# C++ symbol scan (ctags with grep fallback)
# ---------------------------------------------------------------------------

_CPP_CLASS_RE = re.compile(r"^\s*(?:class|struct)\s+(\w+)")
_CPP_FUNC_RE = re.compile(
    r"^\s*(?:inline\s+)?(?:static\s+)?(?:virtual\s+)?(?:explicit\s+)?"
    r"(?:[\w:*&<>\s]+\s+)+(\w+)\s*\("
)
_CPP_SKIP_KEYWORDS = {
    "if", "for", "while", "switch", "catch", "return", "delete", "new",
    "sizeof", "alignof", "decltype", "operator",
}


def _scan_one_cpp_file(cpp_file: Path, root: Path) -> tuple[str, dict, str | None]:
    """Scan one C++ file for symbols. Safe to call from worker threads."""
    rel_path = str(cpp_file.relative_to(root))
    local: dict = {}
    try:
        for lineno, line in enumerate(cpp_file.read_text(errors="replace").splitlines(), 1):
            for pat in (_CPP_CLASS_RE, _CPP_FUNC_RE):
                m = pat.match(line)
                if m:
                    name = m.group(1)
                    if len(name) > 2 and name not in _CPP_SKIP_KEYWORDS and not name.startswith("_"):
                        if name not in local:
                            local[name] = {
                                "file": rel_path,
                                "line": lineno,
                                "anchor": name,
                                "language": "cpp",
                                "resolution": "static",
                            }
                    break
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

    # Try ctags first
    ctags_ok = False
    try:
        r = subprocess.run(["ctags", "--version"], capture_output=True, text=True)
        ctags_ok = r.returncode == 0
    except (FileNotFoundError, OSError):
        pass

    if ctags_ok:
        print(f"  C++: running ctags on {len(cpp_files)} files...")
        try:
            result = subprocess.run(
                ["ctags", "--output-format=json", "--language-force=C++", "--fields=+n", "-L", "-"],
                input="\n".join(str(f) for f in cpp_files),
                capture_output=True, text=True, timeout=120,
            )
            for line in result.stdout.splitlines():
                try:
                    tag = json.loads(line)
                    if tag.get("kind") in ("function", "class", "struct", "namespace"):
                        name = tag.get("name", "")
                        path_str = tag.get("path", "")
                        line_no = tag.get("line", 0)
                        if name and len(name) > 2 and name not in _CPP_SKIP_KEYWORDS:
                            try:
                                rel = str(Path(path_str).relative_to(root))
                            except ValueError:
                                rel = path_str
                            if name not in symbols:
                                symbols[name] = {
                                    "file": rel,
                                    "line": line_no,
                                    "anchor": name,
                                    "language": "cpp",
                                    "resolution": "static",
                                }
                except json.JSONDecodeError:
                    pass
            if symbols:
                print(f"  C++: {len(symbols)} symbols via ctags")
                return symbols
        except subprocess.TimeoutExpired:
            print("  C++: ctags timed out — falling back to grep")

    # Grep fallback — parallel via ThreadPoolExecutor
    total_cpp = len(cpp_files)
    workers = os.cpu_count() or 4
    print(f"  C++: grep fallback on {total_cpp} files using {workers} threads (ctags not available)")

    grep_start = time.time()

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(_scan_one_cpp_file, f, root) for f in cpp_files]

        for file_idx, future in enumerate(futures, 1):
            rel_path, file_symbols, warning = future.result()

            print(f"  C++ [{file_idx}/{total_cpp}] indexing {rel_path}")

            if warning is not None:
                print(f"  C++ grep  WARNING: skipping {rel_path} ({warning})")

            for name, entry in file_symbols.items():
                if name not in symbols:
                    symbols[name] = entry

    grep_elapsed = time.time() - grep_start
    print(f"  C++: {len(symbols)} symbols via grep in {grep_elapsed:.1f}s")
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
