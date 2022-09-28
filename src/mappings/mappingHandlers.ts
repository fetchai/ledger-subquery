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
import {CosmosBlock, CosmosEvent, CosmosMessage, CosmosTransaction,} from "@subql/types-cosmos";
import {
  ExecuteContractMsg,
  DistDelegatorClaimMsg,
  GovProposalVoteMsg,
  LegacyBridgeSwapMsg,
  NativeTransferMsg,
} from "./types";
import {toBech32} from "@cosmjs/encoding";
import {createHash} from "crypto";
import {parseCoins} from "./utils";

// messageId returns the id of the message passed or
// that of the message which generated the event passed.
function messageId(msg: CosmosMessage | CosmosEvent): string {
  return `${msg.tx.hash}-${msg.idx}`;
}

export async function handleBlock(block: CosmosBlock): Promise<void> {
  logger.info(`[handleBlock] (block.header.height): indexing block ${block.block.header.height}`)

  const {id, header: {chainId, height, time}} = block.block;
  const timestamp = new Date(time);
  const blockEntity = Block.create({
    id,
    chainId,
    height: BigInt(height),
    timestamp
  });

  await blockEntity.save()
}

export async function handleTransaction(tx: CosmosTransaction): Promise<void> {
  logger.info(`[handleTransaction] (block ${tx.block.block.header.height}): indexing transaction ${tx.idx + 1} / ${tx.block.txs.length}`)
  logger.debug(`[handleTransaction] (tx.decodedTx): ${JSON.stringify(tx.decodedTx, null, 2)}`)
  logger.debug(`[handleTransaction] (tx.tx.log): ${tx.tx.log}`)

  let status = TxStatus.Error;
  if (tx.tx.log) {
    try {
      JSON.parse(tx.tx.log)
      status = TxStatus.Success;
    } catch {
      // NB: assume tx failed
    }
  }

  const pubKey: Uint8Array | undefined = tx.decodedTx.authInfo.signerInfos[0]?.publicKey?.value;
  let signerAddress;
  if (typeof (pubKey) !== "undefined") {
    // TODO: check key type and handle respectively
    // NB: ripemd160(sha256(pubKey)) only works for secp256k1 keys
    const ripemd160 = createHash("ripemd160");
    const sha256 = createHash("sha256");
    // TODO: understand why!!!
    // NB: pubKey has 2 "extra" bytes at the beginning as compared to the
    // base64-decoded representation/ of the same key when imported to
    // fetchd (`fetchd keys add --recover`) and shown (`fetchd keys show`).
    sha256.update(pubKey.slice(2));
    ripemd160.update(sha256.digest());
    // TODO: move prefix to config value or constant
    signerAddress = toBech32("fetch", ripemd160.digest());
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
    signerAddress,
  });

  await txEntity.save();
}

export async function handleNativeTransfer(msg: CosmosMessage<NativeTransferMsg>): Promise<void> {
  logger.info(`[handleNativeTransfer] (tx ${msg.tx.hash}): indexing message ${msg.idx + 1} / ${msg.tx.decodedTx.body.messages.length}`)
  logger.debug(`[handleNativeTransfer] (msg.msg): ${JSON.stringify(msg.msg, null, 2)}`)
  const {toAddress, fromAddress, amount: amounts} = msg.msg.decodedMsg;
  // workaround: assuming one denomination per transfer message
  const denom = amounts[0].denom;
  const id = messageId(msg);
  const transferEntity = NativeTransfer.create({
    id,
    toAddress,
    fromAddress,
    amounts,
    denom,
    messageId: id,
    transactionId: msg.tx.hash,
    blockId: msg.block.block.id
  });

  await transferEntity.save();
}

export async function handleMessage(msg: CosmosMessage): Promise<void> {
  logger.info(`[handleMessage] (tx ${msg.tx.hash}): indexing message ${msg.idx + 1} / ${msg.tx.decodedTx.body.messages.length}`)
  logger.debug(`[handleMessage] (msg.msg): ${JSON.stringify(msg.msg, null, 2)}`)
  const msgEntity = Message.create({
    id: messageId(msg),
    typeUrl: msg.msg.typeUrl,
    json: JSON.stringify(msg.msg.decodedMsg),
    transactionId: msg.tx.hash,
    blockId: msg.block.block.id,
  });

  await msgEntity.save();
}

