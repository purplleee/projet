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
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Retrieve user by username
        user = User.query.filter_by(username=username).first()

        if user:
            current_app.logger.info(f"Checking login for {username}. Stored hash: {user.password_hash} \n{user.check_password(password)}")
            if user.check_password(password):
                login_user(user)
                user.active_role=user.roles
                flash('Logged in successfully.')
                return redirect(url_for('employee.index'))
            else:
                flash('Invalid password')
                current_app.logger.info(f"Password check failed for {username}. Received password: {password}")
        else:
            flash('Username does not exist')
            current_app.logger.info(f"No user found with username {username}")

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
    if new_role in [role.name for role in current_user.roles]:
        allowed_transitions = Role.query.filter_by(name=current_user.current_role).first().get_allowed_transitions()
        if new_role in allowed_transitions:
            if current_user.switch_role(new_role):
                db.session.commit()
                flash('Role switched successfully!', 'success')
            else:
                flash('Failed to switch role.', 'error')
        else:
            flash('Invalid role selected or insufficient permissions', 'error')
    else:
        flash('Role not found.', 'error')

    return redirect(url_for('current_view'))  # Adjust as necessary to redirect to a relevant view











@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Combine first name and last name to create username
        username = request.form['nom'].strip() + request.form['prenom'].strip()
        password = request.form['password']
        role_names = request.form.getlist('roles')  # Retrieve a list of selected roles
        structure_id = int(request.form['structure_id'])  # Ensure this is an integer

        # Fetch roles from the database
        roles = Role.query.filter(Role.name.in_(role_names)).all()
        if not roles:
            flash('Specified roles are invalid', 'error')
            return redirect(request.url)

        # Create new user instance
        new_user = User(username=username, password=password, role_names=[role.name for role in roles])
        new_user.structure_id = structure_id  # Assign structure

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

