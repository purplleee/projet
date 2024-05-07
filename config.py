import os

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', '1fd34bf367245d1c60c08a5325a2dc72235390ee0a685cf9')
    SQLALCHEMY_DATABASE_URI = 'mysql+mysqlconnector://root:@localhost/datab'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

class TestingConfig(Config):
    TESTING = True
