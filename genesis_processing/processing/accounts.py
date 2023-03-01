from psycopg import Connection

from genesis_processing.db.table_manager import TableManager, DBTypes
from typing import List
from genesis_processing.utils.loggers import get_logger

_logger = get_logger(__name__)

ID = "id"
CHAIN_ID = "chain_id"
TABLE_ID = "accounts"


class AccountsManager():

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
        db_accounts = self.table_manager.select_query([ID])

        genesis_accounts_filtered = self._filter_genesis_accounts(accounts_data, db_accounts)
        with self.table_manager.db_copy() as copy:
            for account in genesis_accounts_filtered:
                copy.write_row([self._get_account_address(account), chain_id])

    def _get_account_data(self, genesis_data: dict) -> List[dict]:
        return genesis_data["app_state"]["bank"]["balances"]

    def _get_account_address(self, account: dict) -> str:
        return str(account["address"])

    def _filter_genesis_accounts(self, accounts_data: List[dict], db_accounts: List[str]) -> List[dict]:
        """
        Filter out genesis_accounts IDs from accounts_data

        :param accounts_data: Account data to be filtered
        :param genesis_accounts: IDs as a filter
        :return: Copy of accounts_data with removed accounts from genesis_accounts filter
        """
        genesis_accounts = [self._get_account_address(x) for x in accounts_data]

        matches = [match for match in set(db_accounts) & set(genesis_accounts)]  # list already indexed accounts
        genesis_accounts_filtered = filter(lambda account: self._get_account_address(account) not in matches,
                                           accounts_data)
        return list(genesis_accounts_filtered)
