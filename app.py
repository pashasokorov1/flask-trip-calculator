from flask import Flask, render_template
from config import Config
from models import db, Vehicle, FuelNorm
import sqlite3
from flask import render_template, request, redirect, url_for


def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

# @app.route('/')
# def index():
#     return render_template('index.html')

@app.route('/')
def index():
    vehicles = Vehicle.query.all()
    return render_template('index.html', vehicles=vehicles)
@app.route('/add_vehicle', methods=['GET', 'POST'])
def add_vehicle():
    if request.method == 'POST':
        number = request.form['number']
        model = request.form['model']

        # Летние нормы
        summer = {
            'city': request.form['summer_city'],
            'highway': request.form['summer_highway'],
            'region': request.form['summer_region'],
            'idle': request.form['summer_idle']
        }

        # Зимние нормы
        winter = {
            'city': request.form['winter_city'],
            'highway': request.form['winter_highway'],
            'region': request.form['winter_region'],
            'idle': request.form['winter_idle']
        }

        conn = get_db_connection()
        cursor = conn.cursor()

        # Добавляем авто
        cursor.execute("INSERT INTO vehicles (number, model) VALUES (?, ?)", (number, model))
        vehicle_id = cursor.lastrowid

        # Добавляем нормы
        cursor.execute('''INSERT INTO fuel_norms (vehicle_id, season, city, highway, region, idle)
                          VALUES (?, 'summer', ?, ?, ?, ?)''',
                       (vehicle_id, summer['city'], summer['highway'], summer['region'], summer['idle']))
        cursor.execute('''INSERT INTO fuel_norms (vehicle_id, season, city, highway, region, idle)
                          VALUES (?, 'winter', ?, ?, ?, ?)''',
                       (vehicle_id, winter['city'], winter['highway'], winter['region'], winter['idle']))

        conn.commit()
        conn.close()
        return redirect(url_for('add_vehicle'))

    return render_template('add_vehicle.html')


@app.route('/vehicles')
def vehicles():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM vehicles')
    vehicles_list = cursor.fetchall()

    vehicles = []
    for vehicle in vehicles_list:
        vehicle_id = vehicle['id']
        cursor.execute("SELECT * FROM fuel_norms WHERE vehicle_id = ?", (vehicle_id,))
        norms = cursor.fetchall()

        data = {
            'id': vehicle_id,
            'number': vehicle['number'],
            'model': vehicle['model'],
        }

        for norm in norms:
            prefix = 'summer_' if norm['season'] == 'summer' else 'winter_'
            data[prefix + 'city'] = norm['city']
            data[prefix + 'highway'] = norm['highway']
            data[prefix + 'region'] = norm['region']
            data[prefix + 'idle'] = norm['idle']

        vehicles.append(data)

    conn.close()
    return render_template('vehicles.html', vehicles=vehicles)

