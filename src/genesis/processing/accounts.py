from typing import List

from psycopg import Connection

from src.genesis.db.table_manager import DBTypes, TableManager
from src.genesis.utils.loggers import get_logger

_logger = get_logger(__name__)

ID = "id"
CHAIN_ID = "chain_id"
TABLE_ID = "accounts"


class AccountsManager:
    def __init__(self, db_conn: Connection):
        columns = (
            (ID, DBTypes.text),
            (CHAIN_ID, DBTypes.text),
        )
        indexes = (
            ID,
            CHAIN_ID,
        )

        self.table_manager = TableManager(db_conn, TABLE_ID, columns, indexes)
        self.table_manager.ensure_table()

    def process_genesis(self, genesis_data: dict, chain_id: str):
        accounts_data = self._get_account_data(genesis_data)
        db_accounts = set(self.table_manager.select_query([ID]))

        with self.table_manager.db_copy() as copy:
            for account in accounts_data:
                account_address = self._get_account_address(account)
                if account_address not in db_accounts:
                    copy.write_row((account_address, chain_id))

    @classmethod
    def _get_account_data(cls, genesis_data: dict) -> List[dict]:
        return genesis_data["app_state"]["bank"]["balances"]

    @classmethod
    def _get_account_address(cls, account: dict) -> str:
        return str(account["address"])
