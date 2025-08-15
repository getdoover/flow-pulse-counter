import logging
import time
import asyncio

from typing import Any

from pydoover.docker import Application
from pydoover import ui
from datetime import datetime, timedelta

from .app_config import FlowPulseCounterConfig
from .app_ui import FlowPulseCounterUI
from .app_state import FlowPulseCounterState
from .flow_meter import FlowMeter
from .utils import hour_to_datetime

log = logging.getLogger("flow_pulse_counter.application")

class FlowPulseCounterApplication(Application):
    config: FlowPulseCounterConfig  # not necessary, but helps your IDE provide autocomplete!

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.started: float = time.time()
        self.ui: FlowPulseCounterUI = None
        self.state: FlowPulseCounterState = None
        
        self.loop_target_period = 0.5
        self.next_reset_time = None
        self.total_count_on_daily_reset = 0
        
    async def setup(self):
        self.ui = FlowPulseCounterUI(self.config) 
        self.ui_manager.add_children(*self.ui.fetch())
        
        self.daily_count = self.get_tag("daily_total")
        if self.daily_count is None:
            await self.set_tag("daily_total", 0)
            self.daily_count = 0
        
        _daily_total_reset_time = self.get_tag("daily_total_reset_time")
        if _daily_total_reset_time is None:
            self.daily_total_reset_time = hour_to_datetime(
                self.config.reset_daily_total_time.value,
                self.config.reset_time_timezone.value
            )
        else:
            # for testing:
            # self.daily_total_reset_time = datetime.fromisoformat(_daily_total_reset_time)
            
            config_daily_total_reset_time = hour_to_datetime(
                self.config.reset_daily_total_time.value,
                self.config.reset_time_timezone.value
            )
            tag_daily_total_reset_time = datetime.fromisoformat(_daily_total_reset_time)
            self.daily_total_reset_time = datetime.combine(tag_daily_total_reset_time, config_daily_total_reset_time.time())    
        await self.set_tag("daily_total_reset_time", self.daily_total_reset_time.isoformat())
        log.info(f"self.daily_total_reset_time: {self.daily_total_reset_time}")
        
        self.tag_count_on_start = self.get_tag("total_count")
        log.info(f"self.tag_count_on_start: {self.tag_count_on_start}")
        if self.tag_count_on_start is None:
            await self.set_tag("total_count", 0)
            self.tag_count_on_start = 0
        
        self.yesterdays_count = self.get_tag("yesterdays_count")
        if self.yesterdays_count:
            self.ui.yesterdays_total.update(self.yesterdays_count*self.config.l_per_pulse)
        
        target_rate = self.get_tag("target_flow_rate")
        if target_rate is None:
            await self.set_tag("target_flow_rate", 0)
            target_rate = 0
        
        self.flow_meter = FlowMeter(
            plt_iface=self.platform_iface,
            l_per_pulse=self.config.l_per_pulse,
            volume_unit_litres=self.config.volume_unit_litres,
            time_unit_seconds=self.config.time_unit_seconds,
            pulse_pin=self.config.pulse_pin,
            pulse_edge_mode=self.config.pulse_edge_mode.value,
            init_estimate=target_rate
        )
        
        self.flow_meter.is_pumping = True

    async def main_loop(self):
        total_flow_count = (self.flow_meter.total_count + self.tag_count_on_start)
        tag_count = self.get_tag("total_count")

        if datetime.now() > self.daily_total_reset_time:
            #update the yesterdays count
            self.yesterdays_count = self.daily_count
            
            #reset the daily count
            self.daily_count = 0
            
            await self.set_tag("yesterdays_count", self.yesterdays_count)
            self.ui.yesterdays_total.update(self.yesterdays_count*self.config.l_per_pulse)
            
            #update the daily total reset time
            self.daily_total_reset_time += timedelta(days=1)
            await self.set_tag("daily_total_reset_time", self.daily_total_reset_time.isoformat())
            log.info(f"Daily total reset at {self.daily_total_reset_time.strftime('%Y-%m-%d %H:%M:%S')}")        
        # If the total flow count hasn't changed, we don't need to update the UI
        if (
            tag_count == total_flow_count
        ):
            total_flow = None
            daily_total = None
        else:
            self.daily_count += (total_flow_count - tag_count)
            total_flow = total_flow_count * self.config.l_per_pulse
            daily_total = self.daily_count * self.config.l_per_pulse
            
            log.info(f"Updating UI; total_flow: {total_flow}, daily_total: {daily_total}, current_flow_rate: {self.flow_meter.flow_rate}")
            await self.set_tag("total_count", total_flow_count)
            await self.set_tag("daily_total", self.daily_count)
            await self.set_tag("current_flow_rate", self.flow_meter.flow_rate)
            
        self.ui.update(
            current_flow_rate=self.flow_meter.flow_rate,
            daily_total=daily_total,
            total_flow=total_flow
        )