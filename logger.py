import logging
from datetime import datetime
from flask import current_app
from app import db
from models import SystemCallLog

def log_system_call(user_id, command, output, status, exit_code, execution_time, ip_address):
    """
    Log a system call to both the database and the application log file.
    
    Args:
        user_id: The ID of the user making the system call
        command: The command that was executed
        output: The output of the command
        status: The status of the command (Success, Error, Denied, Timeout)
        exit_code: The exit code of the command
        execution_time: The time taken to execute the command in seconds
        ip_address: The IP address of the user
    """
    try:
        # Create a new log entry in the database
        log_entry = SystemCallLog(
            user_id=user_id,
            command=command,
            output=output,
            status=status,
            exit_code=exit_code,
            execution_time=execution_time,
            ip_address=ip_address,
            executed_at=datetime.utcnow()
        )
        
        db.session.add(log_entry)
        db.session.commit()
        
        # Log to application log file
        log_message = (
            f"SYSCALL: "
            f"user_id={user_id}, "
            f"command='{command}', "
            f"status={status}, "
            f"exit_code={exit_code}, "
            f"time={execution_time:.2f}s, "
            f"ip={ip_address}"
        )
        
        if status == "Success":
            logging.info(log_message)
        elif status == "Error":
            logging.error(log_message)
        elif status == "Denied":
            logging.warning(log_message)
        else:
            logging.warning(log_message)
            
    except Exception as e:
        # Log any error that occurs during logging
        logging.error(f"Failed to log system call: {e}")
        db.session.rollback()
