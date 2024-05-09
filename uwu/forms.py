from flask_wtf import FlaskForm
from wtforms import (StringField, TextAreaField, IntegerField, BooleanField,RadioField,FieldList, SelectField)
from wtforms.validators import InputRequired, Length




# class TicketForm(FlaskForm):
#     titre = StringField('Titre', validators=[InputRequired(), Length(min=5, max=100)])
#     description_ticket = TextAreaField('Description Ticket', validators=[Length(max=400)])
#     categorie = SelectField('Categorie', validators=[InputRequired()], choices=[
#                             ('panne_inconnue', 'Panne Inconnue'),
#                             ('reseau', 'Réseau'), 
#                             ('si_erp', 'système d\'information - ERP'),
#                             ('si_crm', 'système d\'information - CRM'),
#                             ('si_bi', 'système d\'information - BI'), 
#                             ('panne_hard', 'Panne Hard'),
#                             ('AD', 'AD'), 
#                             ('thunder_bird', 'ThunderBird'), 
#                             ('panne_soft', 'Panne Soft')])
#     materiel = SelectField('Materiel', validators=[InputRequired()], choices=[
#                            ('imprimante', 'Imprimante'),
#                            ('souris', 'Souris'), 
#                            ('cable', 'Cable'),
#                            ('ecran', 'Ecran')])

class TicketForm(FlaskForm):
    titre = StringField('Titre', validators=[InputRequired(), Length(min=5, max=100)])
    description_ticket = TextAreaField('Description Ticket', validators=[Length(max=400)])
    categorie = SelectField('Categorie', validators=[InputRequired()], coerce=int)
    urgent = RadioField('Urgence', validators=[InputRequired()], choices=[
        ('Faible', 'Faible'), ('Moyen', 'Moyen'), ('Élevé', 'Élevé')])
    materiel = SelectField('Materiel', validators=[InputRequired()], coerce=int)


class MaterielForm(FlaskForm):
    name = StringField('name', validators=[InputRequired(), Length( max=100)])
    important_info = StringField('Marque Materiel', validators=[InputRequired(), Length( max=100)])
    type = SelectField('type Materiel', validators=[InputRequired()], choices=[
                            ('imprimante', 'imprimante'),
                            ('sourie', 'sourie'), 
                            ('cable', 'cable'),
                            ('ecran', 'ecran')])