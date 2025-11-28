import networkx as nx
import pandas as pd
import re
from pathlib import Path
from tqdm import tqdm

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

def find_mesh_for_node_optimized(node_label, node_doi, csv_df, normalized_labels_cache):
    """
    Find matching MESH terms from CSV based on node label (title) or DOI
    Uses pre-computed normalized labels cache for faster lookup.
    Returns (mesh_terms, mesh_ids) or (None, None) if not found
    """
    # Strategy 1: Try DOI match (most reliable)
    if pd.notna(node_doi) and str(node_doi).strip():
        doi = str(node_doi).strip()
        matches = csv_df[csv_df['Doi'].astype(str).str.strip() == doi]
        if len(matches) == 1:
            row = matches.iloc[0]
            mesh = row.get('MESH', '')
            mesh_id = row.get('MESH_ID', '')
            if pd.notna(mesh) and str(mesh).strip():
                return str(mesh), str(mesh_id) if pd.notna(mesh_id) else ''
    
    # Strategy 2: Try exact label (title) match
    if pd.notna(node_label) and str(node_label).strip():
        label = str(node_label).strip()
        matches = csv_df[csv_df['Label'].astype(str).str.strip() == label]
        if len(matches) == 1:
            row = matches.iloc[0]
            mesh = row.get('MESH', '')
            mesh_id = row.get('MESH_ID', '')
            if pd.notna(mesh) and str(mesh).strip():
                return str(mesh), str(mesh_id) if pd.notna(mesh_id) else ''
    
    # Strategy 3: Try normalized label match using pre-computed cache (O(1) lookup)
    if pd.notna(node_label):
        normalized_label = normalize_string(node_label)
        if normalized_label and normalized_label in normalized_labels_cache:
            idx = normalized_labels_cache[normalized_label]
            row = csv_df.iloc[idx]
            mesh = row.get('MESH', '')
            mesh_id = row.get('MESH_ID', '')
            if pd.notna(mesh) and str(mesh).strip():
                return str(mesh), str(mesh_id) if pd.notna(mesh_id) else ''
    
    return None, None

