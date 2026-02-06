from datetime import datetime

from pydoover import ui


class FlowPulseCounterUI:
    def __init__(self):
        # Variables (Display)
        self.flow_rate = ui.NumericVariable(
            "flow_rate",
            "Flow Rate",
            precision=2,
            unit="L/min",
            ranges=[
                ui.Range("No Flow", 0, 0.01, ui.Colour.grey),
                ui.Range("Normal", 0.01, 1000, ui.Colour.green),
            ],
        )

        self.total_volume = ui.NumericVariable(
            "total_volume",
            "Total Volume",
            precision=2,
            unit="L",
        )

        self.pulse_count = ui.NumericVariable(
            "pulse_count",
            "Pulse Count",
            precision=0,
        )

        self.status = ui.TextVariable("status", "Status")

        self.last_update = ui.DateTimeVariable("last_update", "Last Update")

        # Warning indicators
        self.low_flow_warning = ui.WarningIndicator(
            "low_flow_warning",
            "Low Flow Warning",
            hidden=True,
        )

        self.high_flow_warning = ui.WarningIndicator(
            "high_flow_warning",
            "High Flow Warning",
            hidden=True,
        )

        # Alert stream for push notifications
        self.notifications = ui.AlertStream()

        # Parameters (User Input)
        self.calibration_factor = ui.NumericParameter(
            "calibration_factor",
            "Calibration Factor (pulses/L)",
            precision=1,
        )

        self.known_volume = ui.NumericParameter(
            "known_volume",
            "Known Volume (L)",
            precision=2,
        )

        # Actions (Commands)
        self.reset_totals = ui.Action(
            "reset_totals",
            "Reset Totals",
            colour=ui.Colour.red,
            requires_confirm=True,
            position=1,
        )

        self.calibrate = ui.Action(
            "calibrate",
            "Start Calibration",
            colour=ui.Colour.blue,
            position=2,
        )

        self.stop_calibration = ui.Action(
            "stop_calibration",
            "Stop Calibration",
            colour=ui.Colour.blue,
            hidden=True,
            position=3,
        )

    def fetch(self):
        return (
            self.flow_rate,
            self.total_volume,
            self.pulse_count,
            self.status,
            self.last_update,
            self.low_flow_warning,
            self.high_flow_warning,
            self.notifications,
            self.calibration_factor,
            self.known_volume,
            self.reset_totals,
            self.calibrate,
            self.stop_calibration,
        )

    def update_readings(self, flow_rate, total_volume, pulse_count, status_text, unit="L/min"):
        """Update display variables with current readings."""
        self.flow_rate.update(flow_rate)
        self.flow_rate.unit = unit
        self.total_volume.update(total_volume)
        self.pulse_count.update(pulse_count)
        self.status.update(status_text)
        self.last_update.update(datetime.now())

    def set_flow_rate_ranges(self, low_threshold, high_threshold):
        """Update flow rate ranges based on configured thresholds."""
        ranges = [ui.Range("No Flow", 0, 0.01, ui.Colour.grey)]

        if low_threshold > 0 and high_threshold > 0:
            ranges.append(ui.Range("Low", 0.01, low_threshold, ui.Colour.yellow))
            ranges.append(ui.Range("Normal", low_threshold, high_threshold, ui.Colour.green))
            ranges.append(ui.Range("High", high_threshold, 99999, ui.Colour.red))
        elif low_threshold > 0:
            ranges.append(ui.Range("Low", 0.01, low_threshold, ui.Colour.yellow))
            ranges.append(ui.Range("Normal", low_threshold, 99999, ui.Colour.green))
        elif high_threshold > 0:
            ranges.append(ui.Range("Normal", 0.01, high_threshold, ui.Colour.green))
            ranges.append(ui.Range("High", high_threshold, 99999, ui.Colour.red))
        else:
            ranges.append(ui.Range("Normal", 0.01, 99999, ui.Colour.green))

        self.flow_rate.ranges = ranges
