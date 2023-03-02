import unittest
from typing import List

from gql import gql

from src.genesis.genesis import get_chain_id
from src.genesis.helpers.field_enums import Accounts
from src.genesis.processing.accounts import AccountsManager
from tests.helpers.clients import TestWithDBConn, TestWithGQLClient
from tests.helpers.genesis_data import test_bank_state_balances, test_genesis_data


class TestAccountsManager(TestWithDBConn, TestWithGQLClient):
    test_manager: AccountsManager
    completed = False
    expected_accounts: List[dict] = [
        {"id": b["address"], "chain_id": get_chain_id(test_genesis_data)}
        for b in test_bank_state_balances
    ]

    @classmethod
    def setUpClass(cls):
        TestWithDBConn().setUpClass()
        TestWithGQLClient().setUpClass()
        cls.truncate_tables("accounts", cascade=True)

        cls.test_manager = AccountsManager(cls.db_conn)
        cls.test_manager.process_genesis(
            test_genesis_data, get_chain_id(test_genesis_data)
        )

    def test_sql_retrieval(self):
        actual_accounts: List[dict] = []

        with self.db_conn.cursor() as db:
            for row in db.execute(Accounts.select_query()).fetchall():
                actual_accounts.append(
                    {
                        "id": row[Accounts.id.value],
                        "chain_id": row[Accounts.chain_id.value],
                    }
                )

        self.assertListEqual(self.expected_accounts, actual_accounts)

    def test_gql_retrieval(self):
        actual_accounts: List[dict] = []

        results = self.gql_client.execute(
            gql(
                """
            query {
                accounts {
                    nodes {
                        id,
                        chainId,
                    }
                }
            }
        """
            )
        )

        for node in results["accounts"]["nodes"]:
            actual_accounts.append(
                {"id": node.get("id"), "chain_id": node.get("chainId")}
            )

        self.assertListEqual(self.expected_accounts, actual_accounts)


if __name__ == "__main__":
    unittest.main()
