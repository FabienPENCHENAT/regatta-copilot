// Shows where the 31 weather scenarios stand (downloading, ready, unavailable) and, while they download,
// asks the server every few seconds; when they become ready, it calls `onReady` so the route is recomputed
// with real options and probabilities.

const POLL_EVERY_MS = 15000;

export class EnsembleStatus {
  #timer = null;
  #status = null;

  constructor(element, { api, translator, onReady }) {
    this.element = element;
    this.api = api;
    this.translator = translator;
    this.onReady = onReady;
  }

  show(status) {
    this.#status = status ?? null;
    this.render();
    clearTimeout(this.#timer);
    if (status?.state === "downloading") this.#timer = setTimeout(() => this.#poll(), POLL_EVERY_MS);
  }

  render() {
    const status = this.#status;
    this.element.hidden = !status;
    if (!status) return;
    this.element.dataset.state = status.state;
    this.element.textContent = this.translator.t(`ensemble.${status.state}`, {
      done: status.done, total: status.total, members: status.member_count,
      percent: status.total ? Math.round((100 * status.done) / status.total) : 0,
    });
  }

  async #poll() {
    try {
      const status = await this.api.getEnsembleStatus();
      if (status.state === "ready") {
        this.show(status);
        this.onReady();
        return;
      }
      this.show(status);
    } catch {
      this.#timer = setTimeout(() => this.#poll(), POLL_EVERY_MS);
    }
  }
}
