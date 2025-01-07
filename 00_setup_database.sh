#!/bin/bash

### setup database for project

echo "Setting up database for project"

initdb -D gvca
pg_ctl -D gvca -l logfile start
createuser --encrypted --pwprompt gvcaadmin
createdb --owner=gvcaadmin gvca_survey
psql -d gvca_survey -U gvcaadmin -f 01_build_database.sql
