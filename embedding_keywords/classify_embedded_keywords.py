import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from pathlib import Path
def str_to_vector(s):
    # remove brackets and split by whitespace
    s = s.strip("[]")
    return np.array([float(x) for x in s.split()])
if __name__ == "__main__":
    root_folder = Path('embedding_keywords')

    embedded_categories_df = pd.read_csv(root_folder/"embedded_categories.csv", sep="\t")
    embedded_keywords_df = pd.read_csv(root_folder/"embedded_keywords.csv", sep="\t")
    
    
    embedded_categories_df['text_for_embedding_embedding_Vector'] = embedded_categories_df['text_for_embedding_embedding_Vector'].apply(str_to_vector)
    embedded_keywords_df['Keywords_embedding_Vector'] = embedded_keywords_df['Keywords_embedding_Vector'].apply(str_to_vector)

    # drop unclassified
    embedded_categories_df = embedded_categories_df.drop(embedded_categories_df.index[-1])

    category_embeddings = np.stack(embedded_categories_df['text_for_embedding_embedding_Vector'].values)
    keyword_embeddings = np.stack(embedded_keywords_df['Keywords_embedding_Vector'].values)

    similarities = cosine_similarity(keyword_embeddings, category_embeddings)

    # Get the index of the max similarity for each keyword
    best_category_idx = similarities.argmax(axis=1)

    # Assign category labels
    embedded_keywords_df['predicted_category'] = embedded_categories_df.iloc[best_category_idx]['category_key'].values

    # Optional: store the similarity score
    embedded_keywords_df['similarity_score'] = similarities.max(axis=1)

    # -----------------------------
    # Save or inspect
    # -----------------------------
    print(np.sum(embedded_keywords_df['similarity_score'] <= 0.25))
    embedded_keywords_df.to_csv(root_folder/"classified_embedded_keywords.csv", index=False, sep='\t')
    print(embedded_keywords_df.head())