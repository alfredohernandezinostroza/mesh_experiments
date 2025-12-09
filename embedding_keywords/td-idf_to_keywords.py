import re
import pandas as pd
import numpy as np
import networkx as nx
from pathlib import Path
import json 
from collections import defaultdict, Counter
from sklearn.feature_extraction.text import TfidfVectorizer

# --- Assume these helpers are imported or defined (essential for processing) ---

def normalize_keyword(keyword: str) -> str:
    """Normalize a keyword to lowercase."""
    return keyword.lower()

def split_keywords(keywords_value: str):
    """Split a keywords string into individual keywords (using robust logic)."""
    # NOTE: Using simplified splitting here for brevity, but use your original 
    # robust split_keywords function that handles parentheses/brackets.
    if keywords_value is None or pd.isna(keywords_value):
        return []
    # Simplified splitting logic (replace with your robust version)
    return [k.strip() for k in str(keywords_value).split(',') if k.strip()]

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

def calculate_canonical_tfidf(gexf_file: str, synonym_dict_path: Path):
    
    # 1. Load Data
    print(f"Reading GEXF file: {gexf_file}")
    G = nx.read_gexf(gexf_file)
    keywords = nx.get_node_attributes(G, "keywords")
    df = pd.DataFrame(list(keywords.items()), columns=['ID_String', 'Keywords'])
    
    # 2. Load and Prepare Synonym Map
    print(f"Loading synonym data from: {synonym_dict_path}")
    synonym_data = load_synonym_data(synonym_dict_path)
    synonym_map = load_synonym_map(synonym_data)
    
    # 3. Rewrite Corpus using Canonical Keywords
    print("Rewriting corpus using canonical keywords...")
    canonical_corpus = []

    for raw_keywords_str in df['Keywords']:
        # a. Split the raw string into individual keywords
        terms = split_keywords(raw_keywords_str)
        
        # b. Normalize each term and map it to its canonical form
        canonical_terms = []
        for term in terms:
            norm_term = normalize_keyword(term)
            # Use the canonical map, falling back to the term itself if not found
            canonical_term = synonym_map.get(norm_term, norm_term)
            canonical_terms.append(canonical_term)
            
        # c. Reconstruct the document string using canonical terms, separated by spaces
        # The TfidfVectorizer will treat each space-separated canonical term as a feature (token)
        canonical_doc = " ".join(canonical_terms)
        canonical_corpus.append(canonical_doc)

    # 4. Apply TfidfVectorizer to the Canonical Corpus
    print("Fitting TfidfVectorizer to the canonical corpus...")
    
    # We must use a simple tokenizer because our "tokens" are already canonical terms
    # that may contain spaces (e.g., "action representation").
    # TfidfVectorizer's default tokenizer splits by space, which is what we want here, 
    # but we must ensure we don't apply further preprocessing if our terms have hyphens, etc.
    vectorizer = TfidfVectorizer(
        tokenizer=lambda x: x.split(' '), # Split by space
        token_pattern=None,              # Disable default regex pattern
        lowercase=False                  # Canonical terms are already lowercase
    )
    
    X = vectorizer.fit_transform(canonical_corpus)
    
    # 5. Output Results
    print("\n--- Results ---")
    
    # The feature names are the unique canonical keywords
    feature_names = vectorizer.get_feature_names_out()
    print(f"Total unique canonical keywords (features): {len(feature_names)}")
    
    # Show example (first paper)
    paper_index = 0
    paper_id = df.loc[paper_index, 'ID_String']
    print(f"\nExample Paper ID: {paper_id}")
    
    # Get the vector for the first paper
    paper_vector = X[paper_index].toarray().flatten()
    
    # Map features to their TD-IDF score
    scores = pd.Series(paper_vector, index=feature_names)
    scores = scores[scores > 0].sort_values(ascending=False)
    
    print(f"Highest TD-IDF scores (first paper):\n{scores.head(10)}")
    print(f"\nSum of TD-IDF scores for the first paper (normalized L2 norm): {np.sum(paper_vector**2)}")
    
    return X, vectorizer, df

# --- Execution ---
gexf_file = "filtered_with_transferred_mesh_fixed_fix_commas.gexf"
synonym_dict_path = Path('embedding_keywords')/"keyword_synonyms_0.99_with_transitivity.json"


X_matrix, vectorizer_model, dataframe = calculate_canonical_tfidf(gexf_file, synonym_dict_path)
print("Script execution successful")