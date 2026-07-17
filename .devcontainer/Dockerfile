# syntax=docker/dockerfile:1.7-labs 
ARG MICROMAMBA_VERSION=2.3.2-cuda12.5.1-ubuntu22.04

FROM mambaorg/micromamba:${MICROMAMBA_VERSION}

# Install rsync for package caching and sudo to allow permission elevation
USER root
RUN apt-get update && apt-get install -y rsync sudo && rm -rf /var/lib/apt/lists/*
# Add sudo permissions for micromamba user
RUN echo "${MAMBA_USER} ALL=(ALL) NOPASSWD: /usr/bin/chown" >> /etc/sudoers
# Add postCreate.sh script to micromamba user home
COPY .devcontainer/postCreate.sh /opt/postCreate.sh
RUN chmod +x /opt/postCreate.sh

# Install packages with caching
USER $MAMBA_USER
COPY --chown=$MAMBA_USER:$MAMBA_USER util/snakemake.yml /tmp/snakemake.yml
RUN --mount=type=cache,target=/opt/pkg_cache,sharing=locked,uid=$MAMBA_USER_ID,gid=$MAMBA_USER_GID \
    rsync -a /opt/pkg_cache/ /opt/conda/pkgs/ && \
    micromamba config set always_yes True && \
    micromamba install -y -n base -f /tmp/snakemake.yml && \
    rsync -a /opt/conda/pkgs/ /opt/pkg_cache/ && \
    micromamba clean --all --yes

ARG MAMBA_DOCKERFILE_ACTIVATE=1

#
# Snakemake caching of conda environments
#
VOLUME "/home/${MAMBA_USER}/snakemake_conda"
ENV SNAKEMAKE_CONDA_PREFIX="/home/${MAMBA_USER}/snakemake_conda"
RUN mkdir -p /home/${MAMBA_USER}/snakemake_conda && \
    chown ${MAMBA_USER}:${MAMBA_USER} /home/${MAMBA_USER}/snakemake_conda

# Shorten the bash prompt to avoid line wrapping issues
RUN echo 'PS1="${PS1//\\w/\\W}"' >> /home/${MAMBA_USER}/.bashrc