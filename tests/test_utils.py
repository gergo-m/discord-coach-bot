import unittest
from datetime import timedelta, date
from utils import (
    format_distance, parse_timedelta, safe_parse_timedelta, format_timedelta,
    format_duration, date_to_string, date_from_string, start_time_to_string,
    start_time_from_string, is_type_appropriate, is_equipment_appropriate,
    get_type_with_sport, format_pace_speed
)
from models import Sport, ActivityType, EquipmentType


class TestUtils(unittest.TestCase):
    def test_format_distance(self):
        self.assertEqual(format_distance(1500, Sport.SWIM), "1500m")
        self.assertEqual(format_distance(10, Sport.RUN), "10km")

    def test_parse_timedelta(self):
        self.assertEqual(parse_timedelta("01:02:03"), timedelta(hours=1, minutes=2, seconds=3))
        self.assertEqual(parse_timedelta(""), timedelta())

    def test_safe_parse_timedelta(self):
        self.assertEqual(safe_parse_timedelta("01:02:03"), timedelta(hours=1, minutes=2, seconds=3))
        self.assertEqual(safe_parse_timedelta("bad"), timedelta())

    def test_format_timedelta(self):
        self.assertEqual(format_timedelta(timedelta(hours=1, minutes=2, seconds=3)), "01:02:03")

    def test_format_duration(self):
        self.assertEqual(format_duration(timedelta(hours=1, minutes=2, seconds=3)), "1h 2m 3s")
        self.assertEqual(format_duration(timedelta(minutes=47, seconds=25)), "47m 25s")
        self.assertEqual(format_duration(timedelta()), "0m")

    def test_date_to_string_and_from_string(self):
        d = date(2024, 5, 18)
        s = date_to_string(d)
        self.assertEqual(date_from_string(s), d)
        self.assertIsNone(date_from_string("bad-date"))

    def test_start_time_to_string_and_from_string(self):
        from datetime import time
        t = time(7, 30)
        s = start_time_to_string(t)
        self.assertEqual(start_time_from_string(s), t)

    def test_is_type_appropriate(self):
        self.assertTrue(is_type_appropriate(ActivityType.WORKOUT, Sport.RUN))
        self.assertFalse(is_type_appropriate(ActivityType.POOL_SWIM, Sport.BIKE))

    def test_is_equipment_appropriate(self):
        self.assertTrue(is_equipment_appropriate(EquipmentType.SWIMSUIT, Sport.SWIM))
        self.assertFalse(is_equipment_appropriate(EquipmentType.BIKE_HELMET, Sport.RUN))

    def test_get_type_with_sport(self):
        self.assertEqual(get_type_with_sport(ActivityType.INTERVAL, Sport.RUN, False), "interval run")
        self.assertEqual(get_type_with_sport(ActivityType.INTERVAL, Sport.RUN, True), "Interval Run")

    def test_format_pace_speed(self):
        from models import Activity
        from datetime import timedelta, date, time
        a = Activity(user_id=1, sport=Sport.RUN, date=date.today(), start_time=time(7, 0), distance=10, duration=timedelta(minutes=50))
        self.assertIn("5:00", format_pace_speed(a))
