// Classic meteorological wind barbs drawn on a canvas: the shaft points to where the wind comes from;
// half feather = 5 kn, full feather = 10 kn, pennant = 50 kn.

const SPACING_PX = 52;
const SHAFT_PX = 24;
const FEATHER_PX = 10;

export class WindBarbsLayer {
  #canvas = null;
  #grid = null;
  #redraw = () => this.#draw();

  constructor(map, colors) {
    this.map = map;
    this.color = colors;
  }

  show(windGrid) {
    this.#grid = windGrid;
    if (!this.#canvas) {
      this.#canvas = L.DomUtil.create("canvas", "wind-barbs", this.map.getPane("wind"));
      this.map.on("moveend zoomend resize", this.#redraw);
    }
    this.#draw();
  }

  hide() {
    if (!this.#canvas) return;
    this.map.off("moveend zoomend resize", this.#redraw);
    this.#canvas.remove();
    this.#canvas = null;
  }

  #draw() {
    const size = this.map.getSize();
    const ratio = window.devicePixelRatio || 1;
    Object.assign(this.#canvas, { width: size.x * ratio, height: size.y * ratio });
    Object.assign(this.#canvas.style, { width: `${size.x}px`, height: `${size.y}px` });
    L.DomUtil.setPosition(this.#canvas, this.map.containerPointToLayerPoint([0, 0]));
    const ctx = this.#canvas.getContext("2d");
    ctx.scale(ratio, ratio);
    ctx.strokeStyle = ctx.fillStyle = this.color("--barb");
    ctx.lineWidth = 1.4;
    for (let y = SPACING_PX / 2; y < size.y; y += SPACING_PX) {
      for (let x = SPACING_PX / 2; x < size.x; x += SPACING_PX) {
        const latLng = this.map.containerPointToLatLng([x, y]);
        const wind = this.#grid.windAt(latLng.lat, latLng.lng);
        if (wind) drawBarb(ctx, x, y, wind);
      }
    }
  }
}

function drawBarb(ctx, x, y, { speedKn, fromDeg }) {
  let remaining = Math.round(speedKn / 5) * 5;
  ctx.save();
  ctx.translate(x, y);
  ctx.rotate((fromDeg * Math.PI) / 180);
  if (remaining < 5) {
    ctx.beginPath();
    ctx.arc(0, 0, 3, 0, 2 * Math.PI);
    ctx.stroke();
    ctx.restore();
    return;
  }
  ctx.beginPath();
  ctx.moveTo(0, 0);
  ctx.lineTo(0, -SHAFT_PX);
  ctx.stroke();
  let offset = -SHAFT_PX;
  while (remaining >= 50) {
    ctx.beginPath();
    ctx.moveTo(0, offset);
    ctx.lineTo(FEATHER_PX, offset + 3);
    ctx.lineTo(0, offset + 6);
    ctx.fill();
    offset += 8;
    remaining -= 50;
  }
  for (; remaining >= 5; remaining -= remaining >= 10 ? 10 : 5) {
    const length = remaining >= 10 ? FEATHER_PX : FEATHER_PX / 2;
    ctx.beginPath();
    ctx.moveTo(0, offset);
    ctx.lineTo(length, offset - 4 * (length / FEATHER_PX));
    ctx.stroke();
    offset += 4.5;
  }
  ctx.restore();
}
