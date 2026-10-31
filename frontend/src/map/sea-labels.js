// Sea and ocean names in italic, the way hydrographic names are lettered on charts.

const SEAS = [
  { key: "sea.channel", latLng: [50.05, -2.2], minZoom: 5 },
  { key: "sea.celtic", latLng: [50.6, -8.0], minZoom: 5 },
  { key: "sea.biscay", latLng: [45.6, -4.6], minZoom: 4 },
  { key: "sea.atlantic", latLng: [41.5, -26.0], minZoom: 3 },
  { key: "sea.sargasso", latLng: [28.0, -58.0], minZoom: 3 },
  { key: "sea.caribbean", latLng: [14.8, -72.0], minZoom: 3 },
];

export class SeaLabels {
  #layer;

  constructor(map, translator) {
    this.map = map;
    this.translator = translator;
    this.#layer = L.layerGroup().addTo(map);
    map.on("zoomend", () => this.render());
  }

  render() {
    this.#layer.clearLayers();
    const zoom = this.map.getZoom();
    for (const sea of SEAS.filter((s) => zoom >= s.minZoom)) {
      const icon = L.divIcon({ className: "sea-label", html: `<span>${this.translator.t(sea.key)}</span>`, iconSize: null });
      L.marker(sea.latLng, { icon, pane: "seaLabels", interactive: false, keyboard: false }).addTo(this.#layer);
    }
  }
}
