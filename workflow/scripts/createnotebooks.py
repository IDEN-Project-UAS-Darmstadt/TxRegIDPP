from pathlib import Path

datanames = [
    "empfaenger_dringlichkeit",
    "empfaenger",
    "empfaenger_immunologie",
    "empfaenger_virologie",
    "followup_niere",
    "followup_niere_medikation",
    "organ_entnahme_niere",
    "spender_postmortem",
    "spender_postmortem_diagnosen",
    "spender_postmortem_labor_blutgase",
    "spender_postmortem_labor_blutgruppe",
    "spender_postmortem_labor_crossmatch",
    "spender_postmortem_labor_hla",
    "spender_postmortem_labor_klinische_chemie",
    "spender_postmortem_labor_mikrobiologie",
    "spender_postmortem_labor_pathologie",
    "spender_postmortem_labor_toxikologie",
    "spender_postmortem_labor_urin",
    "spender_postmortem_labor_virologie",
    "spender_postmortem_medikation",
    "spender_postmortem_monitoring",
    "spender_postmortem_untersuchungen",
    "transplantation_postop_untersuchung",
    "transplantation",
    "warteliste_niere",
]

basepath = Path(__file__).parent.parent / "notebooks"

nametemplate = "1_{step}_{name}.py.ipynb"
filetemplate = "template_{step}_filter.py.ipynb"
emptymarker = "IAMEMPTY"


for step in ["before", "after"]:
    with open(basepath / filetemplate.format(step=step), "rt") as fh:
        filetemplatecon = fh.read()

    for dataname in datanames:
        towrite = basepath / nametemplate.format(name=dataname, step=step)
        if towrite.exists():
            with open(towrite, "rt") as fh:
                txt = fh.read()
            if emptymarker not in txt:
                continue
            print(f"Replacing {towrite.name}!")
        print(f"Writing {towrite.name}...")
        with open(towrite, "wt") as fh:
            fh.write(filetemplatecon.replace("NAMEHERE", dataname))
