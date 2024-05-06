from flask import Blueprint, render_template, request, url_for, flash, redirect, current_app
from uwu.models import Ticket, Materiel
from ...forms import TicketForm, MaterielForm
import uuid
from uwu.database import db
from flask_login import login_required
from uwu.models import Ticket, Materiel, User
from flask_login import current_user

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/')
@login_required
def index():
    # Fetch tickets in different statuses excluding 'nouveau'
    in_progress_tickets = Ticket.query.filter(Ticket.statut == 'en_cours').count()
    in_repair_tickets = Ticket.query.filter(Ticket.statut == 'en_reparation').count()
    closed_tickets = Ticket.query.filter(Ticket.statut == 'ferme').count()

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
    # Exclude super_admins if the user is an admin
    if 'admin' in current_user.roles:
        users = User.query.filter(User.roles != 'super_admin').all()
    return render_template('users.html', users=users, role='admin')



@admin_bp.route('/organigramme/')
@login_required
def organigramme():
    return "organigramme"