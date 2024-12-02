import sys
import subprocess
from modules.controller.main import controller
from modules.utils.logger import logger
from modules.utils.venv import (
    check_venv,
    create_venv,
    restart_in_venv,
    is_correct_venv
)

@controller.on("venv_status")
def handle_venv_status(event_data):
    """Handle venv status check"""
    data = event_data.get('data', {})
    status = data.get('status', 'unknown')
    logger.info(f"Virtual environment status: {status}")

@controller.on("venv_create")
def handle_venv_create(event_data):
    """Handle venv creation"""
    data = event_data.get('data', {})
    path = data.get('path', 'unknown')
    logger.info(f"Virtual environment created at: {path}")

@controller.on("venv_restart")
def handle_venv_restart(event_data):
    """Handle venv restart"""
    data = event_data.get('data', {})
    python_path = data.get('python_path', 'unknown')
    logger.info(f"Restarting with Python: {python_path}")

@controller.on("check_environment")
def handle_venv_check(event_data):
    """Handler for checking and ensuring virtual environment"""
    try:
        # Check current status
        check_venv()
        
        # If not in correct venv
        if not is_correct_venv():
            # Create if needed
            create_venv()
            
            # Get restart info
            restart_data = restart_in_venv()
            python_path = restart_data.get('python_path')
            
            logger.info("Restarting in virtual environment...")
            try:
                # Use subprocess to start a new process with the venv Python
                subprocess.run(
                    [python_path, sys.argv[0]],
                    check=True
                )
                sys.exit(0)  # Exit the current process
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to restart in virtual environment: {e}")
                sys.exit(1)
                
    except Exception as e:
        logger.error(f"Error managing virtual environment: {e}")
        raise