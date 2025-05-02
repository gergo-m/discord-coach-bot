import sqlite3
from typing import List

from models import Activity, Sport, ActivityType, Equipment, EquipmentType
from datetime import time, timedelta, datetime
from utils import start_time_to_string, date_to_string, date_from_string, start_time_from_string, format_timedelta, \
    parse_timedelta, safe_parse_timedelta


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
                    elevation_gain INTEGER,
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
                    model TEXT,
                    sport TEXT,
                    type TEXT,
                    distance_used REAL,
                    time_used TEXT,
                    times_used INTEGER,
                    retired BOOLEAN,
                    bought_on TEXT,
                    retired_on TEXT,
                    added_at TEXT,
                    updated_at TEXT
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
    try:
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
                            title, activity_type, distance, elevation_gain, duration,
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
                    activity.elevation_gain,
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
        activity_id = c.lastrowid
        for equipment in activity.equipment_used:
            c.execute('''INSERT INTO activity_equipment (activity_id, equipment_id)
                        VALUES (?, ?)''',
                      (activity_id, equipment.id))
            c.execute("SELECT time_used FROM equipment WHERE id = ?",
                      (equipment.id,))
            current_time_used_str = c.fetchone()[0] or "00:00:00"
            current_time_used = safe_parse_timedelta(current_time_used_str)
            updated_time_used = current_time_used + activity.duration
            updated_time_used_str = format_timedelta(updated_time_used)
            c.execute('''UPDATE equipment
                        SET distance_used = distance_used + ?,
                            time_used = ?,
                            times_used = times_used + 1,
                            updated_at = ?
                        WHERE id = ?''',
                      (activity.distance if activity.sport != Sport.SWIM else activity.distance / 1000,
                       updated_time_used_str,
                       date_to_string(datetime.now()),
                       equipment.id))
        conn.commit()
    finally:
        conn.close()

def get_activities(user_id=None, sport=None, start_date=None, end_date=None):
    conn = sqlite3.connect("discord_bot.db")
    try:
        c = conn.cursor()
        query = "SELECT * FROM activities WHERE 1=1"
        params = []

        if user_id is not None:
            query += " AND user_id = ?"
            params.append(user_id)
        if sport is not None:
            query += " AND sport = ?"
            params.append(sport.value)
        if start_date is not None:
            query += " AND date >= ?"
            params.append(date_to_string(start_date))
        if end_date is not None:
            query += " AND date <= ?"
            params.append(date_to_string(end_date))

        c.execute(query, params)
        rows = c.fetchall()
        # converting tuples to Activity objects
        activities = []
        # row indices:
        # 0:id, 1:user_id, 2:sport, 3:date, 4:start_time,
        # 5:title, 6:activity_type, 7:distance, 8:elevation_gain, 9:duration,
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
                elevation_gain=row[8],
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
            c.execute('''SELECT e.* FROM equipment e
                        JOIN activity_equipment ae ON e.id = ae.equipment_id
                        WHERE ae.activity_id = ?''',
                      (row[0],))
            equipment_rows = c.fetchall()
            equipments = []

            for eq_row in equipment_rows:
                time_used_val = safe_parse_timedelta(eq_row[7])
                bought_on_val = date_from_string(eq_row[10]) if eq_row[10] else None
                retired_on_val = date_from_string(eq_row[11]) if eq_row[11] else None
                added_at_val = datetime.fromisoformat(eq_row[12]) if eq_row[12] else None
                updated_at_val = datetime.fromisoformat(eq_row[13]) if eq_row[13] else None

                equipment = Equipment(
                    id=eq_row[0],
                    user_id=eq_row[1],
                    name=eq_row[2],
                    model=eq_row[3],
                    sport=Sport(eq_row[4]),
                    type=EquipmentType(eq_row[5]),
                    distance_used=eq_row[6],
                    time_used=time_used_val,
                    times_used=eq_row[8],
                    retired=bool(eq_row[9]),
                    bought_on=bought_on_val,
                    retired_on=retired_on_val,
                    added_at=added_at_val,
                    updated_at=updated_at_val
                )
                equipments.append(equipment)
                activity.equipment_used = equipments
            activities.append(activity)
        return activities
    finally:
        conn.close()

