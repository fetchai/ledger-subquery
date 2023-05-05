#!/bin/bash
set -e

export PGPASSWORD=$DB_PASS
genesisProcessed=$(psql -At -v ON_ERROR_STOP=1 \
        -h $DB_HOST \
        -U $DB_USER \
        -p $DB_PORT \
        -d $DB_DATABASE \
        -c "SELECT to_regclass('genesis_processing.genesisProcessed');")

if [ -n "$genesisProcessed" ]; then
  echo "genesis already processed"
  exit 1
fi

if [ -z "$JSON_URL" ] || [ -z "${NETWORK}" ]; then
  echo "JSON_URL and/or NETWORK ENV missing, e.g. NETWORK='dorado' & JSON_URL='https://storage.googleapis.com/fetch-ai-testnet-genesis/genesis-dorado-827201.json'"
  exit 1
fi

export PGPASSWORD=$DB_PASS
psql -At -v ON_ERROR_STOP=1 \
        -h $DB_HOST \
        -U $DB_USER \
        -p $DB_PORT \
        -d $DB_DATABASE <<EOF
CREATE SCHEMA genesis_processing;
CREATE TABLE IF NOT EXISTS genesis_processing.genesisProcessed (
  network text
);

INSERT INTO genesis_processing.genesisProcessed(network)
  VALUES ('${NETWORK}');
EOF

pipenv run python /app/genesis.py "${JSON_URL}"

