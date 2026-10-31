// Remembers the last race, boat and language in localStorage. Never fails: storage may be unavailable.

const STORAGE_KEY = "routeur-voile.preferences";

export class PreferencesStore {
  read() {
    try {
      return JSON.parse(localStorage.getItem(STORAGE_KEY)) ?? {};
    } catch {
      return {};
    }
  }

  update(changes) {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({ ...this.read(), ...changes }));
    } catch {
      // Private browsing or blocked storage: preferences are a convenience only.
    }
  }
}
