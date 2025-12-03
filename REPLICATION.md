## How to replicate these results?

## 1. Find MeSH terms for ``node_attributes.csv``
Run ``add_mesh_node_attributtes.py`` as it is. It will take around ~20 hours. It will generate:
 - ``node_attributes.csv``
 - ``node_attributes_with_mesh.csv``
 - ``node_attributes_errors.csv``

 *I'm not sure where the bottleneck is, as it should definetely be faster. If it is during the retrieval phase from PubMed, maybe if you add API Credentials to metapub it will be faster.*

## 2. Copy MeSH terms from an existing local database with Mesh and Mesh_id columns into another one
Run ``transfer_mesh_column_to_gexf.py``. It will generate:
- ``filtered_with_transferred_mesh.csv``.

## 3. Manually edit
The code unfortunately makes a mistake: it replaces the attributes' id with a number, and keeps its original string id as a title, which will break app.js. So using search and replace I switched it back for all nodes, and with regex I restored the attributes declarations.
*Output*: filtered_with_transferred_mesh_fixed.gexf

## 4. Fixing MeSH terms with a comma
There was another mistake: there are some MeSH terms that have a comma, thus they get separated if we use the comma as a separator. The code to fix it is ``fix_gexf_mesh_using_mesh_csv``, and was used with the command `pixi run python scripts/fix_gexf_mesh_using_mesh_csv.py filtered_with_transferred_mesh_fixed.gexf MeSH_complete.csv`.

For that, first the file `Mesh_complete.csv` was generated with the script `parse_mesh_ascii_to_csv.py`, using the command `pixi run python scripts/parse_mesh_ascii_to_csv.py d2025.bin MeSH_complete.csv`. The file `d2025.bin` was downloaded from https://www.nlm.nih.gov/databases/download/mesh.html on 02/12/2025, in the subsection ASCII Format -> Download Current Poduction Year MeSH in ASCII format.

## 5. Generate histograms

The files `mesh_histograms_by_modularity.py` and `keywords_histograms_by_modularity.py` were used to generate the histograms, using the commands `pixi run python scripts/mesh_histograms_by_modularity.py filtered_with_transferred_mesh_fixed_fix_commas.gexf` and 
`pixi run python scripts/keywords_histograms_by_modularity.py ./filtered_with_transferred_mesh_fixed_fix_commas.gexf`, respectively.
