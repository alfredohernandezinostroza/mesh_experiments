import re
import pandas as pd
import numpy as np
import networkx as nx
from pathlib import Path
import json 
from collections import defaultdict, Counter
from sklearn.feature_extraction.text import TfidfVectorizer

OUT_DIR = Path("td-idf_results")
OUT_DIR.mkdir(exist_ok=True)

def save_results(X, vectorizer, df):
    feature_names = vectorizer.get_feature_names_out()
    for i in range(X.shape[0]):
        cluster_vector = X[i].toarray().flatten()
        
        scores = pd.Series(cluster_vector, index=feature_names)
        scores = scores[scores > 0].sort_values(ascending=False)
        with open(OUT_DIR/f"cluster_{i}_histogram.csv") as file:
            file.write()
            file.write()

def normalize_keyword(keyword: str) -> str:
    """Normalize a keyword to lowercase."""
    return keyword.lower()

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
def calculate_canonical_tfidf(gexf_file: str, synonym_dict_path: Path):
    
    # 1. Load Data
    print(f"Reading GEXF file: {gexf_file}")
    G = nx.read_gexf(gexf_file)
    keywords = nx.get_node_attributes(G, "keywords")
    modularity_classes = nx.get_node_attributes(G, "modularity_class")
    data_list = []
    for node_id in G.nodes():
        data_list.append({
            'ID_String': node_id,         # Column 1
            'Keywords': keywords.get(node_id),  # Column 2 (Set/List)
            'Modularity_class': modularity_classes.get(node_id) # Column 3 (Scalar)
        })
    df = pd.DataFrame(data_list)
    df = df.dropna().reset_index()
    # 2. Load and Prepare Synonym Map
    print(f"Loading synonym data from: {synonym_dict_path}")
    synonym_data = load_synonym_data(synonym_dict_path)
    synonym_map = load_synonym_map(synonym_data)
    
    # 3. Initialize QA Log
    # Maps: Raw Term -> Canonical Term
    qa_log = {} 
    
    # 4. Rewrite Corpus using Canonical Keywords
    print("Rewriting corpus using canonical keywords...")
    canonical_corpus = {}
    all_canonical_keywords = set([])

    for raw_keywords_str, modularity_class in zip(df['Keywords'], df['Modularity_class']):
        if not canonical_corpus.get(modularity_class):
            canonical_corpus[modularity_class] = []
            
        # a. Split the raw string into individual keywords
        # Use a defaultdict here to track processing per paper
        terms = split_keywords(raw_keywords_str)
        
        # b. Normalize each term and map it to its canonical form
        canonical_terms = []
        
        for raw_term in terms:
            norm_term = normalize_keyword(raw_term)            
            # Use the canonical map, falling back to the term itself if not found
            canonical_term = synonym_map.get(norm_term, norm_term)
            canonical_terms.append(canonical_term)
            all_canonical_keywords.update([canonical_term])
            
            canonical_corpus[modularity_class].append(canonical_term)
            
            # --- QA Logging ---
            # Log the mapping: Raw Term (original case/form) -> Canonical Term
            # This helps track exactly what came from the GEXF and what it became.
            if raw_term not in qa_log:
                qa_log[raw_term] = canonical_term
            # Optional: Check for inconsistent mapping (if the same raw_term somehow maps to different canonical_terms)
            elif qa_log[raw_term] != canonical_term:
                print(f"Warning: Inconsistent canonical mapping detected for raw term '{raw_term}'. Mapped to '{qa_log[raw_term]}' and now '{canonical_term}'.")

            
         # c. Reconstruct the document string using canonical terms, separated by spaces
        # The TfidfVectorizer will treat each space-separated canonical term as a feature (token)
        # canonical_doc = "\t".join(canonical_terms)
        # canonical_corpus[modularity_class].append(canonical_doc)
        
    
    for key, values in canonical_corpus.items():
        canonical_corpus[key] = "\t".join(values)

    # 5. Save the QA Log file
    out_dir = Path("td-idf_results")
    out_dir.mkdir(exist_ok=True)

    qa_log_path = out_dir/"qa_canonical_keyword_mapping.json"
    print(f"\nSaving QA log to: {qa_log_path}")
    
    # Sort for cleaner presentation
    sorted_qa_log = dict(sorted(qa_log.items()))
    
    with open(qa_log_path, 'w', encoding='utf-8') as f:
        json.dump(sorted_qa_log, f, indent=4, ensure_ascii=False)
    print(f"Total unique raw keywords processed and logged: {len(qa_log)}")

    # 5.1 Generate QA report: all unique CANONICAL keywords processed
    # all_keywords = set(canonical_corpus)
    all_keywords_sorted = sorted(all_canonical_keywords)
    qa_path = out_dir / "all_canonical_keywords_processed.txt"
    with open(qa_path, 'w') as f:
        f.write(f"Total unique CANONICAL keywords processed: {len(all_keywords_sorted)}\n")
        f.write("=" * 80 + "\n\n")
        for kw in all_keywords_sorted:  
            f.write(f"{kw.title()}\n")
    print(f"\nQA report saved to: {qa_path}")


    # 6. Apply TfidfVectorizer to the Canonical Corpus
    print("\nFitting TfidfVectorizer to the canonical corpus...")
    
    vectorizer = TfidfVectorizer(
        tokenizer=lambda x: x.split('\t'), 
        token_pattern=None,              
        lowercase=False                  
    )
    
    X = vectorizer.fit_transform(canonical_corpus.values())
    
    # 7. Output Results (Rest of the script remains the same)
    print("\n--- Results ---")
    
    feature_names = vectorizer.get_feature_names_out()
    print(f"Total unique canonical keywords (features): {len(feature_names)}")
    
    # Show example (first cluster)
    if X.shape[0] > 0:        
        cluster_vector = X[0].toarray().flatten()
        
        scores = pd.Series(cluster_vector, index=feature_names)
        scores = scores[scores > 0].sort_values(ascending=False)
        
        print(f"Highest TD-IDF scores (first cluster):\n{scores.head(10)}")
        print(f"\nSum of TD-IDF scores for the first cluster (normalized L2 norm): {np.sum(cluster_vector**2)}")
    
    return X, vectorizer, df

gexf_file = "filtered_with_transferred_mesh_fixed_fix_commas.gexf"
synonym_dict_path = Path('embedding_keywords')/"keyword_synonyms_0.99_with_transitivity.json"


X_matrix, vectorizer_model, dataframe = calculate_canonical_tfidf(gexf_file, synonym_dict_path)
save_results(X_matrix, vectorizer_model, dataframe)

print("Script execution successful")