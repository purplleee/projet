from flask import Blueprint, request, render_template, redirect, url_for, flash ,current_app , abort,session
from flask_login import login_user, logout_user, login_required ,LoginManager, current_user
from uwu.models import Ticket, Materiel, User
from uwu.models.models import Structure ,Role
from werkzeug.security import generate_password_hash, check_password_hash
from ...database import db
from sqlalchemy.exc import SQLAlchemyError
from config import ROLE_ROUTE_MAP





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
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            current_app.logger.debug(f"User {username} roles: {user.get_role_names()}")  # Debugging line
            
            # Assuming the first role is the primary one for redirection
            if user.roles:  # Check if there are any roles assigned
                primary_role_name = user.roles[0].name  # Get the name of the first role
                redirect_url = ROLE_ROUTE_MAP.get(primary_role_name, 'default.index')
                return redirect(url_for(redirect_url))
            else:
                flash('No roles assigned to this user.')
        else:
            flash('Invalid username or password')
            current_app.logger.info(f"Invalid login attempt for {username}")

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

