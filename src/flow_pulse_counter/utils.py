import logging
from datetime import datetime, time, timedelta

log = logging.getLogger()

def hour_to_datetime(hour: int) -> datetime:
    """
    Convert an integer hour (0-23) to a datetime object.
    
    Args:
        hour: Integer representing hour of day (0-23)
        
    Returns:
        datetime: Datetime object for today if current time < target time, else tomorrow
        
    Raises:
        ValueError: If hour is not between 0 and 23
    """
    if not 0 <= hour <= 23:
        raise ValueError("Hour must be between 0 and 23")
    
    now = datetime.now()
    target_time = time(hour=hour)
    
    # Create datetime for today with the target hour
    today_target = datetime.combine(now.date(), target_time)
    
    # If current time is before target time today, use today
    # Otherwise, use tomorrow
    if now.time() < target_time:
        return today_target
    else:
        return today_target + timedelta(days=1)

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
    
