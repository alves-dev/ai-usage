/* global customElements, HTMLElement, window */

class AIUsageWindowsCard extends HTMLElement {
  static getConfigElement() {
    return document.createElement("ai-usage-windows-card-editor");
  }

  static getStubConfig() {
    return {
      type: "custom:ai-usage-windows-card",
      account_entity: "sensor.account",
      availability_entity: "binary_sensor.available",
      windows: [],
    };
  }

  setConfig(config) {
    if (!config || !Array.isArray(config.windows)) {
      throw new Error("Add at least one window to the card configuration.");
    }

    this._config = {
      title: "AI Usage",
      account_entity: "",
      availability_entity: "",
      show_account: true,
      show_updated: true,
      warning_threshold: 40,
      critical_threshold: 15,
      windows: [],
      ...config,
    };
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  getCardSize() {
    const windowCount = Math.max(1, this._config?.windows?.length || 0);
    return 4 + windowCount;
  }

  getGridOptions() {
    const windowCount = Math.max(1, this._config?.windows?.length || 0);
    const rows = 4 + windowCount;
    return {
      rows,
      columns: 6,
      min_rows: 4,
      min_columns: 3,
    };
  }

  _render() {
    if (!this._hass || !this._config) return;

    if (!this._root) {
      this._root = this.attachShadow({ mode: "open" });
      this._root.innerHTML = `<style>${STYLES}</style><ha-card></ha-card>`;
    }

    const card = this._root.querySelector("ha-card");
    const account = this._state(this._config.account_entity);
    const availability = this._state(this._config.availability_entity);
    const windows = this._config.windows.map((window) => this._window(window));
    const available = availability?.state === "on";
    const problem = account?.state === "unavailable" || account?.state === "unknown";
    const title = this._config.title || account?.state || "AI Usage";
    const updated = this._updatedAt(account, windows);

    card.innerHTML = `
      <section class="shell">
        <header class="header">
          <div class="mark"><ha-icon icon="mdi:chart-timeline-variant-shimmer"></ha-icon></div>
          <div class="heading">
            <div class="eyebrow">AI USAGE</div>
            <h1>${this._escape(title)}</h1>
            ${this._config.show_account && account ? `<div class="account">${this._escape(account.state)}</div>` : ""}
          </div>
          <div class="availability ${problem ? "problem" : available ? "available" : "offline"}">
            <span class="dot"></span>
            ${problem ? "Unavailable" : available ? "Available" : "At limit"}
          </div>
        </header>
        <div class="rule"></div>
        ${windows.length ? `<main class="windows">${windows.map((item) => this._windowTemplate(item)).join("")}</main>` : this._emptyState()}
        ${this._config.show_updated && updated ? `<footer>Updated ${this._escape(updated)}</footer>` : ""}
      </section>`;
  }

  _window(config) {
    const used = this._number(config.used_entity);
    const available = this._number(config.available_entity);
    const limit = this._state(config.limit_entity);
    const reset = this._state(config.reset_entity);
    const remaining = available ?? (used == null ? null : 100 - used);
    const value = remaining == null ? null : Math.max(0, Math.min(100, remaining));
    const tone = value == null ? "unknown" : value <= this._config.critical_threshold ? "critical" : value <= this._config.warning_threshold ? "warning" : "good";
    return {
      label: config.label || "Usage window",
      value,
      used,
      reset: reset?.state,
      limitReached: limit?.state === "on",
      tone,
      updated: reset?.last_updated,
    };
  }

  _windowTemplate(item) {
    const value = item.value == null ? "—" : `${Math.round(item.value)}%`;
    const used = item.used ?? (item.value == null ? null : 100 - item.value);
    const width = used == null ? 0 : Math.max(0, Math.min(100, used));
    const limitText = item.limitReached ? "Limit reached" : item.reset ? `Resets ${this._relative(item.reset)}` : "Reset unavailable";
    return `
      <article class="window ${item.tone}">
        <div class="window-top">
          <div class="window-label">${this._escape(item.label)}</div>
          <div class="remaining">${value}<small> left</small></div>
        </div>
        <div class="track"><div class="fill" style="width:${width}%"></div></div>
        <div class="window-bottom">
          <span>${item.used == null ? "Usage unavailable" : `${Math.round(item.used)}% used`}</span>
          <span class="reset ${item.limitReached ? "limit" : ""}">${this._escape(limitText)}</span>
        </div>
      </article>`;
  }

  _emptyState() {
    return `<div class="empty"><ha-icon icon="mdi:chart-box-outline"></ha-icon><strong>No usage windows configured</strong><span>Add window entities in the card editor.</span></div>`;
  }

  _state(entity) {
    return entity ? this._hass.states[entity] : undefined;
  }

  _number(entity) {
    const state = this._state(entity)?.state;
    if (state == null || ["unknown", "unavailable"].includes(state)) return null;
    const value = Number(state);
    return Number.isFinite(value) ? value : null;
  }

  _updatedAt(account, windows) {
    const date = account?.last_updated || windows.find((item) => item.updated)?.updated;
    return date ? this._relative(date) : "";
  }

  _relative(value) {
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    const seconds = Math.max(0, Math.round((Date.now() - date.getTime()) / 1000));
    if (seconds < 60) return "just now";
    if (seconds < 3600) return `${Math.round(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.round(seconds / 3600)}h ago`;
    return `${Math.round(seconds / 86400)}d ago`;
  }

  _escape(value) {
    return String(value ?? "").replace(/[&<>'"]/g, (char) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", "\"": "&quot;",
    }[char]));
  }
}

