from metapub import PubMedFetcher
import json

# Initialize the fetcher
fetch = PubMedFetcher()

# Search for the paper by title
title = "The time course of changes during motor sequence learning: a whole-brain fMRI study"

print(f"Searching for: {title}\n")

# Search PubMed for the article
pmids = fetch.pmids_for_query(title, retmax=5)

if not pmids:
    print("No articles found with that title.")
else:
    print(f"Found {len(pmids)} article(s)\n")
    
    # Get the first result (most relevant)
    pmid = pmids[0]
    print(f"PMID: {pmid}\n")
    
    # Fetch the article details
    article = fetch.article_by_pmid(pmid)
    
    # Display basic information
    print("=" * 80)
    print("ARTICLE INFORMATION")
    print("=" * 80)
    print(f"Title: {article.title}")
    print(f"Authors: {', '.join(article.authors) if article.authors else 'N/A'}")
    print(f"Journal: {article.journal}")
    print(f"Year: {article.year}")
    print(f"PMID: {article.pmid}")
    print(f"DOI: {article.doi if article.doi else 'N/A'}")
    
    # Get MeSH terms
    print("\n" + "=" * 80)
    print("MESH TERMS")
    print("=" * 80)
    
    if hasattr(article, 'mesh') and article.mesh:
        mesh_terms = article.mesh
        print(f"\nFound {len(mesh_terms)} MeSH terms:\n")
        
        for i, term in enumerate(mesh_terms, 1):
            # MeSH terms in metapub are dictionary objects
            if isinstance(term, dict):
                descriptor = term.get('descriptor_name', 'N/A')
                is_major = term.get('is_major_topic', False)
                qualifiers = term.get('qualifier_name', [])
                
                major_indicator = " [MAJOR TOPIC]" if is_major else ""
                print(f"{i}. {descriptor}{major_indicator}")
                
                if qualifiers:
                    for qualifier in qualifiers:
                        if isinstance(qualifier, dict):
                            qual_name = qualifier.get('qualifier_name', 'N/A')
                            qual_major = qualifier.get('is_major_topic', False)
                            qual_indicator = " [MAJOR]" if qual_major else ""
                            print(f"   - {qual_name}{qual_indicator}")
                        else:
                            print(f"   - {qualifier}")
            else:
                # If it's just a string
                print(f"{i}. {term}")
        
        # Save to JSON
        output_data = {
            'pmid': article.pmid,
            'title': article.title,
            'authors': article.authors if article.authors else [],
            'journal': article.journal,
            'year': article.year,
            'doi': article.doi,
            'mesh_terms': mesh_terms
        }
        
        output_file = 'mesh_terms_output.json'
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        print(f"\n\nData saved to: {output_file}")
        
    else:
        print("\nNo MeSH terms found for this article.")
        print("This might mean:")
        print("- The article is too recent and hasn't been indexed yet")
        print("- The article is not in PubMed's database")
        print("- MeSH terms weren't assigned to this article")
    
    # Also try to get the abstract
    if hasattr(article, 'abstract') and article.abstract:
        print("\n" + "=" * 80)
        print("ABSTRACT")
        print("=" * 80)
        print(f"\n{article.abstract}")