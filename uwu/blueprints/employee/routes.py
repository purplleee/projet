from flask import Blueprint, render_template, request, url_for, flash, redirect, current_app,abort
from sqlalchemy.orm import joinedload
from uwu.models import Ticket, Materiel 
from uwu.models.models import  Category,Marque,Modele,Type_m,Role,Structure,Category, FAQ, User, Photo
from ...forms import TicketForm, MaterielForm ,DeleteFAQForm
from uwu.database import db
from flask_login import login_required , LoginManager
from flask_login import current_user

employee_bp = Blueprint('employee', __name__)
login_manager = LoginManager(employee_bp)


@employee_bp.route('/')
@login_required
def index():
    user_id = current_user.user_id  
    new_tickets = Ticket.query.filter_by(statut='nouveau', creator_user_id=user_id).count()
    in_progress_tickets = Ticket.query.filter_by(statut='en_cours', creator_user_id=user_id).count()
    in_repair_tickets = Ticket.query.filter_by(statut='en_reparation', creator_user_id=user_id).count()
    closed_tickets = Ticket.query.filter_by(statut='clos', creator_user_id=user_id).count()
    return render_template('index.html',
                           new_tickets=new_tickets,
                           in_progress_tickets=in_progress_tickets,
                           in_repair_tickets=in_repair_tickets,
                           closed_tickets=closed_tickets)


