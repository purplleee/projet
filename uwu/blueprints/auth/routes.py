from flask import Blueprint, request, render_template, redirect, url_for, flash ,current_app , abort,session
from flask_login import login_user, logout_user, login_required ,LoginManager, current_user
from uwu.models import Ticket, Materiel, User
from uwu.models.models import Structure
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
    allowed_transitions = {
        'employee': ['employee'],
        'admin': ['employee', 'admin'],
        'super_admin': ['employee', 'admin', 'super_admin']
    }
    current_role = current_user.active_role  # Assuming active_role attribute exists

    if new_role in allowed_transitions.get(current_role, []):
        current_user.active_role = new_role
        db.session.commit()
        flash('Role switched successfully!', 'success')
        return redirect(url_for('some_function_based_on_role'))  # Redirect appropriately
    else:
        flash('Invalid role selected or insufficient permissions', 'error')
        return redirect(url_for('current_view'))








@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['nom'] + request.form['prenom']
        password = request.form['password']
        roles = request.form['roles']
        structure_id = request.form['structure_id']
        new_user = User(username=username, roles=roles, active_role=roles[0])
        new_user.set_password(password)  # Set password after creation
        new_user.structure_id = structure_id

        try:
            db.session.add(new_user)
            db.session.commit()
            flash('User registered successfully.')
            return redirect(url_for('auth.login'))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash('An error occurred while registering the user. Please try again.')
            current_app.logger.error(f"Error during user registration: {str(e)}")
        finally:
            db.session.close()
    
    structures = Structure.query.all()
    return render_template('register.html', structures=structures)

