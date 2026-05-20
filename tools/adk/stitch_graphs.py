#!/usr/bin/env python3
"""
Stage 2 — Stitch Python and C++ graphs into unified_graph.graphml.

Reads:
  - python_graph.graphml  (produced by build_index.py Stage 1a)
  - cpp_graph.graphml     (produced by build_index.py Stage 1b)
  - boundary_table.json   (produced by parse_boundaries.py)

Writes:
  - unified_graph.graphml  (Python + C++ nodes, boundary edges labeled with resolution)

Usage:
    python tools/adk/stitch_graphs.py [--index-dir DIR]

GraphML format: every node has id, label, language. Every edge has source, target, resolution.
"""

import json
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


INDEX_DIR = Path(os.environ.get("INDEX_DIR", ".claude/index"))

# GraphML namespace
GRAPHML_NS = "http://graphml.graphdrawing.org/graphml"
ET.register_namespace("", GRAPHML_NS)


def load_graphml(path: Path) -> ET.Element | None:
    """Load a graphml file, return root element or None if not found."""
    if not path.exists():
        return None
    try:
        tree = ET.parse(path)
        return tree.getroot()
    except ET.ParseError as e:
        print(f"  Warning: could not parse {path}: {e}", file=sys.stderr)
        return None


def make_empty_graphml() -> ET.Element:
    root = ET.Element(f"{{{GRAPHML_NS}}}graphml")
    root.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")

    # Key declarations
    for attr_id, attr_name, attr_type, for_elem in [
        ("d0", "language", "string", "node"),
        ("d1", "label", "string", "node"),
        ("d2", "file", "string", "node"),
        ("d3", "line", "int", "node"),
        ("d4", "resolution", "string", "edge"),
        ("d5", "confidence", "double", "edge"),
        ("d6", "test_count", "int", "edge"),
    ]:
        key = ET.SubElement(root, f"{{{GRAPHML_NS}}}key")
        key.set("id", attr_id)
        key.set("attr.name", attr_name)
        key.set("attr.type", attr_type)
        key.set("for", for_elem)

    graph = ET.SubElement(root, f"{{{GRAPHML_NS}}}graph")
    graph.set("id", "G")
    graph.set("edgedefault", "directed")
    return root, graph


def add_node(graph: ET.Element, node_id: str, label: str, language: str, file: str = "", line: int = 0):
    node = ET.SubElement(graph, f"{{{GRAPHML_NS}}}node")
    node.set("id", node_id)
    for key_id, value in [("d0", language), ("d1", label), ("d2", file), ("d3", str(line))]:
        data = ET.SubElement(node, f"{{{GRAPHML_NS}}}data")
        data.set("key", key_id)
        data.text = value


def add_edge(graph: ET.Element, source: str, target: str, resolution: str = "static", confidence: float = 1.0):
    edge = ET.SubElement(graph, f"{{{GRAPHML_NS}}}edge")
    edge.set("source", source)
    edge.set("target", target)
    for key_id, value in [("d4", resolution), ("d5", str(confidence)), ("d6", "0")]:
        data = ET.SubElement(edge, f"{{{GRAPHML_NS}}}data")
        data.set("key", key_id)
        data.text = value


def stitch(python_root: ET.Element | None, cpp_root: ET.Element | None, boundary: dict) -> ET.Element:
    """Merge Python graph + C++ graph + boundary table into unified graph."""
    root, graph = make_empty_graphml()

    # Node sets (track to avoid duplicates)
    node_ids: set[str] = set()

    def merge_graph(src_root: ET.Element | None, language: str):
        if src_root is None:
            return
        for elem in src_root.iter(f"{{{GRAPHML_NS}}}node"):
            nid = elem.get("id", "")
            if nid and nid not in node_ids:
                node_ids.add(nid)
                label = ""
                for data in elem.iter(f"{{{GRAPHML_NS}}}data"):
                    if data.get("key") in ("d1", "label"):
                        label = data.text or nid
                add_node(graph, nid, label, language)

        for elem in src_root.iter(f"{{{GRAPHML_NS}}}edge"):
            src = elem.get("source", "")
            tgt = elem.get("target", "")
            if src and tgt:
                add_edge(graph, src, tgt, "static", 1.0)

    merge_graph(python_root, "python")
    merge_graph(cpp_root, "cpp")

    # Add boundary edges from boundary_table.json
    boundary_count = 0
    for py_call_site, entry in boundary.items():
        if py_call_site.startswith("_meta"):
            continue

        cpp_target = entry.get("cpp_target", "")
        resolution = entry.get("resolution", "static")
        confidence = entry.get("confidence", 1.0)

        # Ensure both nodes exist
        py_id = f"py:{py_call_site}"
        cpp_id = f"cpp:{cpp_target}"

        if py_id not in node_ids:
            node_ids.add(py_id)
            add_node(graph, py_id, py_call_site, "python")

        if cpp_id not in node_ids:
            node_ids.add(cpp_id)
            add_node(graph, cpp_id, cpp_target, "cpp")

        add_edge(graph, py_id, cpp_id, resolution, confidence)
        boundary_count += 1

    print(f"  Stitched {len(node_ids)} nodes, {boundary_count} boundary edges")
    return root


def main():
    print("Stage 2 — stitch_graphs.py")
    print(f"  Index dir: {INDEX_DIR.resolve()}")

    py_graph = load_graphml(INDEX_DIR / "python_graph.graphml")
    cpp_graph = load_graphml(INDEX_DIR / "cpp_graph.graphml")

    # Load boundary table
    boundary_path = INDEX_DIR / "boundary_table.json"
    if boundary_path.exists():
        with open(boundary_path) as f:
            boundary = json.load(f)
        print(f"  Loaded boundary_table.json ({len(boundary) - 1} entries)")
    else:
        print("  Warning: boundary_table.json not found — run parse_boundaries.py first")
        boundary = {}

    unified = stitch(py_graph, cpp_graph, boundary)

    out_path = INDEX_DIR / "unified_graph.graphml"
    tree = ET.ElementTree(unified)
    ET.indent(tree, space="  ")
    tree.write(out_path, encoding="utf-8", xml_declaration=True)
    print(f"  Written: {out_path}")

    # Count verification
    node_count = sum(1 for _ in unified.iter(f"{{{GRAPHML_NS}}}node"))
    edge_count = sum(1 for _ in unified.iter(f"{{{GRAPHML_NS}}}edge"))
    print(f"  Nodes: {node_count}  Edges: {edge_count}")

    # Gate: torch.relu→at::relu must be present with resolution:static
    relu_present = False
    for edge in unified.iter(f"{{{GRAPHML_NS}}}edge"):
        src = edge.get("source", "")
        tgt = edge.get("target", "")
        if "relu" in src.lower() and "relu" in tgt.lower():
            for data in edge.iter(f"{{{GRAPHML_NS}}}data"):
                if data.get("key") == "d4" and data.text == "static":
                    relu_present = True
    print(f"  Gate: torch.relu→at::relu with resolution:static → {'PASS' if relu_present else 'FAIL'}")
    return 0 if relu_present else 1


if __name__ == "__main__":
    sys.exit(main())
