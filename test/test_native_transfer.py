from gql import gql
from functools import reduce
import time, unittest, base


class TestTransfer(base.Base):
    amount = 5000000
    denom = "atestfet"
    msg_type = '/cosmos.bank.v1beta1.MsgSend'
    db_query = 'SELECT * from native_transfers'

    def test_native_transfer(self):
        self.db_cursor.execute('TRUNCATE table native_transfers')
        self.db.commit()
        self.assertFalse(self.db_cursor.execute(self.db_query).fetchall(), "\nError: table not empty after truncation")

        tx = self.ledger_client.send_tokens(self.delegator_wallet.address(), self.amount, self.denom, self.validator_wallet)
        tx.wait_to_complete()
        self.assertTrue(tx.response.is_successful(), "\nTXError: transfer tx unsuccessful")

        time.sleep(5)

        row = self.db_cursor.execute(self.db_query).fetchone()

        self.assertIsNotNone(row, "\nDBError: table is empty - maybe indexer did not find an entry?")
        self.assertEqual(row[1]['amount'][0]['amount'], str(self.amount), "\nDBError: fund amount does not match")
        self.assertEqual(row[1]['amount'][0]['denom'], self.denom, "\nDBError: fund denomination does not match")
        self.assertEqual(row[1]['toAddress'], self.delegator_address, "\nDBError: swap sender address does not match")
        self.assertEqual(row[1]['fromAddress'], self.validator_address, "\nDBError: sender address does not match")

    def test_receive_transfer(self): # As of now, this test depends on the execution of the previous test in this class.
        query = gql(
            """
            query getNativeTransfers {
                nativeTransfers {
                    nodes {
                        transactionId
                        message
                        }
                    }
                }
            """
        )

        result = self.gql_client.execute(query)
        """ 
        ["nodes"][0]["message"] denotes the sequence of keys to access the message queried for above.
        This provides {"toAddress":address, "fromAddress":address, "amount":["amount":amount, "denom":denom]}
        which can further be queried for the values of interest.
        """
        message_ = result["nativeTransfers"]["nodes"][0]["message"]
        self.assertEqual(message_["amount"][0]["amount"], str(self.amount), "\nGQLError: fund amount does not match")
        self.assertEqual(message_["amount"][0]["denom"], self.denom, "\nGQLError: fund denomination does not match")
        self.assertEqual(message_["toAddress"], self.delegator_address, "\nGQLError: destination address does not match")
        self.assertEqual(message_["fromAddress"], self.validator_address, "\nGQLError: from address does not match")


if __name__ == '__main__':
    unittest.main()
