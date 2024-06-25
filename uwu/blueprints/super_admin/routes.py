from flask import Blueprint, render_template, request, url_for, flash, redirect, current_app,abort
from uwu.models import Ticket, Materiel
from ...forms import TicketForm, MaterielForm,FAQForm , AssignTicketForm,EditTicketForm
from uwu.database import db
from flask_login import login_required
from uwu.models import Ticket, Materiel, User
from uwu.models.models import Role,Structure,Category, FAQ,Fournisseur,Panne
from flask_login import current_user ,LoginManager
import logging
from sqlalchemy.orm.exc import DetachedInstanceError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import aliased
from sqlalchemy import func
from datetime import datetime

super_admin_bp = Blueprint('super_admin', __name__)
login_manager = LoginManager(super_admin_bp)

@super_admin_bp.route('/')
@login_required
def index():
    # Fetch tickets in different statuses across the entire system
    new_tickets = Ticket.query.filter_by(statut='nouveau').count()
    in_progress_tickets = Ticket.query.filter_by(statut='en_cours').count()
    in_repair_tickets = Ticket.query.filter_by(statut='en_reparation').count()
    closed_tickets = Ticket.query.filter_by(statut='clos').count()  # Corrected to 'clos'

    # Render the super admin dashboard template with the ticket counts
    return render_template('index.html',
                           new_tickets=new_tickets,
                           in_progress_tickets=in_progress_tickets,
                           in_repair_tickets=in_repair_tickets,
                           closed_tickets=closed_tickets)


@super_admin_bp.route('/tickets/<status>')
@login_required
def view_tickets_by_status(status):
    try:
        # Aliases for User table to distinguish creator and assigned users
        creator_alias = aliased(User)
        assigned_alias = aliased(User)

        tickets_list = db.session.query(
            Ticket.titre.label('titre'),
            Category.category_name.label('category_name'),
            Ticket.urgent.label('urgent'),
            Materiel.code_a_barre.label('material_name'),
            Ticket.statut.label('statut'),
            Ticket.id_ticket.label('id_ticket'),
            creator_alias.username.label('creator_username'),  # Include creator's username
            assigned_alias.username.label('assigned_admin_username'),  # Include assigned admin's username
            Panne.fournisseur_id.label('fournisseur_name'),
            Panne.date_parti_reparation.label('date_parti_reparation'),
            (Ticket.statut == 'en_reparation').label('was_in_repair')  # Add this for the clos status check
        ).join(
            Category, Category.category_id == Ticket.category_id
        ).outerjoin(
            Materiel, Materiel.material_id == Ticket.material_id
        ).join(
            creator_alias, creator_alias.user_id == Ticket.creator_user_id
        ).outerjoin(
            assigned_alias, assigned_alias.user_id == Ticket.assigned_user_id
        ).outerjoin(
            Panne, Panne.material_id == Ticket.material_id  # Ensure this join is correct for your schema
        ).filter(
            Ticket.statut == status
        ).all()
        
        current_date = datetime.utcnow()  # Get the current date
        
        return render_template('tickets.html', tickets_list=tickets_list, status=status, current_date=current_date)
    except Exception as e:
        flash(f'Erreur lors de la récupération des tickets: {str(e)}', 'error')
        current_app.logger.error(f'Failed to fetch tickets by status {status}: {e}')
        return render_template('tickets.html', tickets_list=[], status=status)


