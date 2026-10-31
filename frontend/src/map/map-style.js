// Shared map styling: theme colours (read from the CSS tokens) and the pane stack.
// Panes are drawn bottom to top; wind sits under the land so it only shows at sea.

export const PANES = [
  { name: "depths", zIndex: 210 },
  { name: "wind", zIndex: 220 },
  { name: "land", zIndex: 230 },
  { name: "graticule", zIndex: 240 },
  { name: "course", zIndex: 300 },
  { name: "seaLabels", zIndex: 450 },
];

export function createPanes(map) {
  for (const { name, zIndex } of PANES) {
    const pane = map.createPane(name);
    pane.style.zIndex = String(zIndex);
    if (name !== "course") pane.style.pointerEvents = "none";
  }
}

export function color(token) {
  return getComputedStyle(document.documentElement).getPropertyValue(token).trim();
}

export const WIND_COLOR_TOKENS = ["--wind-1", "--wind-2", "--wind-3", "--wind-4", "--wind-5", "--wind-6", "--wind-7"];
export const WIND_MAX_MS = 18; // ≈ 35 kn: top of the colour scale (7 colours ≈ 5 kn each)