@employee_bp.route('/cree_ticket/', methods=('GET', 'POST'))
@login_required
def cree_ticket():
    form = TicketForm()
    form.categorie.choices = [(c.category_id, c.category_name) for c in Category.query.order_by(Category.category_name)]
    form.materiel.choices = [(0, 'None')] + [(m.material_id, m.code_a_barre) for m in Materiel.query.order_by(Materiel.code_a_barre)]

    if form.validate_on_submit():
        material_id = None if form.materiel.data == 0 else form.materiel.data
        new_ticket = Ticket(
            titre=form.titre.data,
            description_ticket=form.description_ticket.data,
            urgent=form.urgent.data,
            category_id=form.categorie.data,
            material_id=material_id,
            creator_user_id=current_user.user_id
        )
        db.session.add(new_ticket)
        try:
            db.session.commit()
            if form.photos.data:
                for photo_data in form.photos.data:
                    new_photo = Photo(
                        image_data=photo_data.read(),
                        ticket_id=new_ticket.id_ticket  # Attach photo to the ticket
                    )
                    db.session.add(new_photo)
                db.session.commit()
            flash('Ticket créé avec succès! Statut: nouveau', 'success')
            return redirect(url_for('employee.view_tickets_by_status', status='nouveau'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la création du ticket: {str(e)}', 'warning')
        finally:
            db.session.close()
            
    return render_template('creat_ticket.html', form=form)

    
@employee_bp.route('/tickets/<status>')
@login_required
def view_tickets_by_status(status):
    try:
        user_id = current_user.user_id  
        # Join the Tickets table with Categories, Materials, and Users
        tickets_list = db.session.query(
            Ticket.titre.label('titre'),
            Category.category_name.label('category_name'),
            Ticket.urgent.label('urgent'),
            Materiel.code_a_barre.label('material_name'),
            Ticket.statut.label('statut'),
            Ticket.id_ticket.label('id_ticket'),
            User.username.label('creator_username')  # Include creator's username
        ).join(
            Category, Category.category_id == Ticket.category_id
        ).outerjoin(
            Materiel, Materiel.material_id == Ticket.material_id
        ).join(
            User, User.user_id == Ticket.creator_user_id
        ).filter(
            Ticket.statut == status,
            Ticket.creator_user_id == user_id  # Filter by logged-in user's ID
        ).all()
        
        return render_template('tickets.html', tickets_list=tickets_list, status=status)
    except Exception as e:
        flash(f'Erreur lors de la récupération des tickets: {str(e)}', 'warning')
        current_app.logger.warning(f'Failed to fetch tickets by status {status}: {e}')
        return render_template('tickets.html', tickets_list=[], status=status)


@employee_bp.route('/cree_mat/', methods=['GET', 'POST'])
@login_required
def cree_mat():
    if not current_user.get_temp_role() == 'employee':
        # current_app.logger.warning(f"Access denied for user {current_user.username} with role {current_user.get_temp_role()}")
        abort(403)  # Forbidden

    form = MaterielForm()

    # Load dropdown data
    marques = Marque.query.all()
    types = Type_m.query.all()
    modeles = Modele.query.all()
    
    # Set dropdown choices using the correct attribute name
    form.type_id.choices = [(t.type_id, t.type_name) for t in types]
    form.marque_id.choices = [(m.marque_id, m.marque_name) for m in marques]
    form.modele_id.choices = [(mo.modele_id, mo.modele_name) for mo in modeles]

    if form.validate_on_submit():
        # Check if the code_a_barre already exists
        existing_materiel = Materiel.query.filter_by(code_a_barre=form.code_a_barre.data).first()
        if (existing_materiel):
            flash('Erreur: Code à barre existe déjà!', 'warning')
            return render_template('creat_materiel.html', form=form, marques=marques, types=types, modeles=modeles)
        
        try:
            new_materiel = Materiel(
                code_a_barre=form.code_a_barre.data,
                type_id=form.type_id.data,
                marque_id=form.marque_id.data,
                modele_id=form.modele_id.data,
                structure_id=current_user.structure_id  # Ensure the user's structure_id is assigned
            )
            db.session.add(new_materiel)
            db.session.commit()
            flash('Matériel créé avec succès!', 'success')
            return redirect(url_for('employee.materiel'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la création du matériel: {str(e)}', 'warning')
            current_app.logger.error(f'Error creating material: {e}')
            return render_template('creat_materiel.html', form=form, marques=marques, types=types, modeles=modeles)
        finally:
            db.session.close()

    return render_template('creat_materiel.html', form=form, marques=marques, types=types, modeles=modeles)


@employee_bp.route('/materiel/')
@login_required
def materiel():
    try:
        structure_id = current_user.structure_id
        structure = Structure.query.get_or_404(structure_id)
        materiel_list = Materiel.query.filter_by(structure_id=structure_id).all()
        delete_form = DeleteFAQForm()  # Add this line

        return render_template('materiel.html', structure=structure, materiel_list=materiel_list, delete_form=delete_form)
    except Exception as e:
        flash(f'Erreur lors de la récupération du matériel: {str(e)}', 'warning')
        current_app.logger.error(f'Failed to fetch material: {e}')
        return render_template('materiel.html', structure=None, materiel_list=[], delete_form=None)  # Pass delete_form=None
    

@employee_bp.route('/edit_ticket/<int:ticket_id>', methods=['GET', 'POST'])
@login_required
def edit_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    form = TicketForm(obj=ticket)  # Load ticket data into form on GET request

    # Populate choices for category and material
    form.categorie.choices = [(c.category_id, c.category_name) for c in Category.query.order_by(Category.category_name)]
    form.materiel.choices = [(0, 'None')] + [(m.material_id, m.code_a_barre) for m in Materiel.query.order_by(Materiel.code_a_barre)]

    if request.method == 'POST':
        try:
            if form.validate_on_submit():
                # Update ticket properties
                ticket.titre = form.titre.data
                ticket.description_ticket = form.description_ticket.data
                ticket.category_id = form.categorie.data
                ticket.urgent=form.urgent.data
                # Handle nullable material_id
                ticket.material_id = form.materiel.data if form.materiel.data != 0 else None
                db.session.commit()
                flash('Ticket mis à jour avec succès !', 'success')
                return redirect(url_for('employee.index'))
            else:
                # If POST but form is not valid, flash an error
                flash('Erreur lors de la mise à jour du ticket. Veuillez vérifier les données du formulaire.', 'warning')
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la mise à jour du ticket: {str(e)}', 'warning')
        finally:
            db.session.close()
    
    # Ensure correct initial values for select fields are set when rendering the form
    form.categorie.data = ticket.category_id
    form.materiel.data = ticket.material_id if ticket.material_id is not None else 0
    return render_template('edit_ticket.html', form=form, ticket=ticket)


@employee_bp.route('/faqs')
def list_faqs():
    faqs = FAQ.query.all()  
    return render_template('list_faqs.html', faqs=faqs)


@employee_bp.route('/faq/<int:faq_id>')
def view_faq(faq_id):
    faq = FAQ.query.get_or_404(faq_id)  # Fetch the FAQ or return 404 if not found
    return render_template('view_faq.html', faq=faq)

