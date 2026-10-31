// Latitude/longitude grid with degree labels along the left and bottom edges, as on a chart.
// The spacing is the smallest "round" step that keeps labels at least MIN_GAP_PX apart.

const STEPS_DEG = [0.5, 1, 2, 5, 10, 20];
const MIN_GAP_PX = 56;

export class GraticuleLayer {
  #lines;
  #labels;

  constructor(map, colors) {
    this.map = map;
    this.color = colors;
    this.#lines = L.layerGroup().addTo(map);
    this.#labels = L.layerGroup().addTo(map);
    map.on("moveend zoomend", () => this.redraw());
  }

  redraw() {
    this.#lines.clearLayers();
    this.#labels.clearLayers();
    const bounds = this.map.getBounds();
    const step = this.#stepDegrees();
    const style = { pane: "graticule", color: this.color("--graticule"), weight: 0.8, interactive: false };
    const inset = this.#insetDegrees();

    for (let lat = Math.ceil(bounds.getSouth() / step) * step; lat <= bounds.getNorth(); lat += step) {
      L.polyline([[lat, bounds.getWest()], [lat, bounds.getEast()]], style).addTo(this.#lines);
      this.#label([lat, bounds.getWest() + inset.lon], formatLat(lat), "graticule-label lat");
    }
    for (let lon = Math.ceil(bounds.getWest() / step) * step; lon <= bounds.getEast(); lon += step) {
      L.polyline([[bounds.getSouth(), lon], [bounds.getNorth(), lon]], style).addTo(this.#lines);
      this.#label([bounds.getSouth() + inset.lat, lon], formatLon(lon), "graticule-label lon");
    }
  }

  #label(latLng, text, className) {
    const icon = L.divIcon({ className, html: `<span>${text}</span>`, iconSize: null });
    L.marker(latLng, { icon, pane: "graticule", interactive: false, keyboard: false }).addTo(this.#labels);
  }

  #stepDegrees() {
    const width = this.map.getSize().x;
    const span = this.map.getBounds().getEast() - this.map.getBounds().getWest();
    const pxPerDegree = width / span;
    return STEPS_DEG.find((step) => step * pxPerDegree >= MIN_GAP_PX) ?? STEPS_DEG.at(-1);
  }

  // Keeps labels a few pixels inside the map edge whatever the zoom.
  #insetDegrees() {
    const origin = this.map.containerPointToLatLng([0, this.map.getSize().y]);
    const shifted = this.map.containerPointToLatLng([4, this.map.getSize().y - 4]);
    return { lon: shifted.lng - origin.lng, lat: shifted.lat - origin.lat };
  }
}

function formatLat(lat) {
  return `${formatDegrees(Math.abs(lat))}${lat >= 0 ? "N" : "S"}`;
}

function formatLon(lon) {
  return `${formatDegrees(Math.abs(lon))}${lon >= 0 ? "E" : "W"}`;
}

function formatDegrees(value) {
  const degrees = Math.floor(value + 1e-9);
  const minutes = Math.round((value - degrees) * 60);
  return minutes ? `${degrees}°${String(minutes).padStart(2, "0")}'` : `${degrees}°`;
}
