import os
from flask import Flask, render_template, request, session, url_for, redirect, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from passlib.hash import sha256_crypt
from wtforms import Form, BooleanField, StringField, PasswordField, validators
import gc
from functools import wraps
import re
from urllib2 import urlopen
import json
from geopy.geocoders import Nominatim
from geopy.distance import vincenty
from sqlalchemy import and_, func
from flask_paginate import Pagination
import requests
from werkzeug.utils import secure_filename

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(APP_ROOT, 'static/profiles')
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root@localhost/creme'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db = SQLAlchemy(app)


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column('id', db.Integer, primary_key=True)
    username = db.Column('username', db.Unicode)
    email = db.Column('email', db.Unicode)
    password = db.Column('password', db.Unicode)
    profile_picture = db.Column('profile_picture', db.Unicode)
    date_joined = db.Column('date_joined', db.DateTime)
    biz_owner = db.Column('biz_owner', db.Boolean)
    
    def __init__(self, username, email, password, profile_picture, date_joined, biz_owner):
        self.username = username
        self.email = email
        self.password = password
        self.profile_picture = profile_picture
        self.date_joined = date_joined
        self.biz_owner = biz_owner
        

        
class Shop(db.Model):
    __tablename__ = 'shops'
    
    id = db.Column('id', db.Integer, primary_key=True)
    brand = db.Column('brand', db.Unicode)
    address = db.Column('address', db.Unicode)
    city = db.Column('city', db.Unicode)
    state = db.Column('state', db.Unicode)
    postal = db.Column('postal', db.Unicode)
    country = db.Column('country', db.Unicode)
    lat = db.Column('lat', db.DECIMAL)
    lon = db.Column('lon', db.DECIMAL)
    owner = db.Column('owner', db.Integer)
    
    
    def __init__(self, brand, address, city, state, postal, country, lat, lon, owner):
        self.brand = brand
        self.address = address
        self.city = city
        self.state = state
        self.postal = postal
        self.country = country
        self.lat = lat
        self.lon = lon
        self.owner = owner

        
class Item(db.Model):
    __tablename__ = 'items'
    
    id = db.Column('id', db.Integer, primary_key=True)
    name = db.Column('name', db.Unicode)
    size = db.Column('size', db.Unicode)
    from_shop = db.Column('from_shop', db.Unicode)
    calories = db.Column('calories', db.Integer)
    protein = db.Column('protein', db.Integer)
    fat = db.Column('fat', db.Integer)
    
    def __init__(self, name, size, from_shop, calories, protein, fat):
        self.name = name
        self.size = size
        self.from_shop = from_shop
        self.calories = calories
        self.protein = protein
        self.fat = fat
        
        
class CheckIn(db.Model):
    __tablename__ = 'checkins'
    
    id = db.Column('id', db.Integer, primary_key=True)
    brand = db.Column('brand', db.Unicode)
    address = db.Column('address', db.Unicode)
    by_user = db.Column('by_user', db.Integer)
    date_checked = db.Column('date_checked', db.DateTime)
    
    
    def __init__(self, brand, address, by_user, date_checked):
        self.brand = brand
        self.address = address
        self.by_user = by_user
        self.date_checked = date_checked
        
        


        

    
def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash("You need to login first")
            return render_template('index.html', loginmodal_active=True)
    return wrap


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS
    
    
    
import creme.views