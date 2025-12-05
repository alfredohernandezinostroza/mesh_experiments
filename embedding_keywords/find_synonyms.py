import pandas as pd
from pathlib import Path
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import json
from tqdm import tqdm

THRESHOLD = 0.99

class SetEncoder(json.JSONEncoder):
    def __init__(self, *args, **kwargs):
        kwargs['sort_keys'] = True 
        super().__init__(*args, **kwargs)

    def default(self, obj):
        if isinstance(obj, set):
            return sorted(list(obj)) # Convert set to list within encoder
        if isinstance(obj, list):
            return sorted(obj) # Convert set to list within encoder
        return json.JSONEncoder.default(self, obj)

def str_to_vector(s):
    # remove brackets and split by whitespace
    s = s.strip("[]")
    return np.array([float(x) for x in s.split()])

def find_synonyms(keywords: pd.Series, embeddings: pd.Series):
    synonyms = {}
    # synonyms_with_transitivity = {}
    embeddings_matrix = np.vstack(df['Keywords_embedding_Vector'].values)
    print("Calculating N x N similarity matrix...")
    similarity_matrix = cosine_similarity(embeddings_matrix, embeddings_matrix)
    print("Calculation complete. Extracting synonyms...")
    for i, keyword in tqdm(enumerate(keywords), total=len(keywords)):
        similarity = similarity_matrix[i, :]
        indices = np.where(similarity > THRESHOLD)[0] #we unpack the tuple, the second term is empty because we are applying where to a vector
        potential_synonyms = [keywords[j] for j in indices if keywords[j] != keyword]
        if potential_synonyms:
            synonyms[keyword] = potential_synonyms
    return synonyms

def find_synonyms_with_transitivity(keywords: pd.Series, embeddings: pd.Series):
    synonyms = {}
    synonyms_with_transitivity = {}
    embeddings_matrix = np.vstack(df['Keywords_embedding_Vector'].values)
    print("Calculating N x N similarity matrix...")
    similarity_matrix = cosine_similarity(embeddings_matrix, embeddings_matrix)
    print("Calculation complete. Extracting synonyms...")
    for i, keyword in tqdm(enumerate(keywords), total=len(keywords)):
        similarity = similarity_matrix[i, :]
        indices = np.where(similarity > THRESHOLD)[0] #we unpack the tuple, the second term is empty because we are applying where to a vector
        potential_synonyms = set([keywords[j] for j in indices if keywords[j] != keyword])
        if potential_synonyms:
            synonyms[keyword] = potential_synonyms
            synonyms_with_transitivity[keyword] = potential_synonyms.copy()
            for synonym in potential_synonyms:
                this_synonyms = potential_synonyms.copy()
                this_synonyms.add(keyword)
                this_synonyms.remove(synonym)
                if synonym in synonyms_with_transitivity:
                    synonyms_with_transitivity[synonym].update(this_synonyms)
                else:
                    synonyms_with_transitivity[synonym] = set(this_synonyms)
    return synonyms, synonyms_with_transitivity

if __name__ == "__main__":
    root_folder = Path('embedding_keywords')
    df = pd.read_csv(root_folder/"embedded_keywords.csv", sep='\t', converters= {"Keywords_embedding_Vector": str_to_vector})
    keywords  = df["Keywords"]
    embeddings = df["Keywords_embedding_Vector"]
    # synonyms = find_synonyms(keywords, embeddings)
    synonyms, synonyms_with_transitivity = find_synonyms_with_transitivity(keywords, embeddings)
    with open(root_folder/f"keyword_synonyms_{THRESHOLD}.json", 'w') as file:
        json.dump(synonyms, file, indent=4, cls=SetEncoder)
    with open(root_folder/f"keyword_synonyms_{THRESHOLD}_with_transitivity.json", 'w') as file:
        json.dump(synonyms_with_transitivity, file, indent=4, cls=SetEncoder)