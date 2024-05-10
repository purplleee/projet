import os

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')  # No default value, must be set in the environment
    SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI', 'mysql+mysqlconnector://root:@localhost/datab')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

class TestingConfig(Config):
    TESTING = True

# Define a mapping of roles to their respective dashboard routes
ROLE_ROUTE_MAP = {
    'employee': 'employee.index',
    'admin': 'admin.index',
    'super_admin': 'super_admin.index'
}
