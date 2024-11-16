#!/bin/bash

### Script to install container requirements after container creation, as postcreatecommand
### Some container requirements may have already be installed by dockerfile, or devcontainer.json, check if unsure

echo "Installing Container Requirements"

# make aliases expand and work in the script
shopt -s expand_aliases

# Install Mamba - not working, probably because needs to run as user and not as root
# conda init
# /opt/conda/bin/conda install -n base -c conda-forge -y mamba
mamba update -n base -c conda-forge -y --all
mamba clean --all -y

# Install container requirements from environment.yml
if [ -f './.devcontainer/environment.yml' ]; then
    umask 0002 && mamba env update -n base -f ./.devcontainer/environment.yml
fi

# [Optional] Uncomment this section to install additional OS packages.
# RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
#   && apt-get -y install --no-install-recommends <your packages here> \
#   && apt-get autoremove -y && apt-get clean -y && rm -rf /var/lib/apt/lists/*

echo "Container Requirements Installation Complete"
