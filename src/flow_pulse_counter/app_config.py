import enum
from pathlib import Path

from pydoover import config
from .utils import VolumeUnit, TimeUnit, FlowRateUnit

class TimeUnits(enum.Enum):
    SECONDS = TimeUnit("sec", 1)
    MINUTES = TimeUnit("min", 60)
    HOURS = TimeUnit("hr", 3600)
    DAYS = TimeUnit("day", 86400)
    
class VolumeUnits(enum.Enum):
    LITERS = VolumeUnit("L", 1.0)
    GALLONS = VolumeUnit("gal", 3.78541)
    CUBIC_METERS = VolumeUnit("m³", 1000.0)

def generate_flow_rate_units():
    members = {}
    for vol in VolumeUnits:
        for time in TimeUnits:
            name = f"{vol.value.name.upper()}_PER_{time.value.name.upper()}"
            members[name] = FlowRateUnit(vol.value, time.value)
    return enum.Enum("FlowRateUnits", members)

class FlowPulseCounterConfig(config.Schema):
    def __init__(self):  
        FlowRateUnits = generate_flow_rate_units()
        print(f"FlowRateUnits: {FlowRateUnits.__dict__}")
        
        self.litres_per_pulse = config.Number(
            "Litres per Pulse",
            default=0.001,
            description="The volume of fluid dispensed per pulse from the flow meter.",
        )
        
        self.flow_pulse_pin = config.Integer(
            "Flow Pulse Pin",
            default=0,
            description="The DI pin connected to the flow meter pulse output.",
        )
        
        self.flow_rate_units = config.Enum(
            "Flow Rate Units",
            choices=FlowRateUnits,
            default=FlowRateUnits.L_PER_MIN
        )
        
        self.reset_daily_total_time = config.Integer(
            "Reset Daily Total Time",
            default=0,
            minimum=0,
            maximum=23,
            description="The time (in hours) to reset the daily total. e.g. 1 for 1am, 8 for 8am, 19 for 7pm.",
        )
        
        self.enable_daily_total = config.Boolean(
            "Enable Daily Total",
            default=True,
            description="Enable the daily total in the UI",
        )
        
        self.show_totalizer = config.Boolean(
            "Totalizer Enabled",
            default=True,
            description="Enable the totalizer in the UI"
        )

        self.show_flow_rate = config.Boolean(
            "Show Flow Rate",
            default=True,
            description="Enable the flow rate in the UI"
        )

    @property
    def totalizer_enabled(self):
        return self.totalizer.value
    
    @property
    def pulse_pin(self):
        return self.flow_pulse_pin.value
    
    @property
    def l_per_pulse(self):
        return self.litres_per_pulse.value
    
    @property
    def daily_total_enabled(self):
        return self.enable_daily_total.value
    
    @property
    def volume_unit(self):
        return self.flow_rate_units.value.volume_unit
    
    @property
    def volume_unit_litres(self):
        return self.volume_unit.liters
    
    @property
    def time_unit(self):
        return self.flow_rate_units.value.time_unit
    
    @property
    def time_unit_seconds(self):
        return self.time_unit.seconds

def export():
    FlowPulseCounterConfig().export(Path(__file__).parents[2] / "doover_config.json", "flow_pulse_counter")

if __name__ == "__main__":
    export()
