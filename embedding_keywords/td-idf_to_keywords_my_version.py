from sklearn.feature_extraction.text import TfidfVectorizer
import pandas as pd
import numpy as np
import networkx as nx
from pathlib import Path
import json 
from scripts.keywords_histograms_by_modularity import load_synonym_map, load_synonym_data

# Read GEXF file
gexf_file = "filtered_with_transferred_mesh_fixed_fix_commas.gexf"
print(f"\nReading GEXF file: {gexf_file}")
G = nx.read_gexf(gexf_file)
keywords = nx.get_node_attributes(G, "keywords")
df = pd.DataFrame(list(keywords.items()), columns=['ID_String', 'Keywords'])
print(f"Are there NaNs or empty keywords?: \n {df.isna().value_counts()}")
corpus = df['Keywords']

synonym_dict_path =  Path('embedding_keywords')/"keyword_synonyms_0.99_with_transitivity.json"
synonym_data = load_synonym_data(synonym_dict_path)
synonym_map = load_synonym_map(synonym_data)

vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(corpus)
print(X.toarray())
print(np.sum(X.toarray()[0]))