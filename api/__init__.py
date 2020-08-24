from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow


app = Flask(__name__)
app.config.from_object('api.config.TestingConfig')

db = SQLAlchemy(app)
ma = Marshmallow(app)
app.secret_key = 'some_random_key'

import api.routes.views
import api.models.db_creation

db.create_all()
