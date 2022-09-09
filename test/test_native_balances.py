import time
import unittest

import base
from helpers.field_enums import NativeBalanceFields


class TestNativeBalances(base.Base):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.clean_db({"native_balances"})

        tx = cls.ledger_client.send_tokens(cls.delegator_wallet.address(), 10*10**18, "atestfet", cls.validator_wallet)
        tx.wait_to_complete()
        cls.assertTrue(tx.response.is_successful(), "first set-up tx failed")
        
        tx = cls.ledger_client.send_tokens(cls.validator_wallet.address(), 3*10**18, "atestfet", cls.delegator_wallet)
        tx.wait_to_complete()
        cls.assertTrue(tx.response.is_successful(), "second set-up tx failed")

        # Wait for subql node to sync
        time.sleep(5)

    def test_account(self):
        events = self.db_cursor.execute(NativeBalanceFields.select_query()).fetchall()
        self.assertGreater(len(events), 0)

        total = {
            self.validator_wallet.address(): 0,
            self.delegator_wallet.address(): 0,
        }

        for event in events:
            self.assertTrue(
                (event[NativeBalanceFields.account_id.value] == self.validator_wallet.address() or
                event[NativeBalanceFields.account_id.value] == self.delegator_wallet.address())
            )
            self.assertNotEqual(int(event[NativeBalanceFields.balance_offset.value]), 0)
            self.assertEqual(event[NativeBalanceFields.denom.value], "atestfet")
            
            total[event[NativeBalanceFields.account_id.value]] += event[NativeBalanceFields.balance_offset.value]

        self.assertEqual(total[self.validator_wallet.address()], -7*10**18)
        self.assertEqual(total[self.delegator_wallet.address()], 7*10**18)
        
if __name__ == '__main__':
    unittest.main()
