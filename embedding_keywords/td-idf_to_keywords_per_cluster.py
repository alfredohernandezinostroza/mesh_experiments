# td-idf_per_cluster_claude.py
import re
import pandas as pd
import numpy as np
import networkx as nx
from pathlib import Path
import json 
from collections import defaultdict, Counter
from sklearn.feature_extraction.text import TfidfVectorizer
import matplotlib.pyplot as plt

SYNONYMS_THRESHOLD = 0.99
OUT_DIR = Path(f"td-idf_results-per-cluster-{SYNONYMS_THRESHOLD}-claude-only-cluster-mean-top-3")
OUT_DIR.mkdir(exist_ok=True)

MODULARITY_META = {
    2: {"displaylabel": "Basic: Adaptation", "label": "Basic: Adaptation", "color": "#9A9CFF"},
    7: {"displaylabel": "Applied: Feedback and\ntraining scheduling", 
        "label": "Applied: Feedback and\ntraining scheduling", "color": "#FF891B"},
    12: {"displaylabel": "Cognitive Approach", "label": "Cognitive Approach", "color": "#FF6587"},
    15: {"displaylabel": "Applied: Motivation\nand Attention", 
         "label": "Applied: Motivation\nand Attention", "color": "#FC001C"},
    11: {"displaylabel": "Basic: Sequence Learning", 
         "label": "Basic: Sequence Learning", "color": "#0018FF"},
    6: {"displaylabel": "Basic: Motor Cortex", "label": "Basic: Motor Cortex", "color": "#54D3FF"},
    5: {"displaylabel": "Basic: Basal Ganglia", "label": "Basic: Basal Ganglia", "color": "#32AC7C"},
    1: {"displaylabel": "Basic: Cerebellum", "label": "Basic: Cerebellum", "color": "#00A50F"},
    10: {"displaylabel": "Nameless cluster", "label": "Nameless cluster", "color": "#B6D315"},
}

def normalize_keyword(keyword: str) -> str:
    """Normalize a keyword to lowercase."""
    return keyword.lower()

def split_keywords(keywords_value: str):
    """Split a keywords string into individual keywords."""
    if keywords_value is None or pd.isna(keywords_value):
        return []
    s = str(keywords_value).strip()
    if not s:
        return []
    
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
            part = ''.join(current).strip()
            if part:
                parts.append(part)
            current = []
        else:
            current.append(char)
    
    if current:
        part = ''.join(current).strip()
        if part:
            parts.append(part)
    
    return parts

def load_synonym_data(json_path: Path) -> dict:
    """Load the synonym dictionary from a JSON file."""
    if not json_path.exists():
        print(f"Error: Synonym dictionary file not found at {json_path}")
        return {}
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            synonym_dict = json.load(f)
        print(f"Loaded {len(synonym_dict)} synonym groups from {json_path.name}.")
        return synonym_dict
    except Exception as e:
        print(f"Error reading {json_path}: {e}")
        return {}

def load_synonym_map(synonym_dict: dict) -> dict:
    """
    Creates a canonical keyword map with better handling of circular references.
    Chooses the shortest term as canonical to prefer simpler forms.
    """
    canonical_map = {}
    
    # First pass: identify all unique terms and group them
    term_groups = {}
    for key, values in synonym_dict.items():
        all_variants = [key] + values
        # Normalize all variants
        norm_variants = [normalize_keyword(v) for v in all_variants]
        
        # Find shortest normalized form as canonical
        canonical = min(norm_variants, key=len)
        
        for norm_variant in norm_variants:
            if norm_variant not in canonical_map:
                canonical_map[norm_variant] = canonical
            elif canonical_map[norm_variant] != canonical:
                # Handle conflicts: keep the shorter canonical form
                existing = canonical_map[norm_variant]
                if len(canonical) < len(existing):
                    canonical_map[norm_variant] = canonical
    
    return canonical_map