class AIUsageWindowsCardEditor extends HTMLElement {
  setConfig(config) {
    this._config = { windows: [], ...config };
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  _render() {
    if (!this._hass || !this._config || this._root) return;
    this._root = this.attachShadow({ mode: "open" });
    this._root.innerHTML = `<style>${EDITOR_STYLES}</style><div class="form"></div>`;
    this._form = this._root.querySelector(".form");
    this._draw();
  }

  _draw() {
    this._form.innerHTML = `
      <ha-textfield label="Card title" value="${this._value("title", "AI Usage")}" data-key="title"></ha-textfield>
      <div class="picker-field"><label>Account entity</label><ha-entity-picker class="entity-picker" data-key="account_entity"></ha-entity-picker></div>
      <div class="picker-field"><label>Availability entity</label><ha-entity-picker class="entity-picker" data-key="availability_entity"></ha-entity-picker></div>
      <h3>Windows</h3>
      <div class="windows">${this._config.windows.map((item, index) => this._row(item, index)).join("")}</div>
      <button class="add" type="button">Add window</button>`;
    this._form.querySelectorAll("ha-textfield").forEach((field) => field.addEventListener("change", (event) => this._change(event.target.dataset.key, event.target.value)));
    this._form.querySelectorAll(".entity-picker").forEach((picker) => this._configurePicker(picker));
    this._form.querySelectorAll(".window-field").forEach((field) => field.addEventListener("change", (event) => this._windowChange(event.target)));
    this._form.querySelectorAll(".remove").forEach((button) => button.addEventListener("click", (event) => this._remove(Number(event.target.dataset.index))));
    this._form.querySelector(".add").addEventListener("click", () => this._add());
  }

  _row(item, index) {
    return `<div class="row">
      <ha-textfield class="window-field" label="Label" value="${item.label || "Window"}" data-index="${index}" data-field="label"></ha-textfield>
      ${this._pickerMarkup("Used % entity", "used_entity", index, "sensor")}
      ${this._pickerMarkup("Available % entity", "available_entity", index, "sensor")}
      ${this._pickerMarkup("Limit entity", "limit_entity", index, "binary_sensor")}
      ${this._pickerMarkup("Reset entity", "reset_entity", index, "sensor")}
      <button class="remove" type="button" data-index="${index}">Remove</button>
    </div>`;
  }

  _pickerMarkup(label, field, index, domain) {
    return `<div class="picker-field"><label>${label}</label><ha-entity-picker class="entity-picker window-picker" data-index="${index}" data-field="${field}" data-domain="${domain}"></ha-entity-picker></div>`;
  }

  _configurePicker(picker) {
    const index = picker.dataset.index;
    const field = picker.dataset.field || picker.dataset.key;
    const value = index == null ? this._config[field] : this._config.windows[Number(index)]?.[field];
    picker.hass = this._hass;
    picker.value = value || "";
    picker.includeDomains = [picker.dataset.domain || (field === "availability_entity" ? "binary_sensor" : "sensor")];
    picker.addEventListener("value-changed", (event) => {
      if (index == null) {
        this._change(field, event.detail.value || "");
      } else {
        this._windowChange({ dataset: { index, field }, value: event.detail.value || "" });
      }
    });
  }

  _value(key, fallback = "") { return this._config[key] || fallback; }

  _change(key, value) { this._config = { ...this._config, [key]: value }; this._fire(); }

  _windowChange(target) {
    const windows = this._config.windows.map((item, index) => index === Number(target.dataset.index) ? { ...item, [target.dataset.field]: target.value } : item);
    this._config = { ...this._config, windows };
    this._fire();
  }

  _add() { this._config = { ...this._config, windows: [...this._config.windows, { label: "New window" }] }; this._draw(); this._fire(); }

  _remove(index) { this._config = { ...this._config, windows: this._config.windows.filter((_, itemIndex) => itemIndex !== index) }; this._draw(); this._fire(); }

  _fire() { this.dispatchEvent(new CustomEvent("config-changed", { detail: { config: this._config }, bubbles: true, composed: true })); }
}

const STYLES = `
  :host { display:block; }
  * { box-sizing:border-box; }
  ha-card { overflow:hidden; border-radius:var(--ha-card-border-radius, 20px); }
  .shell { padding:22px; background:radial-gradient(circle at 100% 0%, color-mix(in srgb, var(--primary-color) 20%, transparent), transparent 38%), var(--card-background-color); color:var(--primary-text-color); }
  .header { display:flex; align-items:center; gap:14px; }
  .mark { width:48px; height:48px; display:grid; place-items:center; border-radius:16px; background:color-mix(in srgb, var(--primary-color) 16%, transparent); color:var(--primary-color); }
  .mark ha-icon { --mdc-icon-size:28px; }
  .heading { min-width:0; flex:1; }
  .eyebrow { color:var(--secondary-text-color); font-size:10px; letter-spacing:.16em; font-weight:800; }
  h1 { margin:3px 0 0; font-size:22px; line-height:1.1; letter-spacing:-.03em; }
  .account { margin-top:4px; overflow:hidden; color:var(--secondary-text-color); font-size:13px; text-overflow:ellipsis; white-space:nowrap; }
  .availability { display:flex; align-items:center; gap:7px; padding:7px 10px; border-radius:999px; font-size:12px; font-weight:700; white-space:nowrap; }
  .dot { width:7px; height:7px; border-radius:50%; background:currentColor; box-shadow:0 0 9px currentColor; }
  .available { color:var(--success-color, #35c759); background:color-mix(in srgb, currentColor 12%, transparent); }
  .offline,.problem { color:var(--error-color, #ef5350); background:color-mix(in srgb, currentColor 12%, transparent); }
  .rule { height:1px; margin:20px 0 16px; background:var(--divider-color); opacity:.65; }
  .windows { display:grid; gap:12px; }
  .window { padding:16px; border:1px solid var(--divider-color); border-radius:16px; background:color-mix(in srgb, var(--primary-text-color) 3%, transparent); }
  .window-top,.window-bottom { display:flex; align-items:center; justify-content:space-between; gap:12px; }
  .window-label { overflow:hidden; color:var(--secondary-text-color); font-size:13px; font-weight:700; text-overflow:ellipsis; white-space:nowrap; }
  .remaining { font-size:26px; font-weight:800; letter-spacing:-.05em; }
  .remaining small { color:var(--secondary-text-color); font-size:11px; font-weight:600; letter-spacing:0; }
  .track { height:9px; margin:14px 0 10px; overflow:hidden; border-radius:9px; background:var(--divider-color); }
  .fill { height:100%; border-radius:inherit; background:var(--primary-color); transition:width .3s ease; }
  .warning .fill { background:var(--warning-color, #ffb300); }
  .critical .fill { background:var(--error-color, #ef5350); }
  .window-bottom { color:var(--secondary-text-color); font-size:11px; }
  .reset.limit { color:var(--error-color, #ef5350); font-weight:700; }
  footer { margin-top:16px; color:var(--secondary-text-color); font-size:11px; text-align:right; }
  .empty { display:grid; justify-items:center; gap:8px; padding:28px 12px; color:var(--secondary-text-color); text-align:center; }
  .empty ha-icon { --mdc-icon-size:34px; color:var(--primary-color); }
  .empty strong { color:var(--primary-text-color); }
  @media (max-width:500px) { .availability { padding:6px; font-size:0; } .availability .dot { width:9px; height:9px; } }
`;

const EDITOR_STYLES = `
  :host { display:block; padding:8px 0; }
  .form { display:grid; gap:12px; }
  .picker-field { display:grid; gap:4px; }
  .picker-field label { color:var(--secondary-text-color); font-size:12px; }
  h3 { margin:12px 0 0; }
  .windows { display:grid; gap:12px; }
  .row { display:grid; gap:8px; padding:12px; border:1px solid var(--divider-color); border-radius:12px; }
  button { min-height:36px; border:0; border-radius:8px; background:var(--primary-color); color:var(--text-primary-color, white); cursor:pointer; }
  .remove { background:var(--error-color, #ef5350); }
`;

if (!customElements.get("ai-usage-windows-card")) {
  customElements.define("ai-usage-windows-card", AIUsageWindowsCard);
}
if (!customElements.get("ai-usage-windows-card-editor")) {
  customElements.define("ai-usage-windows-card-editor", AIUsageWindowsCardEditor);
}
window.customCards = window.customCards || [];
window.customCards.push({
  type: "ai-usage-windows-card",
  name: "AI Usage Windows",
  description: "Shows AI usage windows, remaining capacity, limits, and reset times.",
  preview: true,
});
