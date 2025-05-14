from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Vehicle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    fuel_type = db.Column(db.String(50), nullable=False)
    norms = db.relationship('FuelNorm', backref='vehicle', lazy=True)

class FuelNorm(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    season = db.Column(db.String(10))  # 'лето' или 'зима'
    city = db.Column(db.Float)
    highway = db.Column(db.Float)
    region = db.Column(db.Float)
    idle = db.Column(db.Float)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicle.id'), nullable=False)
