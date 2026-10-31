// The boat's sail wardrobe, from upwind to downwind sails, with a small silhouette of each.
// The sail to hoist now is highlighted; the others stay visible so the choice makes sense.

import { element } from "../../dom.js";

// Mast on the left (x = 7), bow to the right. Shapes are simplified silhouettes.
const SAILS = [
  { id: "Jib", shape: "M7 3 L7 21 L19 21 Z" },
  { id: "LightJib", shape: "M7 3 L7 21 L19 21 Z", light: true },
  { id: "Staysail", shape: "M7 9 L7 21 L15 21 Z" },
  { id: "Code0", shape: "M7 3 C14 8 17 14 18 21 L7 21 Z" },
  { id: "LightGnk", shape: "M7 3 C20 6 22 15 17 21 L7 21 Z", light: true },
  { id: "HeavyGnk", shape: "M7 3 C20 6 22 15 17 21 L7 21 Z" },
  { id: "Spi", shape: "M12 3 C22 6 22 17 17 21 L7 21 C2 17 2 6 12 3 Z" },
];

export function createSailWardrobe(translator, selectedSail) {
  const list = element("ul", "sail-wardrobe");
  for (const sail of SAILS) {
    const item = element("li", "sail-chip");
    if (sail.id === selectedSail) item.classList.add("selected");
    if (sail.light) item.classList.add("light");
    item.innerHTML = `<svg viewBox="0 0 24 24" aria-hidden="true"><line class="sail-mast" x1="7" y1="2" x2="7" y2="22"/>
      <path class="sail-shape" d="${sail.shape}"/></svg>`;
    item.append(element("span", "", translator.t(`sail.${sail.id}`)));
    if (sail.id === selectedSail) item.setAttribute("aria-current", "true");
    list.append(item);
  }
  return list;
}
