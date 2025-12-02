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
*Output*: filtered_with_transferred_mesh_fixed
