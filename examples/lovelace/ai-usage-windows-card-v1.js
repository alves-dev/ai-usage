class AIUsageWindowsCard extends HTMLElement {
  setConfig(config) {
    const required = [
      "status_entity",
      "primary_available_entity",
      "primary_reset_entity",
      "secondary_available_entity",
      "secondary_reset_entity",
    ];

    for (const key of required) {
      if (!config[key]) {
        throw new Error(`${key} is required`);
      }
    }

    this._config = {
      name: "AI Usage",
      subtitle: "",
      icon: "mdi:chart-arc",
      primary_name: "First window",
      secondary_name: "Second window",
      warning_threshold: 40,
      critical_threshold: 15,
      ...config,
    };
  }

  set hass(hass) {
    this._hass = hass;

    if (!this._content) {
      const shadow = this.attachShadow({ mode: "open" });
      shadow.innerHTML = `
        <style>
          :host {
            display: block;
          }

          * {
            box-sizing: border-box;
          }

          ha-card {
            overflow: hidden;
            border-radius: var(--ha-card-border-radius, 28px);
          }

          .panel {
            padding: 24px;
            color: var(--primary-text-color);
            background:
              radial-gradient(circle at top right, color-mix(in srgb, var(--primary-color) 28%, transparent), transparent 36%),
              linear-gradient(
                180deg,
                color-mix(in srgb, var(--card-background-color) 96%, white 4%),
                color-mix(in srgb, var(--card-background-color) 90%, black 10%)
              );
          }

          .header {
            display: flex;
            align-items: center;
            gap: 16px;
            margin-bottom: 22px;
          }

          .icon-shell {
            width: 60px;
            height: 60px;
            flex: 0 0 60px;
            border-radius: 18px;
            display: grid;
            place-items: center;
            overflow: hidden;
            background: linear-gradient(
              135deg,
              color-mix(in srgb, var(--primary-color) 22%, transparent),
              color-mix(in srgb, var(--primary-color) 8%, transparent)
            );
            border: 1px solid color-mix(in srgb, var(--primary-color) 20%, var(--divider-color));
          }

          .icon-shell img {
            width: 100%;
            height: 100%;
            object-fit: cover;
          }

          .icon-shell ha-icon {
            --mdc-icon-size: 32px;
            color: var(--primary-color);
          }

          .title-wrap {
            min-width: 0;
            flex: 1;
          }

          .name {
            margin: 0;
            font-size: 2rem;
            line-height: 1;
            letter-spacing: -0.04em;
            color: var(--primary-text-color);
          }

          .subtitle {
            margin-top: 6px;
            color: var(--secondary-text-color);
            font-size: 0.92rem;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
          }

          .header-side {
            display: flex;
            flex-direction: column;
            align-items: flex-end;
            gap: 8px;
          }

          .status {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 8px 12px;
            border-radius: 999px;
            font-size: 0.84rem;
            font-weight: 700;
            border: 1px solid transparent;
          }

          .status::before {
            content: "";
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: currentColor;
            box-shadow: 0 0 10px currentColor;
          }

          .status.good {
            color: var(--success-color, #22c55e);
            background: color-mix(in srgb, var(--success-color, #22c55e) 14%, transparent);
            border-color: color-mix(in srgb, var(--success-color, #22c55e) 22%, transparent);
          }

          .status.warning {
            color: var(--warning-color, #f59e0b);
            background: color-mix(in srgb, var(--warning-color, #f59e0b) 14%, transparent);
            border-color: color-mix(in srgb, var(--warning-color, #f59e0b) 22%, transparent);
          }

          .status.critical {
            color: var(--error-color, #ef4444);
            background: color-mix(in srgb, var(--error-color, #ef4444) 14%, transparent);
            border-color: color-mix(in srgb, var(--error-color, #ef4444) 22%, transparent);
          }

          .updated {
            color: var(--secondary-text-color);
            font-size: 0.82rem;
          }

          .grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 16px;
          }

          .limit-card {
            background: linear-gradient(
              180deg,
              color-mix(in srgb, var(--card-background-color) 88%, white 12%),
              color-mix(in srgb, var(--card-background-color) 96%, black 4%)
            );
            border: 1px solid color-mix(in srgb, var(--primary-color) 12%, var(--divider-color));
            border-radius: 24px;
            padding: 22px;
          }

          .limit-card h2 {
            margin: 0 0 16px;
            font-size: 0.82rem;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            color: var(--secondary-text-color);
          }

          .percentage {
            font-size: clamp(3rem, 9vw, 5rem);
            line-height: 0.9;
            font-weight: 800;
            letter-spacing: -0.08em;
            color: color-mix(in srgb, var(--primary-color) 72%, white 28%);
          }

          .percentage span {
            font-size: 1.85rem;
            letter-spacing: 0;
            color: var(--primary-color);
          }

          .bar {
            height: 12px;
            margin: 22px 0;
            border-radius: 999px;
            overflow: hidden;
            background: color-mix(in srgb, var(--divider-color) 72%, transparent);
          }

          .bar-fill {
            height: 100%;
            border-radius: inherit;
            transition: width 180ms ease-in-out;
          }

          .bar-fill.good {
            background: linear-gradient(90deg, var(--primary-color), color-mix(in srgb, var(--primary-color) 42%, white 58%));
            box-shadow: 0 0 18px color-mix(in srgb, var(--primary-color) 48%, transparent);
          }

          .bar-fill.warning {
            background: linear-gradient(90deg, #f59e0b, #fbbf24);
            box-shadow: 0 0 18px rgba(245, 158, 11, 0.35);
          }

          .bar-fill.critical {
            background: linear-gradient(90deg, #ef4444, #f87171);
            box-shadow: 0 0 18px rgba(239, 68, 68, 0.35);
          }

          .renew {
            color: var(--secondary-text-color);
            font-size: 0.92rem;
          }

          .renew strong {
            display: block;
            margin-top: 4px;
            color: var(--primary-text-color);
            font-size: 1.32rem;
            line-height: 1.2;
          }

          .renew-date {
            margin-top: 6px;
            font-size: 0.82rem;
          }

          .error {
            padding: 16px;
            color: var(--error-color);
          }

          @media (max-width: 640px) {
            .panel {
              padding: 20px;
            }

            .grid {
              grid-template-columns: 1fr;
            }

            .header {
              align-items: flex-start;
            }

            .header-side {
              align-items: flex-start;
            }

            .name {
              font-size: 1.7rem;
            }
          }
        </style>
        <ha-card>
          <div class="panel">
            <div id="content"></div>
          </div>
        </ha-card>
      `;
      this._content = shadow.querySelector("#content");
    }

    const statusEntity = hass.states[this._config.status_entity];
    const sections = [
      {
        name: this._config.primary_name,
        available: hass.states[this._config.primary_available_entity],
        reset: hass.states[this._config.primary_reset_entity],
      },
      {
        name: this._config.secondary_name,
        available: hass.states[this._config.secondary_available_entity],
        reset: hass.states[this._config.secondary_reset_entity],
      },
    ];

    const missing = [];
    if (!statusEntity) {
      missing.push(this._config.status_entity);
    }
    for (const [index, section] of sections.entries()) {
      const prefix = index === 0 ? "primary" : "secondary";
      if (!section.available) {
        missing.push(this._config[`${prefix}_available_entity`]);
      }
      if (!section.reset) {
        missing.push(this._config[`${prefix}_reset_entity`]);
      }
    }

    if (missing.length > 0) {
      this._content.innerHTML = `
        <div class="error">
          Missing entities: ${missing.join(", ")}
        </div>
      `;
      return;
    }

    const statusInfo = this._statusInfo(statusEntity);
    const updatedDate = this._updatedDate(statusEntity, sections[0].available);

    this._content.innerHTML = `
      <header class="header">
        <div class="icon-shell">${this._renderIcon()}</div>
        <div class="title-wrap">
          <h1 class="name">${this._escape(this._config.name)}</h1>
          ${this._config.subtitle ? `<div class="subtitle">${this._escape(this._config.subtitle)}</div>` : ""}
        </div>
        <div class="header-side">
          <div class="status ${statusInfo.severity}">${this._escape(statusInfo.label)}</div>
          <div class="updated">${this._escape(this._formatUpdated(updatedDate))}</div>
        </div>
      </header>
      <section class="grid">
        ${sections
          .map((section) => this._renderWindow(section.name, section.available, section.reset))
          .join("")}
      </section>
    `;
  }

  getCardSize() {
    return 5;
  }

  static getStubConfig() {
    return {
      name: "Codex",
      subtitle: "OpenAI Plus",
      icon: "mdi:hexagon-multiple-outline",
      status_entity: "binary_sensor.allowed",
      primary_name: "5-hour window",
      primary_available_entity: "sensor.five_hour_usage_available_percent",
      primary_reset_entity: "sensor.five_hour_usage_reset_at",
      secondary_name: "Weekly window",
      secondary_available_entity: "sensor.weekly_usage_available_percent",
      secondary_reset_entity: "sensor.weekly_usage_reset_at",
    };
  }

  _renderIcon() {
    if (this._config.icon_url) {
      return `<img src="${this._escape(this._config.icon_url)}" alt="">`;
    }
    return `<ha-icon icon="${this._escape(this._config.icon)}"></ha-icon>`;
  }

  _renderWindow(name, availableEntity, resetEntity) {
    const available = this._numberState(availableEntity);
    const severity = this._severityForAvailable(available);
    const resetDate = this._parseDate(resetEntity.state);

    return `
      <article class="limit-card">
        <h2>${this._escape(name)}</h2>
        <div class="percentage">${this._formatPercent(available)}</div>
        <div class="bar">
          <div class="bar-fill ${severity}" style="width: ${this._fillWidth(available)}%"></div>
        </div>
        <div class="renew">
          Renova em
          <strong>${this._escape(this._formatDurationUntil(resetDate))}</strong>
          <div class="renew-date">${this._escape(this._formatDate(resetDate))}</div>
        </div>
      </article>
    `;
  }

  _statusInfo(stateObj) {
    const state = String(stateObj.state).toLowerCase();

    if (stateObj.entity_id.startsWith("binary_sensor.")) {
      return state === "on"
        ? { label: "Allowed", severity: "good" }
        : { label: "Blocked", severity: "critical" };
    }

    if (state === "ok" || state === "allowed" || state === "available") {
      return { label: this._prettyState(stateObj.state), severity: "good" };
    }

    if (
      state.includes("warn") ||
      state.includes("limit") ||
      state.includes("pending")
    ) {
      return { label: this._prettyState(stateObj.state), severity: "warning" };
    }

    if (
      state === "unavailable" ||
      state === "unknown" ||
      state === "off" ||
      state.includes("error") ||
      state.includes("deny") ||
      state.includes("block") ||
      state.includes("problem")
    ) {
      return { label: this._prettyState(stateObj.state), severity: "critical" };
    }

    return { label: this._prettyState(stateObj.state), severity: "warning" };
  }

  _updatedDate(...stateObjects) {
    for (const stateObj of stateObjects) {
      if (!stateObj) {
        continue;
      }
      const raw = stateObj.last_updated || stateObj.last_changed;
      const parsed = this._parseDate(raw);
      if (parsed) {
        return parsed;
      }
    }
    return null;
  }

  _severityForAvailable(available) {
    if (available === null) {
      return "warning";
    }
    if (available <= this._config.critical_threshold) {
      return "critical";
    }
    if (available <= this._config.warning_threshold) {
      return "warning";
    }
    return "good";
  }

  _fillWidth(available) {
    if (available === null) {
      return 0;
    }
    return Math.max(0, Math.min(100, available));
  }

  _numberState(stateObj) {
    if (!stateObj) {
      return null;
    }
    const value = Number(stateObj.state);
    return Number.isFinite(value) ? value : null;
  }

  _parseDate(value) {
    if (!value || value === "unknown" || value === "unavailable") {
      return null;
    }
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? null : date;
  }

  _formatPercent(value) {
    if (value === null) {
      return "—";
    }
    return `${Math.round(value)}<span>%</span>`;
  }

  _formatDate(date) {
    if (!date) {
      return "Reset unavailable";
    }
    return new Intl.DateTimeFormat(undefined, {
      dateStyle: "medium",
      timeStyle: "short",
    }).format(date);
  }

  _formatUpdated(date) {
    if (!date) {
      return "updated unavailable";
    }
    return `updated ${this._formatRelativeTime(date)}`;
  }

  _formatRelativeTime(date) {
    const diffMs = date.getTime() - Date.now();
    const diffMinutes = Math.round(diffMs / 60000);
    const absMinutes = Math.abs(diffMinutes);
    const rtf = new Intl.RelativeTimeFormat(undefined, { numeric: "auto" });

    if (absMinutes < 60) {
      return rtf.format(diffMinutes, "minute");
    }

    const diffHours = Math.round(diffMinutes / 60);
    const absHours = Math.abs(diffHours);
    if (absHours < 48) {
      return rtf.format(diffHours, "hour");
    }

    const diffDays = Math.round(diffHours / 24);
    return rtf.format(diffDays, "day");
  }

  _formatDurationUntil(date) {
    if (!date) {
      return "—";
    }

    const diffMs = Math.max(0, date.getTime() - Date.now());
    const totalMinutes = Math.round(diffMs / 60000);
    const days = Math.floor(totalMinutes / 1440);
    const hours = Math.floor((totalMinutes % 1440) / 60);
    const minutes = totalMinutes % 60;

    if (days > 0) {
      return `${days}d ${hours}h`;
    }

    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    }

    return `${minutes}m`;
  }

  _prettyState(value) {
    return String(value)
      .replaceAll("_", " ")
      .replace(/\b\w/g, (char) => char.toUpperCase());
  }

  _escape(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }
}

customElements.define("ai-usage-windows-card", AIUsageWindowsCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "ai-usage-windows-card",
  name: "AI Usage Windows Card",
  description:
    "Displays a provider header, status entity, and two AI usage windows.",
});
