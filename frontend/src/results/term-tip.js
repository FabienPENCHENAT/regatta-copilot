// A small "?" button that explains a jargon term (TWA, TWS...) in a popover. Works on touch screens.

let nextId = 0;

export function createTermTip(translator, tipKey) {
  const id = `tip-${++nextId}`;
  const wrapper = document.createElement("span");
  wrapper.className = "term-tip";

  const button = document.createElement("button");
  button.type = "button";
  button.className = "term-tip-button";
  button.textContent = "?";
  button.setAttribute("aria-label", translator.t("label.what_is_this"));
  button.setAttribute("popovertarget", id);

  const bubble = document.createElement("span");
  bubble.id = id;
  bubble.popover = "auto";
  bubble.className = "term-tip-bubble";
  bubble.textContent = translator.t(tipKey);

  wrapper.append(button, bubble);
  return wrapper;
}

// Label text followed by its tip, e.g. "TWA ?".
export function labelWithTip(translator, labelKey, tipKey) {
  const label = document.createElement("span");
  label.className = "label-with-tip";
  label.append(translator.t(labelKey), createTermTip(translator, tipKey));
  return label;
}
