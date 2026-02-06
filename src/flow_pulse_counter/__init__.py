from pydoover.docker import run_app

from .application import FlowPulseCounterApplication
from .app_config import FlowPulseCounterConfig


def main():
    """Run the Flow Pulse Counter application."""
    run_app(FlowPulseCounterApplication(config=FlowPulseCounterConfig()))
