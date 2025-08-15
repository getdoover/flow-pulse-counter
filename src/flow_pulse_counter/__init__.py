import logging
from datetime import datetime
from pydoover.docker import run_app

from .application import FlowPulseCounterApplication
from .app_config import FlowPulseCounterConfig

class CustomFormatter(logging.Formatter):
    pass
        # def formatTime(self, record, datefmt=None):
        #     # Convert to 12-hour format with am/pm
        #     dt = datetime.fromtimestamp(record.created)
        #     # Handle macOS compatibility - remove leading zero manually
        #     hour = dt.strftime("%I")
        #     if hour.startswith('0'):
        #         hour = hour[1:]
        #     return f"{hour}:{dt.strftime('%M:%S,%f')[:-3]}{dt.strftime('%p').lower()}"
        
        # def format(self, record):
        #     # Format: time level: message (file:line)
        #     time_str = self.formatTime(record)
        #     return f"{time_str} | {record.levelname}: {record.getMessage()} ({record.filename}:{record.lineno})"

class ApplicationOnlyFilter(logging.Filter):
    """Filter to only show logs from the application module"""
    def filter(self, record):
        # Only show logs from flow_pulse_counter.application logger
        return record.name == "flow_pulse_counter.application"

def main():
    """
    Run the application.
    """
    # logging.getLogger("pydoover.ui.manager").setLevel(logging.DEBUG)
    
    run_app(FlowPulseCounterApplication(config=FlowPulseCounterConfig()))#, log_formatter=CustomFormatter())
