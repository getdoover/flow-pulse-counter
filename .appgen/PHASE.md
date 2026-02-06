# AppGen State

## Current Phase
Phase 6 - Document

## Status
completed

## App Details
- **Name:** flow-pulse-counter
- **Description:** uses pulse counting to allow a doovit to convert pulses from a flow meter into flow rate. Allows for calibration via the UI, and configuration of precisely how pulses are converted to flow rates via config
- **App Type:** docker
- **Has UI:** true
- **Container Registry:** ghcr.io/getdoover
- **Target Directory:** /home/sid/flow-pulse-counter
- **GitHub Repo:** getdoover/flow-pulse-counter
- **Repo Visibility:** public
- **GitHub URL:** https://github.com/getdoover/flow-pulse-counter
- **Icon URL:** pending - no specific brand identified; user to provide a flow meter icon (256x256, transparent background, SVG preferred)

## Completed Phases
- [x] Phase 1: Creation - 2026-02-06T03:23:45Z
- [x] Phase 2: Docker Config - 2026-02-06T03:24:00Z
  - UI kept (has_ui=true)
  - doover_config.json restructured for Docker device app (type: DEV)
  - Icon URL: pending (no URL provided yet, set to empty string in config)
- [x] Phase 3: Docker Plan - 2026-02-06T03:25:00Z
  - PLAN.md created with complete build plan
  - No external integrations required
  - No user questions needed (requirements sufficiently clear)
  - Hardware I/O via platform_interface for pulse counting
  - UI design: flow rate, total volume, pulse count, calibration controls
  - Configuration: input pin, pulses_per_litre, flow rate unit, debounce, thresholds
- [x] Phase 4: Docker Build - 2026-02-06T03:30:00Z
  - Application class with pulse counting via platform_interface GPIO
  - Rising edge detection with configurable software debounce
  - Rolling window flow rate calculation with unit conversion (L/min, L/hr, m3/hr)
  - Calibration routine via UI (start/stop calibration, known volume input)
  - Tag persistence for total volume and pulse count across restarts
  - Low/high flow threshold warnings with alert deduplication
  - Simulator generates realistic pulse patterns at varying flow rates
  - All tests passing (4/4)
  - depends_on: ["platform_interface"] added to doover_config.json
  - No external packages required beyond pydoover
- [x] Phase 5: Docker Check - 2026-02-06T13:35:00Z
  - Dependencies (uv sync): PASS - 25 packages resolved, 24 audited, no errors
  - Imports: PASS - `from flow_pulse_counter.application import *` succeeded
  - Config Schema (doover config-schema export): PASS - schema validated successfully
  - File Structure: PASS - all expected files present (__init__.py, application.py, app_config.py, app_ui.py)
- [x] Phase 6: Document - 2026-02-06T13:45:00Z
  - README.md generated with all required sections
  - 8 configuration items documented
  - 12 UI elements documented (5 variables, 2 warnings, 2 parameters, 3 actions, plus AlertStream)
  - 4 tags documented (total_volume, pulse_count, flow_rate, status)
  - Calibration workflow documented

## References
- **Has References:** false

## User Decisions
- App name: flow-pulse-counter
- Description: uses pulse counting to allow a doovit to convert pulses from a flow meter into flow rate. Allows for calibration via the UI, and configuration of precisely how pulses are converted to flow rates via config
- GitHub repo: getdoover/flow-pulse-counter
- App type: docker
- Has UI: true
- Has references: false
- Icon URL: pending - no specific brand identified; user to provide

## Next Action
Phase 6 complete. README.md documentation generated. Application is fully documented and ready for deployment.
