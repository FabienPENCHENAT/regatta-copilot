// Light/dark switch in the rail. Follows the system until the user picks a theme, then remembers it.

export class ThemeToggle {
  constructor(button, { translator, preferences, onChange }) {
    this.button = button;
    this.translator = translator;
    this.preferences = preferences;
    this.onChange = onChange;
    const saved = preferences.read().theme;
    if (saved) document.documentElement.dataset.theme = saved;
    button.addEventListener("click", () => this.#switch());
  }

  get current() {
    const explicit = document.documentElement.dataset.theme;
    if (explicit === "light" || explicit === "dark") return explicit;
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }

  render() {
    const current = this.current;
    this.button.dataset.current = current;
    const label = this.translator.t(current === "dark" ? "theme.to_light" : "theme.to_dark");
    this.button.setAttribute("aria-label", label);
    this.button.title = label;
  }

  #switch() {
    const next = this.current === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    this.preferences.update({ theme: next });
    this.render();
    this.onChange();
  }
}
