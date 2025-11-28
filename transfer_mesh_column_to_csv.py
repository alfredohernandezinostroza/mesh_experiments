import pandas as pd
import re
from pathlib import Path

def normalize_string(s):
    """
    Normalize a string for comparison by removing punctuation, 
    extra spaces, and converting to lowercase
    """
    if pd.isna(s):
        return ''
    s = str(s).lower()
    s = re.sub(r'[^\w\s]', '', s)  # Remove punctuation
    s = re.sub(r'\s+', ' ', s)  # Normalize whitespace
    return s.strip()

def find_matching_row(target_row, source_df, matching_columns):
    """
    Find a matching row in source_df using multiple matching strategies
    Returns (match_index, match_method) or (None, None) if no match found
    """
    # Strategy 1: Try exact DOI match (most reliable)
    if 'Doi' in matching_columns and pd.notna(target_row.get('Doi')) and target_row.get('Doi').strip():
        doi = str(target_row['Doi']).strip()
        matches = source_df[source_df['Doi'].astype(str).str.strip() == doi]
        if len(matches) == 1:
            return matches.index[0], 'DOI'
        elif len(matches) > 1:
            print(f"Warning: Multiple matches found for DOI {doi}")
    
    # Strategy 2: Try exact title match
    if 'Label' in matching_columns and pd.notna(target_row.get('Label')) and target_row.get('Label').strip():
        title = str(target_row['Label']).strip()
        matches = source_df[source_df['Label'].astype(str).str.strip() == title]
        if len(matches) == 1:
            return matches.index[0], 'Title (exact)'
        elif len(matches) > 1:
            print(f"Warning: Multiple matches found for title: {title[:50]}...")
    
    # Strategy 3: Try normalized title match (handles minor differences)
    if 'Label' in matching_columns and pd.notna(target_row.get('Label')):
        normalized_target = normalize_string(target_row['Label'])
        if normalized_target:
            for idx, row in source_df.iterrows():
                normalized_source = normalize_string(row.get('Label', ''))
                if normalized_source and normalized_target == normalized_source:
                    return idx, 'Title (normalized)'
    
    # Strategy 4: Try combining Author + Date + partial title match
    if all(col in matching_columns for col in ['Author', 'Date', 'Label']):
        if pd.notna(target_row.get('Author')) and pd.notna(target_row.get('Date')) and pd.notna(target_row.get('Label')):
            author = normalize_string(target_row['Author'])
            date = str(target_row['Date']).strip()
            title_words = set(normalize_string(target_row['Label']).split())
            
            if author and date and title_words:
                for idx, row in source_df.iterrows():
                    source_author = normalize_string(row.get('Author', ''))
                    source_date = str(row.get('Date', '')).strip()
                    source_title = normalize_string(row.get('Label', ''))
                    source_words = set(source_title.split())
                    
                    # Check if author matches, date matches, and >80% of title words match
                    if (source_author == author and 
                        source_date == date and 
                        title_words and source_words):
                        overlap = len(title_words & source_words) / len(title_words)
                        if overlap > 0.8:
                            return idx, 'Author+Date+Title'
    
    return None, None

