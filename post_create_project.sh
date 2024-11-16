#!/bin/bash

### Script to install project requirements after container creation, as postcreatecommand
### Some project requirements may have already be installed by dockerfile, or devcontainer.json, check if unsure

echo "Installing Project Requirements"

# make aliases expand and work in the script
shopt -s expand_aliases

# create conda env called "project" and install requirements from environment.yml
if [ -f './environment.yml' ]; then
    umask 0002 && mamba create --name project --clone base -y && mamba env update -n project -f ./environment.yml
    mamba clean --all -y
else
    umask 0002 && mamba create --name project --clone base -y
fi

# [Optional] Uncomment this section to install additional OS packages.
# RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
#   && apt-get -y install --no-install-recommends <your packages here> \
#   && apt-get autoremove -y && apt-get clean -y && rm -rf /var/lib/apt/lists/*

echo "Project Requirements Installation Complete"
