#!/bin/bash

echo "Sleeping $STARTUP_DELAY"
sleep "$STARTUP_DELAY"

exec /sbin/tini -- node /usr/local/lib/node_modules/@subql/query/dist/main "$@"
