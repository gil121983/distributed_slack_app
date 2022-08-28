from flask import Flask
from flask_session import Session

flask_app = Flask(__name__)
flask_app.config["SESSION_PERMANENT"] = False
flask_app.config["SESSION_TYPE"] = "filesystem"
Session(flask_app)

from app import views
