// Collapses a floating panel out of the way of the chart (to a strip, a header or a summary line; the CSS
// decides how, from data-collapsed). A toggle button switches it; optionally, a click anywhere on the
// collapsed panel brings it back.

export class PanelCollapser {
  // labelToggle: false when the toggle already shows its own text (e.g. "Edit").
  constructor(panel, { toggle, translator, expandOnPanelClick = false, labelToggle = true }) {
    this.panel = panel;
    this.toggleButton = toggle;
    this.translator = translator;
    this.labelToggle = labelToggle;
    panel.dataset.collapsed ??= "false";
    toggle.addEventListener("click", (event) => {
      event.stopPropagation();
      this.isCollapsed ? this.expand() : this.collapse();
    });
    if (expandOnPanelClick) {
      panel.addEventListener("click", (event) => {
        if (!this.isCollapsed) return;
        event.preventDefault();
        event.stopPropagation();
        this.expand();
      }, true);
    }
    this.render();
  }

  get isCollapsed() {
    return this.panel.dataset.collapsed === "true";
  }

  collapse() {
    this.panel.dataset.collapsed = "true";
    this.render();
  }

  expand() {
    this.panel.dataset.collapsed = "false";
    this.render();
  }

  render() {
    this.toggleButton.setAttribute("aria-expanded", String(!this.isCollapsed));
    if (!this.labelToggle) return;
    const label = this.translator.t(this.isCollapsed ? "panel.expand" : "panel.collapse");
    this.toggleButton.setAttribute("aria-label", label);
    this.toggleButton.title = label;
  }
}