@super_admin_bp.route('/assign_ticket/<int:ticket_id>', methods=['GET', 'POST'])
@login_required
def assign_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    form = AssignTicketForm(obj=ticket)

    user = User.query.get(current_user.user_id)

    # Populate choices for category and admin assignment
    form.categorie.choices = [(c.category_id, c.category_name) for c in Category.query.order_by(Category.category_name)]
    form.admin_assign.choices = [(a.user_id, a.username) for a in User.query.join(Role).filter(Role.name == 'admin').order_by(User.username)]

    if request.method == 'POST':
        if form.validate_on_submit():
            try:
                # Re-fetch ticket to ensure it is attached to the session
                ticket = Ticket.query.get_or_404(ticket_id)

                # Update ticket properties for super admin
                ticket.category_id = form.categorie.data
                ticket.urgent = form.urgent.data
                ticket.assigned_user_id = form.admin_assign.data
                ticket.statut = 'en_cours'
                db.session.commit()
                flash('Ticket assigned successfully!', 'success')
                return redirect(url_for('super_admin.index'))
            except Exception as e:
                db.session.rollback()
                logging.error(f'Error assigning the ticket: {str(e)}')
                flash(f'Error assigning the ticket: {str(e)}', 'error')
        else:
            # Log form validation errors
            for field, errors in form.errors.items():
                for error in errors:
                    logging.error(f"Error in {field}: {error}")
                    flash(f"Error in {field}: {error}", 'error')
            flash('Error assigning the ticket. Please check the form data.', 'error')

    # Set initial form values
    form.categorie.data = ticket.category_id
    form.urgent.data = ticket.urgent
    form.admin_assign.data = ticket.assigned_user_id
    return render_template('assign_ticket.html', form=form, ticket=ticket, user=user)


@super_admin_bp.route('/edit_ticket/<int:ticket_id>', methods=['GET', 'POST'])
@login_required
def edit_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)

    if current_user.get_temp_role() != 'super_admin':
        flash('Access denied.', 'error')
        return redirect(url_for('super_admin.index'))

    form = EditTicketForm(obj=ticket)
    form.categorie.choices = [(c.category_id, c.category_name) for c in Category.query.order_by(Category.category_name)]
    
    if form.validate_on_submit():
        try:
            ticket.category_id = form.categorie.data
            ticket.urgent = form.urgent.data
            db.session.commit()
            flash('Ticket updated successfully!', 'success')
            return redirect(url_for('super_admin.view_tickets_by_status', status=ticket.statut))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating the ticket: {str(e)}', 'error')

    return render_template('edit_ticket_c.html', form=form, ticket=ticket)


@super_admin_bp.route('/users/')
@login_required
def super_admin_users():
    try:
        # Fetch all structures and create a dictionary mapping IDs to names
        structures = Structure.query.all()
        structure_names = {structure.structure_id: structure.structure_name for structure in structures}

        # Fetch all non-super_admin users
        users = User.query.join(Role).all()
        return render_template('users.html', users=users, structure_names=structure_names)
    except Exception as e:
        current_app.logger.error(f'Failed to fetch user list: {e}')
        flash(f'Erreur lors de la récupération des utilisateurs: {str(e)}', 'error')
        return render_template('users.html', users=[], structure_names={})


@super_admin_bp.route('/stats/')
@login_required
def stats():
    # Fetch reparation statistics
    reparation_per_month = db.session.query(
        func.DATE_FORMAT(Ticket.ticket_creation_date, '%Y-%m').label('month'),
        func.count(Ticket.id_ticket).label('count')
    ).group_by('month').all()

    reparation_per_year = db.session.query(
        func.DATE_FORMAT(Ticket.ticket_creation_date, '%Y').label('year'),
        func.count(Ticket.id_ticket).label('count')
    ).group_by('year').all()

    # Fetch material counts for each fournisseur
    fournisseur_material_counts = db.session.query(
        Fournisseur.fournisseur_id,
        Fournisseur.fournisseur_name,
        func.count(Materiel.material_id).label('material_count')
    ).join(Materiel, Fournisseur.fournisseur_id == Materiel.fournisseur_id)\
    .group_by(Fournisseur.fournisseur_id, Fournisseur.fournisseur_name).all()

    return render_template("stat.html",
                           reparation_per_month=reparation_per_month,
                           reparation_per_year=reparation_per_year,
                           fournisseur_material_counts=fournisseur_material_counts)


@super_admin_bp.route('/fournisseur/<int:fournisseur_id>')
@login_required
def fournisseur_detail(fournisseur_id):
    fournisseur = Fournisseur.query.get_or_404(fournisseur_id)
    materials = Materiel.query.filter_by(fournisseur_id=fournisseur_id).all()
    return render_template('fournisseur_detail.html', fournisseur=fournisseur, materials=materials)




