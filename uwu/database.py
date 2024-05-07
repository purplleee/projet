from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = None  # This will be initialized in the application factory

def init_app(app):
    db.init_app(app)
    global migrate
    migrate = Migrate(app, db)
