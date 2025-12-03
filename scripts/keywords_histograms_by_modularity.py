#!/usr/bin/env python3
"""Generate one histogram per modularity class counting keyword frequencies.

Usage:
    python scripts/keywords_histograms_by_modularity.py path/to/graph.gexf

The script will create PNG files (one per modularity class present in the
graph and defined in the mapping) and CSV files with full keyword counts.
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


def split_keywords(keywords_value: str):
    """Split a keywords string into individual keywords. Returns list of cleaned keywords.
    
    Keywords are split only by commas that are NOT inside parentheses or square brackets.
    """
    if keywords_value is None:
        return []
    if pd.isna(keywords_value):
        return []
    s = str(keywords_value).strip()
    if not s:
        return []
    
    # Split by commas that are not inside parentheses or square brackets
    parts = []
    current = []
    paren_depth = 0
    bracket_depth = 0
    for char in s:
        if char == '(':
            paren_depth += 1
            current.append(char)
        elif char == ')':
            paren_depth -= 1
            current.append(char)
        elif char == '[':
            bracket_depth += 1
            current.append(char)
        elif char == ']':
            bracket_depth -= 1
            current.append(char)
        elif char == ',' and paren_depth == 0 and bracket_depth == 0:
            # this is a delimiter comma
            part = ''.join(current).strip()
            if part:
                parts.append(part)
            current = []
        else:
            current.append(char)
    
    # add remaining part
    if current:
        part = ''.join(current).strip()
        if part:
            parts.append(part)
    
    return parts


def make_histograms(gexf_path: Path, out_dir: Path, top_n: int = 30):
    G = nx.read_gexf(gexf_path)
    out_dir.mkdir(parents=True, exist_ok=True)

    attr = detect_modularity_attribute(G)
    if not attr:
        print("Could not detect a modularity/community attribute in nodes.\n"
              "Please ensure your GEXF contains a community attribute (e.g. 'modularity_class').")
        return

    print(f"Using modularity attribute: '{attr}'")

    # Collect keywords per class
    class_keyword_counts = defaultdict(Counter)
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
        keywords = data.get("keywords") or data.get("Keywords") or data.get("KEYWORDS")
        terms = split_keywords(keywords)
        # normalize keywords to lowercase for counting (case-insensitive counts)
        normalized_terms = [t.lower() for t in terms]
        class_keyword_counts[cls_int].update(normalized_terms)

    # Iterate over modularity mapping (only those present in the graph)
    for cls, meta in MODULARITY_META.items():
        if cls not in seen_classes:
            print(f"Class {cls} not present in graph, skipping")
            continue

        counts = class_keyword_counts.get(cls, Counter())
        if not counts:
            print(f"No keywords found for class {cls}, skipping plot")
            continue

        # Save full counts to CSV (format keywords in Title Case for presentation)
        csv_path = out_dir / f"keywords_counts_mod_{cls}_{sanitize_filename(meta['label'])}.csv"
        df = pd.DataFrame(counts.most_common(), columns=["keyword", "count"]) 
        df["keyword"] = df["keyword"].str.title()
        df.to_csv(csv_path, index=False)

        # Plot top N
        top = df.head(top_n)
        labels = top['keyword'].tolist()[::-1]
        values = top['count'].tolist()[::-1]

        plt.figure(figsize=(10, max(4, len(labels) * 0.25)))
        color = meta.get('color', '#333333')
        plt.barh(labels, values, color=color)
        plt.xlabel('Frequency')
        plt.title(meta.get('displaylabel', meta.get('label', f'Modularity {cls}')))
        plt.tight_layout()

        png_path = out_dir / f"keywords_hist_mod_{cls}_{sanitize_filename(meta['label'])}.png"
        plt.savefig(png_path, dpi=150)
        plt.close()

        print(f"Saved histogram and CSV for class {cls}: {png_path}, {csv_path}")

    # Handle classes present in graph but not in mapping: create files using class id
    unmapped = [c for c in seen_classes if c not in MODULARITY_META]
    for cls in unmapped:
        counts = class_keyword_counts.get(cls, Counter())
        if not counts:
            continue
        label = f"Modularity_{cls}"
        csv_path = out_dir / f"keywords_counts_mod_{cls}_{sanitize_filename(label)}.csv"
        df = pd.DataFrame(counts.most_common(), columns=["keyword", "count"]) 
        df["keyword"] = df["keyword"].str.title()
        df.to_csv(csv_path, index=False)
        top = df.head(top_n)
        labels = top['keyword'].tolist()[::-1]
        values = top['count'].tolist()[::-1]
        plt.figure(figsize=(10, max(4, len(labels) * 0.25)))
        plt.barh(labels, values, color="#666666")
        plt.xlabel('Frequency')
        plt.title(label)
        plt.tight_layout()
        png_path = out_dir / f"keywords_hist_mod_{cls}_{sanitize_filename(label)}.png"
        plt.savefig(png_path, dpi=150)
        plt.close()
        print(f"Saved histogram and CSV for unmapped class {cls}: {png_path}, {csv_path}")

    # Generate QA report: all unique keywords processed
    all_keywords = set()
    for counts in class_keyword_counts.values():
        all_keywords.update(counts.keys())

    # present QA keywords in Title Case
    all_keywords_sorted = sorted(all_keywords)
    qa_path = out_dir / "all_keywords_processed.txt"
    with open(qa_path, 'w') as f:
        f.write(f"Total unique keywords processed: {len(all_keywords_sorted)}\n")
        f.write("=" * 80 + "\n\n")
        for kw in all_keywords_sorted:
            f.write(f"{kw.title()}\n")
    print(f"\nQA report saved to: {qa_path}")


def main(argv):
    if len(argv) < 2:
        print("Usage: python scripts/keywords_histograms_by_modularity.py path/to/graph.gexf [out_dir]")
        return 1
    gexf_path = Path(argv[1])
    if not gexf_path.exists():
        print(f"GEXF file not found: {gexf_path}")
        return 1
    out_dir = Path(argv[2]) if len(argv) > 2 else gexf_path.parent / "keywords_histograms"
    make_histograms(gexf_path, out_dir)
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