export async function handleEvent(event: CosmosEvent): Promise<void> {
  logger.info(`[handleEvent] (tx ${event.tx.hash}): indexing event ${event.idx + 1} / ${event.tx.tx.events.length}`)
  logger.debug(`[handleEvent] (event.event): ${JSON.stringify(event.event, null, 2)}`)
  logger.debug(`[handleEvent] (event.log): ${JSON.stringify(event.log, null, 2)}`)

  // NB: sanitize attribute values (may contain non-text characters)
  const attributes = event.event.attributes.map((attribute) => {
    const {key, value} = attribute;
    return {key, value: JSON.stringify(value)};
  });

  const eventEntity = Event.create({
    id: `${messageId(event)}-${event.idx}`,
    type: event.event.type,
    attributes,
    log: event.log.log,
    transactionId: event.tx.hash,
    blockId: event.block.block.id,
  });

  await eventEntity.save();
}

export async function handleExecuteContractMessage(msg: CosmosMessage<ExecuteContractMsg>): Promise<void> {
  logger.info(`[handleExecuteContractMessage] (tx ${msg.tx.hash}): indexing ExecuteContractMessage ${messageId(msg)}`)
  logger.debug(`[handleExecuteContractMessage] (msg.msg): ${JSON.stringify(msg.msg, null, 2)}`)
  const id = messageId(msg);
  const {funds, contract, msg: _msg} = msg.msg.decodedMsg;
  const method = Object.keys(_msg)[0];
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

  const msg = event.msg.msg.decodedMsg;
  const contract = msg.contract, fromAddress = msg.sender;
  const toAddress = msg.msg?.transfer?.recipient;
  const amount = msg.msg?.transfer?.amount;

  if (typeof(amount)==="undefined" || typeof(toAddress)==="undefined" || typeof(fromAddress)==="undefined" || typeof(contract)==="undefined") {
    logger.warn(`[handleCw20Transfer] (${event.tx.hash}): (!SKIPPED!) message is malformed (event.msg.msg.decodedMsg): ${JSON.stringify(msg, null, 2)}`)
    return
  }

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

  const msg = event.msg.msg.decodedMsg;
  const contract = msg.contract;
  const amount = msg.msg?.mint?.amount;
  const toAddress = msg.msg?.mint?.recipient;

  if (!toAddress || !amount || !contract) {
    logger.warn(`[handleCw20BalanceMint] (tx ${event.tx.hash}): cannot index event (event.event): ${JSON.stringify(event.event, null, 2)}`)
    return
  }

  await saveCw20BalanceEvent(`${id}-mint`, toAddress, BigInt(amount), contract, event);
}

export async function handleCw20BalanceTransfer(event: CosmosEvent): Promise<void> {
  const id = messageId(event.msg);
  logger.info(`[handleCw20BalanceTransfer] (tx ${event.tx.hash}): indexing Cw20BalanceTransfer ${id}`);

  const msg = event.msg.msg.decodedMsg;
  const contract = msg.contract, fromAddress = msg.sender;
  const toAddress = msg.msg?.transfer?.recipient;
  const amount = msg.msg?.transfer?.amount;

  if (!fromAddress || !toAddress || !amount || !contract) {
    logger.warn(`[handleCw20BalanceTransfer] (tx ${event.tx.hash}): cannot index event (event.event): ${JSON.stringify(event.event, null, 2)}`)
    return
  }

  await saveCw20BalanceEvent(`${id}-credit`, toAddress, BigInt(amount), contract, event);
  await saveCw20BalanceEvent(`${id}-debit`, fromAddress, BigInt(0)-BigInt(amount), contract, event);
}

export async function handleGovProposalVote(msg: CosmosMessage<GovProposalVoteMsg>): Promise<void> {
  logger.info(`[handleGovProposalVote] (tx ${msg.tx.hash}): indexing GovProposalVote ${messageId(msg)}`)
  logger.debug(`[handleGovProposalVote] (msg.msg): ${JSON.stringify(msg.msg, null, 2)}`)

  const id = messageId(msg);
  const {proposalId, voter, option} = msg.msg.decodedMsg;
  const vote = GovProposalVote.create({
    id,
    proposalId: proposalId,
    voterAddress: voter,
    option: Object.values(GovProposalVoteOption)[option],
    messageId: id,
    transactionId: msg.tx.hash,
    blockId: msg.block.block.id,
  });

  await vote.save();
}

