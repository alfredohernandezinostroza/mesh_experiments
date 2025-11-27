import pandas as pd
from metapub import PubMedFetcher
import time
from pathlib import Path
import re

def extract_pmid_from_doi(doi):
    """
    Try to extract PMID from DOI if possible, or search by title/author
    """
    if pd.isna(doi) or doi == '':
        return None
    return None  # We'll rely on title search primarily

def get_mesh_terms(fetch, title, author=None, doi=None, max_retries=3):
    """
    Retrieve MeSH terms for a paper by searching PubMed
    Returns a comma-separated string of MeSH terms
    """
    for attempt in range(max_retries):
        try:
            # First try searching by title
            if pd.notna(title) and title.strip():
                # Try exact match first (with quotes)
                search_query = f'"{title}"'
                pmids = fetch.pmids_for_query(search_query, retmax=5)
                
                # If exact match fails, try without quotes
                if not pmids:
                    search_query = title
                    pmids = fetch.pmids_for_query(search_query, retmax=5)
                
                if pmids:
                    # Verify the title matches (at least partially) to avoid false positives
                    for pmid in pmids[:3]:  # Check top 3 results
                        article = fetch.article_by_pmid(pmid)
                        
                        # Simple title similarity check
                        if article.title:
                            # Remove punctuation and convert to lowercase for comparison
                            clean_search = re.sub(r'[^\w\s]', '', title.lower())
                            clean_found = re.sub(r'[^\w\s]', '', article.title.lower())
                            
                            # Check if at least 70% of words match
                            search_words = set(clean_search.split())
                            found_words = set(clean_found.split())
                            
                            if search_words and found_words:
                                overlap = len(search_words & found_words) / len(search_words)
                                
                                if overlap > 0.7:  # 70% word overlap threshold
                                    if hasattr(article, 'mesh') and article.mesh:
                                        # Extract descriptor names from MeSH terms
                                        mesh_list = []
                                        for term in article.mesh:
                                            if isinstance(term, dict):
                                                descriptor = term.get('descriptor_name', '')
                                                if descriptor:
                                                    mesh_list.append(descriptor)
                                            elif isinstance(term, str):
                                                mesh_list.append(term)
                                        
                                        if mesh_list:
                                            return ', '.join(mesh_list)
            
            # If no results, return empty string
            return ''
            
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
                continue
            else:
                print(f"Error retrieving MeSH terms for '{title[:50]}...': {str(e)}")
                return ''
    
    return ''

def process_csv_with_mesh(input_file, output_file=None, errors_file=None, 
                          start_row=0, end_row=None, checkpoint_frequency=100):
    """
    Process CSV file and add MeSH terms
    
    Parameters:
    -----------
    input_file : str or Path
        Path to input CSV file
    output_file : str or Path, optional
        Path to output CSV file. If None, adds '_with_mesh.csv' to input filename
    errors_file : str or Path, optional
        Path to errors CSV file. If None, saves as 'errors.csv' in same directory
    start_row : int
        Row to start processing from (useful for resuming)
    end_row : int, optional
        Row to end processing at (useful for testing on subset)
    checkpoint_frequency : int
        Save progress every N rows
    """
    
    # Read the CSV file
    print(f"Reading CSV file: {input_file}")
    df = pd.read_csv(input_file, sep=',')
    
    print(f"Loaded {len(df)} papers")
    print(f"Columns: {list(df.columns)}")
    
    # Add MeSH terms column if it doesn't exist
    if 'MESH' not in df.columns:
        df['MESH'] = ''
    
    # Initialize PubMed fetcher
    fetch = PubMedFetcher()
    
    # Determine output file names
    if output_file is None:
        input_path = Path(input_file)
        output_file = input_path.parent / f"{input_path.stem}_with_mesh.csv"
    
    if errors_file is None:
        input_path = Path(input_file)
        errors_file = input_path.parent / f"{input_file}_errors.csv"
    
    # List to collect papers without MeSH terms
    error_rows = []
    
    # Determine processing range
    if end_row is None:
        end_row = len(df)
    else:
        end_row = min(end_row, len(df))
    
    print(f"\nProcessing rows {start_row} to {end_row-1}")
    print(f"Checkpoint saves every {checkpoint_frequency} rows to: {output_file}")
    print(f"Papers without MeSH terms will be saved to: {errors_file}\n")
    
    # Process each paper
    processed_count = 0
    found_mesh_count = 0
    
    for idx in range(start_row, end_row):
        # Skip if already has MeSH terms (in case of resuming)
        if pd.notna(df.loc[idx, 'MESH']) and df.loc[idx, 'MESH'].strip():
            processed_count += 1
            found_mesh_count += 1
            continue
        
        title = df.loc[idx, 'Label'] if 'Label' in df.columns else ''
        author = df.loc[idx, 'Author'] if 'Author' in df.columns else ''
        doi = df.loc[idx, 'Doi'] if 'Doi' in df.columns else ''
        
        # Get MeSH terms
        mesh_terms = get_mesh_terms(fetch, title, author, doi)
        df.loc[idx, 'MESH'] = mesh_terms
        
        processed_count += 1
        if mesh_terms:
            found_mesh_count += 1
        else:
            # Save paper to error list if no MeSH terms found
            error_rows.append(df.loc[idx].copy())
        
        # Progress update
        if processed_count % 10 == 0:
            print(f"Processed {processed_count}/{end_row-start_row} papers "
                  f"(found MeSH: {found_mesh_count}, "
                  f"{found_mesh_count/processed_count*100:.1f}%)")
        
        # Checkpoint save
        if processed_count % checkpoint_frequency == 0:
            df.to_csv(output_file, sep=',', index=False)
            # Also save errors at checkpoint
            if error_rows:
                pd.DataFrame(error_rows).to_csv(errors_file, sep=',', index=False)
            print(f"  → Checkpoint saved to {output_file}")
            if error_rows:
                print(f"  → Errors saved to {errors_file} ({len(error_rows)} papers without MeSH)")
        
        # Rate limiting (PubMed allows 3 requests per second without API key)
        time.sleep(0.35)
    
    # Final save
    df.to_csv(output_file, sep=',', index=False)
    
    # Save all papers without MeSH terms to errors.csv
    if error_rows:
        errors_df = pd.DataFrame(error_rows)
        errors_df.to_csv(errors_file, sep=',', index=False)
        print(f"\n{len(error_rows)} papers without MeSH terms saved to: {errors_file}")
    
    print(f"\n{'='*70}")
    print(f"Processing complete!")
    print(f"Total papers processed: {processed_count}")
    print(f"Papers with MeSH terms found: {found_mesh_count} ({found_mesh_count/processed_count*100:.1f}%)")
    print(f"Papers without MeSH terms: {len(error_rows)} ({len(error_rows)/processed_count*100:.1f}%)")
    print(f"Output saved to: {output_file}")
    if error_rows:
        print(f"Errors saved to: {errors_file}")
    print(f"{'='*70}")
    
    return df

# Example usage
if __name__ == "__main__":
    # Configuration
    INPUT_FILE = "node_attributes_moved_8394.csv"  # Replace with your file path
    
    # For testing on first 100 papers:
    df = process_csv_with_mesh(INPUT_FILE, end_row=10)
    
    # For processing all papers:
    # df = process_csv_with_mesh(INPUT_FILE)
    
    # For resuming from row 5000:
    # df = process_csv_with_mesh(INPUT_FILE, start_row=5000)
    
    # Display sample results
    print("\nSample of papers with MeSH terms:")
    print(df[df['MESH'] != ''][['Label', 'MESH']].head(10))