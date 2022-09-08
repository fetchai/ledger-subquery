from dataclasses import dataclass
from dataclasses_json import dataclass_json
import requests, os
from cosmpy.aerial.contract import LedgerContract
from cosmpy.aerial.client import LedgerClient
from cosmpy.aerial.wallet import Wallet


@dataclass_json
@dataclass
class BridgeContractConfig:
    cap: str
    reverse_aggregated_allowance: str
    reverse_aggregated_allowance_approver_cap: str
    lower_swap_limit: str
    upper_swap_limit: str
    swap_fee: str
    paused_since_block: int
    denom: str
    next_swap_id: int

DefaultBridgeContractConfig = BridgeContractConfig(
    cap="250000000000000000000000000",
    reverse_aggregated_allowance="3000000000000000000000000",
    reverse_aggregated_allowance_approver_cap="3000000000000000000000000",
    lower_swap_limit="1",
    upper_swap_limit="1000000000000000000000000",
    swap_fee="0",
    paused_since_block=18446744073709551615,
    denom="atestfet",
    next_swap_id=0
)


@dataclass_json
@dataclass
class CW20BalanceObject:
    amount: int
    address: str


@dataclass_json
@dataclass
class CW20ContractConfig:
    name: str
    symbol: str
    decimals: int
    initial_balances: list[dict[str, str]]


DefaultCW20ContractConfig = CW20ContractConfig(
    name="test coin",
    symbol="TEST",
    decimals=6,
    initial_balances=[{
            "amount": "3000000",
            "address": "fetch1wurz7uwmvchhc8x0yztc7220hxs9jxdjdsrqmn"  # validator address
    }]
)


class CW20Contract(LedgerContract):

    def __init__(self, client: LedgerClient, admin: Wallet, cfg: CW20ContractConfig):
        url = "https://github.com/CosmWasm/cw-plus/releases/download/v0.14.0/cw20_base.wasm"
        if not os.path.exists(".contract"):
            os.mkdir(".contract")
        try:
            temp = open(".contract/cw20.wasm", "rb")
            temp.close()
        except:
            contract_request = requests.get(url)
            file = open(".contract/cw20.wasm", "wb")
            file.write(contract_request.content)
            file.close()

        super().__init__(".contract/cw20.wasm", client)

        self.deploy(
            cfg.to_dict(),
            admin,
            store_gas_limit=3000000
        )


class BridgeContract(LedgerContract):

    def __init__(self, client: LedgerClient, admin: Wallet, cfg: BridgeContractConfig):
        url = "https://github.com/fetchai/fetch-ethereum-bridge-v1/releases/download/v0.2.0/bridge.wasm"
        if not os.path.exists(".contract"):
            os.mkdir(".contract")
        try:
            temp = open(".contract/bridge.wasm", "rb")
            temp.close()
        except:
            contract_request = requests.get(url)
            file = open(".contract/bridge.wasm", "wb")
            file.write(contract_request.content)
            file.close()

        # LedgerContract will attempt to discover any existing contract having the same bytecode hash
        # see https://github.com/fetchai/cosmpy/blob/master/cosmpy/aerial/contract/__init__.py#L74
        super().__init__(".contract/bridge.wasm", client)

        # deploy will store the contract only if no existing contracts was found during init.
        # and it will instantiate the contract only if contract.address is None
        # see: https://github.com/fetchai/cosmpy/blob/master/cosmpy/aerial/contract/__init__.py#L168-L179
        self.deploy(
            cfg.to_dict(),
            admin,
            store_gas_limit=3000000
        )
