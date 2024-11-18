#!/bin/bash

### Script to install container requirements after container creation, as postcreatecommand
### Some container requirements may have already be installed by dockerfile, or devcontainer.json, check if unsure

echo "Installing Container Requirements"

# make aliases expand and work in the script
shopt -s expand_aliases

# install mamba
# add conda-forge to top of channel priority
conda config --add channels conda-forge
echo "Installing mamba for container setup"
conda install -n base -c conda-forge -y mamba
mamba update -n base -c conda-forge -y mamba
mamba clean -all -y

# set up Micromamba mamaba like .bashrc will do
# export MAMBA_EXE='/usr/local/bin/micromamba'
# export MAMBA_ROOT_PREFIX='/opt/conda'
# __mamba_setup="$("$MAMBA_EXE" shell hook --shell bash --root-prefix "$MAMBA_ROOT_PREFIX" 2>/dev/null)"
# if [ $? -eq 0 ]; then
# 	eval "$__mamba_setup"
# else
# 	alias micromamba="$MAMBA_EXE" # Fallback on help from micromamba activate
# fi
# unset __mamba_setup

# Setup env for container using mamba, assuming mamba already installed earlier in build process
if ! mamba --version; then
	echo "Mamba not found when setting up container requirements, check config and rebuild container"
	#/opt/conda/bin/conda install -n base -c conda-forge -y mamba
else
	echo "Mamba found, continuing to setup container requirements..."
	# Install container requirements from environment.yml
	if [ -f './.devcontainer/environment.yml' ]; then
		echo "Container environment.yml found, installing container requirements in base env"
		umask 0002 && mamba env update -y -n base -f ./.devcontainer/environment.yml
	else
		echo "No container environment.yml, if unexpected check config and rebuild container"
	fi
	mamba update -n base -c conda-forge -y --all
	mamba clean --all -y
fi

# [Optional] Uncomment this section to install additional OS packages.
# RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
#   && apt-get -y install --no-install-recommends <your packages here> \
#   && apt-get autoremove -y && apt-get clean -y && rm -rf /var/lib/apt/lists/*

echo "Container Requirements Installation Complete"