def calculate_canonical_tfidf(gexf_file: str, synonym_dict_path: Path):
    """
    Calculate TF-IDF scores at the paper level, then aggregate by cluster.
    """
    # 1. Load Data
    print(f"Reading GEXF file: {gexf_file}")
    G = nx.read_gexf(gexf_file)
    keywords = nx.get_node_attributes(G, "keywords")
    modularity_classes = nx.get_node_attributes(G, "modularity_class")
    
    data_list = []
    for node_id in G.nodes():
        data_list.append({
            'ID_String': node_id,
            'Keywords': keywords.get(node_id),
            'Modularity_class': modularity_classes.get(node_id)
        })
    df = pd.DataFrame(data_list)
    # Filtering
    df = df.drop(df[df['Keywords'].isin(["Unknown keywords"])].index)
    df = df[df["Modularity_class"].isin(MODULARITY_META)]
    df = df.dropna().reset_index(drop=True)
    
    print(f"Loaded {len(df)} papers from GEXF")
    
    # 2. Load Synonym Map
    print(f"Loading synonym data from: {synonym_dict_path}")
    synonym_data = load_synonym_data(synonym_dict_path)
    synonym_map = load_synonym_map(synonym_data)
    
    # 3. Build Paper-Level Corpus (EACH PAPER IS A DOCUMENT)
    print("Building paper-level corpus with canonical keywords...")
    paper_corpus = []
    paper_clusters = []
    qa_log = {}
    all_canonical_keywords = set()
    
    for idx, row in df.iterrows():
        raw_keywords_str = row['Keywords']
        modularity_class = row['Modularity_class']
        
        terms = split_keywords(raw_keywords_str)
        canonical_terms = []
        
        for raw_term in terms:
            norm_term = normalize_keyword(raw_term)
            canonical_term = synonym_map.get(norm_term, norm_term)
            canonical_terms.append(canonical_term)
            all_canonical_keywords.add(canonical_term)
            
            # QA Logging
            if raw_term not in qa_log:
                qa_log[raw_term] = canonical_term
            elif qa_log[raw_term] != canonical_term:
                print(f"Warning: Inconsistent mapping for '{raw_term}': "
                      f"'{qa_log[raw_term]}' vs '{canonical_term}'")
        
        # Each paper becomes ONE document (tab-separated canonical keywords)
        paper_doc = "\t".join(canonical_terms)
        paper_corpus.append(paper_doc)
        paper_clusters.append(modularity_class)
    
    print(f"Created corpus of {len(paper_corpus)} paper documents")
    
    # 4. Save QA Logs
    qa_log_path = OUT_DIR / "qa_canonical_keyword_mapping.json"
    with open(qa_log_path, 'w', encoding='utf-8') as f:
        json.dump(dict(sorted(qa_log.items())), f, indent=4, ensure_ascii=False)
    print(f"Saved QA log: {len(qa_log)} unique raw keywords")
    
    qa_path = OUT_DIR / "all_canonical_keywords_processed.txt"
    with open(qa_path, 'w') as f:
        f.write(f"Total unique CANONICAL keywords: {len(all_canonical_keywords)}\n")
        f.write("=" * 80 + "\n\n")
        for kw in sorted(all_canonical_keywords):
            f.write(f"{kw.title()}\n")
    print(f"Saved canonical keywords list: {len(all_canonical_keywords)} keywords")
    
    # 5. Calculate TF-IDF at Paper Level
    print("\nCalculating TF-IDF at paper level...")
    vectorizer = TfidfVectorizer(
        tokenizer=lambda x: x.split('\t'),
        token_pattern=None,
        lowercase=False
    )
    
    X = vectorizer.fit_transform(paper_corpus)
    feature_names = vectorizer.get_feature_names_out()
    print(f"TF-IDF matrix shape: {X.shape} (papers x keywords)")
    print(f"Total unique canonical keywords in corpus: {len(feature_names)}")
    
    # 6. Aggregate TF-IDF Scores by Cluster
    print("\nAggregating TF-IDF scores by cluster...")
    df['cluster'] = paper_clusters
    
    cluster_tfidf = {}
    for cluster_id in df['cluster'].unique():
        # Get indices of papers in this cluster
        cluster_mask = df['cluster'] == cluster_id
        cluster_indices = df[cluster_mask].index.tolist()
        
        # mean TF-IDF scores across all papers in cluster
        cluster_vector = X[cluster_indices].mean(axis=0).A1
        cluster_tfidf[cluster_id] = cluster_vector
    
    # Convert to matrix format (clusters x keywords)
    cluster_ids = sorted(cluster_tfidf.keys())
    X_clustered = np.vstack([cluster_tfidf[cid] for cid in cluster_ids])
    
    print(f"Aggregated to {len(cluster_ids)} clusters")
    
    return X_clustered, vectorizer, cluster_ids

def sanitize_filename(name):
    """Sanitizes a string for use as a filename."""
    name = str(name).replace('\n', ' ')
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    return re.sub(r'\s+', '_', name).strip()

def save_results(X, vectorizer, cluster_ids, MODULARITY_META, top_n=20):
    """
    Save TF-IDF results per cluster with histograms.
    """
    print("\n--- Generating TF-IDF Histograms and CSVs ---")
    
    feature_names = vectorizer.get_feature_names_out()
    
    for i, cluster_id in enumerate(cluster_ids):
        meta = MODULARITY_META.get(cluster_id, {})
        display_label = meta.get('displaylabel', f"Cluster {cluster_id}")
        plot_color = meta.get('color', '#1f77b4')
        
        # Get scores for this cluster
        cluster_vector = X[i]
        scores = pd.Series(cluster_vector, index=feature_names)
        scores = scores[scores > 0].sort_values(ascending=False)
        
        # Save CSV
        file_label = sanitize_filename(meta.get('label', f'{cluster_id}'))
        csv_path = OUT_DIR / f"cluster_{cluster_id}_{file_label}_tfidf_scores.csv"
        
        df_output = pd.DataFrame({
            "canonical_keyword": scores.index,
            "tfidf_score": scores.values
        })
        df_output["canonical_keyword"] = df_output["canonical_keyword"].str.title()
        df_output.to_csv(csv_path, index=False)
        print(f"Saved CSV for {display_label}: {csv_path.name}")
        
        # Create Histogram
        top = df_output.head(top_n)
        if top.empty:
            print(f"No scores for {display_label}, skipping plot")
            continue
        
        labels = top['canonical_keyword'].tolist()[::-1]
        values = top['tfidf_score'].tolist()[::-1]
        
        plt.figure(figsize=(10, max(4, len(labels) * 0.35)))
        plt.barh(labels, values, color=plot_color)
        plt.xlabel('TF-IDF Score (Mean Across Papers)') # Note: Updated label for clarity
        plt.title(f"{display_label}\nTop {top_n} Keywords", loc='left')
        plt.tight_layout()
        
        png_path = OUT_DIR / f"cluster_{cluster_id}_{file_label}_tfidf_histogram.png"
        plt.savefig(png_path, dpi=150)
        plt.close()
        print(f"Saved histogram: {png_path.name}")
    
    # Return the aggregated top scores for the combined plot
    return _aggregate_top_scores(X, vectorizer, cluster_ids, MODULARITY_META, top_n=3)


