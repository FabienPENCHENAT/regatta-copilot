// Background of the map: OpenStreetMap tiles in the app, or a light coastline drawing when tiles
// cannot load (published mock-up, offline). Leaflet is loaded globally as `L`.

const OSM_TILES = "https://tile.openstreetmap.org/{z}/{x}/{y}.png";
const OSM_ATTRIBUTION = '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>';
const LAND_PANE = "land"; // below Leaflet's overlay pane (z-index 400), so routes stay on top

export async function addBasemap(map, { kind, landUrl, landStyle }) {
  if (kind === "osm") {
    L.tileLayer(OSM_TILES, { maxZoom: 12, attribution: OSM_ATTRIBUTION }).addTo(map);
    return;
  }
  map.createPane(LAND_PANE).style.zIndex = "350";
  const response = await fetch(landUrl);
  const land = await response.json();
  L.geoJSON(land, { pane: LAND_PANE, style: landStyle, interactive: false, attribution: "Natural Earth" }).addTo(map);
}
