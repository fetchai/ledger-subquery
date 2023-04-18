import time
import unittest

from src.genesis.helpers.field_enums import (
    Contracts,
    InstantiateContractMessages,
)
from tests.helpers.contracts import RecursiveContract
from tests.helpers.entity_test import EntityTest
from tests.helpers.graphql import filtered_test_query


class TestContractDeploy(EntityTest):
    depth = 3
    _contract: RecursiveContract
    code_id = None
    address = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.clean_db({"contracts"})
        cls.clean_db({"instantiate_contract_messages"})
        cls._contract = RecursiveContract(cls.ledger_client, cls.validator_wallet)
        cls.code_id = cls._contract._store()
        cls.address = cls._contract._instantiate(cls.code_id, cls.depth)
        time.sleep(5)

    def test_db_instantiation_and_contracts(self):
        instantiate_msg = self.db_cursor.execute(
            InstantiateContractMessages.select_query()
        ).fetchall()
        contracts = self.db_cursor.execute(Contracts.select_query()).fetchall()

        self.assertIsNotNone(
            instantiate_msg,
            "\nDBError: table is empty - maybe indexer did not find an entry?",
        )

        self.assertEqual(
            len(instantiate_msg),
            self.depth,
            "\nDBError: number of instantiation_msgs is not equal to recursion depth",
        )

        self.assertEqual(
            len(contracts),
            self.depth,
            "\nDBError: number of contracts is not equal to recursion depth",
        )

    def test_retrieve_instantiate_contract_msg(self):
        instantiate_contract_nodes = """
            {
                id
                sender
                admin
                codeId
                label
                payload
                funds
                message { id }
                transaction { id }
                block { id }
            }
            """

        def filtered_instantiate_contract_message_query(_filter, order="CODE_ID_ASC"):
            return filtered_test_query(
                "instantiateContractMessages",
                _filter,
                instantiate_contract_nodes,
                _order=order,
            )

        # query instantiate contract messages, filter by codeId
        filter_by_code_id_equals = filtered_instantiate_contract_message_query(
            {"codeId": {"equalTo": self.code_id}}
        )

        instantiation_msgs = filter_by_code_id_equals
        result = self.gql_client.execute(instantiation_msgs)
        instantiation_msgs_list = result["instantiateContractMessages"]["nodes"]

        self.assertEqual(
            len(instantiation_msgs_list),
            self.depth,
            "\nGQLError: number of instantiation_msgs is not equal to recursion depth",
        )

    def test_retrieve_contract(self):
        contract_nodes = """
            {
                id
                interface
                storeMessage {
                    id
                    codeId
                }
                instantiateMessage {
                    id
                    codeId
                }
            }
            """

        default_filter = {  # filter parameter of helper function must not be null, so instead use rhetorical filter
            "storeMessage": {"codeId": {"greaterThanOrEqualTo": 0}}
        }

        def filtered_contract_query(
            _filter, order="CONTRACTS_BY_STORE_CONTRACT_MESSAGES_CODE_ID_ASC"
        ):
            return filtered_test_query(
                "contracts", _filter, contract_nodes, _order=order
            )

        contracts = filtered_contract_query(default_filter)
        result = self.gql_client.execute(contracts)
        contracts_list = result["contracts"]["nodes"]

        self.assertEqual(
            len(contracts_list),
            self.depth,
            "\nGQLError: number of contracts is not equal to recursion depth",
        )


if __name__ == "__main__":
    unittest.main()
