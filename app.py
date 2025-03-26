import os
import logging

from flask import Flask, render_template, redirect, url_for, flash, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_required, current_user
from sqlalchemy.orm import DeclarativeBase
from werkzeug.security import generate_password_hash, check_password_hash

# Configure logging
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                   datefmt='%Y-%m-%d %H:%M:%S')

# Setup database base class
class Base(DeclarativeBase):
    pass

# Initialize extensions
db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()

# Create app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///syscall.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize extensions with app
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'warning'

# Import routes and models after app creation to avoid circular imports
with app.app_context():
    from models import User, SystemCallLog, CommandPermission
    from forms import LoginForm, RegisterForm, SystemCallForm, PermissionForm
    import auth
    import system_calls
    
    # Register blueprints
    app.register_blueprint(auth.bp)
    app.register_blueprint(system_calls.bp)
    
    # Create database tables
    db.create_all()
    
    # Create default admin if it doesn't exist
    try:
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@example.com',
                password_hash=generate_password_hash('admin123'),
                is_admin=True
            )
            # Add some default command permissions for admin
            perm1 = CommandPermission(command_pattern='ls *', description='List files')
            perm2 = CommandPermission(command_pattern='ps aux', description='List processes')
            perm3 = CommandPermission(command_pattern='free -m', description='Show memory usage')
            perm4 = CommandPermission(command_pattern='df -h', description='Disk space usage')
            
            admin.permissions.extend([perm1, perm2, perm3, perm4])
            db.session.add(admin)
            db.session.commit()
            logging.info("Created default admin user")
    except Exception as e:
        logging.error(f"Error creating default admin: {e}")

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return redirect(url_for('auth.login'))

@app.errorhandler(404)
def page_not_found(e):
    return render_template('layout.html', error="404 - Page not found"), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('layout.html', error="500 - Internal server error"), 500

@app.context_processor
def inject_user():
    return dict(user=current_user)
