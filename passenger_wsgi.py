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

# Create a simple application variable for passenger
try:
    # Import the Flask app but make sure it doesn't run with app.run()
    from app import app as application
except Exception as e:
    # Create a simple WSGI application for debugging
    def application(environ, start_response):
        status = '500 Internal Server Error'
        output = f'Passenger Python Application Error: {str(e)}'.encode('utf-8')
        response_headers = [('Content-type', 'text/plain'), ('Content-Length', str(len(output)))]
        start_response(status, response_headers)
        return [output]

# Uncomment this if you need to work around middleware issues
# def application(environ, start_response):
#     environ['SCRIPT_NAME'] = ''
#     return app(environ, start_response)