notebooks := 'workflow/notebooks/'
pythons := "workflow/scripts/*.py"

# List recipes
@default:
  @just --list

# Run linters on the Python, Notebooks and Snakemake files
@lint:
  echo "Linting Snakemake files..."
  snakefmt --check --compact-diff .
  echo "Linting notebooks with Black..."
  black {{notebooks}} --check --diff
  echo "Linting notebooks with flake8..."
  nbqa flake8 {{notebooks}} --nbqa-files '.py.ipynb$' --extend-ignore E501,E402,F821
  echo "Linting python files with Black..."
  black --check --diff {{pythons}}
  echo "Linting python files with Flake8..."
  flake8 {{pythons}} --extend-ignore E501,E402,F821
  echo "Linting markdown files with markdownlint..."
  markdownlint . -i results

# Run formatters on the Python, Notebooks and Snakemake files
@fmt:
  echo "Formatting Snakemake files..."
  snakefmt .
  echo "Removing output cells from notebooks..."
  find . -name '*.py.ipynb' -exec jupyter nbconvert --clear-output --log-level WARN --inplace {} +
  echo "Formatting notebooks with Black..."
  black {{notebooks}}
  echo "Formatting python files with Black..."
  black {{pythons}}
  echo "Formatting markdown files with markdownlint..."
  markdownlint . -i results -q --fix || true

# Clean all outputs
@clean:
  rm -rf results/*

# Pin the versions of the conda packages (In /tmp, to remove temporary files)
@pin:
  cd /tmp && snakedeploy --verbose pin-conda-envs --conda-frontend mamba {{invocation_directory()}}/workflow/envs/*.yml
  echo "Please check the first lines of the pin files, they may contain unnecessary lines."

# Produce the specified file
@create outputfile:
  snakemake --use-conda --rerun-incomplete --keep-going --cores 'all'  --persistence-backend db {{outputfile}}

# Create environments necessary to run the workflow in Snakemake
@env_prep:
  snakemake --use-conda --cores 'all' 'env_setup' --persistence-backend db --conda-create-envs-only

# Edit a specific notebook (give the path to the result)
@edit notebook:
  just create install_kernel
  just create {{notebook}}
  python3 workflow/notebooks/dev/prepare_nb_edit.py {{notebook}}
  echo "Copy dev.py.ipynb to workflow/notebooks/ and rename it to the right name."
  echo "Make sure the right kernel is active"

# Edit a specific notebook, using the snakemake notebook directive (only used for the additional analysis notebooks, not the main workflow notebooks)
@edit_nb outputfile:
  snakemake --use-conda --cores 1 --persistence-backend db --edit-notebook {{outputfile}}