#!/usr/bin/env python3
"""Generate one histogram per modularity class counting canonical keyword frequencies.

Usage:
    python scripts/keywords_histograms_by_modularity.py path/to/graph.gexf

The script will create PNG files (one per modularity class present in the
graph and defined in the mapping) and CSV files with full keyword counts, 
grouped by synonyms.
"""
import re
import sys
import json # New import for JSON loading
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


def normalize_keyword(keyword: str) -> str:
    """Normalize a keyword to lowercase."""
    return keyword.lower()


# --- New Function to Load Synonym Data ---
def load_synonym_data(json_path: Path) -> dict:
    """Load the synonym dictionary from a JSON file."""
    if not json_path.exists():
        print(f"Error: Synonym dictionary file not found at {json_path}. Please create it.")
        return {}
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            synonym_dict = json.load(f)
        print(f"Loaded {len(synonym_dict)} synonym groups from {json_path.name}.")
        return synonym_dict
    except Exception as e:
        print(f"Error reading or processing {json_path}: {e}")
        return {}
# ----------------------------------------


# --- New Function to Create Canonical Map ---
def load_synonym_map(synonym_dict: dict) -> dict:
    """
    Creates a canonical keyword map where all synonyms point to a single
    chosen representative (the normalized name of the original dictionary key).
    The keys and values in the map are normalized (lowercase).
    """
    canonical_map = {}
    
    for key, values in synonym_dict.items():
        # The key is chosen as the canonical form for that group
        canonical_name = normalize_keyword(key)
        
        # Variants include the key itself and all listed values
        all_variants = [key] + values
        
        for variant in all_variants:
            norm_variant = normalize_keyword(variant)
            # Only set the canonical map if the variant hasn't been mapped yet.
            # This ensures that if 'A': ['B'] and 'C': ['D'] overlap, 
            # the first one encountered sets the canonical name.
            if norm_variant not in canonical_map:
                 canonical_map[norm_variant] = canonical_name
    
    return canonical_map
# ------------------------------------------


def load_category_mapping(csv_path: Path) -> dict:
    """Load the keyword -> broad categories mapping from the classification CSV."""
    if not csv_path.exists():
        print(f"Error: Category classification file not found at {csv_path}. Skipping broad category histogram.")
        return {}
    
    mapping = {}
    try:
        df = pd.read_csv(csv_path)
        for _, row in df.iterrows():
            keyword = row['keyword']
            categories_str = row['categories']
            
            # Normalize the keyword for lookup, matching the GEXF processing step
            norm_keyword = normalize_keyword(keyword)
            
            # The categories are semi-colon separated (e.g., 'A. Neuro; B. Bio')
            categories = [c.strip() for c in categories_str.split(';')]
            
            mapping[norm_keyword] = categories
    except Exception as e:
        print(f"Error reading or processing {csv_path}: {e}")
        return {}
        
    print(f"Loaded {len(mapping)} classified keywords from {csv_path.name}.")
    return mapping


