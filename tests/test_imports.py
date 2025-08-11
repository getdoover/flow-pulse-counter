"""
Basic tests for an application.

This ensures all modules are importable and that the config is valid.
"""

def test_import_app():
    from flow_pulse_counter.application import FlowPulseCounterApplication
    assert FlowPulseCounterApplication

def test_config():
    from flow_pulse_counter.app_config import FlowPulseCounterConfig

    config = FlowPulseCounterConfig()
    assert isinstance(config.to_dict(), dict)

def test_ui():
    from flow_pulse_counter.app_ui import FlowPulseCounterUI
    assert FlowPulseCounterUI

def test_state():
    from flow_pulse_counter.app_state import FlowPulseCounterState
    assert FlowPulseCounterState