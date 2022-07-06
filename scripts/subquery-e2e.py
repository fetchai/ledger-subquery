from cosmpy.aerial.wallet import LocalWallet
from cosmpy.crypto.keypairs import PrivateKey
from bip_utils import Bip39SeedGenerator, Bip44, Bip44Coins
from cosmpy.aerial.client import LedgerClient, NetworkConfig

# ledger_client = LedgerClient(NetworkConfig.fetch_mainnet())

cfg = NetworkConfig(
    chain_id="testing",
    url="grpc+http://localhost:9090",
    fee_minimum_gas_price=1,
    fee_denomination="atestfet",
    staking_denomination="atestfet",
)

ledger_client = LedgerClient(cfg)

"""
Validator wallet
"""
validator_mnemonic = "nut grocery slice visit barrel peanut tumble patch slim logic install evidence fiction shield rich brown around arrest fresh position animal butter forget cost"

validator_seed_bytes = Bip39SeedGenerator(validator_mnemonic).Generate()
validator_bip44_def_ctx = Bip44.FromSeed(validator_seed_bytes, Bip44Coins.COSMOS).DeriveDefaultPath()

validator_wallet = LocalWallet(PrivateKey(validator_bip44_def_ctx.PrivateKey().Raw().ToBytes()))

"""
Delegator wallet
"""
delegator_mnemonic = "dismiss domain uniform image cute buzz ride anxiety nose canvas ripple stock buffalo bitter spirit maximum tone inner couch forum equal usage state scan"

delegator_seed_bytes = Bip39SeedGenerator(delegator_mnemonic).Generate()
delegator_bip44_def_ctx = Bip44.FromSeed(delegator_seed_bytes, Bip44Coins.COSMOS).DeriveDefaultPath()

delegator_wallet = LocalWallet(PrivateKey(delegator_bip44_def_ctx.PrivateKey().Raw().ToBytes()))


"""
Delegator reward claim
"""
validator_address: str = "fetch1wurz7uwmvchhc8x0yztc7220hxs9jxdjdsrqmn"
validator_operator_address: str = ""
balances = ledger_client.query_bank_all_balances(validator_address)
print("Validator pre balance:")
print(balances)

send_tx = ledger_client.send_tokens(delegator_wallet.address, 200000, "atestfet", validator_wallet)

delegate_tx = ledger_client.delegate_tokens(validator_operator_address, 100000, delegator_wallet)
delegate_tx.wait_to_complete()

balances = ledger_client.query_bank_all_balances(validator_address)
print("Validator post balance:")
print(balances)

balances = ledger_client.query_bank_all_balances(delegator_wallet.address)
print("Delegator post balance:")
print(balances)

