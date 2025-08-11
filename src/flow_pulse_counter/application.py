import logging
import time

from pydoover.docker import Application
from pydoover import ui
from datetime import datetime, timedelta

from .app_config import FlowPulseCounterConfig
from .app_ui import FlowPulseCounterUI
from .app_state import FlowPulseCounterState
from .flow_meter import FlowMeter

log = logging.getLogger()

class FlowPulseCounterApplication(Application):
    config: FlowPulseCounterConfig  # not necessary, but helps your IDE provide autocomplete!

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.started: float = time.time()
        self.ui: FlowPulseCounterUI = None
        self.state: FlowPulseCounterState = None
        
        self.loop_target_period = 0.5
        self.next_reset_time = None
        self.total_on_daily_reset = 0

    async def setup(self):
        self.ui = FlowPulseCounterUI(self.config)
        
        self.flow_meter = FlowMeter(
            plt_iface=self.platform_iface,
            l_per_pulse=self.config.l_per_pulse,
            volume_unit_litres=self.config.volume_unit_litres,
            time_unit_seconds=self.config.time_unit_seconds,
            pulse_pin=self.config.pulse_pin
        )
        
        hours = self.config.reset_daily_total_time
        tomorrow = datetime.now().date() + timedelta(days=1)
        self.daily_total_reset_time = datetime.combine(tomorrow, datetime.min.time()).replace(hour=hours)
        self.ui_manager.add_children(*self.ui.fetch())

    async def main_loop(self):
        cloud_count_total = self.ui.flow_total_count.current_value
        total_flow = (self.flow_meter.total_count + cloud_count_total) * self.config.l_per_pulse
        daily_total = total_flow - self.total_on_daily_reset
        
        
        if (
            self.ui.total_flow.current_value is not None 
            and self.ui.total_flow.current_value != total_flow
        ):
            total_flow = None
            daily_total = None

        if datetime.now() > self.daily_total_reset_time:
            self.total_on_daily_reset = total_flow
            self.daily_total_reset_time += timedelta(days=1)
            log.info(f"Daily total reset at {self.daily_total_reset_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
        self.ui.flow_total_count.coerce_value(total_flow)

        self.ui.update(
            current_flow_rate=self.flow_meter.flow_rate,
            daily_total=daily_total,
            total_flow=total_flow
        )

