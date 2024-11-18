#!/bin/bash

### Script to install project requirements after container creation, as postcreatecommand
### Some project requirements may have already be installed by dockerfile, or devcontainer.json, check if unsure

echo "Installing Project Requirements"

# make aliases expand and work in the script
shopt -s expand_aliases

# create conda env called "project" and install requirements from environment.yml
# Assumes Mamba already installed earlier in the build process
if ! mamba --version; then
    echo "Mamba not found when setting up project requirements, check config and rebuild container"
else
    echo "Mamba found, continuing to setup project requirements..."
    if [ -f './environment.yml' ]; then
        echo "Project environment.yml found, installing project requirements in project env"
        umask 0002 && mamba create --name project --clone base && mamba env update -n project -f ./environment.yml
    else
        echo "No project environment.yml found, creating project env from base"
        umask 0002 && mamba create --name project --clone base
    fi
    mamba update -n project -y --all
    mamba clean --all -y
fi

# [Optional] Uncomment this section to install additional OS packages.
# RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
#   && apt-get -y install --no-install-recommends <your packages here> \
#   && apt-get autoremove -y && apt-get clean -y && rm -rf /var/lib/apt/lists/*

echo "Project Requirements Installation Complete"
