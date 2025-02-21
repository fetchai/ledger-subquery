import datetime as dt
import time
import unittest

from src.genesis.helpers.field_enums import Cw20BalanceChanges
from tests.helpers.contracts import Cw20Contract
from tests.helpers.entity_test import EntityTest
from tests.helpers.graphql import filtered_test_query


class TestCw20BalanceChange(EntityTest):
    amount = 5000
    _contract: Cw20Contract
    methods = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.clean_db({"cw20_transfers"})
        cls._contract = Cw20Contract(cls.ledger_client, cls.validator_wallet)
        cls._contract._store()
        address = cls._contract._instantiate()
        cls.methods = {
            "burn": {
                "balance_offset": [-cls.amount],
                "account_id": [cls.validator_address],
                "contract": address,
            },
            "mint": {
                "balance_offset": [cls.amount],
                "account_id": [cls.validator_address],
                "contract": address,
            },
            "transfer": {
                "balance_offset": [cls.amount, -cls.amount],
                "account_id": [cls.validator_address, cls.delegator_address],
                "contract": address,
            },
        }
        resp = cls._contract.execute(
            {
                "mint": {
                    "recipient": cls.validator_address,
                    "amount": str(cls.amount),
                }
            },
            cls.validator_wallet,
        )
        cls.ledger_client.wait_for_query_tx(resp.tx_hash)

        resp = cls._contract.execute(
            {
                "transfer": {
                    "recipient": cls.delegator_address,
                    "amount": str(cls.amount),
                }
            },
            cls.validator_wallet,
        )
        cls.ledger_client.wait_for_query_tx(resp.tx_hash)

        resp = cls._contract.execute(
            {"burn": {"amount": str(cls.amount)}}, cls.validator_wallet
        )
        cls.ledger_client.wait_for_query_tx(resp.tx_hash)
        time.sleep(5)

    def test_execute_balance_change(self):
        for method in list(self.methods.keys()):
            changes = self.db_cursor.execute(
                Cw20BalanceChanges.by_execute_contract_method(str(method))
            ).fetchall()
            entry = self.methods[method]
            """Due to differences in structure of each tabled test case, self.assertIn checks if the entry is in
               the short list of possible values given in the methods dict"""
            for query in changes:
                self.assertIsNotNone(
                    changes,
                    "\nDBError: table is empty - maybe indexer did not find an entry?",
                )
                self.assertIn(
                    query[Cw20BalanceChanges.balance_offset.value],
                    entry["balance_offset"],
                    "\nDBError: balance offset does not match",
                )
                self.assertEqual(
                    query[Cw20BalanceChanges.contract_id.value],
                    entry["contract"],
                    "\nDBError: contract address does not match",
                )
                self.assertIn(
                    query[Cw20BalanceChanges.account_id.value],
                    entry["account_id"],
                    "\nDBError: account id amount does not match",
                )

    def test_retrieve_balance_change(self):
        latest_block_timestamp = self.get_latest_block_timestamp()
        # create a second timestamp for five minutes before
        min_timestamp = (
            latest_block_timestamp - dt.timedelta(minutes=5)
        ).isoformat()  # convert both to JSON ISO format
        max_timestamp = latest_block_timestamp.isoformat()

        cw20_balance_change_nodes = """
            {
                id
                balanceOffset
                contract {
                    id
                }
                accountId
                account { id }
                message { id }
                transaction { id }
                block {
                    id
                    height
                }
            }
            """

        default_filter = {  # filter parameter of helper function must not be null, so instead use rhetorical filter
            "block": {"height": {"greaterThanOrEqualTo": "0"}}
        }

        def filtered_cw20_balance_change_query(_filter, order=""):
            return filtered_test_query(
                "cw20BalanceChanges", _filter, cw20_balance_change_nodes, _order=order
            )

        order_by_block_height_asc = filtered_cw20_balance_change_query(
            default_filter, "TIMELINE_ASC"
        )

        order_by_block_height_desc = filtered_cw20_balance_change_query(
            default_filter, "TIMELINE_DESC"
        )

        # query Cw20 transfers, query related block and filter by timestamp, returning all within last five minutes
        for method in list(self.methods.keys()):
            filter_by_block_timestamp_range = filtered_cw20_balance_change_query(
                {
                    "block": {
                        "timestamp": {
                            "greaterThanOrEqualTo": min_timestamp,
                            "lessThanOrEqualTo": max_timestamp,
                        },
                        "executeContractMessages": {
                            "some": {"method": {"equalTo": method}}
                        },
                    }
                }
            )

            # query Cw20 balance changes, filter by contract address
            filter_by_contract_address = filtered_cw20_balance_change_query(
                {
                    "contract": {"id": {"equalTo": str(self._contract.address)}},
                    "block": {
                        "executeContractMessages": {
                            "some": {"method": {"equalTo": method}}
                        }
                    },
                }
            )

            # query Cw20 balance changes, filter by accountID
            filter_by_account_id = filtered_cw20_balance_change_query(
                {
                    "accountId": {"equalTo": str(self.validator_address)},
                    "block": {
                        "executeContractMessages": {
                            "some": {"method": {"equalTo": method}}
                        }
                    },
                }
            )

            # query Cw20 balance changes, filter by balanceOffset
            filter_by_balance_offset = filtered_cw20_balance_change_query(
                {
                    "balanceOffset": {"greaterThan": "1"},
                    "block": {
                        "executeContractMessages": {
                            "some": {"method": {"equalTo": method}}
                        }
                    },
                }
            )

            for name, query in [
                ("by block timestamp range", filter_by_block_timestamp_range),
                ("by balance offset", filter_by_balance_offset),
                ("by account id equals", filter_by_account_id),
                ("by contract address", filter_by_contract_address),
            ]:
                with self.subTest(name):
                    result = self.gql_client.execute(query)
                    """
                    ["cw20BalanceChanges"]["nodes"][0] denotes the sequence of keys to access the message contents queried for above.
                    This provides {"accountId":Account address/id, "balanceOffset: balance change amount, "contract":contract address}
                    which can be destructured for the values of interest.
                    """
                    changes = result["cw20BalanceChanges"]["nodes"]
                    entry = self.methods[method]
                    # assuming that some queries return a list of values, iterate - such as with the method "transfer"
                    for result in changes:
                        self.assertNotEqual(
                            result, [], "\nGQLError: No results returned from query"
                        )
                        self.assertIn(
                            result["accountId"],
                            entry["account_id"],
                            "\nGQLError: transfer recipient address does not match",
                        )
                        self.assertIn(
                            int(result["balanceOffset"]),
                            entry["balance_offset"],
                            "\nGQLError: fund amount does not match",
                        )
                        self.assertEqual(
                            result["contract"]["id"],
                            entry["contract"],
                            "\nGQLError: contract address does not match",
                        )

        for name, query, orderAssert in (
            (
                "order by block height ascending",
                order_by_block_height_asc,
                self.assertGreaterEqual,
            ),
            (
                "order by block height descending",
                order_by_block_height_desc,
                self.assertLessEqual,
            ),
        ):
            with self.subTest(name):
                result = self.gql_client.execute(query)
                cw20_balance_changes = result["cw20BalanceChanges"]["nodes"]
                last = cw20_balance_changes[0]["block"]["height"]
                for entry in cw20_balance_changes:
                    cur = entry["block"]["height"]
                    orderAssert(
                        cur, last, msg="OrderAssertError: order of objects is incorrect"
                    )
                    last = cur


if __name__ == "__main__":
    unittest.main()
