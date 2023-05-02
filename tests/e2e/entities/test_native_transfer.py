import datetime as dt
import time
import unittest

from src.genesis.helpers.field_enums import NativeTransfers
from tests.helpers.entity_test import EntityTest
from tests.helpers.graphql import filtered_test_query
from tests.helpers.regexes import block_id_regex, msg_id_regex, tx_id_regex


class TestNativeTransfer(EntityTest):
    amount = 5000000
    denom = "atestfet"
    msg_type = "/cosmos.bank.v1beta1.MsgSend"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.clean_db({"native_transfers"})
        for i in range(3):  # enough entities are created to verify sorting
            tx = cls.ledger_client.send_tokens(
                cls.delegator_address, cls.amount, cls.denom, cls.validator_wallet
            )
            tx.wait_to_complete()
            cls.assertTrue(
                tx.response.is_successful(), "TXError: transfer unsuccessful"
            )
        # primitive solution to wait for indexer to observe and handle new tx - TODO: add robust solution
        time.sleep(5)

    def test_native_transfer(self):
        native_transfer = self.db_cursor.execute(
            NativeTransfers.select_query()
        ).fetchone()
        self.assertIsNotNone(
            native_transfer,
            "\nDBError: table is empty - maybe indexer did not find an entry?",
        )
        self.assertEqual(
            native_transfer[NativeTransfers.amounts.value][0]["amount"],
            str(self.amount),
            "\nDBError: fund amount does not match",
        )
        self.assertEqual(
            native_transfer[NativeTransfers.denom.value],
            self.denom,
            "\nDBError: fund denomination does not match",
        )
        self.assertEqual(
            native_transfer[NativeTransfers.to_address.value],
            self.delegator_address,
            "\nDBError: swap sender address does not match",
        )
        self.assertEqual(
            native_transfer[NativeTransfers.from_address.value],
            self.validator_address,
            "\nDBError: sender address does not match",
        )

    def test_retrieve_transfer(self):
        result = self.get_latest_block_timestamp()
        # create a second timestamp for five minutes before
        min_timestamp = (
            result - dt.timedelta(minutes=5)
        ).isoformat()  # convert both to JSON ISO format
        max_timestamp = result.isoformat()

        native_transfer_nodes = """
            {
                id,
                message { id }
                transaction { id }
                block {
                    id
                    height
                }
                amounts
                denom
                toAddress
                fromAddress
            }
            """

        default_filter = {  # filter parameter of helper function must not be null, so instead use rhetorical filter
            "block": {"height": {"greaterThanOrEqualTo": "0"}}
        }

        def filtered_native_transfer_query(_filter, order=""):
            return filtered_test_query(
                "nativeTransfers", _filter, native_transfer_nodes, _order=order
            )

        order_by_block_height_asc = filtered_native_transfer_query(
            default_filter, "TIMELINE_ASC"
        )

        order_by_block_height_desc = filtered_native_transfer_query(
            default_filter, "TIMELINE_DESC"
        )

        # query native transactions, query related block and filter by timestamp, returning all within last five minutes
        filter_by_block_timestamp_range = filtered_native_transfer_query(
            {
                "block": {
                    "timestamp": {
                        "greaterThanOrEqualTo": min_timestamp,
                        "lessThanOrEqualTo": max_timestamp,
                    }
                }
            }
        )

        # query native transactions, filter by recipient address
        filter_by_to_address_equals = filtered_native_transfer_query(
            {"toAddress": {"equalTo": self.delegator_address}}
        )

        # query native transactions, filter by sender address
        filter_by_from_address_equals = filtered_native_transfer_query(
            {"fromAddress": {"equalTo": self.validator_address}}
        )

        # query native transactions, filter by denomination
        filter_by_denom_equals = filtered_native_transfer_query(
            {"denom": {"equalTo": self.denom}}
        )

        for name, query in [
            ("by block timestamp range", filter_by_block_timestamp_range),
            ("by toAddress equals", filter_by_to_address_equals),
            ("by fromAddress equals", filter_by_from_address_equals),
            ("by denom equals", filter_by_denom_equals),
        ]:
            with self.subTest(name):
                result = self.gql_client.execute(query)
                """
                ["nativeTransfers"]["nodes"][0] denotes the sequence of keys to access the message contents queried for above.
                This provides {"toAddress":address, "fromAddress":address, "denom":denom, "amount":["amount":amount, "denom":denom]}
                which can be destructured for the values of interest.
                """
                native_transfers = result["nativeTransfers"]["nodes"]
                self.assertNotEqual(
                    native_transfers, [], "\nGQLError: No results returned from query"
                )
                self.assertRegex(native_transfers[0]["id"], msg_id_regex)
                self.assertRegex(native_transfers[0]["message"]["id"], msg_id_regex)
                self.assertRegex(native_transfers[0]["transaction"]["id"], tx_id_regex)
                self.assertRegex(native_transfers[0]["block"]["id"], block_id_regex)
                # NB: `amount` is a list of `Coin`s (i.e. [{amount: "", denom: ""}, ...])
                self.assertEqual(
                    int(native_transfers[0]["amounts"][0]["amount"]),
                    self.amount,
                    "\nGQLError: fund amount does not match",
                )
                self.assertEqual(
                    native_transfers[0]["amounts"][0]["denom"],
                    self.denom,
                    "\nGQLError: fund denom does not match",
                )
                self.assertEqual(
                    native_transfers[0]["denom"],
                    self.denom,
                    "\nGQLError: fund denomination does not match",
                )
                self.assertEqual(
                    native_transfers[0]["toAddress"],
                    self.delegator_address,
                    "\nGQLError: destination address does not match",
                )
                self.assertEqual(
                    native_transfers[0]["fromAddress"],
                    self.validator_address,
                    "\nGQLError: from address does not match",
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
            result = self.gql_client.execute(query)
            native_transfers = result["nativeTransfers"]["nodes"]
            last = native_transfers[0]["block"]["height"]
            for entry in native_transfers:
                cur = entry["block"]["height"]
                orderAssert(
                    cur, last, msg="OrderAssertError: order of objects is incorrect"
                )
                last = cur


if __name__ == "__main__":
    unittest.main()