def delete_activity(activity_id: int):
    conn = sqlite3.connect("discord_bot.db")
    try:
        c = conn.cursor()

        # get activity data
        c.execute('''SELECT distance, duration, sport
                    FROM activities WHERE id = ?''',
                  (activity_id,))
        activity_row = c.fetchone()
        if not activity_row:
            return

        activity_distance, duration_str, sport_str = activity_row
        activity_duration = safe_parse_timedelta(duration_str)
        activity_sport = Sport(sport_str)

        # get linked equipment
        c.execute('''SELECT equipment.id
                    FROM activity_equipment
                    WHERE activity_id = ?''',
                  (activity_id,))
        equipment_ids = [row[0] for row in c.fetchall()]

        # update each equipment's stats
        for eq_id in equipment_ids:
            c.execute('''SELECT distance_used, time_used, times_used
                        FROM equipment
                        WHERE id = ?''',
                      (eq_id,))
            eq_row = c.fetchone()
            if not eq_row:
                continue

            current_distance, time_str, current_times = eq_row
            current_time = safe_parse_timedelta(time_str or "00:00:00")
            # adjust for swim (meters to km)
            adj_distance = (activity_distance / 1000 if activity_sport == Sport.SWIM else activity_distance)
            new_distance = max(current_distance - adj_distance, 0)
            new_time = max(current_time - activity_duration, timedelta(0))
            new_times = max(current_times - 1, 0)

            c.execute('''UPDATE equipment
                        SET distance_used = ?,
                            time_used = ?,
                            times_used = ?,
                            updated_at = ?
                        WHERE id = ?''',
                      (new_distance,
                       format_timedelta(new_time),
                       new_times,
                       date_to_string(datetime.now()),
                       eq_id))

        # delete from junction table
        c.execute('''DELETE FROM activity_equipment
                    WHERE activity_id = ?''',
                  (activity_id,))

        # delete the activity
        c.execute('''DELETE FROM activities
                    WHERE id = ?''',
                  (activity_id,))

        conn.commit()
    finally:
        conn.close()

