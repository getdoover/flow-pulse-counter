class TimeUnit():
    def __init__(self, name: str, seconds: int):
        self.name = name
        self.seconds = seconds
    def __str__(self):
        return self.name
    def __repr__(self):
        return f"TimeUnit({self.name}, {self.seconds})"
    
class VolumeUnit():
    def __init__(self, name: str, liters: float):
        self.name = name
        self.liters = liters
    def __str__(self):
        return self.name
    def __repr__(self):
        return f"VolumeUnit({self.name}, {self.liters})"
    
class FlowRateUnit():
    def __init__(self, volume_unit: VolumeUnit, time_unit: TimeUnit):
        self.volume_unit = volume_unit
        self.time_unit = time_unit
    def __str__(self):
        return f"{self.volume_unit.name}/{self.time_unit.name}"
    def __repr__(self):
        return f"RateUnit({self.volume_unit}, {self.time_unit})"
    
