#!/usr/bin/env python3
"""
PostToolUse hook — after any Edit: identify downstream files and show blast-radius tier.
"""

import json
import os
import sys

BLAST_RADIUS = {
    "Tier 1": [
        "aten/src/ATen/Dispatcher.h",
        "aten/src/ATen/Dispatcher.cpp",
        "c10/core/TensorImpl.h",
        "c10/core/TensorImpl.cpp",
        "c10/core/DispatchKey.h",
        "torch/csrc/autograd/python_variable.cpp",
        "aten/src/ATen/core/op_registration",
    ],
    "Tier 2": [
        "torch/csrc/autograd/engine.cpp",
        "torch/_dynamo/eval_frame.py",
        "torch/fx/graph.py",
        "torch/_inductor/compile_fx.py",
        "torch/distributed/__init__.py",
        "aten/src/ATen/native/native_functions.yaml",
        "torch/testing/_internal/common_methods_invocations.py",
        ".clang-format",
        ".pre-commit-config.yaml",
        "CMakeLists.txt",
        "setup.py",
    ],
}

def classify_tier(file_path: str) -> str:
    for tier, patterns in BLAST_RADIUS.items():
        for pattern in patterns:
            if pattern in file_path:
                return tier
    return "Tier 3"

def get_downstream_impact(file_path: str) -> list[str]:
    """Heuristic downstream impact assessment."""
    impacts = []
    if "Dispatcher" in file_path:
        impacts = ["All operator dispatch", "All backends", "Autograd", "Functionalization"]
    elif "TensorImpl" in file_path:
        impacts = ["All tensor operations", "Memory management", "Autograd graph", "CUDA transfers"]
    elif "DispatchKey" in file_path:
        impacts = ["All dispatch tables", "All backend registrations"]
    elif "engine.cpp" in file_path:
        impacts = ["All backward passes", "All gradient computations"]
    elif "_dynamo" in file_path:
        impacts = ["All torch.compile calls"]
    elif "native_functions.yaml" in file_path:
        impacts = ["All op registrations", "Dispatch table generation", "pybind11 bindings"]
    return impacts

def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return

    changed_file = data.get("file_path", "")
    if not changed_file:
        return

    tier = classify_tier(changed_file)
    impacts = get_downstream_impact(changed_file)

    print(f"\n[post-edit-impact-analysis] {changed_file}")
    print(f"Blast-radius tier: {tier}")

    if tier == "Tier 1":
        print("ACTION REQUIRED: Notify Architecture Owner before proceeding.")
        print("Run the full test suite before submitting PR.")

    if impacts:
        print(f"Downstream impact:")
        for impact in impacts:
            print(f"  - {impact}")

    if tier in ("Tier 1", "Tier 2"):
        print(f"\nRecommended tests to run before PR:")
        if "Dispatcher" in changed_file or "DispatchKey" in changed_file:
            print("  python -m pytest test/test_dispatch.py -v")
        if "TensorImpl" in changed_file:
            print("  python -m pytest test/test_tensor_creation_ops.py -v")
        if "_dynamo" in changed_file:
            print("  python -m pytest test/dynamo/ -v")

if __name__ == "__main__":
    main()
