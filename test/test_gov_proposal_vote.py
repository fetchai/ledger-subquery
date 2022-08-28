from cosmpy.aerial.tx import Transaction
from cosmpy.protos.cosmos.gov.v1beta1 import tx_pb2 as gov_tx, gov_pb2
from cosmpy.protos.cosmos.base.v1beta1 import coin_pb2
from cosmpy.aerial.client import utils
from google.protobuf import any_pb2
from gql import gql
import base, json, time, unittest, datetime as dt
from helpers.field_enums import GovProposalVoteFields


class TestGovernance(base.Base):
    vote_tx = None
    denom = "atestfet"
    amount = "10000000"
    option = 'YES'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.clean_db({"gov_proposal_votes"})

        proposal_content = any_pb2.Any()
        proposal_content.Pack(gov_pb2.TextProposal(
            title="Test Proposal",
            description="This is a test proposal"
        ), "")

        msg = gov_tx.MsgSubmitProposal(
            content=proposal_content,
            initial_deposit=[coin_pb2.Coin(
                denom=cls.denom,
                amount=cls.amount
            )],
            proposer=cls.validator_address
        )

        tx = Transaction()
        tx.add_message(msg)

        tx = utils.prepare_and_broadcast_basic_transaction(cls.ledger_client, tx, cls.validator_wallet)
        tx.wait_to_complete()
        cls.assertTrue(tx.response.is_successful(), "\nTXError: governance proposal tx unsuccessful")

        cls.msg = gov_tx.MsgVote(
            proposal_id=1,
            voter=cls.validator_address,
            option=gov_pb2.VoteOption.VOTE_OPTION_YES
        )
        cls.vote_tx = Transaction()
        cls.vote_tx.add_message(cls.msg)

    def test_proposal_vote(self):
        tx = utils.prepare_and_broadcast_basic_transaction(self.ledger_client, self.vote_tx, self.validator_wallet)
        tx.wait_to_complete()
        self.assertTrue(tx.response.is_successful(), "\nTXError: vote tx unsuccessful")

        # primitive solution to wait for indexer to observe and handle new tx - TODO: add robust solution
        time.sleep(5)

        vote = self.db_cursor.execute(GovProposalVoteFields.select_query()).fetchone()
        self.assertIsNotNone(vote, "\nDBError: table is empty - maybe indexer did not find an entry?")
        self.assertEqual(vote[GovProposalVoteFields.voter_address.value], self.validator_address, "\nDBError: voter address does not match")
        self.assertEqual(vote[GovProposalVoteFields.option.value], self.option, "\nDBError: voter option does not match")

    def test_retrieve_vote(self):  # As of now, this test depends on the execution of the previous test in this class.
        result = self.get_latest_block_timestamp()
        time_before = result - dt.timedelta(minutes=5)  # create a second timestamp for five minutes before
        time_before = json.dumps(time_before.isoformat())  # convert both to JSON ISO format
        time_latest = json.dumps(result.isoformat())

        # query governance votes, query related block and filter by timestamp, returning all within last five minutes
        query_by_timestamp = gql(
            """
            query get_votes_by_timestamp {
                govProposalVotes (
                filter: {
                    block: {
                    timestamp: {
                        greaterThanOrEqualTo: """ + time_before + """,
                                lessThanOrEqualTo: """ + time_latest + """
                            }
                        }
                    }) {
                    nodes {
                        transactionId
                        voterAddress
                        option
                    }
                }
            }
            """
        )

        # query governance votes, filter by voter
        query_by_voter = gql(
            """
            query get_votes_by_voter {
                govProposalVotes (
                filter: {
                    voterAddress: {
                        equalTo: \""""+str(self.validator_address)+"""\"
                    }
                }) {
                    nodes {
                        transactionId
                        voterAddress
                        option
                        }
                    }
                }
            """
        )

        # query governance votes, filter by option
        query_by_option = gql(
            """
            query get_votes_by_option {
                govProposalVotes (
                filter: {
                    option: {
                        equalTo: """+self.option+"""
                    }
                }) {
                    nodes {
                        transactionId
                        voterAddress
                        option
                        }
                    }
                }
            """
        )

        queries = [query_by_timestamp, query_by_voter, query_by_option]
        for query in queries:
            result = self.gql_client.execute(query)
            """
            ["govProposalVotes"]["nodes"][0] denotes the sequence of keys to access the message contents queried for above.
            This provides {"voterAddress":voter address, "option":voter option}
            which can be destructured for the values of interest.
            """
            message = result["govProposalVotes"]["nodes"]
            self.assertTrue(message[0], "\nGQLError: No results returned from query")
            self.assertEqual(message[0]["voterAddress"], self.validator_address, "\nGQLError: voter address does not match")
            self.assertEqual(message[0]["option"], self.option, "\nGQLError: voter option does not match")


if __name__ == '__main__':
    unittest.main()
