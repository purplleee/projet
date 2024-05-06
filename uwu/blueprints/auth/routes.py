from flask import Blueprint, request, render_template, redirect, url_for, flash ,current_app
from flask_login import login_user, logout_user, current_user, login_required
from uwu.models import Ticket, Materiel, User
from werkzeug.security import generate_password_hash, check_password_hash
from ...database import db




auth_bp = Blueprint('auth', __name__, static_folder='static',template_folder='template')


# # Mock database of users (replace with your actual user validation logic)
# users = {
#     'admin': User('admin', ['admin', 'employee']),
#     'employee': User('employee', ['employee']),
#     'superadmin': User('superadmin', ['super_admin', 'admin', 'employee'])
# }


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user:
            current_app.logger.info(f"Checking login for {username}. Stored hash: {user.password_hash}")
            if user.check_password(password):
                login_user(user)
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



@auth_bp.route('/switch_role', methods=['GET', 'POST'])
@login_required
def switch_role():
    if request.method == 'POST':
        new_role = request.form['role']
        if current_user.switch_role(new_role):
            flash(f'Switched to {new_role} role.')
            return redirect(url_for('main.index'))
        flash('Invalid role switch attempt.')
    return render_template('switch_role.html', roles=current_user.roles)




@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            username = request.form['username']
            password = request.form['password']
            role = request.form['roles']  # Assuming roles are sent as part of the form

            # Check if user already exists
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                flash('Username already exists')
                return redirect(url_for('auth.register'))

            # Create a new user instance with the role
            new_user = User(username=username, roles=role)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            flash('User registered successfully!')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred: {e}", 'error')
        finally:
            db.session.close()

    return render_template('register.html')

