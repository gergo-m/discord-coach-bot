from datetime import datetime, timedelta, date

from models import Sport, ActivityType, EquipmentType


def format_distance(distance, sport: Sport):
    distance_str = f"{int(distance)}m" if sport == Sport.SWIM else f"{distance}km"
    return distance_str

def parse_timedelta(duration_str: str) -> timedelta:
    """Convert 'HH:MM:SS' string to timedelta"""
    if not duration_str:
        return timedelta()
    hours, minutes, seconds = map(int, duration_str.split(':'))
    return timedelta(hours=hours, minutes=minutes, seconds=seconds)

def safe_parse_timedelta(time_str: str) -> timedelta:
    try:
        if not time_str:
            return timedelta()
        parts = list(map(int, time_str.split(':')))
        if len(parts) != 3:
            return timedelta()
        return timedelta(hours=parts[0], minutes=parts[1], seconds=parts[2])
    except (ValueError, AttributeError):
        return timedelta()

def format_timedelta(td: timedelta) -> str:
    """Convert timedelta to 'HH:MM:SS' string"""
    total_seconds = int(td.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"

def format_duration(duration: timedelta) -> str:
    total_seconds = duration.total_seconds()
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = int(total_seconds % 60)
    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if seconds > 0:
        parts.append(f"{seconds}s")
    return " ".join(parts) if parts else "0m"

def date_to_string(date):
    return date.isoformat()

def date_from_string(date_str: str | None) -> date | None:
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None

def start_time_to_string(start_time):
    return start_time.strftime("%H:%M")

def start_time_from_string(start_time_str):
    return datetime.strptime(start_time_str, "%H:%M").time()

def is_type_appropriate(type: ActivityType, ch_sport: Sport):
    has_sport = False
    has_spec_sport = False
    for sport in Sport:
        if sport.name.lower() in type.name.lower():
            has_sport = True
            if sport.name.lower() == ch_sport.name.lower():
                has_spec_sport = True
    return has_spec_sport or not has_sport

def is_equipment_appropriate(type: EquipmentType, sport: Sport):
    matches_sport = False
    if sport.name.lower() in type.name.lower():
        matches_sport = True
    return matches_sport

def get_type_with_sport(type: ActivityType, sport: Sport, capitalize: bool):
    return type.value.capitalize().replace("Activity", sport.value.capitalize()) if capitalize else type.value.replace("activity", sport.value)
