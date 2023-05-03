import unittest
from typing import List

from gql import gql

from src.genesis.helpers.field_enums import Contracts
from src.genesis.processing.contracts import ContractsManager
from tests.helpers.clients import TestWithDBConn, TestWithGQLClient
from tests.helpers.genesis_data import test_genesis_data, test_wasm_state_contracts


class TestContractsManager(TestWithDBConn, TestWithGQLClient):
    test_manager: ContractsManager
    completed = False
    expected_contracts: List[dict] = [
        {"id": b["contract_address"]} for b in test_wasm_state_contracts
    ]

    @classmethod
    def setUpClass(cls):
        TestWithDBConn().setUpClass()
        TestWithGQLClient().setUpClass()
        cls.truncate_tables("contracts", cascade=True)

        cls.test_manager = ContractsManager(cls.db_conn)
        cls.test_manager.process_genesis(test_genesis_data)

    def test_sql_retrieval(self):
        actual_contracts: List[dict] = []

        with self.db_conn.cursor() as db:
            for row in db.execute(Contracts.select_query()).fetchall():
                actual_contracts.append({"id": row[Contracts.id.value]})

        self.assertListEqual(self.expected_contracts, actual_contracts)

    def test_gql_retrieval(self):
        actual_contracts: List[dict] = []

        results = self.gql_client.execute(
            gql(
                """
            query {
                contracts {
                    nodes {
                        id
                    }
                }
            }
        """
            )
        )

        for node in results["contracts"]["nodes"]:
            actual_contracts.append({"id": node.get("id")})

        actual_contracts.reverse()
        self.assertListEqual(self.expected_contracts, actual_contracts)


if __name__ == "__main__":
    unittest.main()