def transfer_mesh_terms(source_file, target_file, output_file=None):
    """
    Transfer MESH and MESH_ID columns from source CSV to target CSV
    
    Parameters:
    -----------
    source_file : str or Path
        CSV file with MESH terms already populated
    target_file : str or Path
        CSV file that needs MESH terms
    output_file : str or Path, optional
        Output file path. If None, creates target_with_mesh.csv
    """
    
    print("=" * 80)
    print("MESH TERMS TRANSFER")
    print("=" * 80)
    
    # Read both CSV files
    print(f"\nReading source file: {source_file}")
    source_df = pd.read_csv(source_file, sep=',')
    print(f"  → Loaded {len(source_df)} papers")
    print(f"  → Columns: {list(source_df.columns)}")
    
    print(f"\nReading target file: {target_file}")
    target_df = pd.read_csv(target_file, sep=',')
    print(f"  → Loaded {len(target_df)} papers")
    print(f"  → Columns: {list(target_df.columns)}")
    
    # Verify source has MESH columns
    if 'MESH' not in source_df.columns or 'MESH_ID' not in source_df.columns:
        print("\nERROR: Source file must have 'MESH' and 'MESH_ID' columns!")
        return None
    
    # Add MESH columns to target if they don't exist
    if 'MESH' not in target_df.columns:
        target_df['MESH'] = ''
    if 'MESH_ID' not in target_df.columns:
        target_df['MESH_ID'] = ''
    
    # Determine which columns are available for matching
    matching_columns = ['Doi', 'Label', 'Author', 'Date']
    available_columns = [col for col in matching_columns if col in source_df.columns and col in target_df.columns]
    
    print(f"\nAvailable columns for matching: {available_columns}")
    
    # Determine output file
    if output_file is None:
        target_path = Path(target_file)
        output_file = target_path.parent / f"{target_path.stem}_with_mesh.csv"
    
    print(f"Output will be saved to: {output_file}\n")
    
    # Track statistics
    stats = {
        'total': len(target_df),
        'matched': 0,
        'not_matched': 0,
        'already_had_mesh': 0,
        'methods': {}
    }
    
    unmatched_rows = []
    
    # Process each row in target
    print("Processing papers...")
    for idx in range(len(target_df)):
        # Skip if already has MESH terms
        if pd.notna(target_df.loc[idx, 'MESH']) and target_df.loc[idx, 'MESH'].strip():
            stats['already_had_mesh'] += 1
            continue
        
        # Find matching row in source
        match_idx, match_method = find_matching_row(target_df.loc[idx], source_df, available_columns)
        
        if match_idx is not None:
            # Transfer MESH data
            target_df.loc[idx, 'MESH'] = source_df.loc[match_idx, 'MESH']
            target_df.loc[idx, 'MESH_ID'] = source_df.loc[match_idx, 'MESH_ID']
            stats['matched'] += 1
            stats['methods'][match_method] = stats['methods'].get(match_method, 0) + 1
        else:
            stats['not_matched'] += 1
            unmatched_rows.append(target_df.loc[idx].copy())
        
        # Progress update
        if (idx + 1) % 500 == 0:
            print(f"  Processed {idx + 1}/{len(target_df)} papers...")
    
    # Save output
    target_df.to_csv(output_file, sep=',', index=False)
    
    # Save unmatched rows
    if unmatched_rows:
        unmatched_path = Path(output_file).parent / "unmatched_papers.csv"
        pd.DataFrame(unmatched_rows).to_csv(unmatched_path, sep=',', index=False)
    
    # Print statistics
    print("\n" + "=" * 80)
    print("TRANSFER COMPLETE")
    print("=" * 80)
    print(f"\nTotal papers in target: {stats['total']}")
    print(f"Already had MESH terms: {stats['already_had_mesh']}")
    print(f"Successfully matched: {stats['matched']} ({stats['matched']/stats['total']*100:.1f}%)")
    print(f"Not matched: {stats['not_matched']} ({stats['not_matched']/stats['total']*100:.1f}%)")
    
    print("\nMatching methods used:")
    for method, count in sorted(stats['methods'].items(), key=lambda x: x[1], reverse=True):
        print(f"  {method}: {count} papers ({count/stats['matched']*100:.1f}%)")
    
    print(f"\nOutput saved to: {output_file}")
    if unmatched_rows:
        print(f"Unmatched papers saved to: {unmatched_path}")
    
    print("\nSample of transferred MESH terms:")
    sample = target_df[target_df['MESH'] != ''][['Label', 'MESH', 'MESH_ID']].head(5)
    if not sample.empty:
        print(sample.to_string())
    
    return target_df

# Example usage
if __name__ == "__main__":
    # Configuration
    SOURCE_FILE = "node_attributes_with_mesh.csv"  # File that already has MESH terms
    TARGET_FILE = "filtered.csv"  # File that needs MESH terms
    
    # Transfer MESH terms
    df = transfer_mesh_terms(SOURCE_FILE, TARGET_FILE, output_file=f"{TARGET_FILE}_with_transferred_mesh.csv")