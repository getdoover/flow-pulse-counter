# Flow Pulse Counter

**Convert flow meter pulses into accurate flow rate and volume measurements on your Doover-connected device, with live calibration and configurable thresholds.**

[![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)](https://github.com/getdoover/flow-pulse-counter)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/getdoover/flow-pulse-counter/blob/main/LICENSE)

[Getting Started](#getting-started) | [Configuration](#configuration) | [Developer](https://github.com/getdoover/flow-pulse-counter/blob/main/DEVELOPMENT.md) | [Need Help?](#need-help)

<br/>

## Overview

Flow Pulse Counter is a Doover device application that reads pulse signals from a flow meter connected to a digital input pin and converts them into meaningful flow rate and total volume readings. It is designed for industrial and agricultural use cases where accurate liquid flow measurement is essential, such as water distribution networks, irrigation systems, and process monitoring.

The application uses a rolling window algorithm to compute flow rate in real time, supports multiple display units (litres per minute, litres per hour, or cubic metres per hour), and provides configurable low-flow and high-flow warning thresholds with alert notifications. All accumulated totals (pulse count and volume) are persisted across device restarts via Doover tags.

A built-in calibration routine allows operators to determine the precise pulses-per-litre factor for their specific meter directly from the Doover UI -- no manual calculation or re-deployment required. Simply start calibration, pass a known volume of liquid through the meter, enter the volume, and stop calibration to compute a new factor automatically.

### Features

- Real-time flow rate calculation using a rolling window algorithm
- Configurable display units: L/min, L/hr, or m3/hr
- Software debounce filtering to reject electrical noise on the pulse input
- Live calibration routine accessible from the Doover UI
- Manual calibration factor override via UI parameter
- Configurable low-flow and high-flow warning thresholds with push alert notifications
- Alert deduplication to prevent notification floods
- Persistent total volume and pulse count across device restarts
- Dynamic flow rate colour ranges based on configured thresholds
- 200 ms main loop for reliable high-frequency pulse detection

<br/>

## Getting Started

### Prerequisites

1. A Doover-connected device (doovit) with at least one digital input pin
2. A pulse-output flow meter wired to the digital input pin on your device
3. The `platform_interface` app must be installed and running on the same device (this app depends on it for GPIO access)

### Installation

Add the **Flow Pulse Counter** app to your device through the Doover platform:

1. Navigate to your device in the Doover UI
2. Add the `flow_pulse_counter` application from the app catalogue
3. The container image (`ghcr.io/getdoover/flow_pulse_counter:main`) will be pulled automatically

### Quick Start

1. Install the app on your device as described above
2. Set the **Input Pin** configuration to match the digital input pin your flow meter is connected to (default: pin 1)
3. If you know your meter's pulse-per-litre specification, set **Pulses Per Litre** accordingly (default: 450)
4. Choose your preferred **Flow Rate Unit** (L/min, L/hr, or m3/hr)
5. The app will start counting pulses and displaying flow rate and total volume immediately

<br/>

## Configuration

| Setting | Description | Default |
|---------|-------------|---------|
| **App Display Name** | Display name shown in the Doover UI | `Flow Pulse Counter` |
| **Input Pin** | Digital input pin number connected to the flow meter pulse output | `1` |
| **Pulses Per Litre** | Calibration factor: number of pulses the meter produces per litre of flow | `450.0` |
| **Flow Rate Unit** | Unit for flow rate display. Options: `L/min`, `L/hr`, `m3/hr` | `L/min` |
| **Debounce ms** | Debounce time in milliseconds to filter electrical noise on the pulse input | `50` |
| **Reporting Interval** | Interval in seconds between flow rate calculations (rolling window size) | `10` |
| **Low Flow Threshold** | Flow rate below this value triggers a low-flow warning (0 = disabled) | `0.0` |
| **High Flow Threshold** | Flow rate above this value triggers a high-flow warning (0 = disabled) | `0.0` |

### Example Configuration

```json
{
  "app_display_name": "Main Water Meter",
  "input_pin": 2,
  "pulses_per_litre": 500.0,
  "flow_rate_unit": "L/min",
  "debounce_ms": 50,
  "reporting_interval": 10,
  "low_flow_threshold": 1.0,
  "high_flow_threshold": 100.0
}
```

<br/>

## UI Elements

This application provides the following UI elements on the device page in the Doover platform:

### Variables (Display)

| Element | Description |
|---------|-------------|
| **Flow Rate** | Current flow rate displayed with the selected unit and colour-coded ranges (grey = No Flow, green = Normal, yellow = Low, red = High) |
| **Total Volume** | Cumulative volume in litres since last reset, persisted across restarts |
| **Pulse Count** | Total number of raw pulses counted since last reset, persisted across restarts |
| **Status** | Operational status text: "Running", "No Flow", "Calibrating... (N pulses)", or "Totals Reset" |
| **Last Update** | Timestamp of the most recent reading update |

### Warning Indicators

| Element | Description |
|---------|-------------|
| **Low Flow Warning** | Shown when flow rate is above zero but below the configured low-flow threshold |
| **High Flow Warning** | Shown when flow rate exceeds the configured high-flow threshold |

### Parameters (User Input)

| Element | Description |
|---------|-------------|
| **Calibration Factor (pulses/L)** | View or manually override the active pulses-per-litre calibration factor at runtime |
| **Known Volume (L)** | Enter the known volume of liquid passed through the meter during a calibration run |

### Actions (Buttons)

| Element | Description |
|---------|-------------|
| **Reset Totals** | Resets pulse count and total volume to zero (requires confirmation) |
| **Start Calibration** | Begins a calibration session -- the app records the starting pulse count |
| **Stop Calibration** | Ends the calibration session and computes a new pulses-per-litre factor from recorded pulses and the known volume entered |

### Alert Notifications

The app sends push alert notifications (via the AlertStream) when low-flow or high-flow conditions are detected. Alerts are deduplicated so only one notification is sent per threshold crossing until the condition clears.

<br/>

## How It Works

1. **Pulse Detection** -- The main loop runs every 200 ms, reads the configured digital input pin via `platform_interface`, and detects rising edges. A configurable software debounce filter rejects noise.
2. **Volume Accumulation** -- Each valid pulse increments the pulse counter and adds `1 / pulses_per_litre` litres to the cumulative total volume.
3. **Flow Rate Calculation** -- A rolling window (sized by the reporting interval) of timestamped pulse counts is maintained. The flow rate in L/min is calculated from the pulse difference over the elapsed time, then converted to the configured display unit.
4. **Threshold Monitoring** -- The computed flow rate is compared against the configured low-flow and high-flow thresholds. Warning indicators are shown or hidden accordingly, and push alerts are sent (with deduplication) when thresholds are crossed.
5. **UI Update** -- All display variables (flow rate, total volume, pulse count, status, last update) are refreshed on every loop iteration so the Doover UI shows live data.
6. **State Persistence** -- Every 60 seconds the total volume, pulse count, flow rate, and status are saved to Doover tags, ensuring values survive device restarts.

### Calibration Workflow

1. Press **Start Calibration** in the UI -- the app records the current pulse count.
2. Pass a known volume of liquid through the flow meter.
3. Enter the volume into the **Known Volume (L)** parameter.
4. Press **Stop Calibration** -- the app divides the counted pulses by the known volume to compute a new pulses-per-litre factor, which is applied immediately.

<br/>

## Tags

This application persists the following tags for external consumption and restart recovery:

| Tag | Description |
|-----|-------------|
| **total_volume** | Cumulative volume in litres (rounded to 4 decimal places) |
| **pulse_count** | Total raw pulse count |
| **flow_rate** | Current flow rate in L/min (rounded to 4 decimal places) |
| **status** | Current operational status text ("Running", "No Flow", "Calibrating...") |

<br/>

## Integrations

This device app works with:

- **platform_interface** -- Required dependency for digital GPIO pin access on the Doover device hardware
- **Doover Platform UI** -- Displays live readings, parameters, calibration controls, and alerts on the device page
- **Doover Alerting** -- Push notifications for threshold warnings via the AlertStream

<br/>

## Need Help?

- Email: support@doover.com
- [Doover Documentation](https://docs.doover.com)
- [App Developer Documentation](https://github.com/getdoover/flow-pulse-counter/blob/main/DEVELOPMENT.md)

<br/>

## Version History

### v0.1.0 (Current)
- Initial release
- Real-time flow rate calculation with rolling window algorithm
- Configurable display units (L/min, L/hr, m3/hr)
- Software debounce filtering for electrical noise rejection
- Live calibration routine via Doover UI
- Low-flow and high-flow warning thresholds with push alerts
- Persistent total volume and pulse count across restarts
- Dynamic colour-coded flow rate ranges

<br/>

## License

This app is licensed under the [Apache License 2.0](https://github.com/getdoover/flow-pulse-counter/blob/main/LICENSE).
