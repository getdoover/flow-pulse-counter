import logging
from datetime import datetime, time, timedelta
import pytz

log = logging.getLogger()

def hour_to_datetime(hour: int, timezone: str = "UTC") -> datetime:
    """
    Convert an integer hour (0-23) in the specified timezone to a UTC datetime object.
    
    Args:
        hour: Integer representing hour of day (0-23) in the specified timezone
        timezone: Timezone string (e.g., "America/New_York", "Europe/London", "UTC")
        
    Returns:
        datetime: UTC datetime object for today if current time < target time, else tomorrow
        
    Raises:
        ValueError: If hour is not between 0 and 23
        ValueError: If timezone is invalid
    """
    if not 0 <= hour <= 23:
        raise ValueError("Hour must be between 0 and 23")
    
    try:
        tz = pytz.timezone(timezone)
    except pytz.exceptions.UnknownTimeZoneError:
        raise ValueError(f"Invalid timezone: {timezone}")
    
    # Get current time in the specified timezone
    now_tz = datetime.now(tz)
    target_time = time(hour=hour)
    
    # Create datetime for today with the target hour in the specified timezone
    today_target_tz = datetime.combine(now_tz.date(), target_time)
    today_target_tz = tz.localize(today_target_tz)
    
    # If current time is before target time today, use today
    # Otherwise, use tomorrow
    if now_tz.time() < target_time:
        target_datetime_tz = today_target_tz
    else:
        target_datetime_tz = today_target_tz + timedelta(days=1)
    
    # Convert to UTC
    return target_datetime_tz.astimezone(pytz.UTC)

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
    
