from pathlib import Path

from pydoover import config


class FlowPulseCounterConfig(config.Schema):
    def __init__(self):
        self.app_display_name = config.String(
            "App Display Name",
            description="Display name shown in the Doover UI",
            default="Flow Pulse Counter",
        )

        self.input_pin = config.Integer(
            "Input Pin",
            description="Digital input pin number connected to the flow meter pulse output",
            default=1,
        )

        self.pulses_per_litre = config.Number(
            "Pulses Per Litre",
            description="Calibration factor: number of pulses the meter produces per litre of flow",
            default=450.0,
        )

        self.flow_rate_unit = config.Enum(
            "Flow Rate Unit",
            description="Unit for flow rate display",
            choices=["L/min", "L/hr", "m3/hr"],
            default="L/min",
        )

        self.debounce_ms = config.Integer(
            "Debounce ms",
            description="Debounce time in milliseconds to filter electrical noise on the pulse input",
            default=50,
        )

        self.reporting_interval = config.Integer(
            "Reporting Interval",
            description="Interval in seconds between flow rate calculations (rolling window size)",
            default=10,
        )

        self.low_flow_threshold = config.Number(
            "Low Flow Threshold",
            description="Flow rate below this value triggers a low-flow warning (0 = disabled)",
            default=0.0,
        )

        self.high_flow_threshold = config.Number(
            "High Flow Threshold",
            description="Flow rate above this value triggers a high-flow warning (0 = disabled)",
            default=0.0,
        )


def export():
    FlowPulseCounterConfig().export(
        Path(__file__).parents[2] / "doover_config.json", "flow_pulse_counter"
    )


if __name__ == "__main__":
    export()
