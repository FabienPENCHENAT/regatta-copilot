// One wind field on a regular grid (leaflet-velocity format: U then V, rows north to south, m/s).
// Answers "what is the wind here?" with bilinear interpolation.

const MS_TO_KN = 1.943844;

export class WindGrid {
  constructor([uRecord, vRecord]) {
    this.header = uRecord.header;
    this.u = uRecord.data;
    this.v = vRecord.data;
  }

  // Returns { speedKn, fromDeg } or null outside the grid.
  windAt(lat, lon) {
    const { la1, lo1, dx, dy, nx, ny } = this.header;
    const row = (la1 - lat) / dy;
    const col = (lon - lo1) / dx;
    if (row < 0 || col < 0 || row > ny - 1 || col > nx - 1) return null;
    const u = this.#bilinear(this.u, row, col, nx, ny);
    const v = this.#bilinear(this.v, row, col, nx, ny);
    return {
      speedKn: Math.hypot(u, v) * MS_TO_KN,
      fromDeg: (Math.atan2(-u, -v) * 180 / Math.PI + 360) % 360,
    };
  }

  #bilinear(values, row, col, nx, ny) {
    const r0 = Math.min(Math.floor(row), ny - 2);
    const c0 = Math.min(Math.floor(col), nx - 2);
    const fr = row - r0;
    const fc = col - c0;
    const at = (r, c) => values[r * nx + c];
    return at(r0, c0) * (1 - fr) * (1 - fc) + at(r0 + 1, c0) * fr * (1 - fc)
      + at(r0, c0 + 1) * (1 - fr) * fc + at(r0 + 1, c0 + 1) * fr * fc;
  }
}
