import datetime as dt
import time
import unittest

from src.genesis.helpers.field_enums import (
    Contracts,
    InstantiateContractMessages,
    StoreContractMessages,
)
from tests.helpers.contracts import Cw20Contract
from tests.helpers.entity_test import EntityTest
from tests.helpers.graphql import filtered_test_query


class TestContractDeploy(EntityTest):
    amount = 5000
    _contract: Cw20Contract

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.clean_db({"contracts"})
        cls._contract = Cw20Contract(cls.ledger_client, cls.validator_wallet)
        code_id = cls._contract._store()
        address = cls._contract._instantiate()

        """
        An initial proposal is created in order to make value assertions. These values are stored within a dictionary
        to be recalled for the assertions. However to create enough data for sorting tests, two further contracts are
        stored and instantiated afterwards. These two additional contracts are used only for sorting test data, and their
        unique addresses and contents are ignored.
        """
        cls.entities = {
            "storeContractMsg": {
                "query": StoreContractMessages.select_query(),
                "equal": {
                    StoreContractMessages.sender.value: cls.validator_address,
                    StoreContractMessages.code_id.value: code_id,
                    StoreContractMessages.permission.value: None,
                },
                "not_null": {},
            },
            "instantiateMsg": {
                "query": InstantiateContractMessages.select_query(),
                "equal": {
                    InstantiateContractMessages.sender.value: cls.validator_address,
                    InstantiateContractMessages.code_id.value: code_id,
                    InstantiateContractMessages.admin.value: "",
                    InstantiateContractMessages.funds.value: [],
                },
                "not_null": {
                    InstantiateContractMessages.label.value,
                    InstantiateContractMessages.payload.value,
                },
            },
            "contractEntity": {
                "query": Contracts.select_query(),
                "equal": {
                    Contracts.interface.value: "CW20",
                    Contracts.id.value: address,
                },
                "not_null": {
                    Contracts.instantiate_message_id.value,
                    Contracts.store_message_id.value,
                },
            },
        }
        for i in range(2):
            cls._contract._store()
            cls._contract._instantiate()
        time.sleep(5)

    def test_execute_transfer(self):
        for entity in ["storeContractMsg", "instantiateMsg", "contractEntity"]:
            transfer = self.db_cursor.execute(self.entities[entity]["query"]).fetchone()
            self.assertIsNotNone(
                transfer,
                "\nDBError: table is empty - maybe indexer did not find an entry?",
            )

            for assertion_key in self.entities[entity]["equal"]:
                self.assertEqual(
                    transfer[assertion_key],
                    self.entities[entity]["equal"][assertion_key],
                    f"DBError: `{entity}` attribute not equal",
                )

            for assertion_key in self.entities[entity]["not_null"]:
                self.assertIsNotNone(
                    transfer[assertion_key], f"DBError: `{entity}` attribute not null"
                )

    def test_retrieve_store_contract_msg(self):
        latest_block_timestamp = self.get_latest_block_timestamp()
        # create a second timestamp for five minutes before
        min_timestamp = (
            latest_block_timestamp - dt.timedelta(minutes=5)
        ).isoformat()  # convert both to JSON ISO format
        max_timestamp = latest_block_timestamp.isoformat()

        store_contract_nodes = """
            {
                id
                sender
                permission
                codeId
                message { id }
                transaction { id }
                block { id }
            }
            """

        """
        Each query is sorted by codeId to allow us to test only the initial created contract, from which our tabled
        data is stored.
        """

        def filtered_store_contract_message_query(_filter, order="CODE_ID_ASC"):
            return filtered_test_query(
                "storeContractMessages", _filter, store_contract_nodes, _order=order
            )

        # query store contract messages, query related block and filter by timestamp, returning all within last five minutes
        filter_by_block_timestamp_range = filtered_store_contract_message_query(
            {
                "block": {
                    "timestamp": {
                        "greaterThanOrEqualTo": min_timestamp,
                        "lessThanOrEqualTo": max_timestamp,
                    }
                }
            }
        )

        # query store contract messages, filter by sender address
        filter_by_sender_equals = filtered_store_contract_message_query(
            {"sender": {"equalTo": str(self.validator_address)}}
        )

        # query store contract messages, filter by permission
        filter_by_permission_equals = filtered_store_contract_message_query(
            {"permission": {"isNull": True}}
        )

        # query store contract messages, filter by codeId
        filter_by_code_id_equals = filtered_store_contract_message_query(
            {
                "codeId": {
                    "equalTo": self.entities["storeContractMsg"]["equal"][
                        StoreContractMessages.code_id.value
                    ]
                }
            }
        )

        for (name, query) in [
            ("by block timestamp range", filter_by_block_timestamp_range),
            ("by sender equals", filter_by_sender_equals),
            ("by permission equals", filter_by_permission_equals),
            ("by code_id equals", filter_by_code_id_equals),
        ]:
            with self.subTest(name):
                result = self.gql_client.execute(query)
                """
                ["storeContractMessages"]["nodes"][0] denotes the sequence of keys to access the message contents queried for above.
                This provides {"sender":sender address, "permission: access type enum, "codeId": code ID}
                which can be destructured for the values of interest.
                """
                # We are sorting by code id in order to access contracts in order of creation
                # As can be seen from `transfer[0]`, we only assert values from the initial contract
                transfer = result["storeContractMessages"]["nodes"]
                self.assertNotEqual(
                    transfer, [], "\nGQLError: No results returned from query"
                )
                self.assertEqual(
                    transfer[0]["sender"],
                    self.validator_address,
                    "\nGQLError: sender address does not match",
                )
                self.assertEqual(
                    transfer[0]["permission"],
                    None,
                    "\nGQLError: contract permission does not match",
                )
                self.assertEqual(
                    int(transfer[0]["codeId"]),
                    self.entities["storeContractMsg"]["equal"][
                        StoreContractMessages.code_id.value
                    ],
                    "\nGQLError: code_id does not match",
                )

    def test_retrieve_instantiate_contract_msg(self):
        latest_block_timestamp = self.get_latest_block_timestamp()
        # create a second timestamp for five minutes before
        min_timestamp = (
            latest_block_timestamp - dt.timedelta(minutes=5)
        ).isoformat()  # convert both to JSON ISO format
        max_timestamp = latest_block_timestamp.isoformat()

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

        # query instantiate contract messages, query related block and filter by timestamp, returning all within last five minutes
        filter_by_block_timestamp_range = filtered_instantiate_contract_message_query(
            {
                "block": {
                    "timestamp": {
                        "greaterThanOrEqualTo": min_timestamp,
                        "lessThanOrEqualTo": max_timestamp,
                    }
                }
            }
        )

        # query instantiate contract messages, filter by sender address
        filter_by_sender_equals = filtered_instantiate_contract_message_query(
            {"sender": {"equalTo": str(self.validator_address)}}
        )

        # query instantiate contract messages, filter by admin
        filter_by_admin_equals = filtered_instantiate_contract_message_query(
            {"admin": {"equalTo": ""}}
        )

        # query instantiate contract messages, filter by codeId
        filter_by_code_id_equals = filtered_instantiate_contract_message_query(
            {
                "codeId": {
                    "equalTo": self.entities["instantiateMsg"]["equal"][
                        InstantiateContractMessages.code_id.value
                    ]
                }
            }
        )

        # query instantiate contract messages, filter by label
        filter_by_label_equals = filtered_instantiate_contract_message_query(
            {"label": {"isNull": False}}
        )

        # query instantiate contract messages, filter by payload
        filter_by_payload_equals = filtered_instantiate_contract_message_query(
            {"payload": {"isNull": False}}
        )

        # query instantiate contract messages, filter by funds
        filter_by_funds_equals = filtered_instantiate_contract_message_query(
            {"funds": {"equalTo": []}}
        )

        for (name, query) in [
            ("by block timestamp range", filter_by_block_timestamp_range),
            ("by sender equals", filter_by_sender_equals),
            ("by admin equals", filter_by_admin_equals),
            ("by code_id equals", filter_by_code_id_equals),
            ("by label not null", filter_by_label_equals),
            ("by payload not null", filter_by_payload_equals),
            ("by funds equals", filter_by_funds_equals),
        ]:
            with self.subTest(name):
                result = self.gql_client.execute(query)
                """
                ["instantiateContractMessages"]["nodes"][0] denotes the sequence of keys to access the message contents queried for above.
                This provides {"sender":sender address, "admin: contract admin, "codeId": code ID, "label": contract label,
                "payload": contract configuration/payload, "funds": funds held within contract}
                which can be destructured for the values of interest.
                """
                # As can be seen from `transfer[0]`, we only assert values from the initial contract
                transfer = result["instantiateContractMessages"]["nodes"]
                self.assertNotEqual(
                    transfer, [], "\nGQLError: No results returned from query"
                )
                self.assertEqual(
                    transfer[0]["sender"],
                    self.validator_address,
                    "\nGQLError: sender address does not match",
                )
                self.assertEqual(
                    transfer[0]["admin"],
                    "",
                    "\nGQLError: contract admin does not match",
                )
                self.assertEqual(
                    int(transfer[0]["codeId"]),
                    self.entities["instantiateMsg"]["equal"][
                        InstantiateContractMessages.code_id.value
                    ],
                    "\nGQLError: contract code_id does not match",
                )
                self.assertIsNotNone(
                    transfer[0]["label"], "\nGQLError: contract label is empty"
                )
                self.assertIsNotNone(
                    transfer[0]["payload"], "\nGQLError: contract payload is empty"
                )
                self.assertEqual(
                    transfer[0]["funds"], [], "\nGQLError: contract funds do not match"
                )

    def test_retrieve_contract(self):
        latest_block_timestamp = self.get_latest_block_timestamp()
        # create a second timestamp for five minutes before
        min_timestamp = (
            latest_block_timestamp - dt.timedelta(minutes=5)
        ).isoformat()  # convert both to JSON ISO format
        max_timestamp = latest_block_timestamp.isoformat()

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

        """
        Again here our queries used to assert contract values are by default sorted by codeId in order to allow us to
        separate the initial contract from the dummy contracts used for sorting
        """

        def filtered_contract_query(
            _filter, order="CONTRACTS_BY_STORE_CONTRACT_MESSAGES_CODE_ID_ASC"
        ):
            return filtered_test_query(
                "contracts", _filter, contract_nodes, _order=order
            )

        order_by_store_contract_messages_code_id_asc = filtered_contract_query(
            default_filter, "CONTRACTS_BY_STORE_CONTRACT_MESSAGES_CODE_ID_ASC"
        )

        order_by_store_contract_messages_code_id_desc = filtered_contract_query(
            default_filter, "CONTRACTS_BY_STORE_CONTRACT_MESSAGES_CODE_ID_DESC"
        )

        order_by_instantiate_contract_messages_code_id_desc = filtered_contract_query(
            default_filter, "CONTRACTS_BY_INSTANTIATE_CONTRACT_MESSAGES_CODE_ID_DESC"
        )

        order_by_instantiate_contract_messages_code_id_asc = filtered_contract_query(
            default_filter, "CONTRACTS_BY_INSTANTIATE_CONTRACT_MESSAGES_CODE_ID_ASC"
        )

        # query contract, query related block and filter by timestamp, returning all within last five minutes
        filter_by_block_timestamp_range = filtered_contract_query(
            {
                "storeMessage": {
                    "block": {
                        "timestamp": {
                            "greaterThanOrEqualTo": min_timestamp,
                            "lessThanOrEqualTo": max_timestamp,
                        }
                    }
                }
            }
        )

        # query contract, filter by contract address
        filter_by_id_equals = filtered_contract_query(
            {
                "id": {
                    "equalTo": str(
                        self.entities["contractEntity"]["equal"][Contracts.id.value]
                    )
                }
            }
        )

        # query contract, filter by contract interface
        filter_by_interface_equals = filtered_contract_query(
            {"interface": {"isNull": False}}
        )

        for (name, query) in [
            ("by block timestamp range", filter_by_block_timestamp_range),
            ("by id equals", filter_by_id_equals),
            ("by interface equals", filter_by_interface_equals),
        ]:
            with self.subTest(name):
                result = self.gql_client.execute(query)
                """
                ["contracts"]["nodes"][0] denotes the sequence of keys to access the message contents queried for above.
                This provides {"id":contract address, "interface: predicted contract interface}
                which can be destructured for the values of interest.
                """
                contracts = result["contracts"]["nodes"]
                self.assertNotEqual(
                    contracts, [], "\nGQLError: No results returned from query"
                )
                self.assertEqual(
                    contracts[0]["id"],
                    str(self.entities["contractEntity"]["equal"][Contracts.id.value]),
                    "\nGQLError: contract address does not match",
                )
                self.assertIsNotNone(
                    contracts[0]["interface"],
                    "\nGQLError: contract interface prediction is null",
                )

        for query, entity in {
            # Iterate through contract code_id from related storeMessage & instantiateMessage to assert ascending
            order_by_store_contract_messages_code_id_asc: "storeMessage",
            order_by_instantiate_contract_messages_code_id_asc: "instantiateMessage",
        }.items():
            with self.subTest(f"order {entity} instances by code ID ascending"):
                result = self.gql_client.execute(query)  # use query iterable from above
                contracts = result["contracts"]["nodes"]
                last = contracts[0][entity]["codeId"]  # use relevant entity from above
                for entry in contracts:
                    cur = entry[entity]["codeId"]
                    self.assertGreaterEqual(
                        cur,
                        last,
                        msg="OrderAssertError: order of contracts is incorrect",
                    )
                    last = cur

        for query, entity in {
            # Repeat sorting assertion for descending
            order_by_store_contract_messages_code_id_desc: "storeMessage",
            order_by_instantiate_contract_messages_code_id_desc: "instantiateMessage",
        }.items():
            with self.subTest(f"order {entity} instances by code ID descending"):
                result = self.gql_client.execute(query)
                contracts = result["contracts"]["nodes"]
                last = contracts[0][entity]["codeId"]
                for entry in contracts:
                    cur = entry[entity]["codeId"]
                    self.assertLessEqual(
                        cur,
                        last,
                        msg="OrderAssertError: order of contracts is incorrect",
                    )
                    last = cur


if __name__ == "__main__":
    unittest.main()