def make_histograms(gexf_path: Path, out_dir: Path, top_n: int = 30):
    G = nx.read_gexf(gexf_path)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Load Synonym Data and Create Map
    synonym_dict_path =  Path('embedding_keywords')/"keyword_synonyms_0.99_with_transitivity.json"
    synonym_data = load_synonym_data(synonym_dict_path)
    if not synonym_data:
        print("Cannot proceed without synonym data.")
        return
    synonym_map = load_synonym_map(synonym_data)
    print(f"Created canonical map for {len(synonym_map)} unique keyword variants.")
    
    # 2. Load the broad category mapping
    category_csv_path = Path("keyword_classification_25_categories.csv")
    category_mapping = load_category_mapping(category_csv_path)

    attr = detect_modularity_attribute(G)
    if not attr:
        print("Could not detect a modularity/community attribute in nodes.")
        return

    print(f"Using modularity attribute: '{attr}'")

    # Collect canonical keywords and broad categories per class
    class_canonical_keyword_counts = defaultdict(Counter) 
    class_category_counts = defaultdict(Counter)
    seen_classes = set()

    terms_not_found_in_categories = set([])

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
        
        # Process terms: normalize and find canonical form
        normalized_terms = [normalize_keyword(t) for t in terms]
        canonical_terms = []
        for term in normalized_terms:
            # Get the canonical form, falling back to the term itself if not in the synonym list
            canonical_term = synonym_map.get(term, term)
            canonical_terms.append(canonical_term)
            
            # Use the canonical term for looking up broad categories
            broad_categories = category_mapping.get(canonical_term)
            if broad_categories:
                 class_category_counts[cls_int].update(broad_categories)
            else: 
                 terms_not_found_in_categories.add(canonical_term)

        # Count the canonical forms
        class_canonical_keyword_counts[cls_int].update(canonical_terms)
        
    with open("errors_in_classifying_keywords.txt", 'w') as f:
        f.write("Canonical keywords not found in 'keyword_classification_25_categories.csv':\n")
        for term in sorted(terms_not_found_in_categories):
            f.write(term)
            f.write('\n')
    
    # --- PLOTTING LOOP: Canonical Keywords (Synonym Groups) ---
    print("\n--- Generating Canonical Keyword Histograms (Synonym Groups) ---")
    for cls, meta in MODULARITY_META.items():
        if cls not in seen_classes:
            print(f"Class {cls} not present in graph, skipping")
            continue

        counts = class_canonical_keyword_counts.get(cls, Counter())
        if not counts:
            print(f"No canonical keywords found for class {cls}, skipping plot")
            continue

        # Save full counts to CSV
        csv_path = out_dir / f"canonical_keywords_counts_mod_{cls}_{sanitize_filename(meta['label'])}.csv" 
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
        plt.xlabel('Frequency (Synonyms Grouped)') 
        plt.title(meta.get('displaylabel', meta.get('label', f'Modularity {cls}')) + " (Canonical Keywords)")
        plt.tight_layout()

        png_path = out_dir / f"canonical_keywords_hist_mod_{cls}_{sanitize_filename(meta['label'])}.png"
        plt.savefig(png_path, dpi=150)
        plt.close()

        print(f"Saved canonical histogram and CSV for class {cls}: {png_path}, {csv_path}")

    # --- PLOTTING LOOP: Broad Categories (Remains the same) ---
    print("\n--- Generating Broad Category Histograms ---")
    for cls, meta in MODULARITY_META.items():
        if cls not in seen_classes:
            continue

        counts = class_category_counts.get(cls, Counter())
        if not counts:
            print(f"No broad categories found for class {cls}, skipping plot")
            continue

        # Save full counts to CSV
        csv_path = out_dir / f"categories_counts_mod_{cls}_{sanitize_filename(meta['label'])}.csv"
        df = pd.DataFrame(counts.most_common(), columns=["category", "count"]) 
        df.to_csv(csv_path, index=False)

        # Plot top N 
        top = df.head(top_n)
        labels = top['category'].tolist()[::-1]
        values = top['count'].tolist()[::-1]

        plt.figure(figsize=(10, max(4, len(labels) * 0.25)))
        color = meta.get('color', '#999999')
        plt.barh(labels, values, color=color)
        plt.xlabel('Frequency (Total Keywords Classified into Category)')
        plt.title(meta.get('displaylabel', meta.get('label', f'Modularity {cls}')) + " (Broad Categories)")
        plt.tight_layout()

        png_path = out_dir / f"categories_hist_mod_{cls}_{sanitize_filename(meta['label'])}.png"
        plt.savefig(png_path, dpi=150)
        plt.close()

        print(f"Saved broad category histogram and CSV for class {cls}: {png_path}, {csv_path}")


    # Handle unmapped classes (Modified to include both canonical and broad category saving)
    unmapped = [c for c in seen_classes if c not in MODULARITY_META]
    for cls in unmapped:
      # 1. Canonical Keywords
      counts_kw = class_canonical_keyword_counts.get(cls, Counter())
      if counts_kw:
          label = f"Modularity_{cls}"
          csv_path = out_dir / f"canonical_keywords_counts_mod_{cls}_{sanitize_filename(label)}.csv"
          df = pd.DataFrame(counts_kw.most_common(), columns=["keyword", "count"]) 
          df["keyword"] = df["keyword"].str.title()
          df.to_csv(csv_path, index=False)
          # Plotting logic for unmapped class           
      # 2. Broad Categories
      counts_cat = class_category_counts.get(cls, Counter())
      if counts_cat:
          label = f"Modularity_{cls}"
          csv_path = out_dir / f"categories_counts_mod_{cls}_{sanitize_filename(label)}.csv"
          df = pd.DataFrame(counts_cat.most_common(), columns=["category", "count"]) 
          df.to_csv(csv_path, index=False)
          # Plotting logic for unmapped class

    # Generate QA report: all unique CANONICAL keywords processed
    all_keywords = set()
    for counts in class_canonical_keyword_counts.values():
        all_keywords.update(counts.keys())

    all_keywords_sorted = sorted(all_keywords)
    qa_path = out_dir / "all_canonical_keywords_processed.txt"
    with open(qa_path, 'w') as f:
        f.write(f"Total unique CANONICAL keywords processed: {len(all_keywords_sorted)}\n")
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
    
    # Check for required files
    if not Path("keyword_classification_25_categories.csv").exists():
        print("Error: Required classification file 'keyword_classification_25_categories.csv' not found.")
        return 1
        
    if not  Path('embedding_keywords',"keyword_synonyms_0.99_with_transitivity.json").exists(): # Check for the new JSON file
        print("Error: Required synonym dictionary file 'synonym_dict.json' not found.")
        return 1
        
    # --- Execute the histogram generation ---
    make_histograms(gexf_path, out_dir)
    return 0


if __name__ == '__main__':
    # Your original main execution block, modified for the current environment.
    # To run this script, you would execute it with the path to your GEXF file.
    raise SystemExit(main(sys.argv))
    print("\nScript prepared! This code is now ready to be run in your environment.")
    print("Execute it with the path to your GEXF graph file as the first argument (e.g., python script.py my_graph.gexf).")