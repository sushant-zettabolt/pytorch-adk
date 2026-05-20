---
name: build
description: "PyTorch build system: setup.py develop, CMake integration, and classifying build failures. Use for questions about building PyTorch from source or adding files to the build."
validated-at: 70d99e998b4
---

# Build Skill
## Build System Overview
PyTorch uses CMake + setup.py (+ setuptools). The Python entry point is:
```bash
python setup.py develop   # editable install (preferred for dev)
python setup.py install   # full install
```

## Key Questions

**Q: What does `python setup.py develop` do?**
A: Runs CMake to build C++/CUDA extensions, then installs torch as an editable package.
`setup.py:LINE — "def main"` (citation needed at pinned commit)

**Q: How do you add a new C++ file to the build?**
A:
1. Add the file to the appropriate CMakeLists.txt
2. Run `python setup.py develop` (incremental rebuild)
`CMakeLists.txt:LINE — "add_library.*torch_cpu"` (citation needed)

**Q: How do you classify a build failure?**
A: Categories:
1. Missing CMake entry — file not listed in CMakeLists.txt
2. Missing header — #include not found
3. Linking error — symbol defined but not linked
4. CUDA compilation error — .cu file syntax error
5. Generated file edit — regenerated file differs from edited version

**Q: What is a common "generated file edit" error?**
A: Build fails with "modified generated file detected." The pre-edit-block-generated hook prevents this.

## Blast Radius
- `CMakeLists.txt` — Tier 2 (all C++ builds)
- `setup.py` — Tier 2 (entire build pipeline)
