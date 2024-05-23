from flask import Blueprint, render_template, request, url_for, flash, redirect, current_app,abort
from uwu.models import Ticket, Materiel
from ...forms import TicketForm, MaterielForm,FAQForm,DeleteFAQForm,StructureForm, TypeForm, MarqueForm,ModeleForm
from uwu.database import db
from flask_login import login_required
from uwu.models import Ticket, Materiel, User
from uwu.models.models import Role,Structure,Category, FAQ, Marque ,Type_m, Modele
from flask_login import current_user
from sqlalchemy.exc import SQLAlchemyError

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
        
        # Fetch tickets assigned to the logged-in admin
        tickets_list = Ticket.query.filter_by(statut=status, assigned_user_id=current_user.user_id).all()
        
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


@admin_bp.route('/create_faq', methods=['GET', 'POST'])
@login_required  
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
@login_required
def list_faqs():
    faqs = FAQ.query.all()  # Assuming you're fetching all FAQs
    delete_form = DeleteFAQForm()
    return render_template('list_faqs.html', faqs=faqs, delete_form=delete_form)


@admin_bp.route('/faq/<int:faq_id>')
@login_required
def view_faq(faq_id):
    faq = FAQ.query.get_or_404(faq_id)  # Fetch the FAQ or return 404 if not found
    return render_template('view_faq.html', faq=faq)


@admin_bp.route('/faq/edit/<int:faq_id>', methods=['GET', 'POST'])
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


@admin_bp.route('/faq/delete/<int:faq_id>', methods=['POST'])
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


@admin_bp.route('/create_user', methods=['GET', 'POST'])
@login_required
def add_user():
    if request.method == 'POST':
        username = request.form['nom'].strip() + "_" + request.form['prenom'].strip()
        password = request.form['password']
        role_name = request.form['roles']  # Single role name as string
        structure_id = int(request.form['structure_id'])

        # Check role permissions
        if role_name not in ['employee', 'admin']:
            flash('Admins can only create users with Employee or Admin roles.', 'error')
            return redirect(request.url)

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


@admin_bp.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        user.username = request.form['nom'].strip() + "_" + request.form['prenom'].strip()
        password = request.form['password']
        role_name = request.form['roles']
        structure_id = int(request.form['structure_id'])

        if role_name not in ['employee', 'admin']:
            flash('Admins can only assign Employee or Admin roles.', 'error')
            return redirect(request.url)

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
            return redirect(url_for('admin.admin_users'))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(f'An error occurred while updating the user. Error: {str(e)}', 'error')
            current_app.logger.error(f"Error during user update: {str(e)}")

    structures = Structure.query.all()
    return render_template('edit_user.html', user=user, structures=structures)


@admin_bp.route('/delete_user/<int:user_id>', methods=['POST'])
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

    return redirect(url_for('admin.admin_users'))


@admin_bp.route('/reset_password/<int:user_id>', methods=['POST'])
@login_required
def reset_password_admin(user_id):
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

    return redirect(url_for('admin.admin_users'))


@admin_bp.route('/parametrage/')
@login_required
def parametrage():
    return render_template('para.html')


@admin_bp.route('/structures/', methods=['GET', 'POST'])
@login_required
def structures():
    form = StructureForm()
    if form.validate_on_submit():
        structure = Structure(structure_name=form.structure_name.data)
        db.session.add(structure)
        db.session.commit()
        flash('Structure added successfully!', 'success')
        return redirect(url_for('admin.structures'))
    structures = Structure.query.all()
    return render_template('structures.html', structures=structures, form=form)


@admin_bp.route('/add_structure/', methods=['POST'])
@login_required
def add_structure():
    form = StructureForm()
    if form.validate_on_submit():
        structure = Structure(structure_name=form.structure_name.data)
        db.session.add(structure)
        db.session.commit()
        flash('Structure added successfully!', 'success')
    return redirect(url_for('admin.structures'))


