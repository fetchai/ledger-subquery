import base
from cosmpy.aerial.tx import Transaction
from cosmpy.protos.cosmos.gov.v1beta1 import tx_pb2 as gov_tx, gov_pb2
from cosmpy.protos.cosmos.base.v1beta1 import coin_pb2
from cosmpy.aerial.client import utils
from google.protobuf import any_pb2
from gql import gql
import time, unittest


class TestGovernance(base.Base):
    vote_tx = None
    denom = "atestfet"
    amount = "10000000"
    option = "YES"
    db_query = 'SELECT * from gov_proposal_votes'

    def setUp(self):
        proposal_content = any_pb2.Any()
        proposal_content.Pack(gov_pb2.TextProposal(
            title="Test Proposal",
            description="This is a test proposal"
        ), "")

        msg = gov_tx.MsgSubmitProposal(
            content=proposal_content,
            initial_deposit=[coin_pb2.Coin(
                denom=self.denom,
                amount=self.amount
            )],
            proposer=self.validator_address
        )

        tx = Transaction()
        tx.add_message(msg)

        tx = utils.prepare_and_broadcast_basic_transaction(self.ledger_client, tx, self.validator_wallet)
        tx.wait_to_complete()
        self.assertTrue(tx.response.is_successful(), "\nTXError: governance proposal tx unsuccessful")

        self.msg = gov_tx.MsgVote(
            proposal_id=1,
            voter=self.validator_address,
            option=gov_pb2.VoteOption.VOTE_OPTION_YES
        )
        self.vote_tx = Transaction()
        self.vote_tx.add_message(self.msg)

    def test_proposal_vote(self):
        self.db_cursor.execute('TRUNCATE table gov_proposal_votes')
        self.db.commit()
        self.assertFalse(self.db_cursor.execute(self.db_query).fetchall(), "\nDBError: table not empty after truncation")

        tx = utils.prepare_and_broadcast_basic_transaction(self.ledger_client, self.vote_tx, self.validator_wallet)
        tx.wait_to_complete()
        self.assertTrue(tx.response.is_successful(), "\nTXError: vote tx unsuccessful")

        time.sleep(5)

        row = self.db_cursor.execute(self.db_query).fetchone()
        self.assertIsNotNone(row, "\nDBError: table is empty - maybe indexer did not find an entry?")
        self.assertEqual(row[3], self.option, "\nDBError: voter option does not match")

    def test_retrieve_vote(self): # As of now, this test depends on the execution of the previous test in this class.
        query = gql(
            """
            query getGovernanceVotes {
                govProposalVotes {
                    nodes {
                        transactionId
                        voterAddress
                        option
                        }
                    }
                }
            """
        )

        result = self.gql_client.execute(query)
        self.assertEqual(result["govProposalVotes"]["nodes"][0]["voterAddress"], self.validator_address, "\nGQLError: voter address does not match")
        self.assertEqual(result["govProposalVotes"]["nodes"][0]["option"], self.option, "\nGQLError: voter option does not match")


if __name__ == '__main__':
    unittest.main()