@super_admin_bp.route('/faqs')
@login_required
def list_faqs():
    faqs = FAQ.query.all()
    return render_template('list_faqs.html', faqs=faqs)


@super_admin_bp.route('/faq/<int:faq_id>')
@login_required
def view_faq(faq_id):
    faq = FAQ.query.get_or_404(faq_id)
    return render_template('view_faq.html', faq=faq)


@super_admin_bp.route('/faq/edit/<int:faq_id>', methods=['GET', 'POST'])
@login_required
def edit_faq(faq_id):
    faq = FAQ.query.get_or_404(faq_id)
    form = FAQForm(obj=faq)
    form.category_id.choices = [(c.category_id, c.category_name) for c in Category.query.all()]
    
    if form.validate_on_submit():
        faq.objet = form.objet.data
        faq.contenu = form.contenu.data
        faq.category_id = form.category_id.data
        db.session.commit()
        flash('FAQ updated successfully.', 'success')
        return redirect(url_for('super_admin.list_faqs'))
    
    return render_template('edit_faq.html', form=form, faq=faq)


@super_admin_bp.route('/faq/delete/<int:faq_id>', methods=['POST'])
@login_required
def delete_faq(faq_id):
    faq = FAQ.query.get_or_404(faq_id)
    db.session.delete(faq)
    db.session.commit()
    flash('FAQ deleted successfully.', 'success')
    return redirect(url_for('super_admin.list_faqs'))


@super_admin_bp.route('/create_user', methods=['GET', 'POST'])
@login_required
def add_user():
    if request.method == 'POST':
        username = request.form['nom'].strip() + "_" + request.form['prenom'].strip()
        password = request.form['password']
        role_name = request.form['roles']
        structure_id = int(request.form['structure_id'])

        # Fetch role within the same session context
        role = Role.query.filter_by(name=role_name).first()
        if not role:
            flash('Specified role is invalid', 'error')
            return redirect(request.url)

        new_user = User(username=username, password=password, role=role)
        new_user.structure_id = structure_id

        try:
            db.session.add(new_user)
            db.session.commit()
            flash('User registered successfully.')
            return redirect(url_for('super_admin.super_admin_users'))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(f'An error occurred while registering the user. Error: {str(e)}', 'error')
            current_app.logger.error(f"Error during user registration: {str(e)}")

    structures = Structure.query.all()
    return render_template('register.html', structures=structures)


@super_admin_bp.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        user.username = request.form['nom'].strip() + "_" + request.form['prenom'].strip()
        password = request.form['password']
        role_name = request.form['roles']
        structure_id = int(request.form['structure_id'])

        role = Role.query.filter_by(name=role_name).first()
        if not role:
            flash('Specified role is invalid', 'error')
            return redirect(request.url)

        user.role = role
        user.structure_id = structure_id

        if password:
            user.set_password(password)

        try:
            db.session.commit()
            flash('User updated successfully.')
            return redirect(url_for('super_admin.super_admin_users'))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(f'An error occurred while updating the user. Error: {str(e)}', 'error')
            current_app.logger.error(f"Error during user update: {str(e)}")

    structures = Structure.query.all()
    return render_template('edit_user.html', structures=structures, user=user)


@super_admin_bp.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)

    try:
        db.session.delete(user)
        db.session.commit()
        flash('User deleted successfully.')
    except SQLAlchemyError as e:
        db.session.rollback()
        flash(f'An error occurred while deleting the user. Error: {str(e)}', 'error')
        current_app.logger.error(f"Error during user deletion: {str(e)}")

    return redirect(url_for('super_admin.super_admin_users'))


@super_admin_bp.route('/reset_password/<int:user_id>', methods=['POST'])
@login_required
def reset_password_super_admin(user_id):
    user = User.query.get_or_404(user_id)
    new_password = user.username
    user.set_password(new_password)

    try:
        db.session.commit()
        flash('Password reset successfully.', 'success')
    except SQLAlchemyError as e:
        db.session.rollback()
        flash(f'An error occurred while resetting the password. Error: {str(e)}', 'error')
        current_app.logger.error(f"Error during password reset: {str(e)}")

    return redirect(url_for('super_admin.super_admin_users'))






