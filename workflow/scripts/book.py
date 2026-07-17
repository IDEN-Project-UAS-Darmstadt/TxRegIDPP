#!/usr/bin/env python3
import shutil
import tempfile
from pathlib import Path
import nbformat as nbf
from glob import glob
import subprocess

booktemplatedir = snakemake.input["template"]
temp_dir = tempfile.TemporaryDirectory()
bookdir = Path(temp_dir.name) / "book"

shutil.copytree(booktemplatedir, bookdir)

targetpop = snakemake.input["targetpop"][0]
shutil.copy(targetpop, bookdir / "01_targetpop" / "index.ipynb")
prep = snakemake.input["prep"]
for prepfile in prep:
    shutil.copy(prepfile, bookdir / "02_preprocessing")
cons = snakemake.input["consolidate"][0]
shutil.copy(cons, bookdir / "03_consolidate" / "index.ipynb")
cons = snakemake.input["userfriendly"][0]
shutil.copy(cons, bookdir / "04_userfriendly" / "index.ipynb")

# https://jupyterbook.org/en/stable/content/metadata.html#jupyter-cell-tags
notebooks = list(
    glob((bookdir / "02_preprocessing" / "*.ipynb").as_posix(), recursive=True)
) + [
    bookdir / "03_consolidate" / "index.ipynb",
    bookdir / "04_userfriendly" / "index.ipynb",
    bookdir / "01_targetpop" / "index.ipynb",
]
for ipath in notebooks:
    ntbk = nbf.read(ipath, nbf.NO_CONVERT)

    for cell in ntbk.cells:
        cell_tags = cell.get("metadata", {}).get("tags", [])
        if "remove-input" not in cell_tags:
            cell_tags.append("remove-input")
        if len(cell_tags) > 0:
            cell["metadata"]["tags"] = cell_tags

    nbf.write(ntbk, ipath)

tocf = bookdir / "_toc.yml"
with open(tocf, "w") as toc:
    subprocess.run(
        [
            "jb",
            "toc",
            "from-project",
            "-f",
            "jb-book",
            "-e",
            ".md",
            "-e",
            ".ipynb",
            bookdir.as_posix(),
        ],
        stdout=toc,
    )

with open(tocf, "r") as f:
    contents = f.readlines()

contents.insert(2, "  numbered: True\n")
contents.insert(2, "options:\n")

with open(tocf, "w") as f:
    contents = "".join(contents)
    f.write(contents)

p = subprocess.run(["cat", tocf.as_posix()])
p = subprocess.run(["jb", "build", bookdir.as_posix()])

if p.returncode != 0:
    raise Exception(f"Invalid returncode: { p.returncode }")

# Remove the _sources directory from th html folder
subprocess.run(["rm", "-rf", (bookdir / "_build" / "html" / "_sources").as_posix()])

# This copy function ignores rights, so that it won't fail on mounted windows drives
cmds = [
    "rsync",
    "-a",  # archive mode (recursive + preserves attributes)
    "--no-perms",  # don't preserve permissions
    "--no-owner",  # don't preserve ownership
    "--no-group",  # don't preserve group ownership
    "--no-times",  # don't preserve modification times
    (bookdir / "_build" / "html/").as_posix(),  # note the trailing slash
    snakemake.output[0],
]
subprocess.run(cmds)

temp_dir.cleanup()
