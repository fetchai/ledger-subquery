# Ledger SubQuery

This is the Fetch ledger SubQuery project, an indexer for the Fetch network.


# Developing

## Getting Started

### 1. Ensure submodules are updated

```shell
git submodule update --init --recursive
```

### 2. Install dependencies

```shell
yarn

# install submodule dependencies
(cd ./subql && yarn)
```

### 3. Generate types

```shell
yarn codegen
```

### 4. Build

```shell
yarn build

# build submodule
(cd ./subql && yarn build)
```

### 5. Run locally

```shell
yarn start:docker
```

## End-to-end Testing

### 1. Install dependencies

```shell
pipenv install
```

### 2. Run all e2e tests

_Note: end-to-end tests will truncate tables in the DB and interact with the configured fetchd node._

```shell
pipenv run python -m unittest discover -s ./test
```

## Tips

### Using a local fetchd node

You can use `docker-compose.override.yml` to specify the environment respective variables:
```yaml
services:
  subquery-node:
    environment:
      START_BLOCK: "1"
      NETWORK_ENDPOINT: "http://fetch_node:26657"
      CHAIN_ID: "testing"
```

Until a `fetchd` docker-compose service gets added you may use docker-compose [`networks`](https://docs.docker.com/compose/networking/#use-a-pre-existing-network) to provide connectivity to the local fetchd container.

### Destroying the local DB data directory

The `postgres` docker-compose service mounts a `.data` directory in the repo root.
Removing this directory will reset the DB and allow the subquery node to generate fresh tables.

If your local indexer is stuck at the start height you might want to try this.
