// Measures how much of the screen the floating panels cover, so the map can frame routes in the free area.

const WIDE_LAYOUT_PX = 1000;

export function measureMapInsets() {
  if (window.innerWidth < WIDE_LAYOUT_PX) {
    // Phones: panels scroll below the first half of the screen.
    return { top: 64, left: 0, right: 0, bottom: Math.round(window.innerHeight * 0.45) };
  }
  const form = visibleRect("route-form");
  const dock = visibleRect("dock");
  const tools = document.querySelector(".tools")?.getBoundingClientRect();
  return {
    top: 0,
    left: Math.max(form?.right ?? 0, 72),
    right: tools ? window.innerWidth - tools.left : 0,
    bottom: dock ? window.innerHeight - dock.top : 0,
  };
}

function visibleRect(id) {
  const element = document.getElementById(id);
  return element && !element.hidden ? element.getBoundingClientRect() : null;
}
