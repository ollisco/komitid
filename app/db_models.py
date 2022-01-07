"""
Created on 2020-08-27
                                          71559263e234458bbc45887f651c6e2
Purpose: Interacts with the database
Project: komitid
@author: ollejernstrom
"""

import sqlite3 as sql
import pickle
from os import path
from flask_login import UserMixin

ROOT = path.dirname(path.realpath(__file__))


class User(UserMixin):
    def __init__(self, data):
        if data:
            self.id = data[0]
            self.username = data[1]
            self.password = data[2]

            self.data = data[2:]

    def __repr__(self):
        return f'User#{self.id} {self.username}'


def get_session_user(user_id):
    userdata = get_user_by_id(user_id)
    userobj = User(userdata)
    return userobj


def create_user(uname, pword):
    connection = sql.connect(path.join(ROOT, 'database.db'))
    cursor = connection.cursor()
    cursor.execute('insert into users (Username, Password) values(?, ?)', (uname, pword))
    connection.commit()
    connection.close()


def db_query(key):
    connection = sql.connect(path.join(ROOT, 'database.db'))
    cursor = connection.cursor()
    cursor.execute(f'SELECT {key} from users')
    data = cursor.fetchall()
    return data


def get_data():
    connection = sql.connect(path.join(ROOT, 'database.db'))
    cursor = connection.cursor()
    cursor.execute('select * from users')
    data = cursor.fetchall()
    return data


def delete_user(uname):
    connection = sql.connect(path.join(ROOT, 'database.db'))
    cursor = connection.cursor()
    cursor.execute('delete from users where name=?', (uname,))
    connection.commit()
    connection.close()


def get_user_by_id(user_id):
    db_users = get_data()
    if db_users:
        for user in db_users:
            if user_id == user[0]:
                return user
    return False


def checkuser(try_uname, try_pword):
    valid_users = get_data()
    if valid_users:
        for user in valid_users:
            if try_uname == user[1] and try_pword == user[2]:
                return user[0]
    return False


def get_profile(user_id):
    try:
        with open(f'tokens/{user_id}.pkl', 'rb') as file:
            profile = pickle.load(file)
            return profile
    except (OSError, IOError) as e:
        print(e)
        return -1


def create_profile(user_id, profile):
    with open(f'tokens/{user_id}.pkl', 'wb') as file:
        pickle.dump(profile, file)

