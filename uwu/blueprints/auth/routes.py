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
    # Correct the attribute name to 'current_role'
    current_role_object = Role.query.filter_by(name=current_user.current_role).first()

    if current_role_object and new_role in current_role_object.get_allowed_transitions():
        current_user.current_role = new_role  # Update the current role in the user model
        db.session.commit()  # Commit the changes to the database
        flash('Role switched successfully!', 'success')
        return redirect(url_for(f"{new_role}.index"))  # Redirect to the index page for the new role
    else:
        flash('Transition to selected role is not allowed.', 'error')

    return redirect(url_for('auth.login'))  # Redirect to login page or a more appropriate fallback





@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
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
            return redirect(url_for('auth.login'))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(f'An error occurred while registering the user. Error: {str(e)}', 'error')
            current_app.logger.error(f"Error during user registration: {str(e)}")
        finally:
            db.session.close()

    structures = Structure.query.all()
    return render_template('register.html', structures=structures)

