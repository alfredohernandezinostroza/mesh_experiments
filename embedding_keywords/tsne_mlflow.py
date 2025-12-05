
import mlflow
from itertools import product
import tempfile
import os 
import numpy as np
from pathlib import Path
import pandas as pd
from sklearn.manifold import TSNE
import plotly.express as px
from tqdm import tqdm
RANDOM_SEED = 42
cluster_label_color_map = {
    'A. Neuroscience & Neuroanatomy': '#D98DFF',  # light purple
    'B. Neuropharmacology & Biochemistry': '#6AC500',  # green
    'C. Neurophysiology & Brain Activity': '#00C8FF',  # cyan
    'D. Brain Stimulation & Intervention': '#FF7F00',  # orange
    'E. Motor Skills & Performance': '#FF5A87',  # pink
    'F. Motor Control & Execution': '#00C6A4',  # teal
    'G. Motor Learning: General/Theory': '#DA0A6A',  # magenta
    'H. Motor Learning: Mechanisms & Factors': '#A549F1',  # violet
    'I. Implicit vs. Explicit Learning': '#FFDD00',  # yellow
    'J. Sensory & Perceptual Systems': '#1CA3EC',  # sky blue
    'K. Plasticity & Adaptation': '#FF6F61',  # coral
    'L. Cognition & Executive Function': '#C70039',  # dark pink
    'M. Computational & Modeling': '#900C3F',  # deep red
    'N. Robotics & Technology': '#FFC300',  # gold
    'O. Clinical Conditions & Disease Models': '#2E4057',  # dark slate
    'P. Rehabilitation & Therapy': '#FF5733',  # red-orange
    'Q. Psychological Factors & Motivation': '#DAF7A6',  # light green
    'R. Timing & Rhythm': '#581845',  # dark purple
    'S. Research Methodology & Statistics': '#8B4513',  # brown
    'T. Human & Animal Subjects': '#20B2AA',  # light teal
    'U. Vision & Oculomotor Control': '#FF69B4',  # hot pink
    'V. Speech & Language': '#7FFF00',  # chartreuse
    'W. Development & Lifespan': '#6495ED',  # cornflower blue
    'X. Imaging & Assessment Techniques': '#FF8C00',  # dark orange
    'Z. Unclassified': '#8B8B8B'  # gray
}

def str_to_vector(s):
    # remove brackets and split by whitespace
    s = s.strip("[]")
    return np.array([float(x) for x in s.split()])

mlflow.set_tracking_uri("mlexperiments")
mlflow.set_experiment("tsne_experiment")
root_folder = Path('embedding_keywords')


embedded_keywords_df = pd.read_csv(root_folder/"classified_embedded_keywords.csv", sep="\t")
embedded_keywords_df['Keywords_embedding_Vector'] = embedded_keywords_df['Keywords_embedding_Vector'].apply(str_to_vector)

perplexities = np.arange(5, 60, 5)
learning_rates = np.arange(50.0, 100.0, 50.0)
for combination in tqdm(product(perplexities, learning_rates)):
    perplexity, learning_rate = combination
    with mlflow.start_run():
        mlflow.log_param("perplexity", perplexity)
        mlflow.log_param("learning_rate", learning_rate)
        embeddings = np.array(embedded_keywords_df['Keywords_embedding_Vector'].tolist())
        
        tsne = TSNE(n_components=2, random_state=RANDOM_SEED, perplexity=perplexity, learning_rate=learning_rate)
        embeddings_2d = tsne.fit_transform(embeddings)

        embedded_keywords_df['tsne_x'] = embeddings_2d[:, 0]
        embedded_keywords_df['tsne_y'] = embeddings_2d[:, 1]

        
        # Now use this in your plot
        fig = px.scatter(
            embedded_keywords_df,
            x='tsne_x',
            y='tsne_y',
            color='predicted_category',       # this contains the label names
            # size=1,         
            hover_data=['Keywords', 'predicted_category', 'similarity_score'],
            title='t-SNE Visualization (Colored by Selected Clusters and Sized by Degree)',
            color_discrete_map=cluster_label_color_map,  # map labels to colors
        )

        fig.update_layout(
            hoverlabel=dict(
                bgcolor="white",
                font_size=12
            ),
            legend=dict(
                orientation="v",
                yanchor="middle",
                y=0.5,
                xanchor="left",
                x=1.02
            )
        )
                        # Use temporary files that get automatically cleaned up
        with tempfile.TemporaryDirectory() as temp_dir:
            # Save HTML file temporarily
            html_path = os.path.join(temp_dir, f"tsne_p{perplexity}_lr{learning_rate}.html")
            fig.write_html(html_path, include_plotlyjs="cdn")
            mlflow.log_artifact(html_path, "plots")
            
            # Save CSV file temporarily  
            csv_path = os.path.join(temp_dir, f"tsne_data_p{perplexity}_lr{learning_rate}.csv")
            embedded_keywords_df.to_csv(csv_path, sep="\t", index=False)
            mlflow.log_artifact(csv_path, "data")
            