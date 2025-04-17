import sqlite3

def init_db():
    conn = sqlite3.connect('discord_bot.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS activities
                (id INTEGER PRIMARY KEY, user_id TEXT, sport TEXT, start TEXT, title TEXT,
                distance REAL, duration TEXT, description TEXT, rpe INTEGER''')
    conn.commit()
    conn.close()

def add_activity(activity):
    conn = sqlite3.connect('discord_bot.db')
    c = conn.cursor()
    c.execute('''INSERT INTO activities (user_id, sport, start, title, distance, duration, description, rpe)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', activity)