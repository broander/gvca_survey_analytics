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

# Start the postgres database
# some of these probably fail when container is first built
nohup conda run -n project pg_ctl -D gvca -l logfile start &
if [ $? -ne 0 ]; then
    echo "pg_ctl -D gvca -l logfile start failed"
else
    echo "pg_ctl -D gvca -l logfile start succeeded"
fi

# Start the jupyter notebook
nohup jupyter-lab >/workspaces/gvca_survey_analytics/jupyter-lab.log &
if [ $? -ne 0 ]; then
    echo "jupyter-lab failed"
else
    echo "jupyter-lab succeeded; find log in /workspaces/[repo-name]/jupyter-lab.log"
fi

# how to find command to kill
# ps -ef | grep jupyter-lab
# kill <pid>

echo "Container Start Script Complete"
