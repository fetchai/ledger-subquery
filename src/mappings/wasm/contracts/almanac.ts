import {BaseStructure} from "./base";
import {Interface} from "../../../types";

export class MicroAgentAlmanacStructure extends BaseStructure {
  private stake_denom = "";
  private expiry_height = 0;
  private register_stake_amount = "0";
  private admin = "";

  static listProperties() {
    return Object.getOwnPropertyNames(new MicroAgentAlmanacStructure());
  }

  static getPropertyType(prop: string) {
    return typeof (new MicroAgentAlmanacStructure()[prop]);
  }

  static getInterface() {
    return Interface.MicroAgentAlmanac;
  }
}
