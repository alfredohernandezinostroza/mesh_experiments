import pandas as pd
import json
from pathlib import Path
from SPECTER2Embedder import embed_column

if __name__ == "__main__":
    root_folder = Path('embedding_keywords')
    with open(root_folder/"categories.json") as f:
        cats = json.load(f)

    rows = []

    for key, val in cats.items():
        text = (
            f"{key}: \n"
            f"Definition: {val['definition']}\n"
            f"Examples: {', '.join(val['examples'])}"
        )
        rows.append({"category_key": key, "text_for_embedding": text})

    df = pd.DataFrame(rows)
    print(df)
    print(df.loc[0,"text_for_embedding"])

    print("Embedding categories...")
    embedded_df = embed_column(df, column='text_for_embedding', max_length=128, batch_size=8, device='cuda:1')
    print("saving dataframe...")
    embedded_df.to_csv(root_folder/'embedded_categories.csv', index=False, sep='\t')
    print("finished!...")