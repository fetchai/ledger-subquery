import {
  Account,
  Block,
  DistDelegatorClaim,
  Event,
  ExecuteContractMessage,
  GovProposalVote,
  GovProposalVoteOption,
  LegacyBridgeSwap,
  Message,
  NativeTransfer,
  IbcTransfer,
  NativeBalanceChange,
  Cw20Transfer,
  Cw20BalanceChange,
  Transaction,
  TxStatus,
} from "../types";
import {
  CosmosBlock,
  CosmosEvent,
  CosmosMessage,
  CosmosTransaction,
} from "@subql/types-cosmos";
import {toBech32} from "@cosmjs/encoding";
import {createHash} from "crypto";
import {parseCoins} from "./utils";
import {
  DistDelegatorClaimMsg,
  ExecuteContractMsg,
  GovProposalVoteMsg,
  LegacyBridgeSwapMsg,
  NativeTransferMsg
} from "./types";


export async function handleExecuteContractEvent(event: CosmosEvent): Promise<void> {
  const msg: CosmosMessage<ExecuteContractMsg> = event.msg
  logger.info(`[handleExecuteContractMessage] (tx ${msg.tx.hash}): indexing ExecuteContractMessage ${messageId(msg)}`)
  logger.debug(`[handleExecuteContractMessage] (event.msg.msg): ${JSON.stringify(msg.msg, null, 2)}`)

  const id = messageId(msg);
  const funds = msg?.msg?.decodedMsg?.funds, contract = msg?.msg?.decodedMsg?.contract
  const method = Object.keys(msg?.msg?.decodedMsg?.msg)[0];

  if (!funds || !contract || !method) {
    logger.warn(`[handleExecuteContractEvent] (tx ${event.tx.hash}): cannot index event (event.event): ${JSON.stringify(event.event, null, 2)}`)
    return
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

export async function handleCw20Transfer(event: CosmosEvent): Promise<void> { // TODO: consolidate Cw20 functions and helpers
  const id = messageId(event.msg);
  logger.info(`[handleCw20Transfer] (tx ${event.tx.hash}): indexing Cw20Transfer ${id}`);
  logger.debug(`[handleCw20Transfer] (event.msg.msg): ${JSON.stringify(event.msg.msg, null, 2)}`)

  const msg = event.msg?.msg?.decodedMsg;
  const contract = msg?.contract, fromAddress = msg?.sender;
  const toAddress = msg?.msg?.transfer?.recipient;
  const amount = msg?.msg?.transfer?.amount;


  if (!fromAddress || !amount || !toAddress || !contract) {
    logger.warn(`[handleCw20Transfer] (tx ${event.tx.hash}): cannot index event (event.event): ${JSON.stringify(event.event, null, 2)}`)
    return
  }

  const Cw20transfer = Cw20Transfer.create({
    id,
    toAddress,
    fromAddress,
    contract,
    amount,
    messageId: id,
    transactionId: event.tx.hash,
    blockId: event.block.block.id
  });

  await Cw20transfer.save();
}

export async function handleCw20BalanceBurn(event: CosmosEvent): Promise<void> {
  const id = messageId(event.msg);
  logger.info(`[handleCw20BalanceBurn] (tx ${event.tx.hash}): indexing Cw20BalanceBurn ${id}`);
  logger.debug(`[handleCw20BalanceBurn] (event.msg.msg): ${JSON.stringify(event.msg.msg, null, 2)}`)

  const msg = event.msg.msg.decodedMsg;
  const fromAddress = msg.sender, contract = msg.contract;
  const amount = msg.msg?.burn?.amount;

  if (!fromAddress || !amount || !contract) {
    logger.warn(`[handleCw20BalanceBurn] (tx ${event.tx.hash}): cannot index event (event.event): ${JSON.stringify(event.event, null, 2)}`)
    return
  }

  await saveCw20BalanceEvent(`${id}-burn`, fromAddress, BigInt(0)-BigInt(amount), contract, event);
}

export async function handleCw20BalanceMint(event: CosmosEvent): Promise<void> {
  const id = messageId(event.msg);
  logger.info(`[handleCw20BalanceMint] (tx ${event.tx.hash}): indexing Cw20BalanceMint ${id}`);
  logger.debug(`[handleCw20BalanceMint] (event.msg.msg): ${JSON.stringify(event.msg.msg, null, 2)}`)

  const msg = event.msg?.msg?.decodedMsg;
  const contract = msg?.contract;
  const amount = msg?.msg?.mint?.amount;
  const toAddress = msg?.msg?.mint?.recipient;

  if (!toAddress || !amount || !contract) {
    logger.warn(`[handleCw20BalanceMint] (tx ${event.tx.hash}): cannot index event (event.event): ${JSON.stringify(event.event, null, 2)}`)
    return
  }

  await saveCw20BalanceEvent(`${id}-mint`, toAddress, BigInt(amount), contract, event);
}

export async function handleCw20BalanceTransfer(event: CosmosEvent): Promise<void> {
  const id = messageId(event.msg);
  logger.info(`[handleCw20BalanceTransfer] (tx ${event.tx.hash}): indexing Cw20BalanceTransfer ${id}`);
  logger.debug(`[handleCw20BalanceTransfer] (event.msg.msg): ${JSON.stringify(event.msg.msg, null, 2)}`)

  const msg = event.msg.msg.decodedMsg;
  const contract = msg?.contract, fromAddress = msg?.sender;
  const toAddress = msg?.msg?.transfer?.recipient;
  const amount = msg?.msg?.transfer?.amount;

  if (!fromAddress || !toAddress || !amount || !contract) {
    logger.warn(`[handleCw20BalanceTransfer] (tx ${event.tx.hash}): cannot index event (event.event): ${JSON.stringify(event.event, null, 2)}`)
    return
  }

  await saveCw20BalanceEvent(`${id}-credit`, toAddress, BigInt(amount), contract, event);
  await saveCw20BalanceEvent(`${id}-debit`, fromAddress, BigInt(0)-BigInt(amount), contract, event);
}

export async function handleLegacyBridgeSwap(event: CosmosEvent): Promise<void> {
  const msg: CosmosMessage<LegacyBridgeSwapMsg> = event.msg
  const id = messageId(msg);
  logger.info(`[handleLegacyBridgeSwap] (tx ${msg.tx.hash}): indexing LegacyBridgeSwap ${id}`)
  logger.debug(`[handleLegacyBridgeSwap] (event.msg.msg): ${JSON.stringify(msg.msg, null, 2)}`)

  const contract = msg?.msg?.decodedMsg?.contract;
  const swapMsg = msg?.msg?.decodedMsg?.msg;
  const destination = swapMsg?.swap?.destination;

  const funds = msg?.msg?.decodedMsg?.funds || [];
  const amount = funds[0]?.amount;
  const denom = funds[0]?.denom;

  // gracefully skip indexing "swap" messages that doesn't fullfill the bridge contract
  // otherwise, the node will just crashloop trying to save the message to the db with required null fields.
  if (!destination || !amount || !denom || !contract) {
    logger.warn(`[handleLegacyBridgeSwap] (tx ${msg.tx.hash}): cannot index message (event.msg.msg): ${JSON.stringify(msg.msg, null, 2)}`)
    return
  }

  const legacySwap = LegacyBridgeSwap.create({
    id,
    destination,
    contract,
    amount: BigInt(amount),
    denom,
    executeContractMessageId: id,
    messageId: id,
    transactionId: msg.tx.hash,
    blockId: msg.block.block.id,
  });

  await legacySwap.save();
}
async function saveCw20BalanceEvent(id: string, address: string, amount: BigInt, contract: string, event: CosmosEvent) {
  await checkBalancesAccount(address, event.block.block.header.chainId);
  const msgId = messageId(event.msg);
  const Cw20BalanceChangeEntity = Cw20BalanceChange.create({
    id,
    balanceOffset: amount.valueOf(),
    contract,
    accountId: address,
    eventId: `${messageId(event)}-${event.idx}`,
    executeContractMessageId: msgId,
    messageId: msgId,
    blockId: event.block.block.id,
    transactionId: event.tx.hash,
  });
  await Cw20BalanceChangeEntity.save()
}

export * from "./primitives";
export * from "./bank";
export * from "./dist";
export * from "./gov";
export * from "./ibc";
