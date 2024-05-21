from flask import Blueprint, render_template, request, url_for, flash, redirect, current_app,abort
from uwu.models import Ticket, Materiel
from ...forms import TicketForm, MaterielForm,FAQForm , AssignTicketForm
from uwu.database import db
from flask_login import login_required
from uwu.models import Ticket, Materiel, User
from uwu.models.models import Role,Structure,Category, FAQ
from flask_login import current_user
import logging
from sqlalchemy.orm.exc import DetachedInstanceError
from sqlalchemy.exc import SQLAlchemyError

super_admin_bp = Blueprint('super_admin', __name__)


@super_admin_bp.route('/')
@login_required
def index():
    # Fetch tickets in different statuses
    new_tickets = Ticket.query.filter_by(statut='nouveau').count()
    in_progress_tickets = Ticket.query.filter_by(statut='en_cours').count()
    in_repair_tickets = Ticket.query.filter_by(statut='en_reparation').count()
    closed_tickets = Ticket.query.filter_by(statut='ferme').count()

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
        tickets_list = db.session.query(
            Ticket.titre.label('titre'),
            Category.category_name.label('category_name'),
            Ticket.urgent.label('urgent'),
            Materiel.code_a_barre.label('material_name'),
            Ticket.statut.label('statut'),
            Ticket.id_ticket.label('id_ticket')
        ).join(
            Category, Category.category_id == Ticket.category_id
        ).outerjoin(
            Materiel, Materiel.material_id == Ticket.material_id
        ).filter(
            Ticket.statut == status
        ).all()
        
        return render_template('tickets.html', tickets_list=tickets_list, status=status)
    except Exception as e:
        flash(f'Erreur lors de la récupération des tickets: {str(e)}', 'error')
        current_app.logger.error(f'Failed to fetch tickets by status {status}: {e}')
        return render_template('tickets.html', tickets_list=[], status=status)


@super_admin_bp.route('/assign_ticket/<int:ticket_id>', methods=['GET', 'POST'])
@login_required
def assign_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    form = AssignTicketForm(obj=ticket)

    # Ensure current_user is attached to the session
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
    return "herrrrrrrrr"


@super_admin_bp.route('/faqs')
def list_faqs():
    faqs = FAQ.query.all()  # Assuming you're fetching all FAQs
    return render_template('list_faqs.html', faqs=faqs)


@super_admin_bp.route('/faq/<int:faq_id>')
def view_faq(faq_id):
    faq = FAQ.query.get_or_404(faq_id)  # Fetch the FAQ or return 404 if not found
    return render_template('view_faq.html', faq=faq)


@super_admin_bp.route('/faq/edit/<int:faq_id>', methods=['GET', 'POST'])
@login_required
def edit_faq(faq_id):
    if current_user.role.name != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('admin.list_faqs'))
    
    faq = FAQ.query.get_or_404(faq_id)
    form = FAQForm(obj=faq)  # Populate form with FAQ data

    # Populate category choices
    categories = Category.query.all()
    form.category_id.choices = [(category.category_id, category.category_name) for category in categories]
    
    if form.validate_on_submit():
        faq.objet = form.objet.data
        faq.contenu = form.contenu.data
        faq.category_id = form.category_id.data
        db.session.commit()
        flash('FAQ updated successfully.', 'success')
        return redirect(url_for('admin.list_faqs'))
    
    return render_template('edit_faq.html', form=form, faq=faq)


@super_admin_bp.route('/faq/delete/<int:faq_id>', methods=['POST'])
@login_required
def delete_faq(faq_id):
    if current_user.role.name != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('admin.list_faqs'))
    
    faq = FAQ.query.get_or_404(faq_id)
    db.session.delete(faq)
    db.session.commit()
    flash('FAQ deleted successfully.', 'success')
    return redirect(url_for('admin.list_faqs'))


@super_admin_bp.route('/creat_user', methods=['GET', 'POST'])
@login_required
def add_user():
    if request.method == 'POST':
        username = request.form['nom'].strip() + "_" + request.form['prenom'].strip()
        password = request.form['password']
        role_name = request.form['roles']  # Single role name as string
        structure_id = int(request.form['structure_id'])

        # Fetch role from the database
        role = Role.query.filter_by(name=role_name).first()
        if not role:
            flash('Specified role is invalid', 'error')
            return redirect(request.url)

        # Create new user instance with the specified role
        new_user = User(username=username, password=password, role=role)
        new_user.structure_id = structure_id

        try:
            db.session.add(new_user)
            db.session.commit()
            flash('User registered successfully.')
            return redirect(url_for('admin.admin_users'))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(f'An error occurred while registering the user. Error: {str(e)}', 'error')
            current_app.logger.error(f"Error during user registration: {str(e)}")
        finally:
            db.session.close()

    structures = Structure.query.all()
    return render_template('register.html', structures=structures)


@super_admin_bp.route('/users/delete/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if not current_user.is_super_admin:
        flash('You do not have permission to perform this action.', 'danger')
        return redirect(url_for('super_admin.super_admin_users'))

    user = User.query.get_or_404(user_id)
    
    try:
        db.session.delete(user)
        db.session.commit()
        flash('User has been deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Failed to delete user: {e}')
        flash(f'Error deleting user: {e}', 'error')

    return redirect(url_for('super_admin.super_admin_users'))
