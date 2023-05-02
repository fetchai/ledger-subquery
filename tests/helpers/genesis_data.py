from typing import Dict, List

test_bank_state_balances: List[Dict] = [
    {
        "address": "addr123",
        "coins": [
            {"amount": 123, "denom": "a-token"},
            {"amount": 456, "denom": "b-token"},
        ],
    },
    {
        "address": "addr456",
        "coins": [
            {"amount": 111, "denom": "a-token"},
            {"amount": 222, "denom": "b-token"},
        ],
    },
]

test_bank_state_supply: List[Dict] = [
    {"amount": "987", "denom": "a-token"},
    {"amount": "654", "denom": "b-token"},
]

test_bank_state: Dict = {
    "balances": test_bank_state_balances,
    "denom_metadata": [],
    "params": {},
    "supply": test_bank_state_supply,
}

test_wasm_state_contracts: List[Dict] = [
    {
        "contract_address": "fetch1qxxlalvsdjd07p07y3rc5fu6ll8k4tmetpha8n",
        "contract_info": {
            "code_id": "1",
            "label": "token-bridge-contract"
        },
    },
    {
        "contract_address": "fetch1pvrwmjuusn9wh34j7y520g8gumuy9xtljwctjp",
        "contract_info": {
            "code_id": "2",
            "label": "decibel"
        },
    },
]

test_wasm_state: Dict = {
    "codes": {},
    "contracts": test_wasm_state_contracts,
    "gen_msgs": {},
    "params": {},
    "sequences": {},
}


test_app_state: Dict = {
    "airdrop": {},
    "auth": {},
    "authz": {},
    "bank": test_bank_state,
    "capability": {},
    "crisis": {},
    "distribution": {},
    "evidence": {},
    "feegrant": {},
    "genutil": {},
    "gov": {},
    "ibc": {},
    "mint": {},
    "params": {},
    "slashing": {},
    "staking": {},
    "transfer": {},
    "upgrade": {},
    "vesting": {},
    "wasm": test_wasm_state,
}

test_genesis_data: Dict = {
    "app_hash": {},
    "app_state": test_app_state,
    "chain_id": "test",
    "consensus_params": {},
    "genesis_time": "",
    "initial_height": "",
    "validators": [],
}
