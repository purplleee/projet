from flask import Blueprint, render_template, request, url_for, flash, redirect, current_app,abort
from uwu.models import Ticket, Materiel
from ...forms import TicketForm, MaterielForm,FAQForm
import uuid
from uwu.database import db
from flask_login import login_required
from uwu.models import Ticket, Materiel, User
from uwu.models.models import Role,Structure,Category, FAQ
from flask_login import current_user

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





