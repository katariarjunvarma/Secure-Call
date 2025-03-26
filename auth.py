import logging
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from models import User
from forms import LoginForm, RegisterForm

bp = Blueprint('auth', __name__)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    # Redirect to dashboard if user is already logged in
    if current_user.is_authenticated:
        return redirect(url_for('system_calls.dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=form.remember_me.data)
            
            # Update last login time
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            logging.info(f"User {user.username} logged in from {request.remote_addr}")
            
            # Redirect to the requested page or dashboard
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('system_calls.dashboard')
            return redirect(next_page)
        else:
            flash('Invalid username or password', 'danger')
            logging.warning(f"Failed login attempt for username: {form.username.data} from IP: {request.remote_addr}")
    
    return render_template('login.html', form=form)

@bp.route('/logout')
@login_required
def logout():
    username = current_user.username
    logout_user()
    flash('You have been logged out.', 'info')
    logging.info(f"User {username} logged out")
    return redirect(url_for('auth.login'))

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('system_calls.dashboard'))
    
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=generate_password_hash(form.password.data)
        )
        
        try:
            db.session.add(user)
            db.session.commit()
            flash('Registration successful! You can now log in.', 'success')
            logging.info(f"New user registered: {user.username} from {request.remote_addr}")
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred during registration. Please try again.', 'danger')
            logging.error(f"Registration error: {e}")
    
    return render_template('register.html', form=form)

@bp.route('/profile')
@login_required
def profile():
    # Calculate user statistics
    total_commands = current_user.logs.count()
    successful_commands = current_user.logs.filter_by(status='Success').count()
    error_commands = current_user.logs.filter_by(status='Error').count()
    denied_commands = current_user.logs.filter_by(status='Denied').count()
    
    # Get user's most recent activity
    recent_activity = current_user.logs.order_by(
        db.desc('executed_at')
    ).limit(5).all()
    
    # Get user's permissions
    permissions = current_user.permissions
    
    return render_template(
        'profile.html',
        user=current_user,
        total_commands=total_commands,
        successful_commands=successful_commands,
        error_commands=error_commands,
        denied_commands=denied_commands,
        recent_activity=recent_activity,
        permissions=permissions
    )
