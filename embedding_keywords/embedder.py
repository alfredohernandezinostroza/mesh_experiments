import pandas as pd
from SPECTER2Embedder import embed_column
from pathlib import Path

if __name__ == "__main__":
    root_folder = Path('embedding_keywords')
    # Load your dataframe
    df = pd.read_csv(root_folder/'all_keywords_processed.txt', sep='\t', index_col=False)
    print(df.head)
    embedded_df = embed_column(df, column='Keywords', max_length=32, batch_size=128, device='cuda:1')
    print("saving dataframe...")
    embedded_df.to_csv(root_folder/'embedded_keywords.csv', index=False, sep='\t')
    print("finished!...")