from uwu.database import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

class Ticket(db.Model):
    __tablename__ = 'tickets'
    id_ticket = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(100), nullable=False)
    description_ticket = db.Column(db.Text)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.category_id'))
    urgent = db.Column(db.Enum('Faible', 'Moyen', 'Élevé', name='ticket_urgent'),default="Faible")
    statut = db.Column(db.Enum('nouveau', 'en_cours', 'clos', 'en_reparation', name='ticket_statut'),default="nouveau")
    creator_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    assigned_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=True)
    days_in_repair = db.Column(db.Integer, nullable=True)
    material_id = db.Column(db.Integer, db.ForeignKey('materials.material_id'), nullable=True)



class Materiel(db.Model):
    __tablename__ = 'materials'
    material_id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(100))
    name = db.Column(db.String(100))
    structure_id = db.Column(db.Integer, db.ForeignKey('structures.structure_id'))
    important_info = db.Column(db.Text)




class User(db.Model, UserMixin):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(128))
    password_hash = db.Column(db.String(255))
    structure_id = db.Column(db.Integer, db.ForeignKey('structures.structure_id'))
    roles = db.Column(db.Enum('employee', 'admin', 'super_admin', name='roles'))
    active_role = db.Column(db.String(128))  # Assuming roles are stored as strings

    admin_categories = db.relationship('Category', secondary='admin_categories', backref=db.backref('admins', lazy='dynamic'))

    def __init__(self, username, roles, active_role=None):
        self.username = username
        self.roles = roles
        self.active_role = active_role if active_role else roles[0]  # Set the first role as the active one by default

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def switch_role(self, new_role):
        allowed_transitions = {
            'employee': ['employee'],  # Employees can't switch roles
            'admin': ['employee', 'admin'],  # Admins can switch to employee or back to admin
            'super_admin': ['employee', 'admin', 'super_admin']  # Super admins can switch to any role
        }
        if new_role in allowed_transitions.get(self.active_role, []):
            self.active_role = new_role
            db.session.commit()  # Ensures the change is saved to the database
            return True
        return False



    def get_id(self):
        return str(self.user_id)

    @property
    def is_admin(self):
        return self.active_role == 'admin'

    @property
    def is_employee(self):
        return self.active_role == 'employee'

    @property
    def is_super_admin(self):
        return self.active_role == 'super_admin'


class Structure(db.Model):
    __tablename__ = 'structures'
    structure_id = db.Column(db.Integer, primary_key=True)
    structure_name = db.Column(db.String(255))
    users = db.relationship('User', backref='structure', lazy='dynamic')

class Category(db.Model):
    __tablename__ = 'categories'
    category_id = db.Column(db.Integer, primary_key=True)
    category_name = db.Column(db.String(255))
    tickets = db.relationship('Ticket', backref='category', lazy='dynamic')

class Comment(db.Model):
    __tablename__ = 'comments'
    comment_id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('tickets.id_ticket'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    comment_text = db.Column(db.Text)
    created_at = db.Column(db.DateTime)

class FAQ(db.Model):
    __tablename__ = 'faqs'
    faq_id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(255))
    answer = db.Column(db.Text)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))

class Admin_Category(db.Model):
    __tablename__ = 'admin_categories'
    admin_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.category_id'), primary_key=True)