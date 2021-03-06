from flask import Flask, render_template, request
from flask.ext.admin import Admin
from flask.ext.admin.contrib.sqlamodel import ModelView
from flask.ext.sqlalchemy import SQLAlchemy

import prepa
import os
import json

app = Flask(__name__)
admin = Admin(app)
app.config['SECRET_KEY'] = "@S\x8f\x0e\x1e\x04\xd0\xfa\x9a\xdf,oJ'\x1e\xe6\xc0\xaeZ'\x8am\xee."
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:////tmp/test.db')
db = SQLAlchemy(app)


class Area(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pueblo = db.Column(db.String(80))
    name = db.Column(db.String(80), unique=True)

    def to_dict(self):
        return {
            "id": self.id,
            "pueblo": self.pueblo,
            "name": self.name
        }

    def __repr__(self):
        return u'{}: {}'.format(self.pueblo, self.name)


class Incident(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    area = db.relationship('Area', backref=db.backref('incident_area', lazy='dynamic'))
    area_id = db.Column(db.Integer, db.ForeignKey('area.id'))
    status = db.Column(db.String(140))
    last_update = db.Column(db.DateTime)
    parent_id = db.Column(db.Integer, db.ForeignKey('incident.id'))

    def to_dict(self):
        return {
            "id": self.id,
            "area": self.area.to_dict(),
            "status": self.status,
            "last_update": self.last_update,
            "parent": self.parent_id.to_dict()
        }


class Subscriber(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    area = db.relationship('Area', backref=db.backref('subscriber_area', lazy='dynamic'))
    area_id = db.Column(db.Integer, db.ForeignKey('area.id'))
    email = db.Column(db.String(255))

    def to_dict(self):
        return {
            'id': self.id,
            'area': self.area.to_dict(),
            'email': self.email
        }


# Admin Model views
admin.add_view(ModelView(Area, db.session))
admin.add_view(ModelView(Incident, db.session))
admin.add_view(ModelView(Subscriber, db.session))


@app.route('/', methods=['Get'])
def getAllData():
    json_response = prepa.getAll()
    return json_response


@app.route('/municipios/<municipio>', methods=['Get'])
def getData(municipio):
    if municipio is None:
        return {'error': "municipio can't be empty"}
    else:
        json_response = prepa.getByCity(municipio)
        return json_response


@app.route('/historic', methods=['Get'])
def getAllHistoricData():
    # Retrive all historic data from database
    incidents = Incident.query.all()
    return json.dumps(incidents)


@app.route('/historic/municipios/<municipio>', methods=['Get'])
def getHistoricData(municipio):
    # Retrive historic data for a specified municipality from database
    incidentes = []

    for area in Area.query.filter_by(pueblo=municipio).all():
        for incident in Incident.query.filter_by(area=area).all():
            print incident.to_dict()
            incidentes.append(incident.to_dict())

    return json.dumps(incidentes)


@app.route('/subscribe', methods=['POST'])
def subscribe():
    try:
        data = json.loads(request.data)
    except (ValueError, KeyError, TypeError):
        return json.dumps({'error': 'Invalid data'})

    area = Area.query.filter_by(id=int(data['area_id'])).first()
    if not area:
        return json.dumps({'error': 'Area not found'})

    subscriber = Subscriber(email=data['email'], area=area)
    db.session.add(subscriber)
    db.session.commit()

    return json.dumps(subscriber.to_dict())


@app.route('/map')
def map():
    return render_template('index.html')


@app.route('/geotiles/pueblos.json')
def geotile():
    return render_template('pueblos.json')


if __name__ == "__main__":
    app.debug = True
    app.run()
