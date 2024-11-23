#!/bin/bash

echo "Running postStartCommand script: post_container_start.sh"

### Script that runs every time the container starts
# Called by devcontainer.json postStartCommand
# Example:
# {
#   "postStartCommand": "bash ./post_container_start.sh"
#}
#
#
# Start required features
#
# Start the PostgreSQL server
conda activate project
pg_ctl -D gvca -l logfile start
