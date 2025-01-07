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

# some of these probably fail when container is first built
conda activate project || "project env activation failed"
pg_ctl -D gvca -l logfile start || echo "pg_ctl -D gvca -l logfile start failed"
