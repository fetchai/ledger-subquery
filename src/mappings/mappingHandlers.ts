import {
  Block,
  DistDelegatorClaim,
  ExecuteContractMessage,
  ExecuteEvent,
  GovProposalVote,
  LegacyBridgeSwap,
  Message,
  Transaction,
  TxStatus
} from "../types";
import {CosmosBlock, CosmosEvent, CosmosMessage, CosmosTransaction,} from "@subql/types-cosmos";
import {ExecuteContractMsg, DistDelegatorClaimMsg, GovProposalVoteMsg, LegacyBridgeSwapMsg} from "./types";

// messageId returns the id of the message passed or
// that of the message which generated the event passed.
function messageId(msg: CosmosMessage | CosmosEvent): string {
  return `${msg.tx.hash}-${msg.idx}`;
}

export async function handleBlock(block: CosmosBlock): Promise<void> {
  const {id, header: {chainId, height, time: timestamp}} = block.block;
  const blockEntity = Block.create({
    id,
    chainId,
    height: BigInt(height),
    // TODO: convert to unix timestamp and store as Int.
    timestamp,
  });

  await blockEntity.save()
}

export async function handleTransaction(tx: CosmosTransaction): Promise<void> {
  let status = TxStatus.Error;
  if (tx.tx.log) {
    try {
      JSON.parse(tx.tx.log)
      status = TxStatus.Success;
    } catch {
      // NB: assume tx failed
    }
  }

  const txEntity = Transaction.create({
    id: tx.hash,
    blockId: tx.block.block.id,
    gasUsed: BigInt(Math.trunc(tx.tx.gasUsed)),
    gasWanted: BigInt(Math.trunc(tx.tx.gasWanted)),
    memo: tx.decodedTx.body.memo,
    timeoutHeight: BigInt(tx.decodedTx.body.timeoutHeight.toString()),
    fees: JSON.stringify(tx.decodedTx.authInfo.fee.amount),
    log: tx.tx.log,
    status,
  });

  await txEntity.save();
}

export async function handleMessage(msg: CosmosMessage): Promise<void> {
  const msgEntity = Message.create({
    id: messageId(msg),
    json: JSON.stringify(msg.msg.decodedMsg),
    transactionId: msg.tx.hash,
    blockId: msg.block.block.id,
  });

  await msgEntity.save();
}

export async function handleEvent(event: CosmosEvent): Promise<void> {
  const eventEntity = ExecuteEvent.create({
    id: `${messageId(event)}-${event.idx}`,
    json: JSON.stringify(event.event),
    log: event.log.log,
    transactionId: event.tx.hash,
    blockId: event.block.block.id,
  });

  await eventEntity.save();
}

export async function handleExecuteContractMessage(msg: CosmosMessage<ExecuteContractMsg>): Promise<void> {
  const id = messageId(msg);
  const msgEntity = ExecuteContractMessage.create({
    id,
    sender: msg.msg.decodedMsg.sender,
    contract: msg.msg.decodedMsg.contract,
    funds: JSON.stringify(msg.msg.decodedMsg.funds),
    messageId: id,
    transactionId: msg.tx.hash,
    blockId: msg.block.block.id,
  });

  // NB: no need to update msg ids in txs.

  await msgEntity.save();
}

export async function handleGovProposalVote(msg: CosmosMessage<GovProposalVoteMsg>): Promise<void> {
  const id = messageId(msg);
  const {proposalId, voter, option} = msg.msg.decodedMsg;
  const vote = GovProposalVote.create({
    id,
    proposalId: proposalId,
    voterAddress: voter,
    option: option,
    messageId: id,
    transactionId: msg.tx.hash,
    blockId: msg.block.block.id,
  });

  await vote.save();
}

export async function handleDistDelegatorClaim(msg: CosmosMessage<DistDelegatorClaimMsg>): Promise<void> {

  const id = messageId(msg);
  const {delegatorAddress, validatorAddress} = msg.msg.decodedMsg;
  const claim = DistDelegatorClaim.create({
    id,
    delegatorAddress,
    validatorAddress,
    messageId: id,
    transactionId: msg.tx.hash,
    blockId: msg.block.block.id,
  });

  // TODO:
  // claim.amount =
  // claim.denom =

  await claim.save();
}

export async function handleLegacyBridgeSwap(msg: CosmosMessage<LegacyBridgeSwapMsg>): Promise<void> {

  const id = messageId(msg);
  const {
    msg: {swap: {destination}},
    funds: [{amount, denom}]
  } = msg.msg.decodedMsg;
  const legacySwap = LegacyBridgeSwap.create({
    id,
    destination,
    amount: BigInt(amount),
    denom,
    messageId: id,
    transactionId: msg.tx.hash,
    blockId: msg.block.block.id,
  });

  await legacySwap.save();
}
