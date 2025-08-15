from pydoover import ui
from .app_config import FlowPulseCounterConfig
class FlowPulseCounterUI:
    def __init__(self, config: FlowPulseCounterConfig):
        self.config = config
        
        # self.flow_total_count = ui.NumericParameter(
        #     "flow_total_count", 
        #     f"Total Flow ({self.config.volume_unit})", 
        #     precision=1,
        #     default=0,
        #     hidden=True
        # )
        
        self.current_flow_rate = ui.NumericVariable(
            "current_flow_rate", 
            f"Current Flow Rate ({self.config.flow_rate_units.value})", 
            precision=2,
            hidden=not self.config.show_flow_rate.value
        )
        
        self.daily_total = ui.NumericVariable(
            "daily_total", 
            f"Daily Total ({self.config.volume_unit})", 
            precision=1,
            hidden=not self.config.show_daily_total.value
        )
        
        self.yesterdays_total = ui.NumericVariable(
            "yesterdays_total", 
            f"Yesterday's Total ({self.config.volume_unit})", 
            precision=1,
            hidden=not self.config.show_daily_total.value
        )
        
        self.total_flow = ui.NumericVariable(
            "total_flow", 
            f"Total Flow ({self.config.volume_unit})", 
            precision=1,
            hidden=not self.config.totalizer_enabled
        )
        
    def fetch(self):
        return self.current_flow_rate, self.daily_total, self.total_flow, self.yesterdays_total #, self.flow_total_count

    def update(self, current_flow_rate: float = None , daily_total: float = None, total_flow: float = None):
        if daily_total is not None:
            self.daily_total.update(daily_total)
        if current_flow_rate is not None:
            self.current_flow_rate.update(current_flow_rate)
        if total_flow is not None:
            self.total_flow.update(total_flow)