@app.route('/calculate', methods=['GET', 'POST'])
def calculate():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, number, model FROM vehicles")
    vehicles = cursor.fetchall()

    if request.method == 'POST':
        vehicle_id = request.form['vehicle_id']
        season = request.form['season']
        city_km = float(request.form.get('city_km', 0))
        highway_km = float(request.form.get('highway_km', 0))
        region_km = float(request.form.get('region_km', 0))
        idle_hours = float(request.form.get('idle_hours', 0))
        fuel_start = float(request.form.get('fuel_start', 0))
        fuel_added = float(request.form.get('fuel_added', 0))
        odometer_start = float(request.form.get('odometer_start', 0))

        # Получим нормы расхода
        cursor.execute('''
            SELECT city, highway, region, idle FROM fuel_norms
            WHERE vehicle_id = ? AND season = ?
        ''', (vehicle_id, season))
        norm = cursor.fetchone()

        if norm:
            city_norm = norm['city']
            highway_norm = norm['highway']
            region_norm = norm['region']
            idle_norm = norm['idle']

            # Расчет
            city_fuel = city_km * (city_norm / 100)
            highway_fuel = highway_km * (highway_norm / 100)
            region_fuel = region_km * (region_norm / 100)
            idle_fuel = idle_hours * idle_norm

            total_fuel_used = city_fuel + highway_fuel + region_fuel + idle_fuel
            fuel_end = fuel_start + fuel_added - total_fuel_used
            odometer_end = odometer_start + city_km + highway_km + region_km

            # Сохраняем расчет в БД
            cursor.execute('''
                INSERT INTO calculations (
                    vehicle_id, date, season,
                    city_km, highway_km, region_km, idle_hours,
                    fuel_start, fuel_added, fuel_end
                )
                VALUES (?, date('now'), ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                vehicle_id, season,
                city_km, highway_km, region_km, idle_hours,
                fuel_start, fuel_added, fuel_end
            ))
            conn.commit()

            result = {
                'odometer_start': odometer_start,
                'odometer_end': odometer_end,
                'city_fuel': round(city_fuel, 2),
                'highway_fuel': round(highway_fuel, 2),
                'region_fuel': round(region_fuel, 2),
                'idle_fuel': round(idle_fuel, 2),
                'total_fuel_used': round(total_fuel_used, 2),
                'fuel_start': fuel_start,
                'fuel_added': fuel_added,
                'fuel_end': round(fuel_end, 2)
            }

            return render_template('result.html', result=result)

        else:
            ('Нормы расхода для выбранного автомобиля и сезона не найдены.', 'error')

    conn.close()
    return render_template('calculate.html', vehicles=vehicles)

@app.route('/calculate_month', methods=['GET', 'POST'])
def calculate_month():
    conn = get_db_connection()
    vehicles = conn.execute('SELECT * FROM vehicles').fetchall()
    conn.close()

    if request.method == 'POST':
        vehicle_id = request.form['vehicle_id']
        
        # Первый сезон
        season1 = request.form['season1']
        city_km1 = float(request.form['city_km1'])
        highway_km1 = float(request.form['highway_km1'])
        region_km1 = float(request.form['region_km1'])
        idle_hours1 = float(request.form['idle_hours1'])

        # Второй сезон
        season2 = request.form['season2']
        city_km2 = float(request.form['city_km2'])
        highway_km2 = float(request.form['highway_km2'])
        region_km2 = float(request.form['region_km2'])
        idle_hours2 = float(request.form['idle_hours2'])

        # Топливо
        fuel_start = float(request.form['fuel_start'])
        fuel_added = float(request.form['fuel_added'])

        # Получаем нормы
        conn = get_db_connection()
        norm1 = conn.execute('SELECT * FROM fuel_norms WHERE vehicle_id = ? AND season = ?', (vehicle_id, season1)).fetchone()
        norm2 = conn.execute('SELECT * FROM fuel_norms WHERE vehicle_id = ? AND season = ?', (vehicle_id, season2)).fetchone()
        conn.close()

        if not norm1 or not norm2:
            Flask('Нормы для одного из сезонов не найдены!', 'danger')
            return redirect(url_for('calculate_month'))

        # Расчёт по первому сезону
        total1 = (
            region_km1 * (norm1['region'] / 100) +
            highway_km1 * (norm1['highway'] / 100) +
            city_km1 * (norm1['city'] / 100) +
            idle_hours1 * norm1['idle']
        )

        # Расчёт по второму сезону
        total2 = (
            region_km2 * (norm2['region'] / 100) +
            highway_km2 * (norm2['highway'] / 100) +
            city_km2 * (norm2['city'] / 100) +
            idle_hours2 * norm2['idle']
        )

        total_fuel = total1 + total2
        fuel_end = fuel_start + fuel_added - total_fuel

        return render_template(
            'result_month.html',
            vehicle_id=vehicle_id,
            total1=round(total1, 2),
            total2=round(total2, 2),
            total_fuel=round(total_fuel, 2),
            fuel_end=round(fuel_end, 2),
            season1=season1,
            season2=season2,
            fuel_start=fuel_start,
            fuel_added=fuel_added
        )

    return render_template('calculate_month.html', vehicles=vehicles)

@app.route('/add_norm', methods=['GET', 'POST'])
def add_norm():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute("SELECT id, number, model FROM vehicles")
    vehicles = cursor.fetchall()

    message = None

    if request.method == 'POST':
        vehicle_id = request.form['vehicle_id']
        season = request.form['season']
        city = float(request.form['city'])
        highway = float(request.form['highway'])
        region = float(request.form['region'])
        idle = float(request.form['idle'])

        # Проверяем, есть ли уже нормы для этого авто и сезона
        cursor.execute("""
            SELECT id FROM fuel_norms WHERE vehicle_id = ? AND season = ?
        """, (vehicle_id, season))
        existing = cursor.fetchone()

        if existing:
            # Обновляем существующие нормы
            cursor.execute("""
                UPDATE fuel_norms SET city = ?, highway = ?, region = ?, idle = ?
                WHERE vehicle_id = ? AND season = ?
            """, (city, highway, region, idle, vehicle_id, season))
            message = "Нормы успешно обновлены."
        else:
            # Добавляем новые нормы
            cursor.execute("""
                INSERT INTO fuel_norms (vehicle_id, season, city, highway, region, idle)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (vehicle_id, season, city, highway, region, idle))
            message = "Нормы успешно добавлены."

        conn.commit()

    conn.close()
    return render_template('add_norm.html', vehicles=vehicles, message=message)

@app.route('/reports')
def reports():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT r.id, v.number, v.model, r.date, r.season,
               r.city_km, r.highway_km, r.region_km, r.idle_hours,
               r.fuel_start, r.fuel_added, r.fuel_end
        FROM calculations r
        JOIN vehicles v ON r.vehicle_id = v.id
        ORDER BY r.date DESC
    ''')
    rows = cursor.fetchall()
    conn.close()

    # Добавим расчёт потреблённого топлива
    reports_data = []
    for row in rows:
        (
            report_id, number, model, date, season,
            city_km, highway_km, region_km, idle_hours,
            fuel_start, fuel_added, fuel_end
        ) = row

        # Общий пробег
        total_km = city_km + highway_km + region_km

        fuel_used = (fuel_start + fuel_added) - fuel_end

        reports_data.append({
            'id': report_id,
            'vehicle': f'{number} - {model}',
            'date': date,
            'season': 'Лето' if season == 'summer' else 'Зима',
            'city_km': city_km,
            'highway_km': highway_km,
            'region_km': region_km,
            'idle_hours': idle_hours,
            'fuel_start': fuel_start,
            'fuel_added': fuel_added,
            'fuel_end': fuel_end,
            'fuel_used': round(fuel_used, 2),
            'total_km': total_km
        })

    return render_template('reports.html', reports=reports_data)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
