# Build Plan

## App Summary
- Name: flow-pulse-counter
- Type: docker
- Description: Converts pulses from a flow meter into flow rate and accumulated volume, with calibration via the UI and precise pulse-to-flow configuration

## External Integration
- Service: None
- Documentation: N/A
- Authentication: N/A

## Data Flow
- Inputs: Digital input pulses from a flow meter via platform_interface (GPIO digital input pin)
- Processing:
  1. Read digital input state each loop iteration and detect pulse edges (rising edge counting)
  2. Track pulse count over a rolling time window
  3. Apply calibration factor (pulses per litre) to compute instantaneous flow rate (litres per minute or per hour)
  4. Accumulate total volume by summing calibrated pulse increments
  5. Optionally apply a k-factor or offset for nonlinear meter compensation
- Outputs:
  - Tags: `flow_rate`, `total_volume`, `pulse_count`, `status`
  - UI: Real-time flow rate display, total volume, pulse count, calibration parameters, reset action

## Configuration Schema
| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| display_name | String | no | "Flow Pulse Counter" | Display name shown in the Doover UI |
| input_pin | Integer | yes | 1 | Digital input pin number connected to the flow meter pulse output |
| pulses_per_litre | Number | yes | 450.0 | Calibration factor: number of pulses the meter produces per litre of flow. This is the primary conversion factor |
| flow_rate_unit | Enum | no | "L/min" | Unit for flow rate display. Choices: "L/min", "L/hr", "m3/hr" |
| debounce_ms | Integer | no | 50 | Debounce time in milliseconds to filter electrical noise on the pulse input |
| reporting_interval | Integer | no | 10 | Interval in seconds between flow rate calculations (rolling window size) |
| low_flow_threshold | Number | no | 0.0 | Flow rate below this value triggers a low-flow warning (0 = disabled) |
| high_flow_threshold | Number | no | 0.0 | Flow rate above this value triggers a high-flow warning (0 = disabled) |

## UI Elements

### Variables (Display)
| Name | Type | Description |
|------|------|-------------|
| flow_rate | NumericVariable | Current instantaneous flow rate with unit suffix, with range coloring (green=normal, red=alarm) |
| total_volume | NumericVariable | Accumulated total volume in litres since last reset |
| pulse_count | NumericVariable | Raw pulse count since last reset (useful for diagnostics and calibration) |
| status | TextVariable | Current operational status (e.g., "Running", "No Flow", "Error") |
| last_update | DateTimeVariable | Timestamp of last successful reading |

### Parameters (User Input)
| Name | Type | Default | Description |
|------|------|---------|-------------|
| calibration_factor | NumericParameter | 450.0 | Live-adjustable pulses-per-litre calibration factor (mirrors config but adjustable at runtime via UI) |

### Actions (Commands)
| Name | Description |
|------|-------------|
| reset_totals | Reset the accumulated total volume and pulse count to zero. Requires confirmation |
| calibrate | Start a calibration routine: user passes a known volume through the meter, then the app calculates the correct pulses-per-litre factor based on observed pulses |
| stop_calibration | End the calibration routine and apply (or discard) the computed factor |

## Documentation Chunks

### Required Chunks
- `config-schema.md` - Configuration types and patterns
- `docker-application.md` - Application class structure
- `docker-project.md` - Entry point and Dockerfile

### Recommended Chunks
- `docker-ui.md` - UI component patterns (has_ui=true)
- `docker-advanced.md` - Debounced input pattern, rolling statistics, hardware I/O via platform_interface
- `tags-channels.md` - Tag persistence for total volume, pulse count, and state across restarts

### Discovery Keywords
pulse, flow, rate, volume, calibration, calibrate, gpio, digital input, debounce, counter, accumulate, rolling, threshold, warning, alert, platform_interface, pin

## Implementation Notes

### Architecture
- The application class (`FlowPulseCounterApplication`) will inherit from `pydoover.docker.Application`
- A fast main loop (loop_target_period = 0.1 to 0.2 seconds) is needed to reliably catch pulses via polling; alternatively, a slightly slower loop (0.5s) with edge detection could work if the platform_interface supports interrupt-style reads
- Use `platform_interface` (`depends_on: ["platform_interface"]` in doover_config.json) for reading digital inputs

### Pulse Counting Strategy
- Each loop iteration, read the digital input pin via `self.platform_iface.get_di_async([pin])`
- Detect rising edges by comparing current pin state to previous state
- Apply software debounce: ignore state changes within `debounce_ms` of the last edge
- Increment a running pulse counter on each valid rising edge
- Use a time-windowed approach for flow rate: count pulses in the last N seconds (configurable via `reporting_interval`) and compute `flow_rate = (pulses_in_window / pulses_per_litre) * (60 / window_seconds)` for L/min

### Calibration Routine
- When the user presses "calibrate", enter calibration mode:
  1. Reset a calibration pulse counter to zero
  2. User passes a known volume of fluid through the meter
  3. User presses "stop_calibration"
  4. Prompt user to enter the known volume (via a UI parameter)
  5. Compute `new_factor = calibration_pulses / known_volume`
  6. Update the calibration_factor parameter in the UI
- Display calibration status in the status variable

### Persistence
- Use tags to persist `total_volume` and `pulse_count` across restarts (`set_tag` / `get_tag`)
- On startup, restore `total_volume` and `pulse_count` from tags
- Periodically save (e.g., every 60 seconds or on significant change) to avoid excessive writes

### Flow Rate Calculation
- Maintain a `collections.deque` of `(timestamp, pulse_count)` tuples
- On each loop, append current reading
- Remove entries older than `reporting_interval` seconds
- Flow rate = `(recent_pulses / pulses_per_litre) / elapsed_seconds * 60` (for L/min)
- Support unit conversion: L/min, L/hr, m3/hr

### Unit Conversion
- L/min: base calculation
- L/hr: multiply L/min by 60
- m3/hr: multiply L/hr by 0.001

### Warnings
- If `low_flow_threshold > 0` and `flow_rate < low_flow_threshold` while flow is expected, show a low-flow warning
- If `high_flow_threshold > 0` and `flow_rate > high_flow_threshold`, show a high-flow warning
- Use `ui.WarningIndicator` for visual indicators and `ui.AlertStream` for push notifications

### Dependencies in doover_config.json
- Add `"platform_interface"` to the `depends_on` array to enable GPIO access

### External Packages
- No external packages required beyond `pydoover`
- Standard library: `collections.deque`, `time`, `logging`, `datetime`

### Main Loop Interval
- Recommended: `loop_target_period = 0.2` (200ms) for reliable pulse detection at moderate flow rates
- For very high pulse rates (>100 Hz), consider a threaded counter or platform-level interrupt support

### Simulator
- The simulator should generate realistic pulse patterns by toggling a digital output at configurable frequencies
- Simulate different flow rates (idle, low, normal, high) for testing
- Provide a sample app_config.json with sensible defaults for local testing
