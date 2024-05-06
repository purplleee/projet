from flask import Blueprint, render_template, request, url_for, flash, redirect, current_app
from uwu.models import Ticket, Materiel
from ...forms import TicketForm, MaterielForm
import uuid
from uwu.database import db
from flask_login import login_required

employee_bp = Blueprint('employee', __name__)

def generate_unique_id():
    return str(uuid.uuid4())

@employee_bp.route('/')
@login_required
def index():
    new_tickets = Ticket.query.filter_by(statut='nouveau').count()
    in_progress_tickets = Ticket.query.filter_by(statut='en_cours').count()
    in_repair_tickets = Ticket.query.filter_by(statut='en_reparation').count()
    closed_tickets = Ticket.query.filter_by(statut='ferme').count()
    return render_template('index.html',
                           new_tickets=new_tickets,
                           in_progress_tickets=in_progress_tickets,
                           in_repair_tickets=in_repair_tickets,
                           closed_tickets=closed_tickets)

@employee_bp.route('/cree_ticket/', methods=('GET', 'POST'))
@login_required
def cree_ticket():
    form = TicketForm()
    if form.validate_on_submit():
        new_ticket = Ticket(
            id_ticket=generate_unique_id(),
            titre=form.titre.data,
            description_ticket=form.description_ticket.data,
            categorie=form.categorie.data,
            materiel=form.materiel.data
        )
        try:
            db.session.add(new_ticket)
            db.session.commit()
            flash('Ticket créé avec succès! Statut: nouveau', 'success')
            return redirect(url_for('employee.view_tickets_by_status', status='nouveau'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error creating ticket: {e}')  # Corrected logger usage
            flash(f'Erreur lors de la création du ticket: {str(e)}', 'error')
            return render_template('creat_ticket.html', form=form)
        finally:
            db.session.close()
    return render_template('creat_ticket.html', form=form)

@employee_bp.route('/tickets/<status>')
@login_required
def view_tickets_by_status(status):
    try:
        tickets_list = Ticket.query.filter_by(statut=status).all()
        return render_template('tickets.html', tickets_list=tickets_list, status=status)
    except Exception as e:
        flash(f'Erreur lors de la récupération des tickets: {str(e)}', 'error')
        current_app.logger.error(f'Failed to fetch tickets by status {status}: {e}')  # Corrected logger usage
        return render_template('tickets.html', tickets_list=[], status=status)

@employee_bp.route('/cree_mat/', methods=('GET', 'POST'))
@login_required
def cree_mat():
    form = MaterielForm()
    if form.validate_on_submit():
        new_materiel = Materiel(
            id_mat=form.id_mat.data,
            marque=form.marque.data,
            typeMat=form.typeMat.data
        )
        try:
            db.session.add(new_materiel)
            db.session.commit()
            flash('Matériel créé avec succès!', 'success')
            return redirect(url_for('employee.materiel'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la création du matériel: {str(e)}', 'error')
            current_app.logger.error(f'Error creating material: {e}')  # Corrected logger usage
            return render_template('creat_materiel.html', form=form)
        finally:
            db.session.close()
    return render_template('creat_materiel.html', form=form)

@employee_bp.route('/materiel/')
@login_required
def materiel():
    try:
        materiel_list = Materiel.query.all()
        return render_template('materiel.html', materiel_list=materiel_list)
    except Exception as e:
        flash(f'Erreur lors de la récupération du matériel: {str(e)}', 'error')
        current_app.logger.error(f'Failed to fetch material: {e}')  # Corrected logger usage
        return render_template('materiel.html', materiel_list=[])

@employee_bp.route('/edit_ticket/<int:ticket_id>', methods=['GET', 'POST'])
@login_required
def edit_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    form = TicketForm(obj=ticket)
    if form.validate_on_submit():
        ticket.titre = form.titre.data
        ticket.description_ticket = form.description_ticket.data
        ticket.categorie = form.categorie.data
        ticket.materiel = form.materiel.data
        db.session.commit()
        flash('Ticket updated successfully!', 'success')
        return redirect(url_for('employee.index'))  # Corrected redirect
    elif request.method == 'POST':
        flash('Error updating the ticket. Please check the form data.', 'error')
    return render_template('edit_ticket.html', form=form, ticket=ticket)

@employee_bp.route('/update_ticket/<int:ticket_id>', methods=['POST'])
@login_required
def update_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    form = TicketForm(request.form)
    if form.validate_on_submit():
        ticket.titre = form.titre.data
        ticket.description_ticket = form.description_ticket.data
        ticket.categorie = form.categorie.data
        ticket.materiel = form.materiel.data
        db.session.commit()
        flash('Ticket updated successfully!', 'success')
        return redirect(url_for('employee.index'))  # Corrected redirect
    else:
        for fieldName, errorMessages in form.errors.items():
            for err in errorMessages:
                flash(f"Error in {fieldName}: {err}", 'error')
        return render_template('edit_ticket.html', form=form, ticket=ticket)  # Re-render the edit page with errors
