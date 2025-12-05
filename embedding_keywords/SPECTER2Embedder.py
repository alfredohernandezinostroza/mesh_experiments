import pandas as pd
import numpy as np
from transformers import AutoTokenizer, AutoModel
import torch
from typing import List, Optional
import warnings
warnings.filterwarnings('ignore')

class SPECTER2Embedder:
    """
    A class to embed scientific paper abstracts and titles using SPECTER2
    """
    
    def __init__(self, device: str, model_name: str = "allenai/specter2_base"):
        """
        Initialize the SPECTER2 embedder
        
        Args:
            model_name: The SPECTER2 model to use (default: specter2_base)
        """
        print(f"Loading {model_name}...")
        
        # Check CUDA availability and GPU info
        print(f"CUDA available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"CUDA device count: {torch.cuda.device_count()}")
            print(f"Current CUDA device: {torch.cuda.current_device()}")
            print(f"CUDA device name: {torch.cuda.get_device_name()}")
            print(f"CUDA memory allocated: {torch.cuda.memory_allocated() / 1024**2:.2f} MB")
            print(f"CUDA memory cached: {torch.cuda.memory_reserved() / 1024**2:.2f} MB")
        
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        
        # Load model with explicit device mapping
        if torch.cuda.is_available():
            self.model = AutoModel.from_pretrained(model_name, device_map=device, torch_dtype=torch.float16)
            self.device = torch.device(device)
        else:
            self.model = AutoModel.from_pretrained(model_name)
            self.device = torch.device('cpu')
            
        # Ensure model is on the correct device
        self.model = self.model.to(self.device)
        self.model.eval()  # Set to evaluation mode
        
        print(f"Model loaded on {self.device}")
        
        # Verify model is actually on GPU
        if torch.cuda.is_available():
            print(f"Model device: {next(self.model.parameters()).device}")
            print(f"CUDA memory after model load: {torch.cuda.memory_allocated() / 1024**2:.2f} MB")
    
    def mean_pooling(self, model_output, attention_mask):
        """
        Perform mean pooling on token embeddings
        """
        token_embeddings = model_output[0]
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)
    
    def embed_texts(self, texts: List[str], max_length: int, batch_size: int = 32) -> np.ndarray:
        """
        Embed a list of texts using SPECTER2
        
        Args:
            texts: List of text strings to embed
            batch_size: Batch size for processing
            
        Returns:
            numpy array of embeddings
        """
        all_embeddings = []
        
        # Process in batches
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            print(f"Processing batch {i//batch_size + 1}/{(len(texts)-1)//batch_size + 1}")
            
            # Monitor GPU usage
            if torch.cuda.is_available():
                print(f"  GPU memory before batch: {torch.cuda.memory_allocated() / 1024**2:.2f} MB")
            
            # Tokenize
            encoded_input = self.tokenizer(
                batch_texts, 
                padding=True, 
                truncation=True, 
                max_length=max_length,
                return_tensors='pt' #it means pytorch tensor
            ).to(self.device)
            
            # Verify tensors are on GPU
            if torch.cuda.is_available():
                print(f"  Input tensors device: {encoded_input['input_ids'].device}")
            
            # Generate embeddings
            with torch.no_grad():
                model_output = self.model(**encoded_input)
                embeddings = self.mean_pooling(model_output, encoded_input['attention_mask'])
                embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)
                all_embeddings.append(embeddings.cpu().numpy())
            
            # Monitor GPU usage after processing
            if torch.cuda.is_available():
                print(f"  GPU memory after batch: {torch.cuda.memory_allocated() / 1024**2:.2f} MB")
                # Clear cache to prevent memory buildup
                torch.cuda.empty_cache()
        
        return np.vstack(all_embeddings)

