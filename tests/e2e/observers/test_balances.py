import unittest

from src.genesis.helpers.field_enums import GenesisBalances
from src.genesis.processing.balances import BalanceManager
from tests.helpers.clients import TestWithDBConn
from tests.helpers.genesis_data import test_bank_state_balances, test_genesis_data


class TestBalanceManager(TestWithDBConn):
    @classmethod
    def setUpClass(cls):
        TestWithDBConn().setUpClass()
        super().setUpClass()

    @classmethod
    def reinit_db(cls):
        cls.clean_db(["native_balances", "accounts"])

        with cls.db_conn.cursor() as db:
            # TODO: reference test data rather than more magic string literals
            db.execute("INSERT INTO accounts (id, chain_id) VALUES ('addr123', 'test')")
            db.execute("INSERT INTO accounts (id, chain_id) VALUES ('addr456', 'test')")
            cls.db_conn.commit()

    def test_observe(self):
        # Clean DB to prevent interaction with other tests
        self.reinit_db()

        test_manager = BalanceManager(self.db_conn)
        test_manager.process_genesis(test_genesis_data)

        actual_balances: [dict] = self.collect_actual_balances()
        self.check_balances(test_bank_state_balances, actual_balances)

    def collect_actual_balances(self):
        actual_balances = []

        with self.db_conn.cursor() as db:
            for address in [b["address"] for b in test_bank_state_balances]:
                balance = {"address": address}
                balance["coins"] = []

                for row in db.execute(
                    GenesisBalances.select_where(f"account_id = '{address}'")
                ).fetchall():
                    balance["coins"].append(
                        {
                            "amount": int(row[GenesisBalances.amount.value]),
                            "denom": row[GenesisBalances.denom.value],
                        }
                    )

                actual_balances.append(balance)

        return actual_balances

    def check_balances(self, expected_balances, actual_balances):
        for expected_balance in expected_balances:
            found_balance = False
            actual_balance = None
            for actual_balance_ in actual_balances:
                if actual_balance_["address"] == expected_balance["address"]:
                    found_balance = True
                    actual_balance = actual_balance_
                    break

            self.assertTrue(found_balance)
            self.assertEqual(expected_balance["address"], actual_balance["address"])

            for expected_coin in expected_balance["coins"]:
                found_coin = False
                actual_coin = None
                for actual_coin_ in actual_balance["coins"]:
                    if actual_coin_["denom"] == expected_coin["denom"]:
                        found_coin = True
                        actual_coin = actual_coin_
                        break

                self.assertTrue(found_coin)
                self.assertEqual(expected_coin, actual_coin)


if __name__ == "__main__":
    unittest.main()