def _aggregate_top_scores(X, vectorizer, cluster_ids, MODULARITY_META, top_n=3):
    """
    Helper function to aggregate the top N scores and their metadata for all clusters.
    """
    feature_names = vectorizer.get_feature_names_out()
    combined_scores = []

    for i, cluster_id in enumerate(cluster_ids):
        meta = MODULARITY_META.get(cluster_id, {})
        display_label = meta.get('displaylabel', f"Cluster {cluster_id}")
        plot_color = meta.get('color', '#1f77b4')

        # Get scores for this cluster
        cluster_vector = X[i]
        scores = pd.Series(cluster_vector, index=feature_names)
        scores = scores[scores > 0].sort_values(ascending=False)
        
        # Get top N scores
        top_n_scores = scores.head(top_n)

        for rank, (keyword, score) in enumerate(top_n_scores.items()):
            combined_scores.append({
                'cluster_id': cluster_id,
                'cluster_label': display_label.replace('\n', ' '),
                'cluster_color': plot_color,
                'keyword': keyword.title(),
                'score': score,
                'rank': rank + 1
            })
            
    return combined_scores


def plot_top_three_scores_combined(combined_scores_data, MODULARITY_META):
    """
    Plots the top 3 scores of each cluster with its respective color all in one plot.
    """
    if not combined_scores_data:
        print("No combined scores data to plot.")
        return

    # Create a DataFrame for easier manipulation and sorting
    df_combined = pd.DataFrame(combined_scores_data)
    
    # Sort by cluster label (for grouping) and then by score (for order within group)
    df_combined['sort_label'] = df_combined['cluster_label'].str.split(':').str[-1].str.strip() # Sort by the second part of the label
    df_combined = df_combined.sort_values(by=['sort_label', 'score'], ascending=[False, True])
    df_combined = df_combined.drop(columns=['sort_label'])

    # Create the label for the Y-axis: "Keyword (Cluster Label)"
    df_combined['plot_label'] = df_combined.apply(
        lambda row: f"{row['keyword']} ({row['cluster_label']})", axis=1
    )
    
    labels = df_combined['plot_label'].tolist()
    values = df_combined['score'].tolist()
    colors = df_combined['cluster_color'].tolist()
    
    # Use cluster labels for the legend
    legend_handles = [
        plt.Rectangle((0, 0), 1, 1, fc=meta['color'])
        for cluster_id, meta in sorted(MODULARITY_META.items())
        if cluster_id in df_combined['cluster_id'].unique()
    ]
    legend_labels = [
        meta['displaylabel'].replace('\n', ' ')
        for cluster_id, meta in sorted(MODULARITY_META.items())
        if cluster_id in df_combined['cluster_id'].unique()
    ]
    
    # Plotting
    plt.figure(figsize=(12, max(6, len(labels) * 0.4)))
    plt.barh(labels, values, color=colors)
    
    plt.xlabel('TF-IDF Score (Mean Across Papers)')
    plt.title('Top 3 Canonical Keywords by Cluster', loc='left')
    
    # Add legend
    plt.legend(legend_handles, legend_labels, title="Cluster", loc='lower right', framealpha=0.8)
    
    plt.tight_layout()
    
    png_path = OUT_DIR / "combined_top_3_tfidf_histogram.png"
    plt.savefig(png_path, dpi=150)
    plt.close()
    print(f"\nSaved combined top 3 histogram: {png_path.name}")


# Main execution
gexf_file = "filtered_with_transferred_mesh_fixed_fix_commas.gexf"
synonym_dict_path = Path('embedding_keywords') / f"keyword_synonyms_{SYNONYMS_THRESHOLD}_with_transitivity.json"

# Calculate TF-IDF scores
X_matrix, vectorizer_model, cluster_list = calculate_canonical_tfidf(gexf_file, synonym_dict_path)

# Save individual cluster results and get aggregated top 3 scores
top_three_scores = save_results(X_matrix, vectorizer_model, cluster_list, MODULARITY_META)

# Plot the combined top 3 scores
plot_top_three_scores_combined(top_three_scores, MODULARITY_META)

print("\nScript execution successful!")