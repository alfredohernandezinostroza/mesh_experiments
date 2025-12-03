#!/usr/bin/env python3
"""Generate one histogram per modularity class counting MESH term frequencies.

Usage:
    python scripts/mesh_histograms_by_modularity.py path/to/graph.gexf

The script will create PNG files (one per modularity class present in the
graph and defined in the mapping) and CSV files with full term counts.
"""
import re
import sys
from pathlib import Path
from collections import Counter, defaultdict

import networkx as nx
import pandas as pd
import matplotlib.pyplot as plt


# Mapping provided by the user: keys are modularity class ids (ints)
MODULARITY_META = {
    2: {
        "displaylabel": "Basic: Adaptation",
        "label": "Basic: Adaptation",
        "color": "#9A9CFF",
    },
    7: {
        "displaylabel": "Applied: Feedback and\ntraining scheduling",
        "label": "Applied: Feedback and\ntraining scheduling",
        "color": "#FF891B",
    },
    12: {
        "displaylabel": "Cognitive Approach",
        "label": "Cognitive Approach",
        "color": "#FF6587",
    },
    15: {
        "displaylabel": "Applied: Motivation\nand Attention",
        "label": "Applied: Motivation\nand Attention",
        "color": "#FC001C",
    },
    11: {
        "displaylabel": "Basic: Sequence Learning",
        "label": "Basic: Sequence Learning",
        "color": "#0018FF",
    },
    6: {
        "displaylabel": "Basic: Motor Cortex",
        "label": "Basic: Motor Cortex",
        "color": "#54D3FF",
    },
    5: {
        "displaylabel": "Basic: Basal Ganglia",
        "label": "Basic: Basal Ganglia",
        "color": "#32AC7C",
    },
    1: {
        "displaylabel": "Basic: Cerebellum",
        "label": "Basic: Cerebellum",
        "color": "#00A50F",
    },
}


def sanitize_filename(s: str) -> str:
    """Return a filename-safe version of string s."""
    s = s.replace("\n", " ")
    s = re.sub(r"[^A-Za-z0-9 _-]", "", s)
    s = re.sub(r"\s+", "_", s).strip("_ ")
    return s


def detect_modularity_attribute(G: nx.Graph):
    """Try to detect which node attribute stores modularity/community ids.

    Returns attribute name (string) or None.
    """
    if G.number_of_nodes() == 0:
        return None
    sample = next(iter(G.nodes(data=True)))[1]
    candidates = [
        "modularity_class",
        "modularity class",
        "community",
        "mod",
        "partition",
        "community_id",
        "communityId",
    ]
    for c in candidates:
        if c in sample:
            return c
    # fallback: try any integer-like attribute among node attrs
    for k, v in sample.items():
        if isinstance(v, (int,)):
            return k
        # sometimes modularity is stored as stringified int
        if isinstance(v, str) and v.isdigit():
            return k
    return None


def split_mesh_terms(mesh_value: str):
    """Split a mesh string into individual terms. Returns list of cleaned terms.
    
    Prefers semicolon splitting if present, otherwise falls back to comma splitting.
    """
    if mesh_value is None:
        return []
    if pd.isna(mesh_value):
        return []
    s = str(mesh_value).strip()
    if not s:
        return []
    # If semicolon is present, split by semicolon; otherwise split by comma
    if ';' in s:
        parts = [p.strip() for p in s.split(';')]
    else:
        parts = [p.strip() for p in s.split(',')]
    parts = [p for p in parts if p]
    return parts


