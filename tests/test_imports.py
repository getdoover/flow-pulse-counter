"""
Basic tests for the Flow Pulse Counter application.

This ensures all modules are importable and that the config is valid.
"""


def test_import_app():
    from flow_pulse_counter.application import FlowPulseCounterApplication
    assert FlowPulseCounterApplication


def test_config():
    from flow_pulse_counter.app_config import FlowPulseCounterConfig

    config = FlowPulseCounterConfig()
    schema = config.to_dict()
    assert isinstance(schema, dict)
    props = schema.get("properties", {})
    assert "input_pin" in props
    assert "pulses_per_litre" in props
    assert "flow_rate_unit" in props


def test_ui():
    from flow_pulse_counter.app_ui import FlowPulseCounterUI

    ui = FlowPulseCounterUI()
    components = ui.fetch()
    assert len(components) > 0


def test_ui_has_required_components():
    from flow_pulse_counter.app_ui import FlowPulseCounterUI

    ui = FlowPulseCounterUI()
    assert ui.flow_rate is not None
    assert ui.total_volume is not None
    assert ui.pulse_count is not None
    assert ui.status is not None
    assert ui.calibration_factor is not None
    assert ui.reset_totals is not None
    assert ui.calibrate is not None
    assert ui.stop_calibration is not None
