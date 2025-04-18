from datetime import datetime

from models import Sport, ActivityType


def format_distance(distance, sport: Sport):
    distance_str = f"{int(distance)}m" if sport == Sport.SWIM else f"{distance}km"
    return distance_str

def date_to_string(date):
    return date.isoformat()

def date_from_string(date_str):
    return datetime.strptime(date_str, "%Y-%m-%d").date()

def start_time_to_string(start_time):
    return start_time.strftime("%H:%M")

def start_time_from_string(start_time_str):
    return datetime.strptime(start_time_str, "%H:%M").time()

def is_type_appropriate(type: ActivityType, sport: Sport):
    has_sport = False
    has_spec_sport = False
    for sport_name in Sport:
        if sport_name.name.lower() in type.name.lower():
            has_sport = True
            if sport_name.name.lower() == sport.name.lower():
                has_spec_sport = True
    return has_spec_sport or not has_sport

def get_type_with_sport(type: ActivityType, sport: Sport, capitalize: bool):
    return type.value.capitalize().replace("Activity", sport.value.capitalize()) if capitalize else type.value.replace("activity", sport.value)