def make_histograms(gexf_path: Path, out_dir: Path, top_n: int = 30, generate_plots: bool = True):
    G = nx.read_gexf(gexf_path)
    out_dir.mkdir(parents=True, exist_ok=True)

    attr = detect_modularity_attribute(G)
    if not attr:
        print("Could not detect a modularity/community attribute in nodes.\n"
              "Please ensure your GEXF contains a community attribute (e.g. 'modularity_class').")
        return

    print(f"Using modularity attribute: '{attr}'")

    # Collect meshes per class
    class_mesh_counts = defaultdict(Counter)
    seen_classes = set()

    for _, data in G.nodes(data=True):
        cls = data.get(attr)
        if cls is None:
            continue
        # normalize class to int when possible
        try:
            cls_int = int(cls)
        except Exception:
            cls_int = cls
        seen_classes.add(cls_int)
        mesh = data.get("mesh") or data.get("MESH") or data.get("Mesh")
        terms = split_mesh_terms(mesh)
        class_mesh_counts[cls_int].update(terms)

    if generate_plots:
        # Iterate over modularity mapping (only those present in the graph)
        for cls, meta in MODULARITY_META.items():
            if cls not in seen_classes:
                print(f"Class {cls} not present in graph, skipping")
                continue

            counts = class_mesh_counts.get(cls, Counter())
            if not counts:
                print(f"No mesh terms found for class {cls}, skipping plot")
                continue

            # Save full counts to CSV
            csv_path = out_dir / f"mesh_counts_mod_{cls}_{sanitize_filename(meta['label'])}.csv"
            df = pd.DataFrame(counts.most_common(), columns=["mesh_term", "count"]) 
            df.to_csv(csv_path, index=False)

            # Plot top N
            top = df.head(top_n)
            labels = top['mesh_term'].tolist()[::-1]
            values = top['count'].tolist()[::-1]

            plt.figure(figsize=(10, max(4, len(labels) * 0.25)))
            color = meta.get('color', '#333333')
            plt.barh(labels, values, color=color)
            plt.xlabel('Frequency')
            plt.title(meta.get('displaylabel', meta.get('label', f'Modularity {cls}')))
            plt.tight_layout()

            png_path = out_dir / f"mesh_hist_mod_{cls}_{sanitize_filename(meta['label'])}.png"
            plt.savefig(png_path, dpi=150)
            plt.close()

            print(f"Saved histogram and CSV for class {cls}: {png_path}, {csv_path}")

        # Handle classes present in graph but not in mapping: create files using class id
        unmapped = [c for c in seen_classes if c not in MODULARITY_META]
        for cls in unmapped:
            counts = class_mesh_counts.get(cls, Counter())
            if not counts:
                continue
            label = f"Modularity_{cls}"
            csv_path = out_dir / f"mesh_counts_mod_{cls}_{sanitize_filename(label)}.csv"
            df = pd.DataFrame(counts.most_common(), columns=["mesh_term", "count"]) 
            df.to_csv(csv_path, index=False)
            top = df.head(top_n)
            labels = top['mesh_term'].tolist()[::-1]
            values = top['count'].tolist()[::-1]
            plt.figure(figsize=(10, max(4, len(labels) * 0.25)))
            plt.barh(labels, values, color="#666666")
            plt.xlabel('Frequency')
            plt.title(label)
            plt.tight_layout()
            png_path = out_dir / f"mesh_hist_mod_{cls}_{sanitize_filename(label)}.png"
            plt.savefig(png_path, dpi=150)
            plt.close()
            print(f"Saved histogram and CSV for unmapped class {cls}: {png_path}, {csv_path}")
    else:
        print("Skipping histogram and CSV generation (--no-plots flag used)")
    
    # Generate QA report: all unique mesh terms processed
    all_terms = set()
    for counts in class_mesh_counts.values():
        all_terms.update(counts.keys())
    
    all_terms_sorted = sorted(all_terms)
    qa_path = out_dir / "all_mesh_terms_processed.txt"
    with open(qa_path, 'w') as f:
        f.write(f"Total unique MESH terms processed: {len(all_terms_sorted)}\n")
        f.write("=" * 80 + "\n\n")
        for term in all_terms_sorted:
            f.write(f"{term}\n")
    print(f"\nQA report saved to: {qa_path}")


def main(argv):
    if len(argv) < 2:
        print("Usage: python scripts/mesh_histograms_by_modularity.py path/to/graph.gexf [out_dir] [--no-plots]")
        print("\nOptions:")
        print("  --no-plots    Skip histogram and CSV generation (QA report will still be created)")
        return 1
    gexf_path = Path(argv[1])
    if not gexf_path.exists():
        print(f"GEXF file not found: {gexf_path}")
        return 1
    
    # Parse arguments
    generate_plots = "--no-plots" not in argv
    out_dir_idx = 2
    if generate_plots and len(argv) > 2:
        out_dir = Path(argv[out_dir_idx])
    elif not generate_plots and len(argv) > 2:
        # Check if argv[2] is a flag or directory
        out_dir = Path(argv[out_dir_idx]) if argv[out_dir_idx] != "--no-plots" else gexf_path.parent / "mesh_histograms"
    else:
        out_dir = gexf_path.parent / "mesh_histograms"
    
    make_histograms(gexf_path, out_dir, generate_plots=generate_plots)
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