def embed_papers_dataframe(
    df: pd.DataFrame,
    device,
    title_col: str = 'title',
    abstract_col: str = 'abstract',
    combine_title_abstract: bool = True,
    model_name: str = "allenai/specter2_base",
    batch_size: int = 8
) -> pd.DataFrame:
    """
    Embed papers in a pandas DataFrame using SPECTER2
    
    Args:
        df: DataFrame containing papers
        title_col: Name of the title column
        abstract_col: Name of the abstract column
        combine_title_abstract: Whether to combine title and abstract for embedding
        model_name: SPECTER2 model to use
        batch_size: Batch size for processing
        
    Returns:
        DataFrame with added embedding columns
    """
    # Create a copy to avoid modifying the original
    result_df = df.copy()
    
    # Initialize embedder
    embedder = SPECTER2Embedder(model_name=model_name, device=device)
    
    # Prepare texts for embedding
    if combine_title_abstract:
        # Combine title and abstract with [SEP] token
        texts = []
        for _, row in df.iterrows():
            title = str(row[title_col]) if pd.notna(row[title_col]) else ""
            abstract = str(row[abstract_col]) if pd.notna(row[abstract_col]) else ""
            combined_text = f"{title} [SEP] {abstract}".strip()
            texts.append(combined_text)
        
        print(f"Embedding {len(texts)} combined title+abstract texts...")
        embeddings = embedder.embed_texts(texts, batch_size)
        
        # Add only the embedding vector column (not individual dimensions)
        result_df['embedding_vector'] = [emb for emb in embeddings]
        
    else:
        # Embed titles and abstracts separately
        print(f"Embedding {len(df)} titles...")
        title_texts = [str(title) if pd.notna(title) else "" for title in df[title_col]]
        title_embeddings = embedder.embed_texts(title_texts, batch_size)
        
        print(f"Embedding {len(df)} abstracts...")
        abstract_texts = [str(abstract) if pd.notna(abstract) else "" for abstract in df[abstract_col]]
        abstract_embeddings = embedder.embed_texts(abstract_texts, batch_size)
        
        # Add only the embedding vector columns (not individual dimensions)
        result_df['title_embedding_vector'] = [emb for emb in title_embeddings]
        result_df['abstract_embedding_vector'] = [emb for emb in abstract_embeddings]
    
    print("Embedding complete!")
    return result_df

def embed_column(
    df: pd.DataFrame,
    max_length: int,
    device: str,
    column: str = 'keywords',
    model_name: str = "allenai/specter2_base",
    batch_size: int = 8
) -> pd.DataFrame:
    """
    Embed papers in a pandas DataFrame using SPECTER2
    
    Args:
        df: DataFrame containing papers
        column: Name of the column to be embedded
        model_name: SPECTER2 model to use
        max_length: max stoken size for each text
        batch_size: Batch size for processing
        
    Returns:
        DataFrame with added embedding column
    """
    # Create a copy to avoid modifying the original
    result_df = df.copy()
    
    # Initialize embedder
    embedder = SPECTER2Embedder(model_name=model_name, device=device)
    
    # Prepare texts for embedding

    # Embed titles and abstracts separately
    print(f"Embedding {len(df)} entrise for {column}...")
    column_embeddings = embedder.embed_texts(df[column].to_list(), max_length, batch_size)
    
    # Add only the embedding vector columns (not individual dimensions)
    result_df[f'{column}_embedding_Vector'] = [emb for emb in column_embeddings]
    
    print("Embedding complete!")
    return result_df

# GPU Monitoring and Debugging Functions
def check_gpu_usage():
    """
    Check current GPU usage and PyTorch CUDA status
    """
    print("=== GPU Status Check ===")
    print(f"PyTorch version: {torch.__version__}")
    print(f"CUDA available in PyTorch: {torch.cuda.is_available()}")
    
    if torch.cuda.is_available():
        print(f"CUDA version: {torch.version.cuda}")
        print(f"cuDNN version: {torch.backends.cudnn.version()}")
        print(f"Number of GPUs: {torch.cuda.device_count()}")
        
        for i in range(torch.cuda.device_count()):
            print(f"GPU {i}: {torch.cuda.get_device_name(i)}")
            print(f"  Memory allocated: {torch.cuda.memory_allocated(i) / 1024**2:.2f} MB")
            print(f"  Memory reserved: {torch.cuda.memory_reserved(i) / 1024**2:.2f} MB")
            print(f"  Max memory allocated: {torch.cuda.max_memory_allocated(i) / 1024**2:.2f} MB")
    else:
        print("CUDA not available")
    
    # Try to create a tensor on GPU
    try:
        if torch.cuda.is_available():
            test_tensor = torch.rand(100, 100).cuda()
            print(f"Test tensor created on: {test_tensor.device}")
            del test_tensor
            torch.cuda.empty_cache()
        else:
            print("Cannot create CUDA tensors - CUDA not available")
    except Exception as e:
        print(f"Error creating CUDA tensor: {e}")

