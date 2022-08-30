import datetime as dt
import json
import re
import time
import unittest

from gql import gql

import base
from helpers.field_enums import DistDelegatorClaimFields
from helpers.regexes import msg_id_regex, block_id_regex, tx_id_regex


class TestDelegation(base.Base):
    amount = 100

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.clean_db({"dist_delegator_claims"})

        delegate_tx = cls.ledger_client.delegate_tokens(cls.validator_operator_address, cls.amount, cls.validator_wallet)
        delegate_tx.wait_to_complete()
        cls.assertTrue(delegate_tx.response.is_successful(), "\nTXError: delegation tx unsuccessful")

        claim_tx = cls.ledger_client.claim_rewards(cls.validator_operator_address, cls.validator_wallet)
        claim_tx.wait_to_complete()
        cls.assertTrue(claim_tx.response.is_successful(), "\nTXError: reward claim tx unsuccessful")

        # primitive solution to wait for indexer to observe and handle new tx - TODO: add robust solution
        time.sleep(5)

    def test_claim_rewards(self):
        row = self.db_cursor.execute(DistDelegatorClaimFields.select_query()).fetchone()
        self.assertIsNotNone(row, "\nDBError: table is empty - maybe indexer did not find an entry?")
        self.assertEqual(row[DistDelegatorClaimFields.delegator_address.value], self.validator_address, "\nDBError: delegation address does not match")
        self.assertEqual(row[DistDelegatorClaimFields.validator_address.value], self.validator_operator_address, "\nDBError: delegation address does not match")

    def test_retrieve_claim(self):  # As of now, this test depends on the execution of the previous test in this class.
        latest_block_timestamp = self.get_latest_block_timestamp()
        # create a second timestamp for five minutes before
        min_timestamp = (latest_block_timestamp - dt.timedelta(minutes=5)).isoformat()  # convert both to JSON ISO format
        max_timestamp = latest_block_timestamp.isoformat()

        # TODO: refactor with `TestContractSwap`'s `test_filtered_swaps_query`
        def test_filtered_claim_query(_filter):
            quoted_key_regex = re.compile('"(\w+)":')
            # NB: strip quotes from object keys
            filter_string = quoted_key_regex.sub("\g<1>:", json.dumps(_filter))

            return gql("""
            query {
                distDelegatorClaims (filter: """ + filter_string + """) {
                    nodes {
                        id
                        message { id }
                        transaction { id }
                        block { id }
                        validatorAddress
                        delegatorAddress
                        amount
                        denom
                    }
                }
            }
            """)

        # query governance votes, query related block and filter by timestamp, returning all within last five minutes
        query_by_timestamp = test_filtered_claim_query({
            "block": {
                "timestamp": {
                    "greaterThanOrEqualTo": min_timestamp,
                    "lessThanOrEqualTo": max_timestamp
                }
            }
        })

        # query delegator reward claims, filter by validator address
        query_by_validator = test_filtered_claim_query({
            "validatorAddress": {
                "equalTo": str(self.validator_operator_address)
            }
        })

        # query delegator reward claims, filter by delegator address
        query_by_delegator = test_filtered_claim_query({
            "delegatorAddress": {
                "equalTo": str(self.validator_address)
            }
        })

        for query in [query_by_timestamp, query_by_validator, query_by_delegator]:
            result = self.gql_client.execute(query)
            """
            ["distDelegatorClaims"]["nodes"][0] denotes the sequence of keys to access the message contents queried for above.
            This provides {"delegatorAddress":delegator address, "validatorAddress":validator option}
            which can be destructured for the values of interest.
            """
            claims = result["distDelegatorClaims"]["nodes"]
            self.assertTrue(claims[0], "\nGQLError: No results returned from query")
            self.assertRegex(claims[0]["id"], msg_id_regex)
            self.assertRegex(claims[0]["message"]["id"], msg_id_regex)
            self.assertRegex(claims[0]["transaction"]["id"], tx_id_regex)
            self.assertRegex(claims[0]["block"]["id"], block_id_regex)
            self.assertEqual(claims[0]["delegatorAddress"], self.validator_address,
                             "\nGQLError: delegation address does not match")
            self.assertEqual(claims[0]["validatorAddress"], self.validator_operator_address,
                             "\nGQLError: validator address does not match")
            self.assertRegex(claims[0]["amount"], re.compile("^\d{1,30}$"))
            self.assertRegex(claims[0]["denom"], re.compile("^\w{1,50}$"))


if __name__ == '__main__':
    unittest.main()
