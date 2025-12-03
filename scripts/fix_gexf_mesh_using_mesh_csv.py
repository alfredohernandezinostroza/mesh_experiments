#!/usr/bin/env python3
"""Fix `mesh` attributes in a GEXF by resolving `mesh_id` UIs to MH labels.

For nodes where the number of comma-separated entries in the `mesh` attribute
differs from the number of comma-separated entries in `mesh_id`, this script
rebuilds `mesh` by looking up every UI from `mesh_id` in a MeSH CSV (from
`parse_mesh_ascii_to_csv.py`). The resulting mesh terms are joined with
semicolon separators and written back into the GEXF node `mesh` attvalue.

The script writes a CSV log `gexf_mesh_fix_logs.csv` with columns:
  node_label,node_id,mesh_before,mesh_after

And appends missing UI identifiers to `errors.txt` with the node id and label.

Important: the script edits only the `value` attribute of the existing
`<attvalue for="mesh" .../>` elements in the GEXF text, leaving the
attributes declaration block unchanged.

Usage:
  python scripts/fix_gexf_mesh_using_mesh_csv.py filtered_with_transferred_mesh_fixed.gexf MeSH_complete.csv

Output:
  - writes a new GEXF file named `<input>.mesh_fixed.gexf`
  - `gexf_mesh_fix_logs.csv` and `errors.txt` in the current directory
"""

from pathlib import Path
import sys
import csv
import re
from xml.sax.saxutils import escape as xml_escape


def load_mesh_mapping(mesh_csv_path):
    mapping = {}
    with open(mesh_csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        # normalize header names
        headers = [h.strip() for h in reader.fieldnames]
        ui_col = None
        mh_col = None
        for h in headers:
            if h.upper() == 'UI':
                ui_col = h
            if h.upper() == 'MH':
                mh_col = h
        if ui_col is None or mh_col is None:
            raise ValueError('Mesh CSV must contain UI and MH columns')

        for row in reader:
            ui = row.get(ui_col, '').strip()
            mh_val = row.get(mh_col, '').strip()
            if not ui:
                continue
            # if MH contains '||' joined values, take the first as the main heading
            if '||' in mh_val:
                mh_val = mh_val.split('||', 1)[0].strip()
            mapping[ui] = mh_val
    return mapping


def process_gexf(in_path: Path, out_path: Path, mesh_map: dict, logs_path: Path, errors_path: Path):
    node_buf = []
    inside_node = False
    changed_count = 0
    total_checked = 0

    # prepare logs
    logs_file = open(logs_path, 'a', newline='', encoding='utf-8')
    logs_writer = csv.writer(logs_file)
    if logs_path.stat().st_size == 0:
        logs_writer.writerow(['node_label', 'node_id', 'mesh_before', 'mesh_after'])

    errors_file = open(errors_path, 'a', encoding='utf-8')

    with open(in_path, 'r', encoding='utf-8', errors='replace') as inp, open(out_path, 'w', encoding='utf-8') as out:
        for line in inp:
            if line.lstrip().startswith('<node '):
                inside_node = True
                node_buf = [line]
                continue

            if inside_node:
                node_buf.append(line)
                if line.lstrip().startswith('</node>'):
                    # process node block
                    block = ''.join(node_buf)

                    # extract node id and label from opening tag
                    mnode = re.search(r'<node\s+[^>]*id="(?P<id>[^"]+)"\s+label="(?P<label>[^"]*)"', block)
                    node_id = mnode.group('id') if mnode else ''
                    node_label = mnode.group('label') if mnode else ''

                    # find mesh and mesh_id attvalues
                    mm = re.search(r'<attvalue\s+for="mesh"\s+value="(?P<mesh>[^"]*)"\s*/>', block)
                    mid = re.search(r'<attvalue\s+for="mesh_id"\s+value="(?P<mesh_id>[^"]*)"\s*/>', block)

                    if mm and mid:
                        mesh_before = mm.group('mesh')
                        mesh_id_raw = mid.group('mesh_id')
                        # compute counts
                        mesh_count = len([s for s in mesh_before.split(',') if s.strip()])
                        mesh_id_count = len([s for s in mesh_id_raw.split(',') if s.strip()])
                        total_checked += 1
                        if mesh_count != mesh_id_count:
                            # rebuild mesh from mesh_id UIs
                            mesh_ids = [s.strip() for s in mesh_id_raw.split(',') if s.strip()]
                            mh_list = []
                            missing = []
                            for ui in mesh_ids:
                                if ui in mesh_map and mesh_map[ui]:
                                    mh_list.append(mesh_map[ui])
                                else:
                                    missing.append(ui)
                            if mh_list:
                                mesh_after = '; '.join(mh_list)
                            else:
                                mesh_after = ''

                            # log change
                            logs_writer.writerow([node_label, node_id, mesh_before, mesh_after])
                            logs_file.flush()

                            # log missing IDs
                            for ui in missing:
                                errors_file.write(f'{ui}\t{node_id}\t{node_label}\n')
                            errors_file.flush()

                            # replace mesh value in block (escape for XML)
                            mesh_after_escaped = xml_escape(mesh_after, {'"': '&quot;'})
                            new_block = re.sub(r'(<attvalue\s+for="mesh"\s+value=")(?P<old>[^"]*)("\s*/>)',
                                               r'\1' + mesh_after_escaped + r'\3',
                                               block,
                                               count=1)
                            out.write(new_block)
                            changed_count += 1
                        else:
                            out.write(block)
                    else:
                        # node has no mesh or mesh_id; write unchanged
                        out.write(block)

                    inside_node = False
                # continue reading
            else:
                out.write(line)

    logs_file.close()
    errors_file.close()
    return total_checked, changed_count


def main(argv):
    if len(argv) < 3:
        print('Usage: fix_gexf_mesh_using_mesh_csv.py input.gexf MeSH_complete.csv [out.gexf]')
        return 1
    in_gexf = Path(argv[1])
    mesh_csv = Path(argv[2])
    out_gexf = Path(argv[3]) if len(argv) > 3 else in_gexf.with_name(in_gexf.stem + '_fix_commas.gexf')

    if not in_gexf.exists():
        print('Input GEXF not found:', in_gexf)
        return 1
    if not mesh_csv.exists():
        print('MeSH CSV not found:', mesh_csv)
        return 1

    print('Loading MeSH mapping from', mesh_csv)
    mesh_map = load_mesh_mapping(mesh_csv)
    print('Loaded', len(mesh_map), 'UI -> MH mappings')

    logs_path = Path('gexf_mesh_fix_logs.csv')
    errors_path = Path('errors.txt')

    print('Processing GEXF and writing to', out_gexf)
    total_checked, changed = process_gexf(in_gexf, out_gexf, mesh_map, logs_path, errors_path)
    print(f'Processed {total_checked} nodes (mesh present with mesh_id), changed {changed} nodes')
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
