import {SelectResult} from "./src/utils";

export class Structure {
  static getInterface() {
    return Interface.Uncertain;
  }
}

export class CW20Structure extends Structure {
  private name = "";
  private symbol = "";
  private decimals = 0;
  private initial_balances: [{ amount: bigint, address: string }] = [{amount: BigInt(0), address: ""}];
  private mint: { minter: string } = {minter: ""};

  static listProperties() {
    const a = new CW20Structure();
    return Object.getOwnPropertyNames(a);
  }

  static getPropertyType(prop: string) {
    const a = new CW20Structure();
    return typeof (a[prop]);
  }

  static getInterface() {
    return Interface.CW20;
  }
}

export class LegacyBridgeSwapStructure extends Structure {
  private cap = BigInt(0);
  private reverse_aggregated_allowance = BigInt(0);
  private reverse_aggregated_allowance_approver_cap = BigInt(0);
  private lower_swap_limit = BigInt(0);
  private upper_swap_limit = BigInt(0);
  private swap_fee = BigInt(0);
  private paused_since_block = BigInt(0);
  private denom = "";
  private next_swap_id = "";

  static listProperties() {
    const a = new LegacyBridgeSwapStructure();
    return Object.getOwnPropertyNames(a);
  }

  static getPropertyType(prop: string) {
    const a = new LegacyBridgeSwapStructure();
    return typeof (a[prop]);
  }

  static getInterface() {
    return Interface.LegacyBridgeSwap;
  }
}

interface Message {
  id: string;
  type_url: string;
  json: string,
  transaction_id: string;
  block_id: string;
}

export enum AccessType {
	Unspecified,
	AccessTypeNobody,
	AccessTypeOnlyAddress,
    AccessTypeEverybody,
	AccessTypeAnyOfAddresses
}

export enum Interface {
    Uncertain,
    CW20,
    LegacyBridgeSwap
}

export interface StoreContractMessage {
  id: string,
  sender: string,
  permission: AccessType,
  contracts: [Contract],
  code_id: number,
  message_id: string,
  transaction_id: string,
  block_id: string,
}

export interface InstantiateContractMessage {
  id: string,
  sender: string,
  admin: string,
  code_id: number,
  label: string,
  payload: string,
  funds: [string],
  message_id: string,
  transaction_id: string,
  block_id: string
}

export interface Contract {
  id: string,
  interfaces: [Interface],
  storeMessage: StoreContractMessage,
  instantiateMessage: InstantiateContractMessage
}

function getJaccard(payload: object) {
  let prediction = Structure, prediction_coefficient = 0.5;   // prediction coefficient can be set as a minimum threshold for the certainty of an output
  let diff = 0, match = 0, coefficient = 0;                   // where coefficient of 1 is a perfect property key match, 2 is a perfect match of property and type
  const structs = [CW20Structure, LegacyBridgeSwapStructure];
  structs.forEach((struct) => {
    Object.keys(payload).forEach((payload_key) => {
      if (struct.listProperties().some((prop) => prop === payload_key)) { // If payload property exists as a property within current structure
        match++;
        if (payload[payload_key] && typeof (payload[payload_key]) === struct.getPropertyType(payload_key)) { // award bonus point for same value datatype
          match++;
        }
      } else {
        diff++;
      }
    });
    // If a set of properties is greatly different from ideal set, size of union is larger and num of matches is smaller
    const union = (struct.listProperties().length + diff);  // num of total properties to match + num of those that didn't match
    coefficient = match / union;                          // num of properties that matched divided by union is Jaccard Coefficient
    if (coefficient > prediction_coefficient) { // if current comparison gives the highest matching score (above minimum threshold), set as current best fit
      prediction_coefficient = coefficient;
      prediction = struct;
    }
    coefficient = match = diff = 0;
  });
  return prediction.getInterface();
}

export function migrationAddInterfaceSupport() {
  const storeMsgSelect = "SELECT (m.id, m.type_url, json, m.transaction_id, m.block_id) FROM messages m WHERE type_url = '/cosmwasm.wasm.v1.MsgStoreCode'";
  const instantiateMsgSelect = "SELECT (m.id, m.type_url, json, m.transaction_id, m.block_id) FROM messages m WHERE type_url = '/cosmwasm.wasm.v1.MsgInstantiateContract'";
  const storeCodeMsgResults: Message[] = plv8.execute(storeMsgSelect);
  const instantiateMsgResults: Message[] = plv8.execute(instantiateMsgSelect);

  for (const {id, json, transaction_id, block_id} of storeCodeMsgResults) {
    const jsonMsg = JSON.parse(json);

    const [attributes, tx_hash] = new SelectResult(plv8.execute("select e.attributes, t.hash from messages m join transactions t on m.transaction_id = t.id join events e on t.id = e.transaction_id where m.id = $1;", id));

    const attribute = attributes[0].find(a => (a as Record<string, any>).key === "code_id");
    const code_id = attribute.value;
    if (!attribute || !code_id) {
      throw new Error("store code msg missing code ID from event");
    }

    const msg_id = `${tx_hash}-${id}`;
    plv8.execute("INSERT INTO store_contract_messages (id, sender, permission, code_id, message_id, transaction_id, block_id) ($1, $2, $3, $4, $5, $6, $7)",
      [msg_id, jsonMsg.sender, jsonMsg.permission, code_id, id, transaction_id, block_id]);
  }

  for (const {id, json, transaction_id, block_id} of instantiateMsgResults) {
    const jsonMsg = JSON.parse(json);

    const [attributes, tx_hash] = new SelectResult(plv8.execute("select e.attributes, t.hash from messages m join transactions t on m.transaction_id = t.id join events e on t.id = e.transaction_id where m.id = $1;", id));

    const attribute = attributes[0].find(a => (a as Record<string, any>).key === "code_id");
    const code_id = attribute.value;
    if (!attribute || !code_id) {
      throw new Error("instantiate msg missing code ID from event");
    }

    const msg_id = `${tx_hash}-${id}`;
    plv8.execute("INSERT INTO instantiate_contract_messages (id, sender, admin, code_id, label, payload, funds, message_id, transaction_id, block_id) ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)",
      [msg_id, jsonMsg.sender, jsonMsg.admin, code_id, jsonMsg.label, jsonMsg.msg, jsonMsg.funds, id, transaction_id, block_id]);
  }

  const instantiate_msgs: InstantiateContractMessage[] = plv8.execute("select * from instantiate_contract_messages;");
  for (const {id, payload, transaction_id} of instantiate_msgs) {
    const [store_code_id, attributes] = new SelectResult(plv8.execute("select s.id, e.attributes from instantiate_contract_messages i join store_contract_messages s on i.code_id = s.code_id join messages m on i.message_id = m.id join transactions t on t.id = m.transaction_id join events e on t.id = e.transaction_id where i.id = $1;", [transaction_id]));
    const payload_stripped = JSON.stringify(payload, null);
    const attribute = attributes[0].find(a => (a as Record<string, any>).key === "_contract_address");
    const contract_address = attribute.value;
    if (!attribute || !contract_address) {
      throw new Error("instantiate msg missing contract address from event");
    }
    plv8.execute("insert into contracts (id, interfaces, store_contract_message_id, instantiate_message_id) ($1, {$2}, $3, $4)", [contract_address, getJaccard(JSON.parse(payload_stripped)), id, store_code_id]);
  }
}
