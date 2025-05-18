import unittest
from datetime import timedelta, date, time
from models import Activity, Sport, ActivityType, Equipment, EquipmentType


class TestModels(unittest.TestCase):
    def test_activity_pace_run(self):
        a = Activity(user_id=1, sport=Sport.RUN, date=date.today(), start_time=time(8, 0), distance=10, duration=timedelta(minutes=50))
        self.assertAlmostEqual(a.pace, 5.0, places=2)

    def test_activity_pace_bike(self):
        a = Activity(user_id=1, sport=Sport.BIKE, date=date.today(), start_time=time(8, 0), distance=30, duration=timedelta(hours=1))
        self.assertAlmostEqual(a.pace, 30.0, places=2)

    def test_activity_pace_swim(self):
        a = Activity(user_id=1, sport=Sport.SWIM, date=date.today(), start_time=time(8, 0), distance=1500, duration=timedelta(minutes=30))
        # 30min for 1500m = 2min/100m
        self.assertAlmostEqual(a.pace, 2.0, places=2)

    def test_equipment_defaults(self):
        e = Equipment(user_id=1, name="Test", model="M", sport=Sport.RUN, type=EquipmentType.RUN_SHOES)
        self.assertEqual(e.distance_used, 0.0)
        self.assertFalse(e.retired)
