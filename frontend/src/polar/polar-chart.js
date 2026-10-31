// Polar diagram in SVG: boat speed (radius) by true wind angle (0° up, 180° down), the player's current
// options as a dashed line and the options being tried coloured by best sail. A marker shows the angle read out.

const NS = "http://www.w3.org/2000/svg";
const SIZE = { width: 420, height: 440, cx: 46, cy: 220, radius: 190 };

export class PolarChart {
  constructor(svg, translator) {
    this.svg = svg;
    this.translator = translator;
    svg.setAttribute("viewBox", `0 0 ${SIZE.width} ${SIZE.height}`);
  }

  // twa: angles (deg); current, changed: { speed: [...], sail: [...] }; markerTwa: angle to highlight.
  render({ twa, current, changed, markerTwa }) {
    const maxSpeed = Math.max(...current.speed, ...changed.speed, 1);
    const ringStep = maxSpeed > 16 ? 5 : maxSpeed > 8 ? 2 : 1;
    const scaleMax = Math.ceil(maxSpeed / ringStep) * ringStep;
    const point = (angle, speed) => {
      const r = (speed / scaleMax) * SIZE.radius;
      const rad = (angle * Math.PI) / 180;
      return [SIZE.cx + r * Math.sin(rad), SIZE.cy - r * Math.cos(rad)];
    };
    const nodes = [...this.#grid(scaleMax, ringStep, point)];
    nodes.push(this.#path(twa.map((a, i) => point(a, current.speed[i])), "polar-current"));
    nodes.push(...this.#sailSegments(twa, changed, point));
    const markerIndex = twa.indexOf(markerTwa);
    if (markerIndex >= 0) {
      const [x, y] = point(markerTwa, changed.speed[markerIndex]);
      nodes.push(this.#line(SIZE.cx, SIZE.cy, x, y, "polar-marker-ray"), this.#circle(x, y, 6, "polar-marker"));
    }
    this.svg.replaceChildren(...nodes);
  }

  // Angle (0–180°, whole degrees) under a pointer position, for the read-out.
  angleAt(clientX, clientY) {
    const box = this.svg.getBoundingClientRect();
    const x = ((clientX - box.left) / box.width) * SIZE.width - SIZE.cx;
    const y = SIZE.cy - ((clientY - box.top) / box.height) * SIZE.height;
    const angle = (Math.atan2(Math.max(x, 0), y) * 180) / Math.PI;
    return Math.min(180, Math.max(0, Math.round(angle)));
  }

  *#grid(scaleMax, ringStep, point) {
    for (let speed = ringStep; speed <= scaleMax; speed += ringStep) {
      const r = (speed / scaleMax) * SIZE.radius;
      yield this.#element("path", { d: `M ${SIZE.cx} ${SIZE.cy - r} A ${r} ${r} 0 0 1 ${SIZE.cx} ${SIZE.cy + r}`, class: "polar-ring" });
      const label = this.#element("text", { x: SIZE.cx - 8, y: SIZE.cy - r + 4, class: "polar-ring-label", "text-anchor": "end" });
      label.textContent = `${speed}`;
      yield label;
    }
    for (let angle = 0; angle <= 180; angle += 30) {
      const [x, y] = point(angle, scaleMax);
      yield this.#line(SIZE.cx, SIZE.cy, x, y, "polar-spoke");
      const [lx, ly] = point(angle, scaleMax * 1.08);
      const label = this.#element("text", { x: lx, y: ly + 4, class: "polar-angle-label", "text-anchor": angle === 0 || angle === 180 ? "middle" : "start" });
      label.textContent = `${angle}°`;
      yield label;
    }
    const unit = this.#element("text", { x: SIZE.cx - 8, y: SIZE.cy + 16, class: "polar-ring-label", "text-anchor": "end" });
    unit.textContent = this.translator.t("polar.unit");
    yield unit;
  }

  *#sailSegments(twa, curve, point) {
    let start = 0;
    for (let i = 1; i <= twa.length; i += 1) {
      if (i < twa.length && curve.sail[i] === curve.sail[start]) continue;
      const end = Math.min(i, twa.length - 1);
      const points = twa.slice(start, end + 1).map((a, k) => point(a, curve.speed[start + k]));
      const path = this.#path(points, "polar-changed");
      path.style.stroke = `var(--sail-${curve.sail[start]})`;
      yield path;
      start = i;
    }
  }

  #path(points, className) {
    const d = points.map(([x, y], i) => `${i ? "L" : "M"} ${x.toFixed(1)} ${y.toFixed(1)}`).join(" ");
    return this.#element("path", { d, class: className });
  }

  #line(x1, y1, x2, y2, className) {
    return this.#element("line", { x1, y1, x2, y2, class: className });
  }

  #circle(cx, cy, r, className) {
    return this.#element("circle", { cx, cy, r, class: className });
  }

  #element(tag, attributes) {
    const node = document.createElementNS(NS, tag);
    for (const [name, value] of Object.entries(attributes)) node.setAttribute(name, value);
    return node;
  }
}
