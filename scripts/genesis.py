#!/usr/bin/env python

import argparse
import json
from os import environ
from typing import Dict
from urllib.request import urlopen

import psycopg
from src.genesis.genesis import process_genesis

dorado_genesis_url = (
    "https://storage.googleapis.com/fetch-ai-testnet-genesis/genesis-dorado-827201.json"
)

default_db_host = "localhost"
default_db_port = 5432
default_db_user = "subquery"
default_db_pass = "subquery"
default_db_schema = "app"
default_db_name = "subquery"


def download_json(json_url: str) -> Dict:
    # TODO: can we do this as a stream?

    with urlopen(json_url) as response:
        # TODO: handle error
        data = json.loads(response.read())

    return data


def add_arguments(parser: argparse.ArgumentParser):
    parser.add_argument(
        "json_url",
        metavar="JSON_URL",
        type=str,
        nargs="?",
        default=dorado_genesis_url,
        help="URL to genesis JSON data to process",
    )

    parser.add_argument(
        "--db-host",
        type=str,
        default=default_db_host,
        dest="db_host",
        nargs="?",
        help="Database hostname, either flag OR DB_HOST environment variable must be set",
    )

    parser.add_argument(
        "--db-port",
        type=str,
        default=default_db_port,
        dest="db_port",
        nargs="?",
        help="Database port number (default: 5432)",
    )

    parser.add_argument(
        "--db-user",
        type=str,
        default=default_db_user,
        dest="db_user",
        nargs="?",
        help="Database username (default: subquery)",
    )

    parser.add_argument(
        "--db-pass",
        type=str,
        default=default_db_pass,
        dest="db_pass",
        nargs="?",
        help="Database password (default: subquery)",
    )

    parser.add_argument(
        "--db-schema",
        type=str,
        default=default_db_schema,
        dest="db_schema",
        nargs="?",
        help="Database schema to use (default: 'app')",
    )

    parser.add_argument(
        "--db-name",
        type=str,
        default=default_db_name,
        dest="db_name",
        nargs="?",
        help="Database name to use (default: subquery)",
    )


def main():
    parser = argparse.ArgumentParser(
        description="""
        Process genesis from JSON_URL into DB records.
        Environment variables DB_HOST, DB_PORT, DB_USER, DB_PASS, DB_SCHEMA, and DB_NAME will override flags.
    """
    )

    env_db_host = environ.get("DB_HOST")
    env_db_port = environ.get("DB_PORT")
    env_db_user = environ.get("DB_USER")
    env_db_pass = environ.get("DB_PASS")
    env_db_schema = environ.get("DB_SCHEMA")
    env_db_name = environ.get("DB_NAME")

    add_arguments(parser)
    args = parser.parse_args()

    db_host = env_db_host or args.db_host
    if db_host is None:
        raise Exception("either --db-host flag OR DB_HOST env var must be set")

    db_port = env_db_port or args.db_port
    db_user = env_db_user or args.db_user
    db_pass = env_db_pass or args.db_pass
    db_schema = env_db_schema or args.db_schema or "app"
    db_name = env_db_name or args.db_name

    connection_args = {
        "host": db_host,
        "port": db_port,
        "dbname": db_name,
        "user": db_user,
        "password": db_pass,
        "options": f"-c search_path={db_schema}",
    }

    db_connection = psycopg.connect(**connection_args)
    data = download_json(args.json_url)

    process_genesis(db_connection, data)


if __name__ == "__main__":
    main()
