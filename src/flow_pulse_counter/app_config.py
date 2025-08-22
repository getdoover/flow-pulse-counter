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
    CUBIC_METERS = VolumeUnit("m^3", 1000.0)
    
class EdgeMode(enum.Enum):
    RISING = "rising"
    FALLING = "falling"
    
class Timezone(enum.Enum):
    SYDNEY = "Australia/Sydney"
    BRISBANE = "Australia/Brisbane"
    MELBOURNE = "Australia/Melbourne"
    PERTH = "Australia/Perth"
    ADELAIDE = "Australia/Adelaide"
    DARWIN = "Australia/Darwin"
    HOBART = "Australia/Hobart"
    
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
        
        self.litres_per_pulse = config.Number(
            "Litres per Pulse",
            default=1.1,
            description="The Litres of fluid dispensed per pulse from the flow meter.",
        )
        
        self.pulse_edge_mode = config.Enum(
            "Pulse Edge Mode",
            choices=EdgeMode,
            default=EdgeMode.RISING,
            description="The edge mode for the flow meter pulse pin.",
        )
        
        self.flow_pulse_pin = config.Integer(
            "Flow Pulse Pin",
            default=0,
            description="The DI pin connected to the flow meter pulse output.",
        )
        
        self.flow_rate_units = config.Enum(
            "Flow Rate Units",
            choices=FlowRateUnits,
            default=FlowRateUnits.L_PER_MIN,
            description="The units to use for flow rate measurement on the App.",
            hidden=False
        )
        
        self.reset_daily_total_time = config.Integer(
            "Reset Daily Total Time",
            default=0,
            minimum=0,
            maximum=23,
            description="The time (in hours) to reset the daily total. e.g. 1 for 1am, 8 for 8am, 19 for 7pm etc",
        )
        
        self.reset_time_timezone = config.Enum(
            "Time Timezone",
            choices=Timezone,
            default=Timezone.BRISBANE,
            description="The timezone to use for the reset time.",
        )
        
        self.show_daily_total = config.Boolean(
            "Show Daily Total",
            default=True,
            description="Show the daily total in the UI",
        )
        
        self.show_totalizer = config.Boolean(
            "Show Totalizer",
            default=True,
            description="Show the totalizer in the UI"
        )

        self.show_flow_rate = config.Boolean(
            "Show Flow Rate",
            default=False,
            description="Enable the flow rate in the UI",
            hidden=False
        )
        
        self.flow_rate_sensitivity = config.Number(
            "Flow Rate Sensitivity",
            default=0.2,
            description="The process variance of the flow rate measurement",
            hidden=False
        )
        
        self.measurement_variance = config.Number(
            "Measurement Variance",
            default=25.0,
            description="The measurement variance of the flow rate measurement",
            hidden=False
        )
        
        self.debug_mode = config.Boolean(
            "Debug Mode",
            default=False,
            description="Enable debug mode",
            hidden=True
        )
        
        self.flatten_ui = config.Boolean(
            "Flatten UI",
            default=True,
            description="Flatten the ui in the App.",
            hidden=False
        )

    @property
    def totalizer_enabled(self):
        return self.show_totalizer.value
    
    @property
    def pulse_pin(self):
        return self.flow_pulse_pin.value
    
    @property
    def l_per_pulse(self):
        return self.litres_per_pulse.value
    
    @property
    def daily_total_enabled(self):
        return self.show_daily_total.value

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
