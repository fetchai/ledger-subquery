import {CosmosEvent, CosmosMessage} from "@subql/types-cosmos";
import {ExecuteContractMsg} from "../types";
import {messageId} from "../utils";
import {
  Contract,
  ExecuteContractMessage,
  InstantiateContractMessage,
  Interface,
  StoreContractMessage
} from "../../types/";

export async function handleExecuteContractEvent(event: CosmosEvent): Promise<void> {
  const msg: CosmosMessage<ExecuteContractMsg> = event.msg;
  logger.info(`[handleExecuteContractMessage] (tx ${msg.tx.hash}): indexing ExecuteContractMessage ${messageId(msg)}`);
  logger.debug(`[handleExecuteContractMessage] (event.msg.msg): ${JSON.stringify(msg.msg, null, 2)}`);

  const id = messageId(msg);
  const funds = msg?.msg?.decodedMsg?.funds, contract = msg?.msg?.decodedMsg?.contract;
  const method = Object.keys(msg?.msg?.decodedMsg?.msg)[0];

  if (!funds || !contract || !method) {
    logger.warn(`[handleExecuteContractEvent] (tx ${event.tx.hash}): cannot index event (event.event): ${JSON.stringify(event.event, null, 2)}`);
    return;
  }

  const msgEntity = ExecuteContractMessage.create({
    id,
    method,
    contract,
    funds,
    messageId: id,
    transactionId: msg.tx.hash,
    blockId: msg.block.block.id
  });

  // NB: no need to update msg ids in txs.

  await msgEntity.save();
}

export async function handleContractStoreEvent(event: CosmosEvent): Promise<void> {
  logger.info(`[handleContractStoreEvent] (tx ${event.msg.tx.hash}): indexing event ${messageId(event.msg)}`);
  logger.debug(`[handleContractStoreEvent] (event.event): ${JSON.stringify(event.event, null, 2)}`);
  logger.debug(`[handleContractStoreEvent] (event.log): ${JSON.stringify(event.log, null, 2)}`);

  const id = messageId(event.msg);
  const sender = event.msg?.msg?.decodedMsg?.sender;
  const permission = event.msg?.msg?.decodedMsg?.permission;

  const code_attr = event.event.attributes.find((e) => e.key === "code_id");
  const codeId = Number(code_attr?.value);

  if (!sender || !codeId) {
    logger.warn(`[handleContractStoreEvent] (tx ${event.tx.hash}): cannot index event (event.event): ${JSON.stringify(event.event, null, 2)}`);
    return;
  }


  const storeMsg = StoreContractMessage.create({
    id,
    sender,
    permission,
    codeId,
    messageId: id,
    transactionId: event.msg.tx.hash,
    blockId: event.msg.block.block.id,
  });
  await storeMsg.save();
}

export async function handleContractInstantiateEvent(event: CosmosEvent): Promise<void> {
  logger.info(`[handleContractInstantiateEvent] (tx ${event.msg.tx.hash}): indexing event ${messageId(event.msg)}`);
  logger.debug(`[handleContractInstantiateEvent] (event.event): ${JSON.stringify(event.event, null, 2)}`);
  logger.debug(`[handleContractInstantiateEvent] (event.log): ${JSON.stringify(event.log, null, 2)}`);

  const id = messageId(event.msg);
  const msg_decoded = event.msg?.msg?.decodedMsg;
  const sender = msg_decoded?.sender, admin = msg_decoded?.admin;
  const label = msg_decoded?.label, payload = msg_decoded?.msg, funds = msg_decoded?.funds;

  const code_attr = event.event.attributes.find((e) => e.key === "code_id");
  const address_attr = event.event.attributes.find((e) => e.key === "_contract_address");
  const codeId = Number(code_attr?.value);
  const contract_address = address_attr?.value;

  if (!sender || !codeId || !label || !payload || !codeId || !contract_address) {
    logger.warn(`[handleContractInstantiateEvent] (tx ${event.tx.hash}): cannot index event (event.event): ${JSON.stringify(event.event, null, 2)}`);
    return;
  }

  const instantiateMsg = InstantiateContractMessage.create({
    id,
    sender,
    admin,
    codeId,
    label,
    payload,
    funds,
    messageId: id,
    transactionId: event.msg.tx.hash,
    blockId: event.msg.block.block.id,
  });
  await instantiateMsg.save();
  await saveContractEvent(instantiateMsg, contract_address, event);
}

async function saveContractEvent(instantiateMsg: InstantiateContractMessage, contract_address: string, event: CosmosEvent) {
  const storeCodeMsg = (await StoreContractMessage.getByCodeId(instantiateMsg.codeId))[0];

  if (!storeCodeMsg || !contract_address || !instantiateMsg) {
    logger.warn(`[saveContractEvent] (tx ${event.tx.hash}): failed to save contract (storeCodeMsg, instantiateMsg): ${storeCodeMsg}, ${instantiateMsg}`);
    return;
  }

  const contract = Contract.create({
    id: contract_address,
    interfaces: [await getJaccardResult(instantiateMsg.payload)],
    storeMessageId: storeCodeMsg.id,
    instantiateMessageId: instantiateMsg.id
  });
  await contract.save();
}

async function getJaccardResult(payload: string): Promise<Interface> {
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
  return prediction.getInterface(); // return best matched Interface to contract
}


class Structure {
  static getInterface() {
    return Interface.Uncertain;
  }
}

class CW20Structure extends Structure {
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

class LegacyBridgeSwapStructure extends Structure {
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