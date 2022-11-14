#!/bin/sh
set -e

# perform any updates that are required based on the environment variables
if [[ ! -z "${START_BLOCK}" ]]; then
    echo "[Config Update] Start Block: ${START_BLOCK}"
    yq -i '.dataSources[].startBlock = env(START_BLOCK)' project.yaml
fi

if [[ ! -z "${CHAIN_ID}" ]]; then
    echo "[Config Update] Chain ID: ${CHAIN_ID}"
    yq -i '.network.chainId = env(CHAIN_ID)' project.yaml
fi

if [[ ! -z "${NETWORK_ENDPOINT}" ]]; then
    echo "[Config Update] Network Endpoint: ${NETWORK_ENDPOINT}"
    yq -i '.network.endpoint = strenv(NETWORK_ENDPOINT)' project.yaml
fi

export PGPASSWORD=$DB_PASS
has_migrations=$(psql -h $DB_HOST \
                      -U $DB_USER \
                      -p $DB_PORT \
                      -c "set schema 'graphile_migrate';" -c "\dt" $DB_DATABASE |
                 grep "migrations" |
                 wc -l)
echo "has_migrations: $has_migrations"


if [[ "$has_migrations" == "0" ]]; then
  graphile-migrate reset --erase
fi

# catch-up migrations
graphile-migrate migrate

# run the main node
exec /sbin/tini -- /usr/local/lib/node_modules/@subql/node-cosmos/bin/run "$@"
