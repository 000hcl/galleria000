from db import db
from flask import session, request
from werkzeug.security import check_password_hash, generate_password_hash

def check_validity_login(username, password):

    pwcheck = db.session.execute("SELECT password FROM users WHERE username=:username",{"username":username}).fetchone()
    if pwcheck == None:
        return False
    return check_password_hash(pwcheck[0],password)

def login():
    username = request.form["username"]
    password = request.form["password"]
    result = check_validity_login(username, password)
    if result:
        session["username"] = username
        user_id = get_id(username)
        session["user_id"] = user_id
    return result

def get_id(username):
    return db.session.execute("SELECT id FROM users WHERE username=:username",{"username":username}).fetchone()[0]

def logout():
    del session["username"]
    del session["user_id"]

def register(username, password):
    hash_value = generate_password_hash(password)
    db.session.execute("INSERT INTO users (username,password) VALUES (:username,:password)", {"username":username,"password":hash_value})
    db.session.commit()

def attempt_register():
    username = request.form["username"]
    password = request.form["password"]
    password2 = request.form["password2"]
    message = get_error_message(username, password, password2)
    if message == "":
        register(username, password)
    return message
    

def get_error_message(username, password, password2):
    if len(username)>12 or len(username)<2:
        return "Username must be between 2 and 12 characters long."
    if len(password)>24 or len(password)<8:
        return "Password must be between 8 and 24 characters long."
    if password != password2:
        return "Passwords don't match."
    userexists = db.session.execute("SELECT username FROM users WHERE username=:username",{"username":username}).fetchone()
    if userexists != None:
        return "Username already exists."
    return ""