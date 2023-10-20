import sqlite3

conn = sqlite3.connect('./data.sqlite')
cur = conn.cursor()

cur.execute('''
CREATE TABLE IF NOT EXISTS marker (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    x REAL NOT NULL,
    y REAL NOT NULL,
    detection TEXT,
    timestamp TEXT,
    videos TEXT,
    congestion REAL,
    lineLength REAL
)
''')

cur.execute('''
CREATE TABLE IF NOT EXISTS polyline (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    linename TEXT NOT NULL,
    points TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    videoname TEXT,
    congestion REAL,
    lineLength REAL
)
''')