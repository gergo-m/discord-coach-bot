import sqlite3
import unittest
import os
from datetime import timedelta, date, time, datetime
from models import Activity, Sport, ActivityType, Equipment, EquipmentType
from database import (
    init_db, add_activity, get_activities, delete_activity,
    add_equipment, get_equipments, delete_equipment
)


class TestDatabase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Use a test database
        cls.test_db = 'test_discord_bot.db'
        os.environ['DISCORD_BOT_DB'] = cls.test_db
        init_db()

    def setUp(self):
        # Clean up tables before each test
        conn = sqlite3.connect('discord_bot.db')
        c = conn.cursor()
        c.execute("DELETE FROM activity_equipment")
        c.execute("DELETE FROM activities")
        c.execute("DELETE FROM equipment")
        conn.commit()
        conn.close()

    def test_add_and_get_equipment(self):
        eq = Equipment(
            user_id=1, name="TestEq", model="ModelX", sport=Sport.RUN, type=EquipmentType.RUN_SHOES,
            distance_used=0.0, times_used=0, retired=False, bought_on=date.today(), added_at=datetime.now(), updated_at=datetime.now()
        )
        add_equipment(eq)
        eqs = get_equipments(1, Sport.RUN)
        self.assertTrue(any(e.name == "TestEq" for e in eqs))

    def test_add_and_get_activity(self):
        eq = Equipment(
            user_id=1, name="TestEq", model="ModelX", sport=Sport.RUN, type=EquipmentType.RUN_SHOES,
            distance_used=0.0, times_used=0, retired=False, bought_on=date.today(), added_at=datetime.now(), updated_at=datetime.now()
        )
        add_equipment(eq)
        eqs = get_equipments(1, Sport.RUN)
        eq = next(e for e in eqs if e.name == "TestEq")  # Find the one you just added
        a = Activity(
            user_id=1, sport=Sport.RUN, date=date.today(), start_time=time(7, 0),
            title="Morning Run", activity_type=ActivityType.WORKOUT, distance=10.0, elevation_gain=50,
            duration=timedelta(minutes=50), avg_heart_rate=150, max_heart_rate=160, rpe=7,
            equipment_used=[eq], created_at=datetime.now(), updated_at=datetime.now()
        )
        add_activity(a)
        acts = get_activities(1, Sport.RUN)
        self.assertTrue(any(act.title == "Morning Run" for act in acts))

    def test_delete_activity(self):
        eq = Equipment(
            user_id=1, name="TestEq", model="ModelX", sport=Sport.RUN, type=EquipmentType.RUN_SHOES,
            distance_used=0.0, times_used=0, retired=False, bought_on=date.today(), added_at=datetime.now(), updated_at=datetime.now()
        )
        add_equipment(eq)
        eqs = get_equipments(1, Sport.RUN)
        eq = next(e for e in eqs if e.name == "TestEq")  # Find the one you just added
        a = Activity(
            user_id=1, sport=Sport.RUN, date=date.today(), start_time=time(7, 0),
            title="Morning Run", activity_type=ActivityType.WORKOUT, distance=10.0, elevation_gain=50,
            duration=timedelta(minutes=50), avg_heart_rate=150, max_heart_rate=160, rpe=7,
            equipment_used=[eq], created_at=datetime.now(), updated_at=datetime.now()
        )
        add_activity(a)
        acts = get_activities(1, Sport.RUN)
        self.assertTrue(any(act.title == "Morning Run" for act in acts))
        # Delete
        for act in acts:
            if act.title == "Morning Run":
                delete_activity(act.id)
        acts = get_activities(1, Sport.RUN)
        self.assertFalse(any(act.title == "Morning Run" for act in acts))

    def test_delete_equipment(self):
        eq = Equipment(
            user_id=1, name="TestEq", model="ModelX", sport=Sport.RUN, type=EquipmentType.RUN_SHOES,
            distance_used=0.0, times_used=0, retired=False, bought_on=date.today(), added_at=datetime.now(), updated_at=datetime.now()
        )
        add_equipment(eq)
        eqs = get_equipments(1, Sport.RUN)
        self.assertTrue(any(e.name == "TestEq" for e in eqs))
        # Delete
        for e in eqs:
            if e.name == "TestEq":
                delete_equipment(e.id)
        eqs = get_equipments(1, Sport.RUN)
        self.assertFalse(any(e.name == "TestEq" for e in eqs))


if __name__ == "__main__":
    unittest.main()
