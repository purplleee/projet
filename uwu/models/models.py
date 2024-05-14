from uwu.database import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from sqlalchemy.sql import func
from sqlalchemy import Table, Integer, ForeignKey, Column, String
from sqlalchemy.orm import relationship




# Define a many-to-many association table for role transitions
role_transitions = Table('role_transitions', db.Model.metadata,
    Column('role_id', Integer, ForeignKey('roles.role_id'), primary_key=True),
    Column('allowed_role_id', Integer, ForeignKey('roles.role_id'), primary_key=True)
)

class Role(db.Model):
    __tablename__ = 'roles'
    role_id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True)

    # Relationships for allowed transitions
    allowed_transitions = relationship(
        'Role', 
        secondary=role_transitions,
        primaryjoin=(role_id == role_transitions.c.role_id),
        secondaryjoin=(role_id == role_transitions.c.allowed_role_id),
        backref="allowed_by"
    )

    def __repr__(self):
        return f'<Role {self.name}>'

    def get_allowed_transitions(self):
        return [role.name for role in self.allowed_transitions]


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    user_id = Column(Integer, primary_key=True)
    username = Column(String(128), unique=True, nullable=False)
    password_hash = Column(String(255))
    structure_id = Column(Integer, ForeignKey('structures.structure_id'))

    # New direct relationship with Role
    role_id = Column(Integer, ForeignKey('roles.role_id'))
    role = relationship('Role', backref='users')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __init__(self, username, password, role=None):
        self.username = username
        self.set_password(password)
        self.role = role

    def assign_role(self, role_name):
        role = Role.query.filter_by(name=role_name).first()
        if role:
            self.role = role

    def get_role_name(self):
        return self.role.name if self.role else None

    def get_id(self):
        return str(self.user_id)

    @property
    def is_admin(self):
        return self.current_role == 'admin'

    @property
    def is_employee(self):
        return self.current_role == 'employee'

    @property
    def is_super_admin(self):
        return self.current_role == 'super_admin'


class Structure(db.Model):
    __tablename__ = 'structures'
    structure_id = db.Column(db.Integer, primary_key=True)
    structure_name = db.Column(db.String(255))

class Category(db.Model):
    __tablename__ = 'categories'
    category_id = db.Column(db.Integer, primary_key=True)
    category_name = db.Column(db.String(255))

class Ticket(db.Model):
    __tablename__ = 'tickets'
    id_ticket = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(100), nullable=False)
    description_ticket = db.Column(db.Text)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.category_id'))
    urgent = db.Column(db.Enum('Faible', 'Moyen', 'Élevé', name='ticket_urgency'), default="Faible")
    statut = db.Column(db.Enum('nouveau', 'en_cours', 'clos', 'en_reparation', 'suspended', name='ticket_status'), default="nouveau")
    creator_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    assigned_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=True)
    days_in_repair = db.Column(db.Integer, nullable=True)
    material_id = db.Column(db.Integer, db.ForeignKey('materials.material_id'), nullable=True)
    ticket_creation_date = db.Column(db.DateTime, server_default=func.now())

class Type_m(db.Model):
    __tablename__ = 'type_m'
    type_id = db.Column(db.Integer, primary_key=True)
    type_name = db.Column(db.String(100), nullable=False)


class Fournisseur(db.Model):
    __tablename__ = 'fournisseurs'
    fournisseur_id = db.Column(db.Integer, primary_key=True)
    fournisseur_name = db.Column(db.String(100))
    # Define a relationship that links back to the 'Materiel' table
    materials = db.relationship('Materiel', backref='fournisseur', lazy='dynamic')

class Materiel(db.Model):
    __tablename__ = 'materials'
    material_id = db.Column(db.Integer, primary_key=True)
    code_a_barre = db.Column(db.Integer, nullable=False)
    # Ensure this foreign key points back to the 'fournisseurs' table
    fournisseur_id = db.Column(db.Integer, db.ForeignKey('fournisseurs.fournisseur_id'))

    # Other fields remain unchanged
    type_id = db.Column(db.Integer, db.ForeignKey('type_m.type_id'))
    type = db.relationship('Type_m', backref='materiels')
    marque_id = db.Column(db.Integer, db.ForeignKey('marques.marque_id'))
    marque = db.relationship('Marque', backref='materiels')
    modele_id = db.Column(db.Integer, db.ForeignKey('modeles.modele_id'))
    structure_id = Column(Integer, ForeignKey('structures.structure_id'))
    modele = db.relationship('Modele', backref='materiels')




class Marque(db.Model):
    __tablename__ = 'marques'
    marque_id = db.Column(db.Integer, primary_key=True)
    marque_name = db.Column(db.String(100))

class Modele(db.Model):
    __tablename__ = 'modeles'
    modele_id = db.Column(db.Integer, primary_key=True)
    modele_name = db.Column(db.String(100))
    marque_id = db.Column(db.Integer, db.ForeignKey('marques.marque_id'))

class Comment(db.Model):
    __tablename__ = 'comments'
    comment_id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('tickets.id_ticket'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    comment_text = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=func.now())

class FAQ(db.Model):
    __tablename__ = 'faqs'
    faq_id = db.Column(db.Integer, primary_key=True)
    objet = db.Column(db.String(255), nullable=False)
    contenu = db.Column(db.Text, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.category_id'))
    category = db.relationship('Category', backref='faqs', lazy=True)  # This is important
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    user = db.relationship('User', backref='faqs', lazy=True)



class Panne(db.Model):
    __tablename__ = 'pannes'
    panne_id = db.Column(db.Integer, primary_key=True)
    date_parti_reparation = db.Column(db.DateTime)
    fournisseur_id = db.Column(db.Integer, db.ForeignKey('fournisseurs.fournisseur_id'))
    material_id = db.Column(db.Integer, db.ForeignKey('materials.material_id'))
