from flask import Blueprint, render_template, request, url_for, flash, redirect, current_app,abort
from uwu.models import Ticket, Materiel
from ...forms import TicketForm, MaterielForm,FAQForm
import uuid
from uwu.database import db
from flask_login import login_required
from uwu.models import Ticket, Materiel, User
from uwu.models.models import Role,Structure,Category, FAQ
from flask_login import current_user

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/')
@login_required
def index():
    # Fetch tickets in different statuses excluding 'nouveau'
    in_progress_tickets = Ticket.query.filter(Ticket.statut == 'en_cours').count()
    in_repair_tickets = Ticket.query.filter(Ticket.statut == 'en_reparation').count()
    closed_tickets = Ticket.query.filter(Ticket.statut == 'clos').count()

    # Render the admin dashboard template with the ticket counts
    return render_template('index.html',
                           in_progress_tickets=in_progress_tickets,
                           in_repair_tickets=in_repair_tickets,
                           closed_tickets=closed_tickets)

@admin_bp.route('/tickets/<status>')
@login_required
def view_tickets_by_status(status):
    try:
        if status == 'nouveau':
            return redirect(url_for('admin.index'))  # Redirect if trying to access 'nouveau'
        tickets_list = Ticket.query.filter_by(statut=status).all()
        return render_template('tickets.html', tickets_list=tickets_list, status=status)
    except Exception as e:
        flash(f'Erreur lors de la récupération des tickets: {str(e)}', 'error')
        current_app.logger.error(f'Failed to fetch tickets by status {status}: {e}')
        return render_template('tickets.html', tickets_list=[], status=status)


@admin_bp.route('/users/')
@login_required
def admin_users():
    if current_user.role.name != 'admin':
        flash('Access denied', 'error')
        abort(403)

    try:
        # Fetch all structures and create a dictionary mapping IDs to names
        structures = Structure.query.all()
        structure_names = {structure.structure_id: structure.structure_name for structure in structures}

        # Fetch all non-super_admin users
        users = User.query.join(Role).filter(Role.name != 'super_admin').all()
        return render_template('users.html', users=users, structure_names=structure_names)
    except Exception as e:
        current_app.logger.error(f'Failed to fetch user list: {e}')
        flash(f'Erreur lors de la récupération des utilisateurs: {str(e)}', 'error')
        return render_template('users.html', users=[], structure_names={})




@admin_bp.route('/organigramme/')
@login_required
def organigramme():
    return "organigramme"




@admin_bp.route('/create_faq', methods=['GET', 'POST'])
@login_required  # Ensure user is logged in
def create_faq():
    form = FAQForm()
    
    # Set choices for category_id using the correct attribute name
    form.category_id.choices = [(c.category_id, c.category_name) for c in Category.query.all()]
    
    if form.validate_on_submit():
        new_faq = FAQ(
            objet=form.objet.data,
            contenu=form.contenu.data,
            category_id=form.category_id.data,
            created_by_user_id=current_user.user_id  # Securely fetch from logged-in user context
        )
        db.session.add(new_faq)
        db.session.commit()
        flash('FAQ created successfully!', 'success')
        return redirect(url_for('admin.admin_users'))  # Redirect to a relevant page after creation

    return render_template('create_faq.html', form=form)


@admin_bp.route('/faqs')
def list_faqs():
    faqs = FAQ.query.all()  # Assuming you're fetching all FAQs
    return render_template('list_faqs.html', faqs=faqs)

@admin_bp.route('/faq/<int:faq_id>')
def view_faq(faq_id):
    faq = FAQ.query.get_or_404(faq_id)  # Fetch the FAQ or return 404 if not found
    return render_template('view_faq.html', faq=faq)

