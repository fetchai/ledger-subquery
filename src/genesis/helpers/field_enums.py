from enum import Enum
from typing import List, Optional


def _class_name_to_snake_case(input_: str) -> str:
    output = [input_[0].lower()]
    for char in input_[1:]:
        if char in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            output.append("_")
            output.append(char.lower())
        else:
            output.append(char)

    return "".join(output)


class NamedFields(Enum):
    @classmethod
    def select_column_names(cls) -> List[str]:
        return [f'"{field.name}"' for field in cls]

    @classmethod
    def select_query(cls, tables: Optional[List[str]] = None, prefix=False) -> str:
        if tables is None:
            tables = [cls.get_table()]

        columns = cls.select_column_names()
        """ More complex queries might require disambiguation, eg. where two 'id' attributes are being referenced
            - 'relevant_table.id' this prefix would solve it"""
        if prefix:
            columns = [f"{cls.get_table()}.{column}" for column in columns]

        if len(tables) == 1:
            tables_str = tables[0]
        else:
            tables_str = ", ".join(tables)

        return f"SELECT {', '.join(columns)} FROM {tables_str}"

    @classmethod
    def select_where(
        cls, where_clause: str, tables: Optional[List[str]] = None, prefix=False
    ) -> str:
        return f"{cls.select_query(tables=tables, prefix=True)} WHERE {where_clause}"

    @classmethod
    def get_table(cls):
        # NB: lower_snake_case of class name must match table name
        return _class_name_to_snake_case(cls.__name__)


class Blocks(NamedFields):
    id = 0
    chain_id = 1
    height = 2
    timestamp = 3


class Transactions(NamedFields):
    id = 0
    block_id = 1
    gas_used = 2
    gas_wanted = 3
    fees = 4
    memo = 5
    status = 6
    log = 7
    timeout_height = 8
    signer_address = 9


class Messages(NamedFields):
    id = 0
    transaction_id = 1
    block_id = 2
    type_url = 3
    json = 4


class Events(NamedFields):
    id = 0
    transaction_id = 1
    block_id = 2
    type = 3


class NativeTransfers(NamedFields):
    id = 0
    amounts = 1
    denom = 2
    to_address = 3
    from_address = 4


class StoreContractMessages(NamedFields):
    id = 0
    sender = 1
    permission = 2
    code_id = 3
    message_id = 4
    transaction_id = 5
    block_id = 6


class InstantiateContractMessages(NamedFields):
    id = 0
    sender = 1
    admin = 2
    code_id = 3
    label = 4
    payload = 5
    funds = 6
    message_id = 7
    transaction_id = 8
    block_id = 9


class Contracts(NamedFields):
    id = 0
    interface = 1
    store_message_id = 2
    instantiate_message_id = 3


class Cw20Transfers(NamedFields):
    id = 0
    message_id = 1
    transaction_id = 2
    block_id = 3
    amount = 4
    to_address = 5
    from_address = 6
    contract_id = 7


class Cw20BalanceChanges(NamedFields):
    id = 0
    balance_offset = 1
    contract_id = 2
    account_id = 3
    event_id = 4
    transaction_id = 5
    block_id = 6

    @classmethod
    def by_execute_contract_method(cls, method):
        where = f" execute_contract_messages.id = execute_contract_message_id and method = '{method}'"
        tables = (cls.get_table(), "execute_contract_messages")
        return cls.select_where(where_clause=where, tables=tables, prefix=True)


class LegacyBridgeSwaps(NamedFields):
    id = 0
    message_id = 1
    transaction_id = 2
    block_id = 3
    destination = 4
    amount = 5
    denom = 6
    contract_id = 7


class GovProposalVotes(NamedFields):
    id = 0
    message_id = 1
    transaction_id = 2
    block_id = 3
    proposal_id = 4
    voter_address = 5
    option = 6


class ExecuteContractMessages(NamedFields):
    id = 0
    message_id = 1
    transaction_id = 2
    block_id = 3
    contract_id = 4
    method = 5
    funds = 6


class DistDelegatorClaims(NamedFields):
    id = 0
    message_id = 1
    transaction_id = 2
    block_id = 3
    delegator_address = 4
    validator_address = 5
    amount = 6
    denom = 7


class NativeBalanceChanges(NamedFields):
    id = 0
    balance_offset = 1
    denom = 2
    account_id = 3
    event_id = 4
    transaction_id = 5
    block_id = 6


class Accounts(NamedFields):
    id = 0
    chain_id = 1


class GenesisBalances(NamedFields):
    id = 0
    account_id = 1
    amount = 2
    denom = 3


class IBCTransfers(NamedFields):
    id = 0
    to_address = 1
    from_address = 2
    amount = 3
    denom = 4
    source_channel = 5
    source_port = 6
    event_id = 7
    message_id = 8
    transaction_id = 9
    block_id = 10

    @classmethod
    def get_table(cls):
        return "ibc_transfers"


class AuthzExecs(NamedFields):
    id = 0
    grantee = 1
    message_id = 2
    transaction_id = 3
    block_id = 4


class AuthzExecMessages(NamedFields):
    id = 0
    authz_exec_id = 1
    message_id = 2


class Agents(NamedFields):
    id = 0


class AlmanacRegistrations(NamedFields):
    id = 0
    expiry_height = 1
    signature = 2
    sequence = 3
    agent_id = 4
    record_id = 5
    transaction_id = 6
    block_id = 7
    #     event_id = 8
    #     record_id = 9


class AlmanacRecords(NamedFields):
    id = 0
    service = 1
    transaction_id = 2
    block_id = 3
    #     event_id = 4
