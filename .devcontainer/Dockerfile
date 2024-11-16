# image source here: https://github.com/devcontainers/images/tree/main/src/universal
FROM mcr.microsoft.com/devcontainers/universal:linux
# mcr.microsoft.com/devcontainers/universal:focal

# Copy environment.yml (if found) to a temp location so we update the environment. Also
# copy "noop.txt" so the COPY instruction does not fail if no environment.yml exists.
# COPY environment.yml* .devcontainer/noop.txt /tmp/conda-tmp/
# RUN if [ -f "/tmp/conda-tmp/environment.yml" ]; then umask 0002 && /opt/conda/bin/conda env update -n base -f /tmp/conda-tmp/environment.yml; fi \
#     && rm -rf /tmp/conda-tmp

### install devcontainer python dependencies for environment:

# Install mamba if not installed, as faster for managing a lot of python packages
USER codespace
RUN /opt/conda/bin/conda install -n base -c conda-forge -y mamba
RUN mamba update -n base -c conda-forge -y mamba
#RUN mamba update -n base -c conda-forge -y --all
RUN mamba clean -all -y
USER root

# COPY .devcontainer/environment.yml* .devcontainer/noop.txt /tmp/conda-tmp/
# RUN if [ -f "/tmp/conda-tmp/environment.yml" ]; then umask 0002 && /opt/conda/bin/mamba env update -n base -f /tmp/conda-tmp/environment.yml; fi \
#     && rm -rf /tmp/conda-tmp

# install project dependencies defined in an environment.yml in the root git directory / workspace root
# assumes environment.yml file exists in workspace root;  probably best done as postcreatecommand in devcontainer.json instead
#COPY environment.yml* .devcontainer/noop.txt /tmp/conda-tmp/
#RUN if [ -f "/tmp/conda-tmp/environment.yml" ]; then umask 0002 && /opt/conda/bin/mamba create --name project --clone base && /opt/conda/bin/mamba env update -n project -f /tmp/conda-tmp/environment.yml; fi \
#    && rm -rf /tmp/conda-tmp

# [Optional] Uncomment this section to install additional OS packages.
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive && \
  apt-get -y install --no-install-recommends postgresql && \
  apt-get autoremove -y && apt-get clean -y && rm -rf /var/lib/apt/lists/*
