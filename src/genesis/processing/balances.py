from typing import List

from psycopg import Connection

from src.genesis.db.table_manager import DBTypes, TableManager
from src.genesis.utils.loggers import get_logger

_logger = get_logger(__name__)

ID = "id"
ACCOUNT_ID = "account_id"
AMOUNT = "amount"
DENOM = "denom"

TABLE_ID = "genesis_balances"


class BalanceManager:
    def __init__(self, db_conn: Connection):
        columns = (
            (ID, DBTypes.text),
            (ACCOUNT_ID, DBTypes.text),
            (AMOUNT, DBTypes.numeric),
            (DENOM, DBTypes.text),
        )
        indexes = (
            ID,
            ACCOUNT_ID,
            DENOM,
        )

        self.table_manager = TableManager(db_conn, TABLE_ID, columns, indexes)
        self.table_manager.ensure_table()

    def process_genesis(self, genesis_data: dict):
        balances_data = self._get_balances_data(genesis_data)
        db_accounts = set(self.table_manager.select_query([ID]))

        with self.table_manager.db_copy() as copy:
            for balance in balances_data:
                for coin in balance["coins"]:
                    db_id = self._get_db_id(balance["address"], coin["denom"])

                    if db_id not in db_accounts:
                        copy.write_row(
                            (
                                str(db_id),
                                str(balance["address"]),
                                str(coin["amount"]),
                                str(coin["denom"]),
                            )
                        )

    @classmethod
    def _get_balances_data(cls, genesis_data: dict) -> List[dict]:
        return genesis_data["app_state"]["bank"]["balances"]

    @classmethod
    def _get_db_id(cls, address: str, denom: str):
        return f"{address}-{denom}"
