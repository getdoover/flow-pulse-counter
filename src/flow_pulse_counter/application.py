import logging
import time
from collections import deque
from datetime import datetime

from pydoover.docker import Application
from pydoover import ui

from .app_config import FlowPulseCounterConfig
from .app_ui import FlowPulseCounterUI

log = logging.getLogger(__name__)


class FlowPulseCounterApplication(Application):
    config: FlowPulseCounterConfig  # Type hint for IDE autocomplete

    loop_target_period = 0.2  # 200ms for reliable pulse detection

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.ui: FlowPulseCounterUI = None

        # Pulse counting state
        self.prev_pin_state = None
        self.last_edge_time = 0.0
        self.pulse_count = 0
        self.total_volume = 0.0

        # Rolling window for flow rate calculation: deque of (timestamp, cumulative_pulse_count)
        self.pulse_history = deque()

        # Current flow rate
        self.flow_rate = 0.0

        # Active calibration factor (may differ from config if adjusted at runtime)
        self.pulses_per_litre = 450.0

        # Calibration mode state
        self.calibrating = False
        self.calibration_start_pulses = 0

        # Tag persistence throttle
        self.last_tag_save_time = 0.0
        self.TAG_SAVE_INTERVAL = 60.0  # seconds

        # Alert deduplication
        self.active_alerts = set()

    async def setup(self):
        """Initialize UI and restore persisted state."""
        self.ui = FlowPulseCounterUI()
        self.ui_manager.add_children(*self.ui.fetch())
        self.ui_manager.set_display_name(self.config.app_display_name.value)

        # Load calibration factor from config
        self.pulses_per_litre = self.config.pulses_per_litre.value

        # Restore persisted state from tags
        saved_total_volume = self.get_tag("total_volume")
        if saved_total_volume is not None:
            try:
                self.total_volume = float(saved_total_volume)
            except (TypeError, ValueError):
                self.total_volume = 0.0

        saved_pulse_count = self.get_tag("pulse_count")
        if saved_pulse_count is not None:
            try:
                self.pulse_count = int(saved_pulse_count)
            except (TypeError, ValueError):
                self.pulse_count = 0

        # Set initial calibration factor in UI
        self.ui.calibration_factor.update(self.pulses_per_litre)

        # Configure flow rate ranges based on thresholds
        low_threshold = self.config.low_flow_threshold.value
        high_threshold = self.config.high_flow_threshold.value
        self.ui.set_flow_rate_ranges(low_threshold, high_threshold)

        log.info(
            "Flow Pulse Counter started - pin=%d, pulses_per_litre=%.1f, restored volume=%.2f L, pulses=%d",
            self.config.input_pin.value,
            self.pulses_per_litre,
            self.total_volume,
            self.pulse_count,
        )

    async def main_loop(self):
        """Main loop: read pin, detect pulses, calculate flow rate, update UI."""
        try:
            # Read the digital input pin
            pin = self.config.input_pin.value
            values = await self.platform_iface.get_di_async([pin])
            current_state = values.get(pin, False)

            # Detect rising edge with debounce
            now = time.time()
            debounce_s = self.config.debounce_ms.value / 1000.0

            if self.prev_pin_state is not None and current_state and not self.prev_pin_state:
                # Rising edge detected
                if (now - self.last_edge_time) >= debounce_s:
                    # Valid pulse after debounce
                    self.pulse_count += 1
                    self.last_edge_time = now

                    # Accumulate volume
                    if self.pulses_per_litre > 0:
                        self.total_volume += 1.0 / self.pulses_per_litre

            self.prev_pin_state = current_state

            # Record pulse history for flow rate calculation
            self.pulse_history.append((now, self.pulse_count))

            # Remove entries older than the reporting interval
            reporting_interval = self.config.reporting_interval.value
            cutoff = now - reporting_interval
            while self.pulse_history and self.pulse_history[0][0] < cutoff:
                self.pulse_history.popleft()

            # Calculate flow rate from rolling window
            self.flow_rate = self._calculate_flow_rate(now, reporting_interval)

            # Convert flow rate to selected unit
            display_flow_rate = self._convert_flow_rate(self.flow_rate)
            unit = self.config.flow_rate_unit.value

            # Determine status text
            status = self._get_status_text()

            # Update UI
            self.ui.update_readings(
                flow_rate=display_flow_rate,
                total_volume=self.total_volume,
                pulse_count=self.pulse_count,
                status_text=status,
                unit=unit,
            )

            # Check warning thresholds
            await self._check_warnings(display_flow_rate)

            # Periodically persist state to tags
            await self._persist_state(now)

        except Exception as e:
            log.error("Error in main loop: %s", e, exc_info=True)
            self.ui.status.update(f"Error: {e}")

    def _calculate_flow_rate(self, now, reporting_interval):
        """Calculate flow rate in L/min from the rolling pulse window."""
        if len(self.pulse_history) < 2:
            return 0.0

        oldest_time, oldest_pulses = self.pulse_history[0]
        newest_time, newest_pulses = self.pulse_history[-1]

        elapsed = newest_time - oldest_time
        if elapsed <= 0 or self.pulses_per_litre <= 0:
            return 0.0

        pulse_diff = newest_pulses - oldest_pulses
        litres = pulse_diff / self.pulses_per_litre

        # Flow rate in L/min
        return (litres / elapsed) * 60.0

    def _convert_flow_rate(self, rate_lpm):
        """Convert flow rate from L/min to the configured display unit."""
        unit = self.config.flow_rate_unit.value
        if unit == "L/hr":
            return rate_lpm * 60.0
        elif unit == "m3/hr":
            return rate_lpm * 60.0 * 0.001
        else:
            # Default: L/min
            return rate_lpm

    def _get_status_text(self):
        """Determine the current operational status text."""
        if self.calibrating:
            cal_pulses = self.pulse_count - self.calibration_start_pulses
            return f"Calibrating... ({cal_pulses} pulses)"

        if self.flow_rate > 0.01:
            return "Running"
        else:
            return "No Flow"

    async def _check_warnings(self, display_flow_rate):
        """Check flow rate against warning thresholds and update indicators."""
        low_threshold = self.config.low_flow_threshold.value
        high_threshold = self.config.high_flow_threshold.value

        # Low flow warning
        if low_threshold > 0 and display_flow_rate > 0 and display_flow_rate < low_threshold:
            self.ui.low_flow_warning.hidden = False
            await self._send_alert_once(
                "low_flow",
                f"Low flow detected: {display_flow_rate:.2f} {self.config.flow_rate_unit.value}",
            )
        else:
            self.ui.low_flow_warning.hidden = True
            self._clear_alert("low_flow")

        # High flow warning
        if high_threshold > 0 and display_flow_rate > high_threshold:
            self.ui.high_flow_warning.hidden = False
            await self._send_alert_once(
                "high_flow",
                f"High flow detected: {display_flow_rate:.2f} {self.config.flow_rate_unit.value}",
            )
        else:
            self.ui.high_flow_warning.hidden = True
            self._clear_alert("high_flow")

    async def _send_alert_once(self, alert_id, message):
        """Send an alert only once until cleared."""
        if alert_id in self.active_alerts:
            return
        await self.ui.notifications.send_alert(message)
        self.active_alerts.add(alert_id)

    def _clear_alert(self, alert_id):
        """Clear an alert so it can fire again."""
        self.active_alerts.discard(alert_id)

    async def _persist_state(self, now):
        """Periodically save state to tags for persistence across restarts."""
        if (now - self.last_tag_save_time) >= self.TAG_SAVE_INTERVAL:
            await self.set_tag("total_volume", round(self.total_volume, 4))
            await self.set_tag("pulse_count", self.pulse_count)
            await self.set_tag("status", self._get_status_text())
            await self.set_tag("flow_rate", round(self.flow_rate, 4))
            self.last_tag_save_time = now
            log.debug(
                "Persisted state: volume=%.2f, pulses=%d",
                self.total_volume,
                self.pulse_count,
            )

    # ---- UI Callbacks ----

    @ui.callback("reset_totals")
    async def on_reset_totals(self, new_value):
        """Reset accumulated totals when user presses the reset button."""
        log.info("Resetting totals")
        self.pulse_count = 0
        self.total_volume = 0.0
        self.pulse_history.clear()
        self.flow_rate = 0.0

        # Persist immediately
        await self.set_tag("total_volume", 0.0)
        await self.set_tag("pulse_count", 0)

        self.ui.update_readings(0.0, 0.0, 0, "Totals Reset")
        self.ui.reset_totals.coerce(None)

    @ui.callback("calibrate")
    async def on_calibrate(self, new_value):
        """Start calibration mode."""
        log.info("Starting calibration mode")
        self.calibrating = True
        self.calibration_start_pulses = self.pulse_count

        # Show stop button, hide start button
        self.ui.stop_calibration.hidden = False
        self.ui.calibrate.hidden = True

        self.ui.status.update("Calibrating... (0 pulses)")
        self.ui.calibrate.coerce(None)

    @ui.callback("stop_calibration")
    async def on_stop_calibration(self, new_value):
        """Stop calibration and compute new calibration factor."""
        log.info("Stopping calibration")
        calibration_pulses = self.pulse_count - self.calibration_start_pulses
        self.calibrating = False

        # Hide stop button, show start button
        self.ui.stop_calibration.hidden = True
        self.ui.calibrate.hidden = False

        # Get the known volume from the UI parameter
        known_volume = self.ui.known_volume.current_value

        if known_volume and known_volume > 0 and calibration_pulses > 0:
            new_factor = calibration_pulses / known_volume
            self.pulses_per_litre = new_factor
            self.ui.calibration_factor.update(new_factor)
            self.ui.status.update(
                f"Calibration complete: {new_factor:.1f} pulses/L ({calibration_pulses} pulses / {known_volume:.2f} L)"
            )
            log.info(
                "Calibration result: %d pulses / %.2f L = %.1f pulses/L",
                calibration_pulses,
                known_volume,
                new_factor,
            )
        else:
            self.ui.status.update(
                f"Calibration ended: {calibration_pulses} pulses counted. Set 'Known Volume' and retry to compute factor."
            )
            log.warning(
                "Calibration ended without valid known volume (pulses=%d, volume=%s)",
                calibration_pulses,
                known_volume,
            )

        self.ui.stop_calibration.coerce(None)

    @ui.callback("calibration_factor")
    async def on_calibration_factor_change(self, new_value):
        """Update the active calibration factor when user changes it via UI."""
        if new_value is not None and new_value > 0:
            self.pulses_per_litre = new_value
            log.info("Calibration factor updated via UI: %.1f pulses/L", new_value)