def add_mesh_to_gexf(gexf_file, csv_file, output_file=None):
    """
    Add MESH and MESH_ID attributes to nodes in a GEXF file from a CSV
    
    Parameters:
    -----------
    gexf_file : str or Path
        Path to input GEXF file
    csv_file : str or Path
        Path to CSV file containing MESH terms
    output_file : str or Path, optional
        Path to output GEXF file. If None, creates input_with_mesh.gexf
    """
    
    print("=" * 80)
    print("ADDING MESH TERMS TO GEXF FILE")
    print("=" * 80)
    
    # Read CSV file
    print(f"\nReading CSV file: {csv_file}")
    csv_df = pd.read_csv(csv_file, sep=',')
    print(f"  → Loaded {len(csv_df)} papers with MESH terms")
    print(f"  → Columns: {list(csv_df.columns)}")
    
    # Verify CSV has MESH columns
    if 'MESH' not in csv_df.columns:
        print("\nERROR: CSV file must have 'MESH' column!")
        return False
    
    mesh_id_available = 'MESH_ID' in csv_df.columns
    if not mesh_id_available:
        print("\nWarning: CSV file doesn't have 'MESH_ID' column. Only MESH terms will be added.")
    
    # Read GEXF file
    print(f"\nReading GEXF file: {gexf_file}")
    G = nx.read_gexf(gexf_file)
    print(f"  → Loaded graph with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")
    
    # Get sample of existing attributes
    if G.number_of_nodes() > 0:
        sample_node = list(G.nodes())[0]
        sample_attrs = list(G.nodes[sample_node].keys())
        print(f"  → Sample node attributes: {sample_attrs[:5]}...")
    
    # Determine output file
    if output_file is None:
        gexf_path = Path(gexf_file)
        output_file = gexf_path.parent / f"{gexf_path.stem}_with_mesh.gexf"
    
    print(f"\nOutput will be saved to: {output_file}\n")
    
    # Track statistics
    stats = {
        'total_nodes': G.number_of_nodes(),
        'matched': 0,
        'not_matched': 0,
        'already_had_mesh': 0,
        'match_methods': {
            'DOI': 0,
            'Title (exact)': 0,
            'Title (normalized)': 0
        }
    }
    
    unmatched_nodes = []
    
    # Pre-compute normalized labels cache for faster lookup (O(1) instead of O(n))
    print("\nBuilding normalized labels cache...")
    normalized_labels_cache = {}
    for idx, row in csv_df.iterrows():
        normalized = normalize_string(row.get('Label', ''))
        if normalized:
            normalized_labels_cache[normalized] = idx
    print(f"  → Built cache with {len(normalized_labels_cache)} normalized labels")
    
    # Process each node
    print("\nProcessing nodes...")
    for i, (node_id, node_data) in enumerate(tqdm(G.nodes(data=True), total=G.number_of_nodes(), desc="Processing nodes")):
        # Check if already has MESH attribute
        if 'mesh' in node_data and node_data['mesh']:
            stats['already_had_mesh'] += 1
            continue
        
        # Get node label and DOI
        node_label = node_data.get('label', '')
        node_doi = node_data.get('doi', '')
        
        # Find matching MESH terms
        mesh, mesh_id = find_mesh_for_node_optimized(node_label, node_doi, csv_df, normalized_labels_cache)
        
        if mesh:
            # Add MESH attributes to node
            G.nodes[node_id]['mesh'] = mesh
            if mesh_id_available and mesh_id:
                G.nodes[node_id]['mesh_id'] = mesh_id
            
            stats['matched'] += 1
            
            # Track which method worked
            if node_doi and pd.notna(node_doi):
                # Check if DOI match worked
                doi_matches = csv_df[csv_df['Doi'].astype(str).str.strip() == str(node_doi).strip()]
                if len(doi_matches) == 1:
                    stats['match_methods']['DOI'] += 1
                elif normalize_string(node_label) == normalize_string(csv_df[csv_df['MESH'] == mesh].iloc[0].get('Label', '')):
                    stats['match_methods']['Title (normalized)'] += 1
                else:
                    stats['match_methods']['Title (exact)'] += 1
            else:
                # Must be title match
                exact_match = csv_df[csv_df['Label'].astype(str).str.strip() == str(node_label).strip()]
                if len(exact_match) == 1:
                    stats['match_methods']['Title (exact)'] += 1
                else:
                    stats['match_methods']['Title (normalized)'] += 1
        else:
            stats['not_matched'] += 1
            unmatched_nodes.append({
                'node_id': node_id,
                'label': node_label,
                'doi': node_doi
            })
    
    # Save modified GEXF
    print(f"\nSaving modified GEXF file...")
    nx.write_gexf(G, output_file)
    
    # Save unmatched nodes if any
    if unmatched_nodes:
        unmatched_path = Path(output_file).parent / "unmatched_nodes.csv"
        pd.DataFrame(unmatched_nodes).to_csv(unmatched_path, sep=',', index=False)
    
    # Print statistics
    print("\n" + "=" * 80)
    print("PROCESS COMPLETE")
    print("=" * 80)
    print(f"\nTotal nodes in graph: {stats['total_nodes']}")
    print(f"Already had MESH terms: {stats['already_had_mesh']}")
    print(f"Successfully matched: {stats['matched']} ({stats['matched']/stats['total_nodes']*100:.1f}%)")
    print(f"Not matched: {stats['not_matched']} ({stats['not_matched']/stats['total_nodes']*100:.1f}%)")
    
    print("\nMatching methods used:")
    for method, count in sorted(stats['match_methods'].items(), key=lambda x: x[1], reverse=True):
        if count > 0:
            print(f"  {method}: {count} nodes ({count/stats['matched']*100:.1f}% of matched)")
    
    print(f"\nOutput saved to: {output_file}")
    if unmatched_nodes:
        print(f"Unmatched nodes saved to: {unmatched_path}")
        print(f"\nYou can run the PubMed search script on unmatched_nodes.csv to get their MESH terms.")
    
    # Show sample of nodes with MESH terms
    print("\nSample of nodes with MESH terms added:")
    sample_count = 0
    for node_id, node_data in G.nodes(data=True):
        if 'mesh' in node_data and node_data['mesh']:
            print(f"\nNode {node_id}:")
            print(f"  Label: {node_data.get('label', 'N/A')[:80]}...")
            print(f"  MESH: {node_data['mesh'][:100]}...")
            if 'mesh_id' in node_data:
                print(f"  MESH_ID: {node_data['mesh_id'][:100]}...")
            sample_count += 1
            if sample_count >= 3:
                break
    
    return G

# Example usage
if __name__ == "__main__":
    # Configuration
    GEXF_FILE = "filtered.gexf"  # Your graph file
    CSV_FILE = "node_attributes_with_mesh.csv"  # CSV with MESH terms
    
    # Add MESH terms to graph
    G = add_mesh_to_gexf(GEXF_FILE, CSV_FILE, output_file=f"{GEXF_FILE}_with_transferred_mesh.gexf")
    