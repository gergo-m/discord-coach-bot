import sqlite3
from typing import List

from models import Activity, Sport, ActivityType, Equipment, EquipmentType
from datetime import time, timedelta, datetime
from utils import start_time_to_string, date_to_string, date_from_string, start_time_from_string


def init_db():
    conn = sqlite3.connect('discord_bot.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS activities (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    sport TEXT,
                    date TEXT,
                    start_time TEXT,
                    title TEXT,
                    activity_type TEXT,
                    distance REAL,
                    elevation INTEGER,
                    duration TEXT,
                    avg_heart_rate INTEGER,
                    max_heart_rate INTEGER,
                    rpe INTEGER,
                    description TEXT,
                    location TEXT,
                    weather TEXT,
                    feelings TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS equipment (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    name TEXT,
                    sport TEXT,
                    type TEXT,
                    distance_used REAL,
                    time_used TEXT,
                    times_used INTEGER,
                    retired BOOLEAN
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS activity_equipment (
                    activity_id INTEGER,
                    equipment_id INTEGER,
                    PRIMARY KEY (activity_id, equipment_id),
                    FOREIGN KEY(activity_id) REFERENCES activities(id),
                    FOREIGN KEY(equipment_id) REFERENCES equipment(id)
                )''')
    conn.commit()
    conn.close()

def add_activity(activity: Activity):
    conn = sqlite3.connect('discord_bot.db')
    c = conn.cursor()

    # convert times to string
    date_str = date_to_string(activity.date)
    start_time_str = start_time_to_string(activity.start_time)
    duration_seconds = int(activity.duration.total_seconds())
    hours, remainder = divmod(duration_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    duration_str = f"{hours:02}:{minutes:02}:{seconds:02}"
    created_at_str = date_to_string(activity.created_at)
    updated_at_str = date_to_string(activity.updated_at)

    c.execute('''INSERT INTO activities (
                        user_id, sport, date, start_time,
                        title, activity_type, distance, elevation, duration,
                        avg_heart_rate, max_heart_rate, rpe,
                        description, location, weather, feelings,
                        created_at, updated_at
                    )
                VALUES (?, ?, ?, ?,
                        ?, ?, ?, ?, ?,
                        ?, ?, ?,
                        ?, ?, ?, ?,
                        ?, ?)''',
            (
                activity.user_id,
                activity.sport.value,
                date_str,
                start_time_str,
                activity.title,
                activity.activity_type.value,
                activity.distance,
                activity.elevation,
                duration_str,
                activity.avg_heart_rate,
                activity.max_heart_rate,
                activity.rpe,
                activity.description,
                activity.location,
                activity.weather,
                activity.feelings,
                created_at_str,
                updated_at_str
            ))
    conn.commit()
    conn.close()

def get_activities(user_id, sport=None):
    conn = sqlite3.connect("discord_bot.db")
    c = conn.cursor()
    if sport is not None:
        # sport is provided, filter by user_id and sport
        c.execute(
            "SELECT * FROM activities WHERE user_id = ? AND sport = ?",
            (user_id, sport.value)
        )
    else:
        # sport is not provided, filter only by user_id
        c.execute(
            "SELECT * FROM activities WHERE user_id = ?",
            (user_id,)
        )
    rows = c.fetchall()
    conn.close()

    # converting tuples to Activity objects
    activities = []
    # row indices:
    # 0:id, 1:user_id, 2:sport, 3:date, 4:start_time,
    # 5:title, 6:activity_type, 7:distance, 8:elevation, 9:duration,
    # 10:avg_hr, 11:max_hr, 12:rpe,
    # 13:description, 14:location, 15:weather, 16:feelings,
    # 17:created_at, 18:updated_at
    for row in rows:

        date_val = date_from_string(row[3])
        start_time_val = start_time_from_string(row[4])
        h, m, s = map(int, row[9].split(':'))
        duration_val = timedelta(hours=h, minutes=m, seconds=s)
        created_at_val = datetime.fromisoformat(row[17]) if row[17] else None
        updated_at_val = datetime.fromisoformat(row[18]) if row[18] else None

        activity = Activity(
            id=row[0],
            user_id=row[1],
            sport=Sport(row[2]),
            date=date_val,
            start_time=start_time_val,
            title=row[5],
            activity_type=ActivityType(row[6]),
            distance=row[7],
            elevation=row[8],
            duration=duration_val,
            avg_heart_rate=row[10],
            max_heart_rate=row[11],
            rpe=row[12],
            description=row[13],
            location=row[14],
            weather=row[15],
            feelings=row[16],
            created_at=created_at_val,
            updated_at=updated_at_val
        )
        activities.append(activity)

    return activities

def delete_activity(activity_id: int):
    conn = sqlite3.connect("discord_bot.db")
    c = conn.cursor()
    c.execute("DELETE FROM activities WHERE id = ?", (activity_id,))
    conn.commit()
    conn.close()

def add_equipment(equipment: Equipment):
    conn = sqlite3.connect('discord_bot.db')
    c = conn.cursor()

    time_used_seconds = int(equipment.time_used.total_seconds())
    hours, remainder = divmod(time_used_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    time_used_str = f"{hours:02}:{minutes:02}:{seconds:02}"

    c.execute('''INSERT INTO equipment (
                        user_id, name, sport, type, distance_used,
                        time_used, times_used, retired
                    )
                VALUES (?, ?, ?, ?, ?,
                        ?, ?, ?)''',
            (
                equipment.user_id,
                equipment.name,
                equipment.sport.value,
                equipment.type.value,
                equipment.distance_used,
                time_used_str,
                equipment.times_used,
                equipment.retired
            ))
    conn.commit()
    conn.close()


def get_equipments(user_id: int, sport=None) -> List[Equipment]:
    conn = sqlite3.connect("discord_bot.db")
    c = conn.cursor()
    if sport is not None:
        c.execute(
            "SELECT * FROM equipment WHERE user_id = ? AND sport = ?",
            (user_id, sport.value)
        )
    else:
        c.execute(
            "SELECT * FROM equipment WHERE user_id = ?",
            (user_id,)
        )
    rows = c.fetchall()
    conn.close()

    equipments = []

    for row in rows:
        h, m, s = map(int, row[6].split(':'))
        time_used_val = timedelta(hours=h, minutes=m, seconds=s)

        equipment = Equipment(
            id=row[0],
            user_id=row[1],
            name=row[2],
            sport=Sport(row[3]),
            type=EquipmentType(row[4]),
            distance_used=row[5],
            time_used=time_used_val,
            times_used=row[7],
            retired=bool(row[8])
        )
        equipments.append(equipment)

    return equipments
