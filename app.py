from flask import Flask
#from db import db
from os import getenv

app = Flask(__name__)

app.secret_key = getenv("SECRET_KEY")

import routes
