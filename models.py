from dataclasses import dataclass, field
from datetime import timedelta, time, date, datetime
from enum import Enum
from typing import List

class Sport(Enum):
    ALL = "all"
    SWIM = "swim"
    BIKE = "bike"
    RUN = "run"

class ActivityType(Enum):
    TRAINING = "training"
    WORKOUT = "workout"
    INTERVAL = "interval activity"
    TEMPO = "tempo activity"
    LONG = "long activity"
    RACE = "activity race"
    COMMUTE = "activity commute"
    OPEN_WATER_SWIM = "open water activity"
    POOL_SWIM = "pool activity"

class EquipmentType(Enum):
    SWIM_GOGGLES = "goggles"
    SWIM_CAP = "cap"
    SWIMSUIT = "swimsuit"
    SWIM_WETSUIT = "wetsuit"
    BIKE_HELMET = "helmet"
    BIKE_SHOES = "bike shoes"
    ROAD_BIKE = "road bike"
    TT_BIKE = "TT bike"
    GRAVEL_BIKE = "gravel bike"
    MTB_BIKE = "mountain bike"
    RUN_SHOES = "running shoes"
    RUN_WATCH = "running watch"

class PaceUnit(Enum):
    SWIM = "/100m"
    BIKE = "km/h"
    RUN = "/km"


@dataclass
class Equipment:
    user_id: int
    name: str
    model: str
    sport: Sport
    type: EquipmentType
    distance_used: float = field(default=0.0)
    time_used: timedelta = field(default=timedelta(hours=0, minutes=0, seconds=0))
    times_used: int = field(default=0)
    retired: bool = field(default=False)
    id: int = field(default=None)
    bought_on: date = field(default=datetime.now().date())
    retired_on: date = field(default=datetime.now().date())
    added_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class Activity:
    # Core
    user_id: int
    sport: Sport
    date: date
    start_time: time

    # Basic info
    title: str = ""
    activity_type: ActivityType = field(default=ActivityType.TRAINING)
    distance: float = field(default=0.0)
    elevation: int = field(default=0)
    duration: timedelta = field(default=timedelta(hours=0, minutes=0, seconds=0))

    # Performance metrics
    avg_heart_rate: int = field(default=0)
    max_heart_rate: int = field(default=0)
    rpe: int = field(default=0)

    # Contextual
    description: str = field(default="")
    location: str = field(default="")
    weather: str = field(default="")
    feelings: str = field(default="")

    # Equipment tracking
    equipment_used: List[Equipment] = field(default_factory=list)

    # System
    id: int = field(default=None)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    # Calculated
    @property
    def pace(self) -> float:
        """ Returns pace/speed in sport-appropriate units:
        - Swim: min/100m
        - Bike: km/h
        - Run: min/km """
        total_seconds = self.duration.total_seconds()

        if self.sport == Sport.SWIM:
            if self.distance <= 0:
                return 0.0
            return total_seconds / (self.distance / 100) / 60 # min/100m
        elif self.sport == Sport.RUN:
            if self.distance <= 0:
                return 0.0
            return total_seconds / self.distance / 60 # min/km
        elif self.sport == Sport.BIKE:
            if total_seconds <= 0:
                return 0.0
            hours = total_seconds / 3600
            return self.distance / hours # km/h
        return 0.0