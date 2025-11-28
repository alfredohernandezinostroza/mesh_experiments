# %%
from pymedx import PubMed
from pathlib import Path
import json

pubmed = PubMed(tool="GetMotorLearningPublications", email="your@email.address")
# query = 'The time course of changes during motor sequence learning: a whole-brain fMRI study '
query = '"Motor Learning" OR "Skill Acquisition" OR "Motor Adaptation" OR "Motor Sequence Learning" OR "Sport Practice" OR "Motor Skill Learning" OR "Sensorimotor Learning" OR "Motor Memory" OR "Motor Training"[Title] AND ("1933/01/01"[Date - Publication]: "2025/04/08"[Date - Publication])'

# Get just one result to inspect
results = list(pubmed.query(query, max_results=1))

if results:
    article = results[0]
    
    print(article)
    print(f"Title: {article.title}")
    # print(f"Link: {article.link}")
    # Check available attributes
    print("Available attributes:")
    print(dir(article))
    
    # Try to access MeSH terms in different ways
    print("\nChecking for MeSH terms:")
    
    # Common attribute names
    for attr in ['mesh', 'mesh_terms', 'meshTerms', 'keywords']:
        if hasattr(article, attr):
            print(f"{attr}: {getattr(article, attr)}")
    
    # Check the XML directly
    if hasattr(article, 'xml'):
        print("\nXML structure available")
# %%
