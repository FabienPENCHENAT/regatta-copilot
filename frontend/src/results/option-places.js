// Where an option sits in the list and which colour it wears, from its name alone, so an option keeps both from
// one computation to the next: listed as on the chart (north at the top, west before east, direct in between),
// one colour per side of the line to the mark.

const LIST_ORDER = [
  "north_far", "north_wide", "north", "west_far", "west_wide", "west",
  "direct", "consensus", "gfs",
  "east", "east_wide", "east_far", "south", "south_wide", "south_far",
];

// Colour slot (--route-N): direct in blue, then one colour per side and per rank on that side. "_far" only
// exists with three options on one side, hence no direct option: it takes the direct colour.
const COLOUR_SLOT = {
  direct: 1, consensus: 1, gfs: 1,
  north: 2, west: 2, south: 3, east: 3,
  north_wide: 4, west_wide: 4, south_wide: 5, east_wide: 5,
  north_far: 1, west_far: 1, south_far: 1, east_far: 1,
};

export function inListOrder(options) {
  const rank = (option) => LIST_ORDER.indexOf(option.id) >>> 0; // unknown names last
  return [...options].sort((a, b) => rank(a) - rank(b));
}

export function colourSlot(optionId) {
  return COLOUR_SLOT[optionId] ?? 1;
}
