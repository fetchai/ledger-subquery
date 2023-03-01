from psycopg import Connection

from .accounts import AccountsManager
from .balances import BalanceManager
from .contracts import ContractsManager


def get_chain_id(genesis_data: dict):
    return genesis_data["chain_id"]


def process_genesis(db_conn: Connection, genesis_data: dict):
    chain_id = get_chain_id(genesis_data)
    accounts_manager = AccountsManager(db_conn)
    balances_manager = BalanceManager(db_conn)
    contracts_manager = ContractsManager(db_conn)

    print("processing...")
    accounts_manager.process_genesis(genesis_data, chain_id)
    balances_manager.process_genesis(genesis_data)
    contracts_manager.process_genesis(genesis_data)
