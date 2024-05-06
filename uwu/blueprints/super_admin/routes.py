from flask import Blueprint, render_template, request, url_for, flash, redirect, current_app
from uwu.models import Ticket, Materiel
from ...forms import TicketForm, MaterielForm
import uuid
from uwu.database import db
from flask_login import login_required
from uwu.models import Ticket, Materiel, User

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
    users = User.query.all()  # Assuming super_admins can see everyone
    return render_template('users.html', users=users, role='super_admin')


@super_admin_bp.route('/stats/')
@login_required
def stats():
    return "herrrrrrrrr"




