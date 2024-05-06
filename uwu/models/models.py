from uwu.database import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

class Ticket(db.Model):
    __tablename__ = 'tickets'
    id_ticket = db.Column(db.Integer, primary_key=True)  # Correct primary key name
    titre = db.Column(db.String(100), nullable=False, unique=True)
    description_ticket = db.Column(db.String(400))
    categorie = db.Column(db.String(10), nullable=False)
    materiel = db.Column(db.String(30))
    statut = db.Column(db.String(7), default='nouveau')


class Materiel(db.Model):
    __tablename__ = 'materiel'
    id_mat = db.Column(db.String(10), primary_key=True)
    marque = db.Column(db.String(100), nullable=False)
    typeMat = db.Column(db.String(20), nullable=False)



class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    roles = db.Column(db.String(15), nullable=False)  

    def __init__(self, username, roles):
        self.username = username
        self.roles = roles
        self.active_role = roles[0]

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)


    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def switch_role(self, new_role):
        if new_role in self.roles:
            self.active_role = new_role
            return True
        return False

    @property
    def is_admin(self):
        return self.active_role == 'admin'

    @property
    def is_employee(self):
        return self.active_role == 'employee'

    @property
    def is_super_admin(self):
        return self.active_role == 'super_admin'
