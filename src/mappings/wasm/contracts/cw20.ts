import {Interface} from "../../../types";
import {BaseStructure} from "./base";

export class CW20Structure extends BaseStructure {
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
