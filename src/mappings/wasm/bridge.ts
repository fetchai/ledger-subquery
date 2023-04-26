import {CosmosEvent, CosmosMessage} from "@subql/types-cosmos";
import {LegacyBridgeSwapMsg} from "../types";
import {attemptHandling, messageId, primitivesFromEvent, trackUnprocessed} from "../utils";
import {LegacyBridgeSwap} from "../../types";

export async function handleLegacyBridgeSwap(event: CosmosEvent): Promise<void> {
  await attemptHandling(event, _handleLegacyBridgeSwap, _handleLegacyBridgeSwapError);
}

async function _handleLegacyBridgeSwap(event: CosmosEvent): Promise<void> {
  const msg: CosmosMessage<LegacyBridgeSwapMsg> = event.msg;
  const id = messageId(msg);
  logger.info(`[handleLegacyBridgeSwap] (tx ${msg.tx.hash}): indexing LegacyBridgeSwap ${id}`);
  logger.debug(`[handleLegacyBridgeSwap] (event.msg.msg): ${JSON.stringify(msg.msg, null, 2)}`);
  const timeline = BigInt((event.block.block.header.height * 1000000) + (event.msg.idx * 10000) + (event.tx.idx * 1000));

  const contractId = msg?.msg?.decodedMsg?.contract;
  const swapMsg = msg?.msg?.decodedMsg?.msg;
  const destination = swapMsg?.swap?.destination;

  const funds = msg?.msg?.decodedMsg?.funds || [];
  const amount = funds[0]?.amount;
  const denom = funds[0]?.denom;

  // gracefully skip indexing "swap" messages that doesn't fullfill the bridge contract
  // otherwise, the node will just crashloop trying to save the message to the db with required null fields.
  if (!destination || !amount || !denom || !contractId) {
    logger.warn(`[handleLegacyBridgeSwap] (tx ${msg.tx.hash}): cannot index message (event.msg.msg): ${JSON.stringify(msg.msg, null, 2)}`);
    return;
  }

  const legacySwap = LegacyBridgeSwap.create({
    id,
    destination,
    contractId,
    amount: BigInt(amount),
    denom,
    executeContractMessageId: id,
    timeline,
    messageId: id,
    transactionId: msg.tx.hash,
    blockId: msg.block.block.id,
  });

  await legacySwap.save();
}

async function _handleLegacyBridgeSwapError(err: Error, event: CosmosEvent): Promise<void> {
  await trackUnprocessed(err, primitivesFromEvent(event));
}
