#!/bin/bash
set -e

echo "checking genesis processing requirements..."

if [ -z "$DB_DATABASE" ] || [ -z "$DB_HOST" ] || [ -z "$DB_PASS" ] || [ -z "$DB_SCHEMA" ] || [ -z "$DB_USER" ] || [ -z "$DB_PORT" ]; then
  echo "One or more database envs missing from: DB_HOST, DB_DATABASE, DB_PASS, DB_SCHEMA, DB_USER, DB_PORT"
  exit 1
fi

export PGPASSWORD=$DB_PASS
genesisProcessed=$(psql -At -v ON_ERROR_STOP=1 \
        -h $DB_HOST \
        -U $DB_USER \
        -p $DB_PORT \
        -d $DB_DATABASE \
        -c "SELECT to_regclass('genesis_processing.genesisProcessed');")

if [ -n "$genesisProcessed" ] && [[ -z "$FORCE_PROCESS" || "$FORCE_PROCESS" == "false" ]]; then
  echo "genesis already processed"
  exit 1
fi

if [ -z "$JSON_URL" ] || [ -z "${NETWORK}" ]; then
  echo "JSON_URL and/or NETWORK ENV missing, e.g. NETWORK='dorado' & JSON_URL='https://storage.googleapis.com/fetch-ai-testnet-genesis/genesis-dorado-827201.json'"
  exit 1
fi

pipenv run python /app/genesis.py \
                    "${JSON_URL}" \
                    --db-host="${DB_HOST}" \
                    --db-name="${DB_DATABASE}" \
                    --db-pass="${DB_PASS}" \
                    --db-schema="${DB_SCHEMA}" \
                    --db-user="${DB_USER}" \
                    --db-port="${DB_PORT}"

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
