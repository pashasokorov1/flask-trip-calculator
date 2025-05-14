import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Таблица пользователей
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL
)
''')


# Создание таблицы автомобилей
cursor.execute('''
CREATE TABLE IF NOT EXISTS vehicles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    number TEXT NOT NULL,
    model TEXT NOT NULL
)
''')

# Создание таблицы норм расхода топлива
cursor.execute('''
CREATE TABLE IF NOT EXISTS fuel_norms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_id INTEGER NOT NULL,
    season TEXT CHECK(season IN ('summer', 'winter')) NOT NULL,
    city REAL,
    highway REAL,
    region REAL,
    idle REAL,
    FOREIGN KEY(vehicle_id) REFERENCES vehicles(id)
)
''')

# Таблица для расчётов
cursor.execute('''
CREATE TABLE IF NOT EXISTS calculations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_id INTEGER,
    date TEXT,
    season TEXT,
    city_km REAL,
    highway_km REAL,
    region_km REAL,
    idle_hours REAL,
    fuel_start REAL,
    fuel_added REAL,
    fuel_end REAL,
    FOREIGN KEY(vehicle_id) REFERENCES vehicles(id)
)
''')

conn.commit()
conn.close()
