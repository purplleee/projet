from flask_wtf import FlaskForm
from wtforms import (StringField, TextAreaField, IntegerField, BooleanField,RadioField,FieldList, SelectField)
from wtforms.validators import InputRequired, Length , Regexp
from wtforms import HiddenField



class TicketForm(FlaskForm):
    titre = StringField('Titre', validators=[InputRequired(), Length(min=5, max=100)])
    description_ticket = TextAreaField('Description Ticket', validators=[Length(max=400)])
    categorie = SelectField('Categorie', validators=[InputRequired()], coerce=int)
    urgent = RadioField('Urgence', validators=[InputRequired()], choices=[
        ('Faible', 'Faible'), ('Moyen', 'Moyen'), ('Élevé', 'Élevé')])
    materiel = SelectField('Materiel', validators=[InputRequired()], coerce=int)
    creator_user_id = HiddenField('Created By')


class AssignTicketForm(FlaskForm):
    categorie = SelectField('Categorie', validators=[InputRequired()], coerce=int)
    urgent = RadioField('Urgence', validators=[InputRequired()], choices=[
        ('Faible', 'Faible'), ('Moyen', 'Moyen'), ('Élevé', 'Élevé')])
    admin_assign = SelectField('Affecter à l\'Administrateur', coerce=int)

class MaterielForm(FlaskForm):
    # Assuming 'code_a_barre' should be a numeric code, use a validator that checks for numeric range instead of length
    code_a_barre = StringField(
        'Code à Barre', 
        validators=[
            InputRequired(), 
            Length(min=10, max=10, message="The code must be exactly 10 digits long."),
            Regexp('^\d{10}$', message="The code must consist only of digits.")
        ]
    )
    type_id = SelectField('Type', validators=[InputRequired()], coerce=int)
    marque_id = SelectField('Marque', validators=[InputRequired()], coerce=int)
    modele_id = SelectField('Modèle', validators=[InputRequired()], coerce=int)

class FAQForm(FlaskForm):
    objet = StringField('Subject', validators=[InputRequired(), Length(min=5, max=255)])
    contenu = TextAreaField('Content', validators=[InputRequired(), Length(min=20)])
    category_id = SelectField('Category', validators=[InputRequired()], coerce=int)
    # Ensure the creator's ID is properly captured but not manipulated by the client
    created_by_user_id = HiddenField('Created By')

class DeleteFAQForm(FlaskForm):
    pass