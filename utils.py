from datetime import datetime, timedelta

from models import Sport, ActivityType, EquipmentType


def format_distance(distance, sport: Sport):
    distance_str = f"{int(distance)}m" if sport == Sport.SWIM else f"{distance}km"
    return distance_str

def format_duration(duration: timedelta) -> str:
    total_seconds = duration.total_seconds()
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = duration.seconds
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

def date_from_string(date_str):
    return datetime.strptime(date_str, "%Y-%m-%d").date()

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
