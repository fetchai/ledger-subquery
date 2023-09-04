import time
from cosmpy.aerial.client import LedgerClient, NetworkConfig
from cosmpy.aerial.wallet import LocalWallet

VALIDATOR_MNEMONIC = "nut grocery slice visit barrel peanut tumble patch slim logic install evidence fiction shield rich brown around arrest fresh position animal butter forget cost"
RECEIVER_MNEMONIC = "plug ceiling shine proud offer pact song pottery rate float water network hurry custom erupt leader render lucky clarify lecture stool cube fall exotic"

receiver_wallet = LocalWallet.from_mnemonic(RECEIVER_MNEMONIC)
validator_wallet = LocalWallet.from_mnemonic(VALIDATOR_MNEMONIC)

cfg = NetworkConfig(
    chain_id="test",
    url="grpc+http://fetch-node:9090",
    fee_minimum_gas_price=1,
    fee_denomination="atestfet",
    staking_denomination="atestfet",
)

client = LedgerClient(cfg)

while True:
    query = client.query_bank_balance(validator_wallet.address(), "atestfet")
    print(query)
    tx = client.send_tokens(receiver_wallet.address(), 5, "atestfet", validator_wallet)
    tx.wait_to_complete()
    time.sleep(5)
