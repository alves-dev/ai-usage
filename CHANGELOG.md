# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---
## [2026.8.1] - 2026-08-21

### Fixed

- Redacted webhook IDs from invalid-payload logs and sensor state attributes.
- Moved provider image and Lovelace card file checks off the event loop.

## [2026.8.0] - 2026-08-12

### Changed

- Replaced the provider-specific payload with schema `2.0`, using
  `collector_data`, `account_data.id` and normalized `usage_data.windows`.
- Replaced Codex/Ollama-specific usage entities with dynamic window entities.
- The integration now derives available percentage and account availability
  from normalized windows.
- Provider metadata and entity images are resolved internally from the
  provider identifier; `provider_data` is no longer part of the payload.

### Added

- Added `scripts/manual_collector.py` and its usage documentation for manual
  webhook testing.
- Added the AI Usage Windows Lovelace card to the integration and registered it
  automatically in the Home Assistant frontend.

## [0.0.3] - 2026-08-02

### Changed

- Updated the Codex payload contract to schema `1.1`.
- Replaced the ambiguous `primary_window` and `secondary_window` fields with
  semantic `five_hour_window` and `weekly_window` fields.
- Allowed either Codex usage window to be `null` when the provider does not
  report it; the integration no longer copies one window into the other.
- This is a breaking contract change. Collectors must send schema `1.1`; the
  integration does not support the previous window field names.

### Added

- Added an example Home Assistant Lovelace custom card for displaying two AI
  usage windows with available percentage and reset timestamps.

---
## [0.0.2] - 2026-06-06

### Added

- Added available percentage sensors for Codex and Ollama Cloud usage windows.
- Added `sensor.last_sample_age` for account staleness tracking.
- Added README tables explaining Home Assistant entities and status/limit
  signals.

### Changed

- Changed Codex reset-after duration sensors to show hours instead of raw
  seconds.
- Renamed Codex primary/secondary window entities to 5-hour and weekly usage
  limit entities.
- Changed percentage sensors to use zero decimal places by default.
- Changed low-level diagnostic entities to be disabled by default.
- Documented the beta status before `v1.0.0` and clarified entity contract
  stability expectations.

---
## [0.0.1] - 2026-06-03

### Added

- Initial HACS-ready release of AI Usage.
- Added Home Assistant webhook ingestion for normalized AI usage payloads.
- Added support for Codex usage payloads.
- Added support for Ollama Cloud usage payloads.
