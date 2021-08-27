from flask_sqlalchemy import SQLAlchemy
import pickle

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String)
    password = db.Column(db.String)
    profil = db.Column(db.PickleType, default=None)

def username_query(key):
    return User.query.filter_by(username=key).all()

def get_user_by_id(id):
    return User.query.get(id)

def create_user(username, password):
    user = User(username=username, password=password)
    db.session.add(user)
    db.session.commit()

def check_user(username, password):
    check = User.query.filter_by(username=username, password=password)
    if check:
        return True, check.first().id
    else:
        return False, -1

def create_profile(user, profile):
    user.profil = pickle.dumps(profile)
    db.session.commit()

def get_profile(user):
    if user.profil == None:
        return -1
    else:
        return pickle.loads(user.profil)
