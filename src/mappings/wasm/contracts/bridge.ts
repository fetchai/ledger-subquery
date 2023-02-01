import {Interface} from "../../../types";
import {BaseStructure} from "./base";

export class LegacyBridgeSwapStructure extends BaseStructure {
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
