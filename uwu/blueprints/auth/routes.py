from flask import Blueprint, request, render_template, redirect, url_for, flash ,current_app , abort,session
from flask_login import login_user, logout_user, login_required ,LoginManager, current_user
from uwu.models import Ticket, Materiel, User
from uwu.models.models import Structure ,Role
from werkzeug.security import generate_password_hash, check_password_hash
from ...database import db
from sqlalchemy.exc import SQLAlchemyError



auth_bp = Blueprint('auth', __name__, static_folder='static',template_folder='template')
login_manager = LoginManager(auth_bp)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    try:
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            user = User.query.filter_by(username=username).first()

            if not user:
                flash('Username does not exist', 'danger')
                current_app.logger.info(f"Login attempt for non-existent username: {username}")
                return render_template('login.html')

            if not user.check_password(password):
                flash('Incorrect password', 'danger')
                current_app.logger.info(f"Incorrect password for username: {username}")
                return render_template('login.html')

            login_user(user)
            current_app.logger.debug(f"User {username} logged in with role: {user.role.name}")
            if user.role.name == 'admin':
                current_app.logger.debug("Redirecting to admin.index")
                return redirect(url_for('admin.index'))
            elif user.role.name == 'employee':
                current_app.logger.debug("Redirecting to employee.index")
                return redirect(url_for('employee.index'))
            elif user.role.name == 'super_admin':
                current_app.logger.debug("Redirecting to super_admin.index")
                return redirect(url_for('super_admin.index'))
            else:
                flash('No roles assigned to this user.', 'warning')
                return redirect(url_for('auth.register'))

    except Exception as e:
        flash('An error occurred during login', 'danger')
        current_app.logger.error(f"An error occurred during login: {str(e)}")

    finally:
        if request.method == 'GET':
            return render_template('login.html')


@auth_bp.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('auth.login'))


@auth_bp.route('/switch_role', methods=['POST'])
@login_required
def switch_role():
    new_role = request.form.get('role')
    # Correct the attribute name to 'role.name'
    current_role_name = current_user.role.name
    current_role_object = Role.query.filter_by(name=current_role_name).first()

    if current_role_object and new_role in current_role_object.get_allowed_transitions():
        new_role_object = Role.query.filter_by(name=new_role).first()
        if new_role_object:
            current_user.role = new_role_object  # Update the role in the user model
            db.session.commit()  # Commit the changes to the database
            flash('Role switched successfully!', 'success')
            return redirect(url_for(f"{new_role}.index"))  # Redirect to the index page for the new role
        else:
            flash('The selected role does not exist.', 'error')
    else:
        flash('Transition to the selected role is not allowed.', 'error')

    return redirect(url_for('auth.login'))  # Redirect to login page or a more appropriate fallback


@auth_bp.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    structure_id = current_user.structure_id
    structure = Structure.query.get_or_404(structure_id)
    role = current_user.role.name
    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        if not current_user.check_password(current_password):
            flash('Current password is incorrect', 'danger')
            return redirect(url_for('auth.change_password'))

        if new_password != confirm_password:
            flash('New passwords do not match', 'danger')
            return redirect(url_for('auth.change_password'))

        current_user.set_password(new_password)
        db.session.commit()
        flash('Password has been updated', 'success')
        return redirect(url_for(current_user.role.name + '.index'))

    return render_template('change_password.html', structure=structure)


