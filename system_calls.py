import os
import re
import time
import logging
import subprocess
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from models import SystemCallLog, CommandPermission, User
from forms import SystemCallForm, PermissionForm
from logger import log_system_call

bp = Blueprint('system_calls', __name__, url_prefix='/system')

def is_command_allowed(user, command):
    """Check if the command is allowed for the user based on their permissions."""
    if user.is_admin:
        return True
        
    for permission in user.permissions:
        pattern = permission.command_pattern
        # Convert glob pattern to regex
        pattern = pattern.replace('*', '.*')
        if re.match(f"^{pattern}$", command):
            return True
    return False

def execute_command(command, timeout=30):
    """Execute a system command with timeout and return result."""
    start_time = time.time()
    
    try:
        # Use subprocess with security considerations
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        stdout, stderr = process.communicate(timeout=timeout)
        exit_code = process.returncode
        execution_time = time.time() - start_time
        
        if exit_code != 0:
            output = stderr
            status = "Error"
        else:
            output = stdout
            status = "Success"
            
        return {
            "status": status,
            "output": output,
            "exit_code": exit_code,
            "execution_time": execution_time
        }
    except subprocess.TimeoutExpired:
        # Kill the process if it exceeds timeout
        process.kill()
        return {
            "status": "Timeout",
            "output": "Command execution timed out",
            "exit_code": -1,
            "execution_time": timeout
        }
    except Exception as e:
        logging.error(f"Error executing command: {e}")
        return {
            "status": "Error",
            "output": str(e),
            "exit_code": -1,
            "execution_time": time.time() - start_time
        }

@bp.route('/execute', methods=['GET', 'POST'])
@login_required
def execute():
    form = SystemCallForm()
    
    # Get user's permissions for display
    permissions = current_user.permissions
    
    if form.validate_on_submit():
        command = form.command.data
        
        # Check if command is allowed
        if not is_command_allowed(current_user, command):
            flash(f'You do not have permission to execute: {command}', 'danger')
            # Log unauthorized attempt
            log_system_call(
                user_id=current_user.id,
                command=command,
                output="Unauthorized attempt",
                status="Denied",
                exit_code=-1,
                execution_time=0,
                ip_address=request.remote_addr
            )
            return redirect(url_for('system_calls.execute'))
        
        # Execute the command
        result = execute_command(command)
        
        # Log the command execution
        log_system_call(
            user_id=current_user.id,
            command=command,
            output=result["output"],
            status=result["status"],
            exit_code=result["exit_code"],
            execution_time=result["execution_time"],
            ip_address=request.remote_addr
        )
        
        # Flash appropriate message
        if result["status"] == "Success":
            flash('Command executed successfully', 'success')
        else:
            flash(f'Command execution failed: {result["status"]}', 'danger')
            
        return render_template('execute.html', form=form, result=result, permissions=permissions)
    
    return render_template('execute.html', form=form, permissions=permissions)

@bp.route('/logs')
@login_required
def logs():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # For admin, show all logs, for regular users, show only their logs
    if current_user.is_admin:
        logs_pagination = SystemCallLog.query.order_by(
            SystemCallLog.executed_at.desc()
        ).paginate(page=page, per_page=per_page)
    else:
        logs_pagination = SystemCallLog.query.filter_by(
            user_id=current_user.id
        ).order_by(
            SystemCallLog.executed_at.desc()
        ).paginate(page=page, per_page=per_page)
    
    return render_template('logs.html', logs=logs_pagination)

