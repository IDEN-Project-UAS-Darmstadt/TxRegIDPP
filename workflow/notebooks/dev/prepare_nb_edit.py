import os
import nbformat
import sys
from pprint import pprint
import re

targetkernel = "txregidpp"
targetkernel_display_name = "Python (TxReg Vorverarbeitung)"

# Read the existing notebook path from the first argument
if len(sys.argv) < 2:
    print("Usage: python prepare_nb_edit.py <existing_notebook_path>")
    sys.exit(1)

existing_notebook_path = sys.argv[1]

inj = None
par = None
with open(existing_notebook_path, "r", encoding="utf-8") as f:
    existing_nb = nbformat.read(f, as_version=4)
    for i, cell in enumerate(existing_nb.cells):
        if "tags" in cell.metadata:
            if "injected-parameters" in cell.metadata.tags:
                inj = i
            if "parameters" in cell.metadata.tags:
                par = i

pattern = r"\"\/.*?TxReg_Vorverarbeitung\/"
# Cell Source
# input_data = "resources/input/element_organ_entnahme_niere.csv"
# display_util = "/home/finesim/.cache/snakemake/snakemake/source-cache/runtime-cache/tmpf13l3vpd/file/mnt/f/Nextcloud/Workspaces/Linux/forschungsprojekt-iden/Teilprojekte/TxReg_Vorverarbeitung/workflow/scripts/display_util.py"
# util = "/home/finesim/.cache/snakemake/snakemake/source-cache/runtime-cache/tmpf13l3vpd/file/mnt/f/Nextcloud/Workspaces/Linux/forschungsprojekt-iden/Teilprojekte/TxReg_Vorverarbeitung/workflow/scripts/util.py"
# input_doc = "results/officialdoc.csv"
# output_data = (
#     "results/data/checkpoints/beforefilter_intermediate_organ_entnahme_niere.pq"
# )
#
if par is not None and inj is not None:
    existing_nb.cells[par] = existing_nb.cells[inj]
    if "source" in existing_nb.cells[par]:
        existing_nb.cells[par].source = "\n".join(
            re.sub(pattern, '"', line)
            for line in existing_nb.cells[par].source.splitlines()
        )
    existing_nb.cells[par].metadata.tags = ["parameters"]

if inj is not None:
    del existing_nb.cells[inj]

# Set the kernel to targetkernel
if "metadata" not in existing_nb:
    existing_nb.metadata = {}
if "kernelspec" not in existing_nb.metadata:
    existing_nb.metadata.kernelspec = {}
existing_nb.metadata.kernelspec["name"] = targetkernel
existing_nb.metadata.kernelspec["display_name"] = targetkernel_display_name

with open("dev.py.ipynb", "w", encoding="utf-8") as f:
    nbformat.write(existing_nb, f)
