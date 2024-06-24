from flask_wtf import FlaskForm
from wtforms import (StringField, TextAreaField, IntegerField, BooleanField, RadioField, FieldList, SelectField, DateField, FileField)
from wtforms.validators import InputRequired, Length, Regexp, DataRequired, ValidationError
from wtforms import HiddenField, SubmitField
from flask_wtf.file import FileField, FileAllowed, FileRequired

class TicketForm(FlaskForm):
    titre = StringField('Titre', validators=[InputRequired(), Length(min=5, max=100)])
    description_ticket = TextAreaField('Description du Ticket', validators=[Length(max=400)])
    categorie = SelectField('Catégorie', validators=[InputRequired()], coerce=int)
    urgent = RadioField('Urgence', validators=[InputRequired()], choices=[
        ('Faible', 'Faible'), ('Moyen', 'Moyen'), ('Élevé', 'Élevé')])
    materiel = SelectField('Matériel', coerce=int)
    creator_user_id = HiddenField('Créé par')

class CloseTicketForm(FlaskForm):
    close = SubmitField('Clôturer le Ticket')

class AddRepairDetailsForm(FlaskForm):
    fournisseur = SelectField('Fournisseur', coerce=int, validators=[InputRequired()])
    date_parti_reparation = DateField('Date de départ en réparation', format='%Y-%m-%d', validators=[InputRequired()])
    add_repair_details = SubmitField('Ajouter les Détails de Réparation')

class EditTicketForm(FlaskForm):
    categorie = SelectField('Catégorie', validators=[InputRequired()], coerce=int)
    urgent = RadioField('Urgence', validators=[InputRequired()], choices=[
        ('Faible', 'Faible'), ('Moyen', 'Moyen'), ('Élevé', 'Élevé')])

class AssignTicketForm(FlaskForm):
    categorie = SelectField('Catégorie', validators=[InputRequired()], coerce=int)
    urgent = RadioField('Urgence', validators=[InputRequired()], choices=[
        ('Faible', 'Faible'), ('Moyen', 'Moyen'), ('Élevé', 'Élevé')])
    admin_assign = SelectField('Affecter à l\'Administrateur', coerce=int)

class MaterielForm(FlaskForm):
    code_a_barre = StringField(
        'Code à Barre', 
        validators=[
            InputRequired(), 
            Length(min=10, max=10, message="Le code doit contenir exactement 10 chiffres."),
            Regexp('^\d{10}$', message="Le code doit être composé uniquement de chiffres.")
        ]
    )
    type_id = SelectField('Type', validators=[InputRequired()], coerce=int)
    marque_id = SelectField('Marque', validators=[InputRequired()], coerce=int)
    modele_id = SelectField('Modèle', validators=[InputRequired()], coerce=int)

class FAQForm(FlaskForm):
    objet = StringField('Objet', validators=[InputRequired(), Length(min=5, max=255)])
    contenu = TextAreaField('Contenu', validators=[InputRequired(), Length(min=20)])
    category_id = SelectField('Catégorie', validators=[InputRequired()], coerce=int)
    # Ensure the creator's ID is properly captured but not manipulated by the client
    created_by_user_id = HiddenField('Créé par')

class DeleteFAQForm(FlaskForm):
    pass

class StructureForm(FlaskForm):
    structure_name = StringField('Nom de la Structure', validators=[DataRequired()])
    submit = SubmitField('Ajouter la Structure')

class TypeForm(FlaskForm):
    type_name = StringField('Nom du Type', validators=[DataRequired()])
    submit = SubmitField('Ajouter le Type')

class MarqueForm(FlaskForm):
    marque_name = StringField('Nom de la Marque', validators=[DataRequired()])
    submit = SubmitField('Ajouter la Marque')

class ModeleForm(FlaskForm):
    modele_name = StringField('Nom du Modèle', validators=[DataRequired()])
    submit = SubmitField('Ajouter le Modèle')


def file_size_limit(max_size_in_mb):
    max_bytes = max_size_in_mb * 1024 * 1024

    def _file_size_limit(form, field):
        if field.data:
            if len(field.data.read()) > max_bytes:
                raise ValidationError(f'File size must be less than {max_size_in_mb}MB')
            field.data.seek(0)  # Reset file pointer after read

    return _file_size_limit

class CommentForm(FlaskForm):
    comment_text = TextAreaField('Commentaire', validators=[DataRequired()])
    photo = FileField('ajouter une pièce jointe', validators=[FileAllowed(['jpg', 'jpeg', 'png']), file_size_limit(5)])
    submit = SubmitField('Ajouter le Commentaire')

