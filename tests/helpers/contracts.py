import os
from dataclasses import dataclass

import requests
from cosmpy.aerial.client import LedgerClient
from cosmpy.aerial.contract import LedgerContract
from cosmpy.aerial.wallet import Wallet
from cosmpy.crypto.address import Address
from dataclasses_json import dataclass_json


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
    next_swap_id=0,
)


def ensure_contract(name: str, url: str) -> str:
    contract_path = f".contract/{name}.wasm"
    if not os.path.exists(".contract"):
        os.mkdir(".contract")
    try:
        temp = open(contract_path, "rb")
        temp.close()
    except OSError:
        contract_request = requests.get(url)
        with open(contract_path, "wb") as file:
            file.write(contract_request.content)
    finally:
        return contract_path


class DeployTestContract(LedgerContract):

    def __init__(self, client: LedgerClient, admin: Wallet):
        """ Using a slightly older version of CW20 contract as a test contract - as this will still be classified as the
            CW20 interface, but is different enough to allow a unique store_code message during testing."""
        url = "https://github.com/CosmWasm/cw-plus/releases/download/v0.14.0/cw20_base.wasm"
        contract_path = ensure_contract("test_contract", url)
        super().__init__(contract_path, client)

        self.deploy({
            "name": "test coin",
            "symbol": "TEST",
            "decimals": 6,
            "initial_balances": [{
                "amount": "3000000000000000000000000",
                "address": str(admin.address())
            }],
            "mint": {"minter": str(admin.address())}
        },
            admin,
            store_gas_limit=3000000
        )


class Cw20Contract(LedgerContract):
    admin: Wallet = None
    gas_limit: int = 3000000

    def __init__(self, client: LedgerClient, admin: Wallet):
        self.admin = admin
        url = "https://github.com/CosmWasm/cw-plus/releases/download/v0.16.0/cw20_base.wasm"
        contract_path = ensure_contract("cw20", url)
        super().__init__(contract_path, client)

    def _store(self) -> int:
        assert self.admin is not None
        return self.store(self.admin, self.gas_limit)

    def _instantiate(self, code_id) -> Address:
        assert self.admin is not None
        return self.instantiate(
            code_id,
            {
                "name": "test coin",
                "symbol": "TEST",
                "decimals": 6,
                "initial_balances": [
                    {
                        "amount": "3000000000000000000000000",
                        "address": str(self.admin.address()),
                    }
                ],
                "mint": {"minter": str(self.admin.address())},
            },
            self.admin,
        )


class BridgeContract(LedgerContract):
    def __init__(self, client: LedgerClient, admin: Wallet, cfg: BridgeContractConfig):
        url = "https://github.com/fetchai/contract-agent-almanac/releases/download/v0.1.0/contract_agent_almanac.wasm"
        contract_path = ensure_contract("bridge", url)

        # LedgerContract will attempt to discover any existing contract having the same bytecode hash
        # see https://github.com/fetchai/cosmpy/blob/master/cosmpy/aerial/contract/__init__.py#L74
        super().__init__(contract_path, client)

        # deploy will store the contract only if no existing contracts was found during init.
        # and it will instantiate the contract only if contract.address is None
        # see: https://github.com/fetchai/cosmpy/blob/master/cosmpy/aerial/contract/__init__.py#L168-L179
        self.deploy(cfg.to_dict(), admin, store_gas_limit=3000000)
