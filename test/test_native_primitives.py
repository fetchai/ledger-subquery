import json
import time
import unittest

import base
from helpers.field_enums import BlockFields, TxFields, MsgFields, EventFields
from helpers.regexes import block_id_regex, tx_id_regex, msg_id_regex, event_id_regex


class TestNativePrimitives(base.Base):
    tables = ("blocks", "transactions", "messages", "events")

    amount = 5000000
    denom = "atestfet"

    expected_blocks_len = 2
    expected_txs_len = 2
    expected_msgs_len = 2
    expected_msg_type_url = '/cosmos.bank.v1beta1.MsgSend'
    # NB: for each transfer:
    #   - coin_received
    #   - coin_spent
    #   - message
    #   - transfer
    expected_events_len = 2 * 4

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.db_cursor.execute(f"TRUNCATE table {', '.join(cls.tables)} CASCADE")
        cls.db.commit()

        for table in list(reversed(cls.tables)):
            results = cls.db_cursor.execute(f"SELECT id FROM {table}").fetchall()
            if len(results) != 0:
                raise Exception(f"truncation of table \"{table}\" failed, {len(results)} records remain")

        tx = cls.ledger_client.send_tokens(cls.delegator_wallet.address(), cls.amount, cls.denom, cls.validator_wallet)
        tx.wait_to_complete()
        if not tx.response.is_successful():
            raise Exception(f"first set-up tx failed")

        tx = cls.ledger_client.send_tokens(cls.delegator_wallet.address(), cls.amount, cls.denom, cls.validator_wallet)
        tx.wait_to_complete()
        if not tx.response.is_successful():
            raise Exception(f"second set-up tx failed")

        # Wait for subql node to sync
        time.sleep(5)

    def test_blocks(self):
        blocks = self.db_cursor.execute(BlockFields.select_query()).fetchall()
        self.assertNotEqual(blocks, [], f"\nDBError: block table is empty - maybe indexer did not find an entry?")

        self.assertGreaterEqual(len(blocks), self.expected_blocks_len)
        for block in blocks:
            # NB: continually increments while test run
            self.assertGreaterEqual(len(blocks), 2)
            self.assertRegex(block[BlockFields.id.value], block_id_regex)
            # TODO: expect proper chainId
            self.assertNotEqual(block[BlockFields.chain_id.value], "")
            self.assertTrue(block[BlockFields.height.value] > 0)
            # TODO: assert timestamp within last 5 min
            # TODO: timestamp is a number
            self.assertNotEqual(block[BlockFields.timestamp.value], "")

    def test_transactions(self):
        txs = self.db_cursor.execute(TxFields.select_query()).fetchall()
        self.assertEqual(len(txs), self.expected_txs_len)
        for tx in txs:
            self.assertRegex(tx[TxFields.id.value], tx_id_regex)
            self.assertTrue(len(tx[TxFields.block_id.value]) == 64)
            self.assertGreater(tx[TxFields.gas_used.value], 0)
            self.assertGreater(tx[TxFields.gas_wanted.value], 0)

            fees = json.loads(tx[TxFields.fees.value])
            # print(fees[0])
            self.assertEqual(len(fees), 1)
            self.assertEqual(fees[0]["denom"], self.denom)
            self.assertGreater(int(fees[0]["amount"]), 0)
            self.assertEqual(tx[TxFields.memo.value], "")
            self.assertEqual(tx[TxFields.status.value], "Success")
            self.assertNotEqual(tx[TxFields.log.value], "")

    def test_messages(self):

        msgs = self.db_cursor.execute(MsgFields.select_query()).fetchall()
        self.assertEqual(len(msgs), self.expected_msgs_len)
        for msg in msgs:
            self.assertRegex(msg[MsgFields.id.value], msg_id_regex)
            self.assertRegex(msg[MsgFields.transaction_id.value], tx_id_regex)
            self.assertNotEqual(msg[MsgFields.block_id.value], "")
            self.assertEqual(msg[MsgFields.type_url.value], self.expected_msg_type_url)
            self.assertNotEqual(msg[MsgFields.json.value], "")

    def test_events(self):
        events = self.db_cursor.execute(EventFields.select_query()).fetchall()
        self.assertEqual(len(events), self.expected_events_len)
        for event in events:
            self.assertRegex(event[EventFields.id.value], event_id_regex)
            self.assertRegex(event[EventFields.transaction_id.value], tx_id_regex)
            self.assertNotEqual(event[EventFields.block_id.value], "")
            self.assertNotEqual(event[EventFields.type.value], "")
            # TODO: more assertions (?)


if __name__ == '__main__':
    unittest.main()
