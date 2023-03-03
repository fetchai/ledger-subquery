from typing import List

from psycopg import Connection

from src.genesis.db.table_manager import DBTypes, TableManager
from src.genesis.utils.loggers import get_logger

_logger = get_logger(__name__)

ID = "id"
INTERFACE = "interface"
STORE_MESSAGE_ID = "store_message_id"
INSTANTIATE_MESSAGE_ID = "instantiate_message_id"
TABLE_ID = "contracts"


class ContractsManager:
    def __init__(self, db_conn: Connection):
        columns = (
            (ID, DBTypes.text),
            (INTERFACE, DBTypes.interface),
            (STORE_MESSAGE_ID, DBTypes.text),
            (INSTANTIATE_MESSAGE_ID, DBTypes.text),
        )
        indexes = (ID,)

        self.table_manager = TableManager(db_conn, TABLE_ID, columns, indexes)
        self.table_manager.ensure_table()

    def process_genesis(self, genesis_data: dict):
        contracts_data = self._get_contract_data(genesis_data)
        db_contracts = self.table_manager.select_query([ID])

        genesis_accounts_filtered = self._filter_genesis_contracts(
            contracts_data, db_contracts
        )
        with self.table_manager.db_copy() as copy:
            for contract in genesis_accounts_filtered:
                copy.write_row(
                    (self._get_contract_address(contract), "Uncertain", None, None)
                )

    def _get_contract_data(self, genesis_data: dict) -> List[dict]:
        return genesis_data["app_state"]["wasm"]["contracts"]

    def _get_contract_address(self, contract: dict) -> str:
        return str(contract["contract_address"])

    def _filter_genesis_contracts(
        self, contracts_data: List[dict], db_contracts: List[str]
    ) -> List[dict]:
        """
        Filter out genesis_contracts IDs from contracts_data

        :param contracts_data: Contract data to be filtered
        :param db_contracts: IDs as a filter
        :return: Copy of contracts_data with removed contracts from db_contracts filter
        """
        genesis_accounts = [self._get_contract_address(x) for x in contracts_data]

        matches = [
            match for match in set(db_contracts) & set(genesis_accounts)
        ]  # list already indexed accounts
        genesis_contracts_filtered = filter(
            lambda account: self._get_contract_address(account) not in matches,
            contracts_data,
        )
        return list(genesis_contracts_filtered)
