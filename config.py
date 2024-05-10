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
