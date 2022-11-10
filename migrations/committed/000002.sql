--! Previous: sha1:07039c1f7e5327105f926f5d9288c9e3f97b876f
--! Hash: sha1:415d74da72c751f950e11c4af2b2aa289c84eab9

DROP FUNCTION IF EXISTS plv8ify_migrationAddInterfaceSupport();
CREATE OR REPLACE FUNCTION plv8ify_migrationAddInterfaceSupport() RETURNS JSONB AS $plv8ify$
var plv8ify = (() => {
  var __defProp = Object.defineProperty;
  var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
  var __getOwnPropNames = Object.getOwnPropertyNames;
  var __hasOwnProp = Object.prototype.hasOwnProperty;
  var __export = (target, all) => {
    for (var name in all)
      __defProp(target, name, { get: all[name], enumerable: true });
  };
  var __copyProps = (to, from, except, desc) => {
    if (from && typeof from === "object" || typeof from === "function") {
      for (let key of __getOwnPropNames(from))
        if (!__hasOwnProp.call(to, key) && key !== except)
          __defProp(to, key, { get: () => from[key], enumerable: !(desc = __getOwnPropDesc(from, key)) || desc.enumerable });
    }
    return to;
  };
  var __toCommonJS = (mod) => __copyProps(__defProp({}, "__esModule", { value: true }), mod);

  // migrations/current.ts
  var current_exports = {};
  __export(current_exports, {
    AccessType: () => AccessType,
    CW20Structure: () => CW20Structure,
    Interface: () => Interface,
    LegacyBridgeSwapStructure: () => LegacyBridgeSwapStructure,
    Structure: () => Structure,
    migrationAddInterfaceSupport: () => migrationAddInterfaceSupport
  });

  // migrations/src/utils.ts
  function getSelectResults(rows) {
    if (rows.length < 1) {
      return null;
    }
    return rows.map((row) => Object.entries(row).map((e) => e[1]));
  }

  // migrations/current.ts
  var Structure = class {
    static getInterface() {
      return Interface.Uncertain;
    }
  };
  var CW20Structure = class extends Structure {
    constructor() {
      super(...arguments);
      this.name = "";
      this.symbol = "";
      this.decimals = 0;
      this.initial_balances = [{ amount: BigInt(0), address: "" }];
      this.mint = { minter: "" };
    }
    static listProperties() {
      const a = new CW20Structure();
      return Object.getOwnPropertyNames(a);
    }
    static getPropertyType(prop) {
      const a = new CW20Structure();
      return typeof a[prop];
    }
    static getInterface() {
      return Interface.CW20;
    }
  };
  var LegacyBridgeSwapStructure = class extends Structure {
    constructor() {
      super(...arguments);
      this.cap = BigInt(0);
      this.reverse_aggregated_allowance = BigInt(0);
      this.reverse_aggregated_allowance_approver_cap = BigInt(0);
      this.lower_swap_limit = BigInt(0);
      this.upper_swap_limit = BigInt(0);
      this.swap_fee = BigInt(0);
      this.paused_since_block = BigInt(0);
      this.denom = "";
      this.next_swap_id = "";
    }
    static listProperties() {
      const a = new LegacyBridgeSwapStructure();
      return Object.getOwnPropertyNames(a);
    }
    static getPropertyType(prop) {
      const a = new LegacyBridgeSwapStructure();
      return typeof a[prop];
    }
    static getInterface() {
      return Interface.LegacyBridgeSwap;
    }
  };
  var AccessType = /* @__PURE__ */ ((AccessType2) => {
    AccessType2[AccessType2["Unspecified"] = 0] = "Unspecified";
    AccessType2[AccessType2["AccessTypeNobody"] = 1] = "AccessTypeNobody";
    AccessType2[AccessType2["AccessTypeOnlyAddress"] = 2] = "AccessTypeOnlyAddress";
    AccessType2[AccessType2["AccessTypeEverybody"] = 3] = "AccessTypeEverybody";
    AccessType2[AccessType2["AccessTypeAnyOfAddresses"] = 4] = "AccessTypeAnyOfAddresses";
    return AccessType2;
  })(AccessType || {});
  var Interface = /* @__PURE__ */ ((Interface2) => {
    Interface2[Interface2["Uncertain"] = 0] = "Uncertain";
    Interface2[Interface2["CW20"] = 1] = "CW20";
    Interface2[Interface2["LegacyBridgeSwap"] = 2] = "LegacyBridgeSwap";
    return Interface2;
  })(Interface || {});
  function getJaccard(payload) {
    let prediction = Structure, prediction_coefficient = 0.5;
    let diff = 0, match = 0, coefficient = 0;
    const structs = [CW20Structure, LegacyBridgeSwapStructure];
    structs.forEach((struct) => {
      Object.keys(payload).forEach((payload_key) => {
        if (struct.listProperties().some((prop) => prop === payload_key)) {
          match++;
          if (payload[payload_key] && typeof payload[payload_key] === struct.getPropertyType(payload_key)) {
            match++;
          }
        } else {
          diff++;
        }
      });
      const union = struct.listProperties().length + diff;
      coefficient = match / union;
      if (coefficient > prediction_coefficient) {
        prediction_coefficient = coefficient;
        prediction = struct;
      }
      coefficient = match = diff = 0;
    });
    return prediction.getInterface();
  }
  function migrationAddInterfaceSupport() {
    const storeMsgSelect = "SELECT (m.id, m.type_url, json, m.transaction_id, m.block_id) FROM messages m WHERE type_url = '/cosmwasm.wasm.v1.MsgStoreCode'";
    const instantiateMsgSelect = "SELECT (m.id, m.type_url, json, m.transaction_id, m.block_id) FROM messages m WHERE type_url = '/cosmwasm.wasm.v1.MsgInstantiateContract'";
    const storeCodeMsgResults = plv8.execute(storeMsgSelect);
    const instantiateMsgResults = plv8.execute(instantiateMsgSelect);
    for (const { id, json, transaction_id, block_id } of storeCodeMsgResults) {
      const jsonMsg = JSON.parse(json);
      const [attributes, tx_hash] = getSelectResults(plv8.execute("select e.attributes, t.hash from messages m join transactions t on m.transaction_id = t.id join events e on t.id = e.transaction_id where m.id = $1;", id));
      const attribute = attributes[0].find((a) => a.key === "code_id");
      const code_id = attribute.value;
      if (!attribute || !code_id) {
        throw new Error("store code msg missing code ID from event");
      }
      const msg_id = `${tx_hash}-${id}`;
      plv8.execute(
        "INSERT INTO store_contract_messages (id, sender, permission, code_id, message_id, transaction_id, block_id) ($1, $2, $3, $4, $5, $6, $7)",
        [msg_id, jsonMsg.sender, jsonMsg.permission, code_id, id, transaction_id, block_id]
      );
    }
    for (const { id, json, transaction_id, block_id } of instantiateMsgResults) {
      const jsonMsg = JSON.parse(json);
      const [attributes, tx_hash] = getSelectResults(plv8.execute("select e.attributes, t.hash from messages m join transactions t on m.transaction_id = t.id join events e on t.id = e.transaction_id where m.id = $1;", id));
      const attribute = attributes[0].find((a) => a.key === "code_id");
      const code_id = attribute.value;
      if (!attribute || !code_id) {
        throw new Error("instantiate msg missing code ID from event");
      }
      const msg_id = `${tx_hash}-${id}`;
      plv8.execute(
        "INSERT INTO instantiate_contract_messages (id, sender, admin, code_id, label, payload, funds, message_id, transaction_id, block_id) ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)",
        [msg_id, jsonMsg.sender, jsonMsg.admin, code_id, jsonMsg.label, jsonMsg.msg, jsonMsg.funds, id, transaction_id, block_id]
      );
    }
    const instantiate_msgs = plv8.execute("select * from instantiate_contract_messages;");
    for (const { id, payload, transaction_id } of instantiate_msgs) {
      const [store_code_id, attributes] = getSelectResults(plv8.execute("select s.id, e.attributes from instantiate_contract_messages i join store_contract_messages s on i.code_id = s.code_id join messages m on i.message_id = m.id join transactions t on t.id = m.transaction_id join events e on t.id = e.transaction_id where i.id = $1;", [transaction_id]));
      const payload_stripped = JSON.stringify(payload, null);
      const attribute = attributes[0].find((a) => a.key === "_contract_address");
      const contract_address = attribute.value;
      if (!attribute || !contract_address) {
        throw new Error("instantiate msg missing contract address from event");
      }
      plv8.execute("insert into contracts (id, interfaces, store_contract_message_id, instantiate_message_id) ($1, {$2}, $3, $4)", [contract_address, getJaccard(JSON.parse(payload_stripped)), id, store_code_id]);
    }
  }
  return __toCommonJS(current_exports);
})();

return plv8ify.migrationAddInterfaceSupport()

$plv8ify$ LANGUAGE plv8 IMMUTABLE STRICT;