def force_gpu_usage_test():
    """
    Run a simple computation to force GPU usage
    """
    if not torch.cuda.is_available():
        print("CUDA not available for testing")
        return
    
    print("=== GPU Usage Test ===")
    device = torch.device('cuda')
    
    print("Creating large tensors to force GPU usage...")
    try:
        # Create large tensors that should show up in GPU monitoring
        a = torch.randn(5000, 5000, device=device)
        b = torch.randn(5000, 5000, device=device)
        
        print(f"GPU memory after tensor creation: {torch.cuda.memory_allocated() / 1024**2:.2f} MB")
        
        # Perform computation
        print("Performing matrix multiplication...")
        for i in range(10):
            c = torch.mm(a, b)
            if i == 0:
                print(f"GPU memory during computation: {torch.cuda.memory_allocated() / 1024**2:.2f} MB")
        
        print("Computation complete. Check your GPU monitoring tool now!")
        
        # Clean up
        del a, b, c
        torch.cuda.empty_cache()
        print(f"GPU memory after cleanup: {torch.cuda.memory_allocated() / 1024**2:.2f} MB")
        
    except Exception as e:
        print(f"Error during GPU test: {e}")

# GPU Monitoring and Debugging Functions
def create_sample_dataframe():
    """Create a sample dataframe for testing"""
    data = {
        'title': [
            'Deep Learning for Natural Language Processing',
            'Quantum Computing and Machine Learning',
            'Biodiversity Conservation in Tropical Forests',
            'Climate Change Impact on Ocean Ecosystems'
        ],
        'abstract': [
            'This paper presents a comprehensive survey of deep learning techniques applied to natural language processing tasks. We review recent advances in transformer architectures and their applications.',
            'We explore the intersection of quantum computing and machine learning, proposing novel quantum algorithms for optimization problems in artificial intelligence.',
            'This study examines biodiversity patterns in tropical forests and proposes conservation strategies based on ecological modeling and species distribution analysis.',
            'We analyze the effects of climate change on marine ecosystems, focusing on temperature changes and their impact on species migration patterns.'
        ],
        'authors': [
            'Smith, J. et al.',
            'Johnson, A. et al.',
            'Brown, M. et al.',
            'Davis, R. et al.'
        ],
        'year': [2023, 2023, 2022, 2024]
    }
    return pd.DataFrame(data)

def compute_similarity_matrix(embeddings: np.ndarray) -> np.ndarray:
    """
    Compute cosine similarity matrix between embeddings
    
    Args:
        embeddings: Array of embeddings
        
    Returns:
        Similarity matrix
    """
    from sklearn.metrics.pairwise import cosine_similarity
    return cosine_similarity(embeddings)

def find_similar_papers(df: pd.DataFrame, paper_index: int, top_k: int = 5):
    """
    Find similar papers based on embeddings
    
    Args:
        df: DataFrame with embeddings
        paper_index: Index of the query paper
        top_k: Number of similar papers to return
        
    Returns:
        DataFrame of similar papers
    """
    if 'embedding_vector' not in df.columns:
        raise ValueError("DataFrame must contain 'embedding_vector' column")
    
    embeddings = np.vstack(df['embedding_vector'].values)
    similarity_matrix = compute_similarity_matrix(embeddings)
    
    # Get similarities for the query paper
    similarities = similarity_matrix[paper_index]
    
    # Get top-k similar papers (excluding the paper itself)
    similar_indices = np.argsort(similarities)[::-1][1:top_k+1]
    
    result_df = df.iloc[similar_indices].copy()
    result_df['similarity_score'] = similarities[similar_indices]
    
    return result_df

# Example usage
if __name__ == "__main__":
    # Create sample data
    print("Creating sample dataframe...")
    df = create_sample_dataframe()
    print(f"Created dataframe with {len(df)} papers")
    print("\nSample data:")
    print(df[['title', 'authors', 'year']].head())
    
    # Embed the papers
    print("\nEmbedding papers...")
    embedded_df = embed_papers_dataframe(
        df, 
        title_col='title',
        abstract_col='abstract',
        combine_title_abstract=True,
        batch_size=4
    )
    
    print(f"\nEmbedded dataframe shape: {embedded_df.shape}")
    print("Embedding columns added:", [col for col in embedded_df.columns if 'embedding' in col])
    
    # Find similar papers
    print(f"\nFinding papers similar to: '{df.iloc[0]['title']}'")
    similar_papers = find_similar_papers(embedded_df, paper_index=0, top_k=3)
    print("\nMost similar papers:")
    for idx, row in similar_papers.iterrows():
        print(f"- {row['title']} (similarity: {row['similarity_score']:.3f})")
    
    print("\nDone! Your papers are now embedded and ready for similarity search, clustering, or other downstream tasks.")