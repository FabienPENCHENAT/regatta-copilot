// Keeps the latest computation (result and the route followed until then) in localStorage, so reloading the
// page shows the same routes, computed at the same time, instead of computing again. Never fails: storage may be
// unavailable or full.

const STORAGE_KEY = "routeur-voile.last-result";

export class LastResultStore {
  // { result, followed } or null.
  read() {
    try {
      return JSON.parse(localStorage.getItem(STORAGE_KEY));
    } catch {
      return null;
    }
  }

  save(result, followed) {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({ result, followed }));
    } catch {
      // Private browsing or storage full: the page then computes again when reloaded.
    }
  }
}
