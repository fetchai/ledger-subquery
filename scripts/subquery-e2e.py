from cosmpy.aerial.wallet import LocalWallet
from cosmpy.aerial.tx import Transaction
from cosmpy.crypto.keypairs import PrivateKey
from cosmpy.crypto.address import Address
from cosmpy.protos.cosmos.gov.v1beta1 import tx_pb2 as gov_tx, gov_pb2, query_pb2_grpc
from cosmpy.protos.cosmos.base.v1beta1 import coin_pb2
from cosmpy.aerial.contract import LedgerContract
from bip_utils import Bip39SeedGenerator, Bip44, Bip44Coins
from cosmpy.aerial.client import LedgerClient, NetworkConfig, utils
from google.protobuf import any_pb2
import grpc, os, requests

# ledger_client = LedgerClient(NetworkConfig.fetch_mainnet())

cfg = NetworkConfig(
    chain_id="testing",
    url="grpc+http://localhost:9090",
    fee_minimum_gas_price=1,
    fee_denomination="atestfet",
    staking_denomination="atestfet",
)

gov_cfg = grpc.insecure_channel('localhost:9090')

ledger_client = LedgerClient(cfg)
gov_module = query_pb2_grpc.QueryStub(gov_cfg)

"""
Validator wallet
"""
validator_mnemonic = "nut grocery slice visit barrel peanut tumble patch slim logic install evidence fiction shield rich brown around arrest fresh position animal butter forget cost"
validator_seed_bytes = Bip39SeedGenerator(validator_mnemonic).Generate()
validator_bip44_def_ctx = Bip44.FromSeed(validator_seed_bytes, Bip44Coins.COSMOS).DeriveDefaultPath()
validator_wallet = LocalWallet(PrivateKey(validator_bip44_def_ctx.PrivateKey().Raw().ToBytes()))
validator_address = str(validator_wallet.address())
validator_operator_address = Address(bytes(validator_wallet.address()), prefix="fetchvaloper")

"""
Delegator wallet
"""
delegator_mnemonic = "dismiss domain uniform image cute buzz ride anxiety nose canvas ripple stock buffalo bitter spirit maximum tone inner couch forum equal usage state scan"
delegator_seed_bytes = Bip39SeedGenerator(delegator_mnemonic).Generate()
delegator_bip44_def_ctx = Bip44.FromSeed(delegator_seed_bytes, Bip44Coins.COSMOS).DeriveDefaultPath()
delegator_wallet = LocalWallet(PrivateKey(delegator_bip44_def_ctx.PrivateKey().Raw().ToBytes()))
delegator_address = str(delegator_wallet.address())

"""
Transaction event
"""
tx = ledger_client.send_tokens(delegator_wallet.address(), 10000000, "atestfet", validator_wallet)
tx.wait_to_complete()

"""
Govt proposal
"""

proposal_content = any_pb2.Any()
proposal_content.Pack(gov_pb2.TextProposal(
    title="Test Proposal",
    description="This is a test proposal"
), "")

msg = gov_tx.MsgSubmitProposal(
    content=proposal_content,
    initial_deposit=[coin_pb2.Coin(
        denom="atestfet",
        amount="10000000"
    )],
    proposer=validator_address
)

tx = Transaction()
tx.add_message(msg)

tx = utils.prepare_and_broadcast_basic_transaction(ledger_client, tx, validator_wallet)
tx.wait_to_complete()

"""
Governance deposit
"""

msg = gov_tx.MsgDeposit(
    proposal_id=1,
    depositor=delegator_address,
    amount=[coin_pb2.Coin(denom="atestfet", amount="1")]
)
tx = Transaction()
tx.add_message(msg)

tx = utils.prepare_and_broadcast_basic_transaction(ledger_client, tx, delegator_wallet)
tx.wait_to_complete()

"""
Governance vote
"""

msg = gov_tx.MsgVote(
    proposal_id=1,
    voter=validator_address,
    option=gov_pb2.VoteOption.VOTE_OPTION_YES
)
vote_tx = Transaction()
vote_tx.add_message(msg)

tx = utils.prepare_and_broadcast_basic_transaction(ledger_client, vote_tx, validator_wallet)
tx.wait_to_complete()

"""
Delegator reward claim
"""

delegate_tx = ledger_client.delegate_tokens(validator_operator_address, 100000, delegator_wallet)
delegate_tx.wait_to_complete()

claim_tx = ledger_client.claim_rewards(validator_operator_address, delegator_wallet)
claim_tx.wait_to_complete()

undelegate_tx = ledger_client.undelegate_tokens(validator_operator_address, 100000, delegator_wallet)

"""
Legacy Bridge Swap
"""
url = "https://github.com/fetchai/fetch-ethereum-bridge-v1/releases/download/v0.2.0/bridge.wasm"
contract_request = requests.get(url)

if not os.path.exists("../.contract"):
    os.mkdir("../.contract")
try:
    temp = open("../.contract/bridge.wasm", "rb")
    temp.close()
except:
    open("../.contract/bridge.wasm", "wb").write(contract_request.content)

contract = LedgerContract("../.contract/bridge.wasm", ledger_client)
contract.deploy(
    {"cap": "250000000000000000000000000",
     "reverse_aggregated_allowance": "3000000000000000000000000",
     "reverse_aggregated_allowance_approver_cap": "3000000000000000000000000",
     "lower_swap_limit": "1",
     "upper_swap_limit": "1000000000000000000000000",
     "swap_fee": "0",
     "paused_since_block": 18446744073709551615,
     "denom": "atestfet",
     "next_swap_id": 0
     },
    validator_wallet
)
contract.execute(
    {"swap": {"destination": validator_address}},
    validator_wallet,
    funds="10000atestfet"
)