def add_equipment(equipment: Equipment):
    conn = sqlite3.connect('discord_bot.db')
    try:
        c = conn.cursor()

        time_used_seconds = int(equipment.time_used.total_seconds())
        hours, remainder = divmod(time_used_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        time_used_str = f"{hours:02}:{minutes:02}:{seconds:02}"
        bought_on_str = date_to_string(equipment.bought_on)
        retired_on_str = date_to_string(equipment.retired_on)
        added_at_str = date_to_string(equipment.added_at)
        updated_at_str = date_to_string(equipment.updated_at)

        c.execute('''INSERT INTO equipment (
                            user_id, name, model, sport, type,
                            distance_used, time_used, times_used, retired,
                            bought_on, retired_on, added_at, updated_at
                        )
                    VALUES (?, ?, ?, ?, ?,
                            ?, ?, ?, ?,
                            ?, ?, ?, ?)''',
                (
                    equipment.user_id,
                    equipment.name,
                    equipment.model,
                    equipment.sport.value,
                    equipment.type.value,
                    equipment.distance_used,
                    time_used_str,
                    equipment.times_used,
                    equipment.retired,
                    bought_on_str,
                    retired_on_str,
                    added_at_str,
                    updated_at_str
                ))
        conn.commit()
    finally:
        conn.close()


def get_equipments(user_id: int, sport=None) -> List[Equipment] | None:
    conn = sqlite3.connect("discord_bot.db")
    try:
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
        equipments = []

        for row in rows:
            time_used_val = safe_parse_timedelta(row[7])
            bought_on_val = date_from_string(row[10]) if row[10] else None
            retired_on_val = date_from_string(row[11]) if row[11] else None
            added_at_val = datetime.fromisoformat(row[12]) if row[12] else None
            updated_at_val = datetime.fromisoformat(row[13]) if row[13] else None

            equipment = Equipment(
                id=row[0],
                user_id=row[1],
                name=row[2],
                model=row[3],
                sport=Sport(row[4]),
                type=EquipmentType(row[5]),
                distance_used=row[6],
                time_used=time_used_val,
                times_used=row[8],
                retired=bool(row[9]),
                bought_on=bought_on_val,
                retired_on=retired_on_val,
                added_at=added_at_val,
                updated_at=updated_at_val
            )
            equipments.append(equipment)

        return equipments
    finally:
        conn.close()


def get_equipment_by_id(equipment_id: int, user_id: int) -> Equipment | None:
    conn = sqlite3.connect('discord_bot.db')
    try:
        c = conn.cursor()
        c.execute("SELECT * FROM equipment WHERE id = ? AND user_id = ?",
                  (equipment_id, user_id))
        row = c.fetchone()
        if row:
            return Equipment(
                id=row[0],
                user_id=row[1],
                name=row[2],
                model=row[3],
                sport=Sport(row[4]),
                type=EquipmentType(row[5]),
                distance_used=row[6],
                time_used=safe_parse_timedelta(row[7]),
                times_used=row[8],
                retired=bool(row[9]),
                bought_on=date_from_string(row[10]),
                retired_on=date_from_string(row[11]),
                added_at=datetime.fromisoformat(row[12]),
                updated_at=datetime.fromisoformat(row[13])
            )
        return None
    finally:
        conn.close()

def delete_equipment(equipment_id: int):
    conn = sqlite3.connect("discord_bot.db")
    try:
        c = conn.cursor()

        # get linked activities
        c.execute('''SELECT activity_id
                    FROM activity_equipment
                    WHERE equipment_id = ?''',
                  (equipment_id,))
        activity_ids = [row[0] for row in c.fetchall()]

        # update activities' equipment links
        for act_id in activity_ids:
            # get activity details
            c.execute('''SELECT distance, duration, sport
                        FROM activities
                        WHERE id = ?''',
                      (act_id,))
            activity_row = c.fetchone()
            if not activity_row:
                continue

            activity_distance, duration_str, sport_str = activity_row
            activity_duration = safe_parse_timedelta(duration_str)
            activity_sport = Sport(sport_str)

            # adjust equipment stats
            c.execute('''SELECT distance_used, time_used, times_used
                        FROM equipment WHERE id = ?''',
                      (equipment_id,))
            eq_row = c.fetchone()
            if not eq_row:
                continue

            current_distance, time_str, current_times = eq_row
            current_time = safe_parse_timedelta(time_str or "00:00:00")
            # correct for swims
            adj_distance = (activity_distance / 1000 if activity_sport == Sport.SWIM else activity_distance)
            new_distance = max(current_distance - adj_distance, 0)
            new_time = max(current_time - activity_duration, timedelta(0))
            new_times = max(current_times - 1, 0)

            c.execute('''UPDATE equipment
                        SET distance_used = ?,
                            time_used = ?,
                            times_used = ?,
                            updated_at = ?
                        WHERE id = ?''',
                      (new_distance,
                       format_timedelta(new_time),
                       new_times,
                       date_to_string(datetime.now()),
                       equipment_id))

        # delete from junction table
        c.execute('''DELETE FROM activity_equipment
                    WHERE equipment_id = ?''',
                  (equipment_id,))

        # delete the equipment
        c.execute('''DELETE FROM equipment
                    WHERE id = ?''',
                  (equipment_id,))

        conn.commit()
    finally:
        conn.close()

def retire_equipment(equipment_id: int):
    conn = sqlite3.connect("discord_bot.db")
    try:
        c = conn.cursor()
        current_date = date_to_string(datetime.now().date())
        current_datetime = date_to_string(datetime.now())

        c.execute('''UPDATE equipment
                        SET retired = ?,
                            retired_on = ?,
                            updated_at = ?
                        WHERE id = ?''',
                  (True, current_date, current_datetime, equipment_id))
        conn.commit()
    finally:
        conn.close()
