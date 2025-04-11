import sys
import os

# Get the current directory
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# Add virtualenv if it exists (cPanel Python App creates this)
VIRTUALENV = os.path.join(CURRENT_DIR, 'venv')
if os.path.exists(VIRTUALENV):
    PYTHON_PATH = os.path.join(VIRTUALENV, 'bin', 'python')
    if os.path.exists(PYTHON_PATH):
        # Use virtualenv Python
        if sys.executable != PYTHON_PATH:
            os.execl(PYTHON_PATH, PYTHON_PATH, *sys.argv)
else:
    # Use system Python if no virtualenv
    INTERP = "/usr/bin/python3"
    if sys.executable != INTERP:
        os.execl(INTERP, INTERP, *sys.argv)

# Add application directory to Python path
sys.path.insert(0, CURRENT_DIR)

# Create the 'application' object that Passenger looks for
from app import app as application

# Uncomment this if you need to work around middleware issues
# def application(environ, start_response):
#     environ['SCRIPT_NAME'] = ''
#     return app(environ, start_response)