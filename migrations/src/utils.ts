
export type FieldValues = Record<string, Record<string, any>>;
export interface Row {
  row: FieldValues
}

export class SelectResult {
  private i = -1;
  constructor(private readonly rows: Row[]) {}

  *[Symbol.iterator]() {
    this.i++;
    // Row looks like {"row": {"f1": <field 1 value>, ...}}
    yield Object.entries(this.rows[this.i].row).map(e => e[1]);
  }
}