@bp.route('/logs/data')
@login_required
def logs_data():
    """API endpoint for logs data for charting."""
    days = request.args.get('days', 7, type=int)
    
    # For admin, get logs for all users
    if current_user.is_admin:
        query = db.session.query(
            db.func.date(SystemCallLog.executed_at).label('date'),
            db.func.count().label('count'),
            SystemCallLog.status
        ).filter(
            db.func.date(SystemCallLog.executed_at) >= db.func.date_sub(
                db.func.current_date(), days
            )
        ).group_by(
            db.func.date(SystemCallLog.executed_at),
            SystemCallLog.status
        ).order_by(
            db.func.date(SystemCallLog.executed_at)
        )
    else:
        # For regular users, get only their logs
        query = db.session.query(
            db.func.date(SystemCallLog.executed_at).label('date'),
            db.func.count().label('count'),
            SystemCallLog.status
        ).filter(
            SystemCallLog.user_id == current_user.id,
            db.func.date(SystemCallLog.executed_at) >= db.func.date_sub(
                db.func.current_date(), days
            )
        ).group_by(
            db.func.date(SystemCallLog.executed_at),
            SystemCallLog.status
        ).order_by(
            db.func.date(SystemCallLog.executed_at)
        )
    
    result = query.all()
    
    # Format data for Chart.js
    dates = sorted(list(set([row.date.strftime('%Y-%m-%d') for row in result])))
    
    # Create datasets by status
    statuses = sorted(list(set([row.status for row in result])))
    datasets = []
    
    # Colors for different statuses
    colors = {
        'Success': 'rgba(40, 167, 69, 0.8)',
        'Error': 'rgba(220, 53, 69, 0.8)',
        'Denied': 'rgba(255, 193, 7, 0.8)',
        'Timeout': 'rgba(108, 117, 125, 0.8)'
    }
    
    for status in statuses:
        data = []
        for date in dates:
            count = 0
            for row in result:
                if row.date.strftime('%Y-%m-%d') == date and row.status == status:
                    count = row.count
                    break
            data.append(count)
        
        datasets.append({
            'label': status,
            'data': data,
            'backgroundColor': colors.get(status, 'rgba(0, 123, 255, 0.8)')
        })
    
    return jsonify({
        'labels': dates,
        'datasets': datasets
    })

@bp.route('/dashboard')
@login_required
def dashboard():
    # Get recent logs
    if current_user.is_admin:
        recent_logs = SystemCallLog.query.order_by(
            SystemCallLog.executed_at.desc()
        ).limit(10).all()
        # Get user statistics
        user_count = User.query.count()
        admin_count = User.query.filter_by(is_admin=True).count()
    else:
        recent_logs = SystemCallLog.query.filter_by(
            user_id=current_user.id
        ).order_by(
            SystemCallLog.executed_at.desc()
        ).limit(10).all()
        user_count = None
        admin_count = None
    
    # Get command execution statistics
    success_count = SystemCallLog.query.filter_by(
        status="Success", 
        user_id=current_user.id if not current_user.is_admin else None
    ).count()
    
    error_count = SystemCallLog.query.filter_by(
        status="Error",
        user_id=current_user.id if not current_user.is_admin else None
    ).count()
    
    denied_count = SystemCallLog.query.filter_by(
        status="Denied",
        user_id=current_user.id if not current_user.is_admin else None
    ).count()
    
    return render_template(
        'dashboard.html', 
        recent_logs=recent_logs,
        success_count=success_count,
        error_count=error_count,
        denied_count=denied_count,
        user_count=user_count,
        admin_count=admin_count
    )

@bp.route('/permissions', methods=['GET', 'POST'])
@login_required
def permissions():
    if not current_user.is_admin:
        flash('You do not have permission to access this page', 'danger')
        return redirect(url_for('system_calls.dashboard'))
    
    # Form for adding new permissions
    form = PermissionForm()
    form.user_id.choices = [(user.id, user.username) for user in User.query.all()]
    
    if form.validate_on_submit():
        user = User.query.get(form.user_id.data)
        if user:
            # Check if permission already exists
            existing_perm = CommandPermission.query.filter_by(
                command_pattern=form.command_pattern.data
            ).first()
            
            if not existing_perm:
                # Create new permission
                permission = CommandPermission(
                    command_pattern=form.command_pattern.data,
                    description=form.description.data
                )
                db.session.add(permission)
                db.session.commit()
            else:
                permission = existing_perm
                
            # Add permission to user if not already assigned
            if permission not in user.permissions:
                user.permissions.append(permission)
                db.session.commit()
                flash(f'Permission {permission.command_pattern} added to {user.username}', 'success')
            else:
                flash(f'User already has this permission', 'warning')
                
        return redirect(url_for('system_calls.permissions'))
    
    # Get all permissions and users for display
    permissions = CommandPermission.query.all()
    users = User.query.all()
    
    return render_template('permissions.html', permissions=permissions, users=users, form=form)

@bp.route('/permissions/delete/<int:user_id>/<int:perm_id>', methods=['POST'])
@login_required
def delete_permission(user_id, perm_id):
    if not current_user.is_admin:
        flash('You do not have permission to perform this action', 'danger')
        return redirect(url_for('system_calls.dashboard'))
    
    user = User.query.get_or_404(user_id)
    permission = CommandPermission.query.get_or_404(perm_id)
    
    if permission in user.permissions:
        user.permissions.remove(permission)
        db.session.commit()
        flash(f'Permission removed from {user.username}', 'success')
    else:
        flash('Permission not found for this user', 'warning')
    
    return redirect(url_for('system_calls.permissions'))