export async function handleDistDelegatorClaim(msg: CosmosMessage<DistDelegatorClaimMsg>): Promise<void> {
  logger.info(`[handleDistDelegatorClaim] (tx ${msg.tx.hash}): indexing DistDelegatorClaim ${messageId(msg)}`)
  logger.debug(`[handleDistDelegatorClaim] (msg.msg): ${JSON.stringify(msg.msg, null, 2)}`)

  const id = messageId(msg);
  const {delegatorAddress, validatorAddress} = msg.msg.decodedMsg;
  const claim = DistDelegatorClaim.create({
    id,
    delegatorAddress,
    validatorAddress,
    messageId: id,
    transactionId: msg.tx.hash,
    blockId: msg.block.block.id,
    amount: BigInt(-1),
    denom: "",
  });

  // TODO:
  // claim.amount =
  // claim.denom =

  await claim.save();
}

export async function handleLegacyBridgeSwap(msg: CosmosMessage<LegacyBridgeSwapMsg>): Promise<void> {
  const id = messageId(msg);
  logger.info(`[handleLegacyBridgeSwap] (tx ${msg.tx.hash}): indexing LegacyBridgeSwap ${id}`)
  logger.debug(`[handleLegacyBridgeSwap] (msg.msg): ${JSON.stringify(msg.msg, null, 2)}`)

  const {
    msg: {swap: {destination}},
    funds: [{amount, denom}],
    contract,
  } = msg.msg.decodedMsg;

  // gracefully skip indexing "swap" messages that doesn't fullfill the bridge contract
  // otherwise, the node will just crashloop trying to save the message to the db with required null fields.
  if (!destination || !amount || !denom || !contract) {
    logger.warn(`[handleLegacyBridgeSwap] (tx ${msg.tx.hash}): cannot index message (msg.msg): ${JSON.stringify(msg.msg, null, 2)}`)
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

export async function handleDelegatorWithdrawRewardEvent(event: CosmosEvent): Promise<void> {
  logger.debug(`[handleDelegateWithdrawRewardEvent] (event.event): ${JSON.stringify(event.event, null, 2)}`)
  logger.debug(`[handleDelegateWithdrawRewardEvent] (event.log): ${JSON.stringify(event.log, null, 2)}`)

  const attrs: Record<string, any> = event.event.attributes.reduce((acc, attr) => {
    acc[attr.key] = attr.value;
    return acc;
  }, {});

  if (typeof(attrs.amount) === "undefined" || typeof(attrs.validator) === "undefined") {
    // Skip this call as unprocessable and allow indexer to continue.
    logger.warn(`[handleDelegateWithdrawRewardEvent] (!SKIPPED!) malformed attributes: ${JSON.stringify(attrs)}`);
    return;
  }

  const claims = await DistDelegatorClaim.getByTransactionId(event.tx.hash);

  const {amount: amountStr, validator} = attrs as {amount: string, validator: string};
  const claim = claims.find((claim) => claim.validatorAddress === validator);
  if (typeof(claim) === "undefined") {
    // Skip this call as unprocessable and allow indexer to continue.
    logger.warn(`[handleDelegateWithdrawRewardEvent] (!SKIPPED!) no claim msgs found in tx: ${event.tx.hash}`);
    return;
  }

  const coins = parseCoins(amountStr);
  if (coins.length === 0) {
    // Skip this call as unprocessable and allow indexer to continue.
    logger.warn(`[handleDelegateWithdrawRewardEvent] (!SKIPPED!) error parsing claim amount: ${amountStr}`);
    return;
  }

  const {amount, denom} = coins[0];
  claim.amount = BigInt(amount);
  claim.denom = denom;
  await claim.save();
}

export async function handleNativeBalanceDecrement(event: CosmosEvent): Promise<void> {
  logger.info(`[handleNativeBalanceDecrement] (tx ${event.tx.hash}): indexing event ${event.idx + 1} / ${event.tx.tx.events.length}`)
  logger.debug(`[handleNativeBalanceDecrement] (event.event): ${JSON.stringify(event.event, null, 2)}`)
  logger.debug(`[handleNativeBalanceDecrement] (event.log): ${JSON.stringify(event.log, null, 2)}`)

  // sample event.event.attributes:
  // [
  //   {"key":"spender","value":"fetch1jv65s3grqf6v6jl3dp4t6c9t9rk99cd85zdctg"},
  //   {"key":"amount","value":"75462013217046121atestfet"},
  //   {"key":"spender","value":"fetch1wurz7uwmvchhc8x0yztc7220hxs9jxdjdsrqmn"},
  //   {"key":"amount","value":"100atestfet"}
  // ]
  let spendEvents = [];
  for (const [i, e] of Object.entries(event.event.attributes)) {
    if (e.key !== "spender") {
      continue
    }
    const spender = e.value;
    const amountStr = event.event.attributes[parseInt(i)+1].value;

    const coin = parseCoins(amountStr)[0];
    const amount = BigInt(0) - BigInt(coin.amount); // save a negative amount for a "spend" event
    spendEvents.push({spender: spender, amount: amount, denom: coin.denom})
  };
  
  for (const [i, spendEvent] of Object.entries(spendEvents)) {
    await saveNativeBalanceEvent(`${messageId(event)}-spend-${i}`, spendEvent.spender, spendEvent.amount, spendEvent.denom, event);
  }
}

export async function handleNativeBalanceIncrement(event: CosmosEvent): Promise<void> {
  logger.info(`[handleNativeBalanceIncrement] (tx ${event.tx.hash}): indexing event ${event.idx + 1} / ${event.tx.tx.events.length}`)
  logger.debug(`[handleNativeBalanceIncrement] (event.event): ${JSON.stringify(event.event, null, 2)}`)
  logger.debug(`[handleNativeBalanceIncrement] (event.log): ${JSON.stringify(event.log, null, 2)}`)

  // sample event.event.attributes:
  // [
  //   {"key":"receiver","value":"fetch1jv65s3grqf6v6jl3dp4t6c9t9rk99cd85zdctg"},
  //   {"key":"amount","value":"75462013217046121atestfet"},
  //   {"key":"receiver","value":"fetch1wurz7uwmvchhc8x0yztc7220hxs9jxdjdsrqmn"},
  //   {"key":"amount","value":"100atestfet"}
  // ]
  let receiveEvents = [];
  for (const [i, e] of Object.entries(event.event.attributes)) {
    if (e.key !== "receiver") {
      continue
    }
    const receiver = e.value;
    const amountStr = event.event.attributes[parseInt(i)+1].value;

    const coin = parseCoins(amountStr)[0];
    const amount = BigInt(coin.amount);
    receiveEvents.push({receiver: receiver, amount: amount, denom: coin.denom})
  };
  
  for (const [i, receiveEvent] of Object.entries(receiveEvents)) {
    await saveNativeBalanceEvent(`${messageId(event)}-receive-${i}`, receiveEvent.receiver, receiveEvent.amount, receiveEvent.denom, event);
  }
}

async function checkBalancesAccount(address: string) {
  let accountEntity = await Account.get(address);
  if (typeof(accountEntity) === "undefined") {
    accountEntity = Account.create({id: address});
    await accountEntity.save();
  }
}

async function saveNativeBalanceEvent(id: string, address: string, amount: BigInt, denom: string, event: CosmosEvent) {
  await checkBalancesAccount(address);
  const nativeBalanceChangeEntity = NativeBalanceChange.create({
    id,
    balanceOffset: amount.valueOf(),
    denom,
    accountId: address,
    eventId: `${messageId(event)}-${event.idx}`,
    blockId: event.block.block.id,
    transactionId: event.tx.hash,
  });
  await nativeBalanceChangeEntity.save()
}

export async function handleIBCTransfer(event: CosmosEvent): Promise<void> {
  const msg = event.msg;
  logger.info(`[handleIBCTransfer] (tx ${msg.tx.hash}): indexing message ${msg.idx + 1} / ${msg.tx.decodedTx.body.messages.length}`)
  logger.debug(`[handleIBCTransfer] (msg.msg): ${JSON.stringify(msg.msg, null, 2)}`)
  
  const decodedMsg = msg.msg.decodedMsg;
  const sourcePort = decodedMsg.sourcePort;
  const sourceChannel = decodedMsg.sourceChannel;
  const tokenAmount = decodedMsg.token?.amount;
  const tokenDenom = decodedMsg.token?.denom;
  const sender = decodedMsg.sender;
  const receiver = decodedMsg.receiver;
  
  if (!sourcePort || !sourceChannel || !tokenAmount || !tokenDenom || !sender || !receiver) {
    logger.warn(`[handleIBCTransfer] (tx ${msg.tx.hash}): cannot index message (msg.msg): ${JSON.stringify(msg.msg, null, 2)}`)
    return 
  }
  
  const id = messageId(msg);
  const transferEntity = IbcTransfer.create({
    id,
    toAddress: receiver,
    fromAddress: sender,
    amount: {amount: tokenAmount, denom: tokenDenom},
    denom: tokenDenom,
    sourcePort,
    sourceChannel,
    messageId: id,
    transactionId: msg.tx.hash,
    blockId: msg.block.block.id
  });

  await transferEntity.save();
}

async function saveCw20BalanceEvent(id: string, address: string, amount: BigInt, contract: string, event: CosmosEvent) {
  await checkBalancesAccount(address);
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

