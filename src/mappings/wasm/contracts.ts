import {CosmosEvent, CosmosMessage} from "@subql/types-cosmos";
import {ExecuteContractMsg} from "../types";
import {
  attemptHandling,
  getJaccardResult,
  getTimeline,
  messageId,
  unprocessedEventHandler
} from "../utils";
import {
  Contract,
  ExecuteContractMessage,
  InstantiateContractMessage,
  StoreContractMessage
} from "../../types/";

export async function handleExecuteContractEvent(event: CosmosEvent): Promise<void> {
  await attemptHandling(event,
    _handleExecuteContractEvent,
    unprocessedEventHandler);
}

export async function handleContractStoreEvent(event: CosmosEvent): Promise<void> {
  await attemptHandling(event,
    _handleContractStoreEvent,
    unprocessedEventHandler);
}

export async function handleContractInstantiateEvent(event: CosmosEvent): Promise<void> {
  await attemptHandling(event,
    _handleContractInstantiateEvent,
    unprocessedEventHandler);
}

async function _handleExecuteContractEvent(event: CosmosEvent): Promise<void> {
  const msg: CosmosMessage<ExecuteContractMsg> = event.msg;
  logger.info(`[handleExecuteContractMessage] (tx ${msg.tx.hash}): indexing ExecuteContractMessage ${messageId(msg)}`);
  logger.debug(`[handleExecuteContractMessage] (event.msg.msg): ${JSON.stringify(msg.msg, null, 2)}`);
  const timeline = getTimeline(event);

  const id = messageId(msg);
  const funds = msg?.msg?.decodedMsg?.funds, contractId = msg?.msg?.decodedMsg?.contract;
  const method = Object.keys(msg?.msg?.decodedMsg?.msg)[0];

  if (!funds || !contractId || !method) {
    logger.warn(`[handleExecuteContractEvent] (tx ${event.tx.hash}): cannot index event (event.event): ${JSON.stringify(event.event, null, 2)}`);
    return;
  }

  const msgEntity = ExecuteContractMessage.create({
    id,
    method,
    contractId,
    funds,
    timeline,
    messageId: id,
    transactionId: msg.tx.hash,
    blockId: msg.block.block.id
  });

  // NB: no need to update msg ids in txs.

  await msgEntity.save();
}

async function _handleContractStoreEvent(event: CosmosEvent): Promise<void> {
  logger.info(`[handleContractStoreEvent] (tx ${event.msg.tx.hash}): indexing event ${messageId(event.msg)}`);
  logger.debug(`[handleContractStoreEvent] (event.event): ${JSON.stringify(event.event, null, 2)}`);
  logger.debug(`[handleContractStoreEvent] (event.log): ${JSON.stringify(event.log, null, 2)}`);
  const timeline = getTimeline(event);

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
    timeline,
    messageId: id,
    transactionId: event.msg.tx.hash,
    blockId: event.msg.block.block.id,
  });
  await storeMsg.save();
}

async function _handleContractInstantiateEvent(event: CosmosEvent): Promise<void> {
  logger.info(`[handleContractInstantiateEvent] (tx ${event.msg.tx.hash}): indexing event ${messageId(event.msg)}`);
  logger.debug(`[handleContractInstantiateEvent] (event.event): ${JSON.stringify(event.event, null, 2)}`);
  logger.debug(`[handleContractInstantiateEvent] (event.log): ${JSON.stringify(event.log, null, 2)}`);
  const timeline = getTimeline(event);

  const msg_decoded = event.msg?.msg?.decodedMsg;
  const sender = msg_decoded?.sender, admin = msg_decoded?.admin, label = msg_decoded?.label;
  const payload = JSON.stringify(msg_decoded?.msg, null), funds = msg_decoded?.funds;
  const code_ids = event.event.attributes.filter((e) => e.key === "code_id");
  const contract_addresses = event.event.attributes.filter((e) => e.key === "_contract_address");

  for (const [i, e] of Object.entries(code_ids)) {
    const codeId = Number(e.value);
    const id = `${messageId(event.msg)}-${i}`;
    const contract_address = Object.entries(contract_addresses)[i][1].value;

    if (!sender || !payload || !codeId || !contract_address) {
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
      timeline,
      messageId: messageId(event.msg),
      transactionId: event.msg.tx.hash,
      blockId: event.msg.block.block.id,
    });
    await instantiateMsg.save();
    await saveContractEvent(instantiateMsg, contract_address, event);
  }
}

async function saveContractEvent(instantiateMsg: InstantiateContractMessage, contract_address: string, event: CosmosEvent) {
  const storeCodeMsg = (await StoreContractMessage.getByCodeId(instantiateMsg.codeId))[0];

  if (!storeCodeMsg || !contract_address || !instantiateMsg) {
    logger.warn(`[saveContractEvent] (tx ${event.tx.hash}): failed to save contract (storeCodeMsg): ${(storeCodeMsg?.id)}, (instantiateMsg): ${(instantiateMsg?.id)})`);
    return;
  }

  const contract = Contract.create({
    id: contract_address,
    interface: getJaccardResult(JSON.parse(instantiateMsg.payload)),
    storeMessageId: storeCodeMsg.id,
    instantiateMessageId: instantiateMsg.id,
    codeId: storeCodeMsg.codeId
  });
  await contract.save();
}
