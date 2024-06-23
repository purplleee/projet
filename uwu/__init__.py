import base64
from flask import Flask
from flask_login import LoginManager
from config import DevelopmentConfig 
from .blueprints.employee.routes import employee_bp
from .blueprints.admin.routes import admin_bp
from .blueprints.super_admin.routes import super_admin_bp
from .blueprints.auth.routes import auth_bp
from .blueprints.common.errors import register_error_handlers
from uwu.models import Ticket, Materiel, User
from .database import db, init_app as init_db
import logging
from sqlalchemy.orm import joinedload

def create_app(config_class=DevelopmentConfig):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Configure session cookies
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SESSION_COOKIE_SECURE'] = True  
    app.config['SESSION_COOKIE_HTTPONLY'] = True  

    # Initialize database and migrations
    init_db(app)

    # Logging setup
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)

    # Flask-Login setup
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'  
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.options(joinedload(User.role)).get(user_id)

    # Blueprint registrations
    app.register_blueprint(employee_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(super_admin_bp, url_prefix='/super_admin')
    app.register_blueprint(auth_bp, url_prefix='/auth')

    # Error handlers
    register_error_handlers(app)

    # Custom Jinja2 filter for base64 encoding
    @app.template_filter('b64encode')
    def b64encode_filter(data):
        """Base64 encode filter."""
        return base64.b64encode(data).decode('utf-8')

    # Register the filter with your Flask application
    app.jinja_env.filters['b64encode'] = b64encode_filter

    return app
