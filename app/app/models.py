from datetime import datetime
from hashlib import md5
#from msilib.schema import tables
from time import time
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from app import app, db, login
from flask import url_for


class User(UserMixin, db.Model):
    __tablename__='user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    rezepte = db.relationship('Rezepteintrag', backref='user', lazy='dynamic')
    bewertungposts = db.relationship('Bewertung', backref='userbewertung', lazy='dynamic')
    

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
            digest, size)


    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            app.config['SECRET_KEY'], algorithm='HS256')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)

    def to_dict(self, include_email=False):
        data = {
        'id': self.id,
        'username': self.username,
        'rezepte_count': self.rezepte.count(),
        'bewertungen_count': self.bewertungposts.count(),
        '_links': {
        'self': url_for('get_user', id=self.id),
        'avatar': self.avatar(128)
            }
        }
        if include_email:
            data['email'] = self.email
        return data


    @staticmethod
    def to_collection():
        users = User.query.all()
        data = {'items': [item.to_dict() for item in users]}
        return(data)

  

@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class Rezepteintrag(db.Model):
    __tablename__='rezepteintrag'
    id = db.Column(db.Integer, primary_key=True)
    titel = db.Column(db.String(255))
    rezeptbeschreibung = db.Column(db.Text(3000))
    zutat = db.Column(db.Text(3000))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rezeptebewertung = db.relationship('Bewertung', backref='rezepte', lazy='dynamic')
    
    def __init__(self, titel, rezeptbeschreibung, zutat, user_id):
        self.titel = titel
        self.rezeptbeschreibung = rezeptbeschreibung
        self.zutat = zutat
        self.user_id = user_id

    def get_bewertungen(self):
        print(self.id)
        bewertungen = Bewertung.query.filter(Bewertung.rezepteintrag_id==self.id)
        return bewertungen
        
    @staticmethod
    def to_collection():
        resources = Rezepteintrag.query.all()
        data = {'items': [item.to_dict() for item in resources]}
        return(data)

class Bewertung(db.Model):
    __tablename__='bewertung'
    id = db.Column(db.Integer, primary_key=True)
    bewertung = db.Column(db.Text(1000))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    rezepteintrag_id = db.Column(db.Integer, db.ForeignKey('rezepteintrag.id'))
    
    def __init__(self, bewertung, user_id, rezepteintrag_id):
        self.bewertung = bewertung
        self.user_id = user_id
        self.rezepteintrag_id = rezepteintrag_id

    def get_username(self):
        u = User.query.get(self.user_id)
        return u.username
    
    def __repr__(self):
        return '<Bewertung {}>'.format(self.bewertung)

    def to_dict(self):
        data = {
            'id' : self.id,
            'url': url_for('get_posts', id=self.id, _external=True),
            'body': self.body,
            'timestamp': self.timestamp,
            'author': url_for('get_user', id=self.user_id, _external=True)
            }

        return data

    @staticmethod
    def to_collection():
        resources = Bewertung.query.all()
        data = {'items': [item.to_dict() for item in resources]}
        return(data)

    

