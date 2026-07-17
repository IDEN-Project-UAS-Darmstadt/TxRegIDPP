# TxReg Data Preprocessing Pipeline (TxReg Vorverarbeitung)

A reproducible, Snakemake-based data preprocessing workflow designed to ingest,
clean, and consolidate legacy kidney export data from the
German Transplantation Registry (*Deutsches Transplantationsregister*).

This pipeline processes raw registry exports and generates a clean, validated,
and user-friendly dataset specifically focused on
**adult recipients of first kidney transplants from deceased donors**. It heavily
utilizes parameterized Jupyter Notebooks (via Papermill) to ensure every
step of the data transformation is transparent, auditable, and automatically
compiled into a comprehensive report.

This was part of the [IDEN project](https://iden.h-da.io/), which
ended in 2026 and the code is provided here for archival
and reproducibility purposes.

## 🚀 Key Features

* **Target Population Filtering:** Automatically excludes pediatric cases
    (<18 years), living donors, multi-organ recipients, and repeat
    transplantations.
* **Data Harmonization:** Integrates and harmonizes data from different
    registry contributors (e.g., ET and IQTIG), resolving redundancies
    and unifying unit measurements.
* **Longitudinal Data Aggregation:** Consolidates complex time-series and
    long-format laboratory/monitoring data into a single, flat,
    patient-level format.
* **Automated Reporting:** Generates an end-to-end HTML book/report of the
    data processing steps using Jupyter notebooks without any code.
* **Reproducible Infrastructure:** Fully containerized development environment
    (Devcontainer) with strictly pinned Conda environments and `just` command
    integration.

## 🛠 Tech Stack

* **Workflow Management:** [Snakemake](https://snakemake.github.io/)
* **Notebook Execution:** [Papermill](https://papermill.readthedocs.io/) & Jupyter
* **Data Processing:** Python, Pandas, PyArrow (Parquet)
* **Data Validation:** [Pandera](https://pandera.readthedocs.io/)
* **Task Runner:** [Just](https://just.systems/)
* **Environment:** Docker (Devcontainer) & micromamba

## 📂 Project Structure

```text
txreg-idpp/
├── config/              # Default pipeline configurations (YAML/CSV)
├── resources/
│   ├── book_template/   # Templates for the generated Jupyter Book report
│   ├── docdata/         # Official registry documentation used to extract info
│   └── input/           # ⚠️ RAW DATA DIR: Place your input *.csv files here
├── results/             # Pipeline outputs (processed data, checkpoints, full_report)
├── util/                # Installation and setup utilities
└── workflow/
    ├── envs/            # Conda environment specifications for Snakemake rules
    ├── notebooks/       # Parameterized Jupyter Notebooks (the core pipeline logic)
    └── scripts/         # Shared Python utility scripts

```

The project contains a DVC file, but this is only used internally.

## ⚙️ Prerequisites & Setup

This project uses a Devcontainer, which automates the setup and installation of
all required dependencies.

1. Install [Docker](https://www.docker.com/) and [VS Code](https://code.visualstudio.com/).
2. Install the **Dev Containers** extension in VS Code.
3. Clone this repository and open it in VS Code. You will be prompted to
   "Reopen in Container".
4. *Alternatively*, if running locally without Docker, ensure you have `mamba` or
   `conda` installed and use the provided `util/snakemake.yml` to create the
   required environment.

## 🏃‍♂️ Usage & Pipeline Execution

1. **Provide the Data:** Place the raw `*.csv` legacy export files into the
    `resources/input/` directory.
    *(Note: Registry data is strictly confidential and is not
    version-controlled).*
2. **Run the Pipeline:** Execute the following command to trigger Snakemake
    and process the data:

```bash
just create report
# The "consolidation" and "userfriendly" step take some time
```

1. **Retrieve Results:** * The final `.pq` (Parquet) dataset
    will be available in `results/data/flat_consolidated.pq`.

* A full HTML report documenting the entire run will be generated in `results/full_report/`.

*Troubleshooting:* If Snakemake encounters caching issues, clearing the
    `.snakemake` directory often resolves them. To clean all generated outputs,
    run `just clean`.

## 📝 Outputs

See the [outputs](outputs.ipynb) notebook for more details on the generated
files and their structure.

## 👨‍💻 Development

We use `just` as a command runner to simplify development tasks.

```bash
# Check code for style and syntax issues
just lint

# Automatically format code and strip outputs from notebooks
just fmt
```

**Editing Pipeline Notebooks**
Because the pipeline relies on parameterized notebooks,
editing them requires a specific
workflow to ensure parameters are handled correctly:

```bash
# 1. Provide the path to the resulting notebook checkpoint you wish to edit
just edit results/reports/checkpoints/1_beforefilter_organ_entnahme_niere.ipynb

# 2. This will generate a dev.py.ipynb file. Copy this file back to workflow/notebooks/
#    and overwrite the corresponding source notebook.
```

## 📄 License & Data Privacy

This code is licensed under the MIT License. See the [LICENSE](LICENSE)
file for details.

**Data Privacy Notice:** This repository contains the code for processing
sensitive medical data. No actual patient data or registry exports are
included in this repository. Users must obtain their own legal access to the
legacy kidney data from the
[Deutsches Transplantationsregister](https://www.transplantations-register.de/)
to utilize this pipeline.

**Documentation Archive Note:** The files located in the `resources/docdata/` 
directory are official documentation mirrored for archival purposes from the 
transplantation registry website. The MIT License of this repository does **not** 
apply to these files; they remain the intellectual property of their original 
publishers and respective copyright holders.