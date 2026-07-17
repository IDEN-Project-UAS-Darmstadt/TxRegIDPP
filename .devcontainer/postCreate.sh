#!/usr/bin/env bash
set -euo pipefail

# Fix the permissions, requires sudo access to chown
fix_directory_permissions() {
    local target_dir="${1}"
    local check_subdir="${2:-}"
    
    # Determine the directory to check permissions on
    local check_path="${target_dir}"
    if [ -n "${check_subdir}" ]; then
        check_path="${target_dir}/${check_subdir}"
    fi
    
    local current_user=$(whoami)
    local current_uid=$(id -u)
    local current_gid=$(id -g)
    local dir_uid=$(stat -c '%u' "${check_path}")
    local dir_gid=$(stat -c '%g' "${check_path}")
    
    if [ "${current_uid}" -eq "${dir_uid}" ] && [ "${current_gid}" -eq "${dir_gid}" ]; then
        echo "Permissions of ${target_dir} are already correct. Skipping..."
    else
        echo "Fixing permissions of ${target_dir} for user ${current_user}..."
        echo "This may take a few minutes..."
        sudo chown -R "${current_user}":"${current_user}" "${target_dir}"
    fi
}
# First argument is the target of chown
# second optional argument is a subdirectory to check permissions on
fix_directory_permissions /opt/conda pkgs
# This is on a volume, the rights may be wrong
mkdir -p  ~/snakemake_conda
fix_directory_permissions ~/snakemake_conda

just env_prep
just create install_kernel
micromamba clean --all -y