"""
Build concept dependency graph from Taiwan 12-Year Math Curriculum data.

Extracts relationships between learning content items by analyzing
explicit cross-references in remarks/description/title fields (e.g., "N-2-3", "同S-1-1").

Output: docs/data/concept_graph.json

Usage:
    python scripts/build_graph.py
    (run from the project root directory)
"""

import json
import os
import re
from datetime import date

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, "docs", "data")
CONTENT_PATH = os.path.join(DATA_DIR, "learning_content.json")
OUTPUT_PATH = os.path.join(DATA_DIR, "concept_graph.json")
VERSION_FILE = os.path.join(PROJECT_ROOT, "VERSION")

# Pattern to match learning content codes like N-5-3, N-11A-1, F-12甲-3
CODE_PATTERN = re.compile(r"[A-Z]-\d+[AB甲乙]?-\d+")

# Patterns that indicate "same topic" across domains
SAME_TOPIC_KEYWORDS = ["同"]


def read_version():
    try:
        with open(VERSION_FILE, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return "0.0.0"


def load_content():
    with open(CONTENT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["items"]


def parse_grade(code):
    """Extract grade number from a code like N-5-3 -> 5, N-11A-1 -> 11."""
    m = re.match(r"^[A-Z]-(\d+)", code)
    return int(m.group(1)) if m else None


def parse_domain(code):
    """Extract domain letter from a code like N-5-3 -> N."""
    return code[0] if code else None


def parse_sequence(code):
    """Extract sequence number from a code like N-5-3 -> 3."""
    m = re.match(r"^[A-Z]-\d+[AB甲乙]?-(\d+)$", code)
    return int(m.group(1)) if m else None


def extract_explicit_edges(items):
    """Extract edges from explicit cross-references in text fields."""
    edges = []
    code_set = {item["code"] for item in items}
    items_by_code = {item["code"]: item for item in items}

    for item in items:
        source = item["code"]
        source_grade = item["grade"]

        # Combine all text fields to search for references
        title = item.get("title", "")
        description = item.get("description", "")
        remarks = item.get("remarks", "")

        # Find all referenced codes in each field
        for field_name, text in [("title", title), ("description", description), ("remarks", remarks)]:
            if not text:
                continue

            referenced_codes = CODE_PATTERN.findall(text)
            for target in referenced_codes:
                if target == source or target not in code_set:
                    continue

                # Determine relationship type based on context
                rel_type = classify_reference(source, target, text, field_name, items_by_code)

                edges.append({
                    "source": source,
                    "target": target,
                    "type": rel_type,
                    "field": field_name,
                    "evidence": extract_evidence(text, target),
                })

    return deduplicate_edges(edges)


def classify_reference(source, target, text, field_name, items_by_code):
    """Classify the type of relationship between source and target.

    'same_topic' is only assigned when '同' appears in the title or description
    (meaning the two codes represent the same topic across domains).
    Remarks that say '同X備註' are just cross-referencing teaching notes,
    and are classified as 'reference'.
    """
    if field_name in ("title", "description"):
        same_pattern = re.compile(r"同\s*" + re.escape(target))
        if same_pattern.search(text):
            return "same_topic"

    return "reference"


def extract_evidence(text, target_code):
    """Extract a short snippet around the target code reference for context."""
    idx = text.find(target_code)
    if idx == -1:
        return ""
    start = max(0, idx - 20)
    end = min(len(text), idx + len(target_code) + 20)
    snippet = text[start:end]
    if start > 0:
        snippet = "…" + snippet
    if end < len(text):
        snippet = snippet + "…"
    return snippet


def deduplicate_edges(edges):
    """Remove duplicate edges, keeping the most informative one.

    For same_topic edges, merge bidirectional pairs (A→B + B→A) into a single
    undirected edge using the alphabetically smaller code as source.
    """
    seen = {}
    for edge in edges:
        if edge["type"] == "same_topic":
            # Normalize to alphabetical order so A→B and B→A become the same key
            a, b = sorted([edge["source"], edge["target"]])
            key = (a, b, "same_topic")
        else:
            key = (edge["source"], edge["target"])

        if key not in seen:
            if edge["type"] == "same_topic":
                edge = {**edge, "source": a, "target": b, "directed": False}
            seen[key] = edge
        else:
            existing = seen[key]
            priority = {"same_topic": 0, "reference": 1}
            if priority.get(edge["type"], 99) < priority.get(existing["type"], 99):
                seen[key] = edge
    return list(seen.values())


def build_nodes(items):
    """Build node list from learning content items."""
    nodes = []
    for item in items:
        node = {
            "code": item["code"],
            "title": item["title"],
            "domain": item["domain"],
            "domain_name": item["domain_name"],
            "grade": item["grade"],
            "stage": item["stage"],
            "stage_name": item["stage_name"],
            "sequence": item["sequence"],
        }
        if "class_type" in item:
            node["class_type"] = item["class_type"]
        nodes.append(node)
    return nodes


def compute_stats(nodes, edges):
    """Compute summary statistics for the graph."""
    edge_types = {}
    for e in edges:
        t = e["type"]
        edge_types[t] = edge_types.get(t, 0) + 1

    # Nodes with no incoming edges
    targets = {e["target"] for e in edges}
    sources = {e["source"] for e in edges}
    all_codes = {n["code"] for n in nodes}
    root_nodes = sorted(all_codes - targets)

    # Nodes with no outgoing edges (terminal concepts)
    terminal_nodes = sorted(all_codes - sources)

    return {
        "total_nodes": len(nodes),
        "total_edges": len(edges),
        "edges_by_type": edge_types,
        "root_concepts_count": len(root_nodes),
        "terminal_concepts_count": len(terminal_nodes),
    }


def main():
    items = load_content()
    print(f"Loaded {len(items)} learning content items")

    # Build nodes
    nodes = build_nodes(items)

    # Extract edges from explicit cross-references only
    explicit_edges = extract_explicit_edges(items)
    print(f"Explicit cross-reference edges: {len(explicit_edges)}")

    all_edges = deduplicate_edges(explicit_edges)
    print(f"Total edges after dedup: {len(all_edges)}")

    # Compute stats
    stats = compute_stats(nodes, all_edges)

    # Build output
    version = read_version()
    output = {
        "version": version,
        "source": "十二年國民基本教育課程綱要—數學領域",
        "source_url": "https://www.k12ea.gov.tw",
        "data_type": "concept_graph",
        "generated_at": date.today().isoformat(),
        "description": "數學概念先備知識圖譜。節點為學習內容條目，邊為概念間的關係。",
        "edge_types": {
            "same_topic": "同一主題跨領域出現（如 N-1-5 與 S-1-1 皆為「長度」）",
            "reference": "課綱文字中的交叉引用（附原文，語意待人工標註）",
        },
        "stats": stats,
        "nodes": nodes,
        "edges": all_edges,
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\nOutput written to {OUTPUT_PATH}")
    print(f"\n--- Stats ---")
    print(f"Nodes: {stats['total_nodes']}")
    print(f"Edges: {stats['total_edges']}")
    for etype, count in sorted(stats["edges_by_type"].items()):
        print(f"  {etype}: {count}")
    print(f"Root concepts (no prerequisites): {stats['root_concepts_count']}")
    print(f"Terminal concepts (no successors): {stats['terminal_concepts_count']}")


if __name__ == "__main__":
    main()
