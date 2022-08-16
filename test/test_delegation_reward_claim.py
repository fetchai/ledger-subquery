import base
from gql import gql
import time, unittest


class TestDelegation(base.Base):
    amount = 100
    db_query = 'SELECT * from dist_delegator_claims'

    def setUp(self):
        delegate_tx = self.ledger_client.delegate_tokens(self.validator_operator_address, self.amount, self.validator_wallet)
        delegate_tx.wait_to_complete()
        self.assertTrue(delegate_tx.response.is_successful(), "\nTXError: delegation tx unsuccessful")

    def test_claim_rewards(self):
        self.db_cursor.execute('TRUNCATE table dist_delegator_claims')
        self.db.commit()
        self.assertFalse(self.db_cursor.execute(self.db_query).fetchall(), "\nDBError: table not empty after truncation")

        claim_tx = self.ledger_client.claim_rewards(self.validator_operator_address, self.validator_wallet)
        claim_tx.wait_to_complete()
        self.assertTrue(claim_tx.response.is_successful(), "\nTXError: reward claim tx unsuccessful")

        time.sleep(5)

        row = self.db_cursor.execute(self.db_query).fetchone()
        self.assertIsNotNone(row, "\nDBError: table is empty - maybe indexer did not find an entry?")
        self.assertEqual(row[1], self.validator_address, "\nDBError: delegation address does not match")

    def test_retrieve_claim(self): # As of now, this test depends on the execution of the previous test in this class.
        query = gql(
            """
            query getDelegatorRewardClaim {
                distDelegatorClaims {
                    nodes {
                        transactionId
                        delegatorAddress
                        validatorAddress
                        }
                    }
                }
            """
        )

        result = self.gql_client.execute(query)
        self.assertEqual(result["distDelegatorClaims"]["nodes"][0]["delegatorAddress"], self.validator_address, "\nGQLError: delegation address does not match")
        self.assertEqual(result["distDelegatorClaims"]["nodes"][0]["validatorAddress"], str(self.validator_operator_address), "\nGQLError: validator address does not match")


if __name__ == '__main__':
    unittest.main()
