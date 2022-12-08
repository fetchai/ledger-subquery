import {getSelectResults} from "./src/utils";

export function migrationMicroAgentAlmanacRegistrations() {
  // NB: collect all contract execution events with "register" action.
  const selectRegisterEventIds = `SELECT ev.id
                                  FROM events ev
                                           JOIN event_attributes ea ON ev.id = ea.event_id
                                  WHERE ev.type = "/cosmwasm.wasm.v1.MsgExecuteContract"
                                    AND ea.key = "action"
                                    AND ea.value = "register"`;

  const selectRegisterEventData = `SELECT ev.id ev.transaction_id, ev.block_id, ea.key, ea.value
                                   FROM events ev
                                            JOIN event_attributes ea ON ev.id = ea.event_id
                                   WHERE ev.id in (${selectRegisterEventIds})`;

  // eslint-disable-next-line @typescript-eslint/ban-ts-comment
  // @ts-ignore
  const registerEventData = getSelectResults(plv8.execute(selectRegisterEventData));

  // NB: organize register event data
  const eventIds = {};
  const agents = {};
  const services = {};
  const expiryHeights = {};
  const signatures = {};
  const sequences = {};
  const contracts = {};
  const txIds = {};
  const blockIds = {};
  for (const record of registerEventData) {
    if (record.length < 5) {
      // eslint-disable-next-line @typescript-eslint/ban-ts-comment
      // @ts-ignore
      plv8.elog(WARNING, `unable to migrate registration event; event ID: ${record[0]}`);
      continue;
    }

    const [eventId, txId, blockId, key, value] = record;
    eventIds[eventId] = null;

    if (!txIds[eventId]) {
      txIds[eventId] = txId;
    }

    if (!blockIds[eventId]) {
      blockIds[eventId] = blockId;
    }

    switch (key) {
    case "_contract_address":
      contracts[eventId] = value;
      break;
    case "agent_address":
      agents[eventId] = value;
      break;
    case "record":
      try {
        const service = JSON.parse(value).service;
        if (!service) {
          throw new Error("expected record to contain service key but none found");
        }

        services[eventId] = JSON.stringify(service);
      } catch {
        // eslint-disable-next-line @typescript-eslint/ban-ts-comment
        // @ts-ignore
        plv8.elog(WARNING, `unable to parse expected JSON value: "${value}"`);
        continue;
      }
      break;
    case "signature":
      signatures[eventId] = value;
      break;
    case "sequence":
      sequences[eventId] = value;
      break;
    case "expiry_height":
      expiryHeights[eventId] = value;
      break;
    }
  }

  // NB: bulk insert agents
  const agentIdValues = Object.values(agents).map(id => `('${id}')`).join(", ");
  const insertAgents = `INSERT INTO agents (id) VALUES ${agentIdValues} ON CONFLICT DO NOTHING`;
  // eslint-disable-next-line @typescript-eslint/ban-ts-comment
  // @ts-ignore
  plv8.execute(insertAgents);

  // NB: bulk insert records
  const recordValues = Object.keys(eventIds).map(eventId => {
    return "(" + [
      eventId,
      services[eventId],
      txIds[eventId],
      blockIds[eventId],
    ].map(e => `'${e}'`).join(", ") + ")";
  }).join(", ");
  // eslint-disable-next-line @typescript-eslint/ban-ts-comment
  // @ts-ignore
  plv8.execute(`INSERT INTO records (id, service, transaction_id, block_id)
                VALUES ${recordValues}`);

  // NB: bulk insert registrations
  const registrationValues = Object.keys(eventIds).map(eventId => {
    return "(" + [
      eventId,
      expiryHeights[eventId],
      signatures[eventId],
      sequences[eventId],
      agents[eventId],
      eventId,
      contracts[eventId],
      txIds[eventId],
      blockIds[eventId],
    ].map(e => `'${e}'`).join(", ") + ")";
  }).join(", ");

  const insertRegistrations = `INSERT INTO registrations (id, expiry_height, signature, sequence, agent_id, record_id,
                                                          contract_id, transaction_id, block_id)
                               VALUES ${registrationValues}`;
  // eslint-disable-next-line @typescript-eslint/ban-ts-comment
  // @ts-ignore
  plv8.execute(insertRegistrations);
}
