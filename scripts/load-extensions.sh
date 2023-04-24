#!/bin/sh

psql -v ON_ERROR_STOP=1 --username "subquery" <<EOF
CREATE EXTENSION IF NOT EXISTS btree_gist;
EOF