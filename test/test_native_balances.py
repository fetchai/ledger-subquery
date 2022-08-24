import time

import base
from helpers.field_enums import NativeBalanceFields
from helpers.regexes import native_addr_id_regex, native_addr_regex


class TestNativeBalances(base.Base):
    amount = 5000000
    denom = "atestfet"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.db_cursor.execute("TRUNCATE table account_balances")
        cls.db.commit()

        results = cls.db_cursor.execute("SELECT id FROM account_balances").fetchall()
        if len(results) != 0:
            raise Exception(f"truncation of table \"accounts\" failed, {len(results)} records remain")

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

    def test_account(self):
        balances = self.db_cursor.execute(NativeBalanceFields.select_query()).fetchall()
        self.assertGreater(len(balances), 0)

        for balance in balances:
            self.assertRegex(balance[NativeBalanceFields.id.value], native_addr_id_regex)
            self.assertRegex(balance[NativeBalanceFields.address.value], native_addr_regex)
            self.assertEqual(int(balance[NativeBalanceFields.amount]), self.amount)
