// The boat's sail wardrobe, from upwind to downwind sails, with a small silhouette of each.
// The sail to hoist now is highlighted; sails the player does not own are faded. Every VR boat has these
// same 7 sails (numbered 1 to 7 in the polars); names follow the game's interface.

import { element } from "../../dom.js";

// Mast on the left (x = 7), bow to the right. Shapes are simplified silhouettes.
const SAILS = [
  { id: "Jib", shape: "M7 3 L7 21 L19 21 Z" },
  { id: "LightJib", shape: "M7 3 L7 21 L19 21 Z", light: true },
  { id: "Staysail", shape: "M7 9 L7 21 L15 21 Z" },
  { id: "Code0", shape: "M7 3 C14 8 17 14 18 21 L7 21 Z" },
  { id: "LightGnk", shape: "M7 3 C20 6 22 15 17 21 L7 21 Z", light: true },
  { id: "HeavyGnk", shape: "M7 3 C20 6 22 15 17 21 L7 21 Z" },
  { id: "Spi", shape: "M7 2.5 C20 2.5 24.5 13 19 21 L8 21 C9 16 8.5 8 7 2.5 Z" }, // hoisted at the masthead, full, all forward of the mast
];

export function createSailWardrobe(translator, selectedSail, ownedSails) {
  const list = element("ul", "sail-wardrobe");
  for (const sail of SAILS) {
    const item = element("li", "sail-chip");
    if (sail.id === selectedSail) item.classList.add("selected");
    if (sail.light) item.classList.add("light");
    if (!ownedSails.includes(sail.id)) {
      item.classList.add("not-owned");
      item.title = translator.t("sail.not_owned");
    }
    item.innerHTML = `<svg viewBox="0 0 24 24" aria-hidden="true"><line class="sail-mast" x1="7" y1="2" x2="7" y2="22"/>
      <path class="sail-shape" d="${sail.shape}"/></svg>`;
    item.append(element("span", "sail-name", translator.t(`sail.${sail.id}`)));
    if (sail.id === selectedSail) item.setAttribute("aria-current", "true");
    list.append(item);
  }
  return list;
}
