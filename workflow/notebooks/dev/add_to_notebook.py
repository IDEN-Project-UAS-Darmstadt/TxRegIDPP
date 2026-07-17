import os
import nbformat
import sys
from pprint import pprint

# Define the directory containing the notebooks
notebook_dir = "."

# Define the path to the existing notebook with the specific cell
existing_notebook_path = "1_after_empfaenger_dringlichkeit.py.ipynb"

# Read the existing notebook to get the specific cell content
with open(existing_notebook_path, "r", encoding="utf-8") as f:
    existing_nb = nbformat.read(f, as_version=4)
    specific_cell = existing_nb.cells[:2]

pprint(specific_cell)

# Iterate over each file in the directory
for filename in os.listdir(notebook_dir):
    if (
        filename.endswith(".ipynb")
        and filename != existing_notebook_path
        and filename.startswith("1_after_")
    ):
        # Construct the full file path
        file_path = os.path.join(notebook_dir, filename)
        print(file_path)

        # Read the notebook
        with open(file_path, "r", encoding="utf-8") as f:
            nb = nbformat.read(f, as_version=4)

        # Prepend the specific cell to the notebook
        for cell in reversed(specific_cell):
            nb.cells.insert(0, cell)

        # Write the modified notebook back to the file
        with open(file_path, "w", encoding="utf-8") as f:
            nbformat.write(nb, f)