@admin_bp.route('/edit_structure/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_structure(id):
    structure = Structure.query.get_or_404(id)
    form = StructureForm(obj=structure)
    if form.validate_on_submit():
        structure.structure_name = form.structure_name.data
        db.session.commit()
        flash('Structure updated successfully!', 'success')
        return redirect(url_for('admin.structures'))
    return render_template('edit_structure.html', form=form, structure=structure)


@admin_bp.route('/delete_structure/<int:id>', methods=['POST'])
@login_required
def delete_structure(id):
    structure = Structure.query.get_or_404(id)
    db.session.delete(structure)
    db.session.commit()
    flash('Structure deleted successfully!', 'success')
    return redirect(url_for('admin.structures'))


@admin_bp.route('/structure/<int:structure_id>', methods=['GET'])
@login_required
def structure_materiel(structure_id):
    structure = Structure.query.get_or_404(structure_id)
    materiel_list = Materiel.query.filter_by(structure_id=structure_id).all()
    return render_template('materiel.html', structure=structure, materiel_list=materiel_list)


@admin_bp.route('/edit_mat/<int:materiel_id>', methods=['GET', 'POST'])
@login_required
def edit_mat(materiel_id):
    if not (current_user.is_admin or current_user.is_employee):
        abort(403)  # Forbidden
    materiel = Materiel.query.get_or_404(materiel_id)
    form = MaterielForm(obj=materiel)
    
    # Load dropdown data
    marques = Marque.query.all()
    types = Type_m.query.all()
    modeles = Modele.query.all()
    
    # Set dropdown choices
    form.type_id.choices = [(t.type_id, t.type_name) for t in types]
    form.marque_id.choices = [(m.marque_id, m.marque_name) for m in marques]
    form.modele_id.choices = [(mo.modele_id, mo.modele_name) for mo in modeles]

    if form.validate_on_submit():
        materiel.code_a_barre = form.code_a_barre.data
        materiel.type_id = form.type_id.data
        materiel.marque_id = form.marque_id.data
        materiel.modele_id = form.modele_id.data
        db.session.commit()
        flash('Materiel updated successfully!', 'success')
        return redirect(url_for('admin.structure_materiel', structure_id=materiel.structure_id))

    return render_template('edit_materiel.html', form=form, marques=marques, types=types, modeles=modeles, materiel=materiel)


@admin_bp.route('/delete_mat/<int:materiel_id>', methods=['POST'])
@login_required
def delete_mat(materiel_id):
    if not current_user.is_admin:
        abort(403)  # Forbidden
    materiel = Materiel.query.get_or_404(materiel_id)
    db.session.delete(materiel)
    db.session.commit()
    flash('Materiel deleted successfully!', 'success')
    return redirect(url_for('admin.structure_materiel', structure_id=materiel.structure_id))


@admin_bp.route('/marques/', methods=['GET', 'POST'])
@login_required
def marques():
    form = MarqueForm()
    if form.validate_on_submit():
        marque = Marque(marque_name=form.marque_name.data)
        db.session.add(marque)
        db.session.commit()
        flash('Marque added successfully!', 'success')
        return redirect(url_for('admin.marques'))
    marques = Marque.query.all()
    return render_template('marques.html', marques=marques, form=form)


@admin_bp.route('/add_marque/', methods=['POST'])
@login_required
def add_marque():
    form = MarqueForm()
    if form.validate_on_submit():
        marque = Marque(marque_name=form.marque_name.data)
        db.session.add(marque)
        db.session.commit()
        flash('Marque added successfully!', 'success')
    return redirect(url_for('admin.marques'))


@admin_bp.route('/edit_marque/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_marque(id):
    marque = Marque.query.get_or_404(id)
    form = MarqueForm(obj=marque)
    if form.validate_on_submit():
        marque.marque_name = form.marque_name.data
        db.session.commit()
        flash('Marque updated successfully!', 'success')
        return redirect(url_for('admin.marques'))
    return render_template('edit_marque.html', form=form, marque=marque)


@admin_bp.route('/delete_marque/<int:id>', methods=['POST'])
@login_required
def delete_marque(id):
    marque = Marque.query.get_or_404(id)
    db.session.delete(marque)
    db.session.commit()
    flash('Marque deleted successfully!', 'success')
    return redirect(url_for('admin.marques'))


@admin_bp.route('/marque/<int:marque_id>/models', methods=['GET', 'POST'])
@login_required
def models_by_marque(marque_id):
    marque = Marque.query.get_or_404(marque_id)
    models = Modele.query.filter_by(marque_id=marque_id).all()
    add_form = ModeleForm()
    
    # Generate a dictionary of forms for each model for editing
    edit_forms = {model.modele_id: ModeleForm(obj=model) for model in models}
    
    return render_template('models_by_marque.html', marque=marque, models=models, add_form=add_form, edit_forms=edit_forms)



@admin_bp.route('/marque/<int:marque_id>/add_model', methods=['GET', 'POST'])
@login_required
def add_model(marque_id):
    form = ModeleForm()
    if form.validate_on_submit():
        model = Modele(modele_name=form.modele_name.data, marque_id=marque_id)
        db.session.add(model)
        db.session.commit()
        flash('Model added successfully!', 'success')
        return redirect(url_for('admin.models_by_marque', marque_id=marque_id))
    return render_template('add_model.html', form=form, marque_id=marque_id)


@admin_bp.route('/edit_model/<int:model_id>', methods=['GET', 'POST'])
@login_required
def edit_model(model_id):
    model = Modele.query.get_or_404(model_id)
    form = ModeleForm(obj=model)
    if form.validate_on_submit():
        model.modele_name = form.modele_name.data
        db.session.commit()
        flash('Model updated successfully!', 'success')
        return redirect(url_for('admin.models_by_marque', marque_id=model.marque_id))
    return render_template('edit_model.html', form=form, model=model)


@admin_bp.route('/delete_model/<int:model_id>', methods=['POST'])
@login_required
def delete_model(model_id):
    model = Modele.query.get_or_404(model_id)
    marque_id = model.marque_id
    db.session.delete(model)
    db.session.commit()
    flash('Model deleted successfully!', 'success')
    return redirect(url_for('admin.models_by_marque', marque_id=marque_id))


@admin_bp.route('/types/', methods=['GET', 'POST'])
@login_required
def types():
    form = TypeForm()
    if form.validate_on_submit():
        type_m = Type_m(type_name=form.type_name.data)
        db.session.add(type_m)
        db.session.commit()
        flash('Type added successfully!', 'success')
        return redirect(url_for('admin.types'))
    types = Type_m.query.all()
    return render_template('types.html', types=types, form=form)


@admin_bp.route('/add_type/', methods=['POST'])
@login_required
def add_type():
    form = TypeForm()
    if form.validate_on_submit():
        type_m = Type_m(type_name=form.type_name.data)
        db.session.add(type_m)
        db.session.commit()
        flash('Type added successfully!', 'success')
    return redirect(url_for('admin.types'))


@admin_bp.route('/edit_type/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_type(id):
    type_m = Type_m.query.get_or_404(id)
    form = TypeForm(obj=type_m)
    if form.validate_on_submit():
        type_m.type_name = form.type_name.data
        db.session.commit()
        flash('Type updated successfully!', 'success')
        return redirect(url_for('admin.types'))
    return render_template('edit_type.html', form=form, type=type_m)


@admin_bp.route('/delete_type/<int:id>', methods=['POST'])
@login_required
def delete_type(id):
    type_m = Type_m.query.get_or_404(id)
    db.session.delete(type_m)
    db.session.commit()
    flash('Type deleted successfully!', 'success')
    return redirect(url_for('admin.types'))

