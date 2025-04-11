# LinkedIn CRM Deployment Guide

This guide will help you deploy the LinkedIn CRM application to cPanel, configure the domain name, and set up the browser extension.

## Requirements

- cPanel access
- Python 3.6+ support on your hosting
- Domain or subdomain (3rm.inlinkai.com)
- FTP access or cPanel File Manager

## 1. Preparing the Application

1. Create a ZIP file of your entire project folder (exclude venv/ and any other unnecessary files)
2. Make sure your `app.py` is configured to run in production:
   - Remove debug mode (`debug=True`)
   - Set the host to '0.0.0.0' to allow external connections

```python
if __name__ == '__main__':
    init_db()  # Initialize DB schema
    app.run(host='0.0.0.0', port=5000, debug=False)
```

## 2. Setting up cPanel

1. Log in to your cPanel account
2. In the "Files" section, click on "File Manager"
3. Navigate to the root directory or create a new directory for your application (e.g., `public_html/3rm`)

## 3. Uploading Your Application

1. In File Manager, click "Upload" and select your project ZIP file
2. Extract the ZIP file
3. Ensure proper file permissions:
   - Python files (.py): 644
   - Directories: 755
   - database.db (and its directory): 755

## 4. Setting Up Python Application in cPanel

### Option 1: Using Python App (if available in your cPanel)

1. In cPanel, look for "Setup Python App" or similar
2. Create a new Python application:
   - Python version: 3.6+
   - Application root: path to your app folder (e.g., `/home/username/public_html/3rm`)
   - Application URL: http://3rm.inlinkai.com
   - Application startup file: app.py (now in the root directory)
   - Application Entry point: app

3. Install dependencies:
   - In the application configuration, add your requirements.txt
   - Or manually install using SSH: `pip install -r requirements.txt`

### Option 2: Using Passenger (if Python App is not available)

1. Create a `.htaccess` file in your application root directory with:

```
PassengerEnabled On
PassengerAppType wsgi
PassengerAppRoot /home/username/public_html/3rm
PassengerPython /usr/bin/python3
PassengerStartupFile passenger_wsgi.py
```

2. The `passenger_wsgi.py` file is already configured to use the app.py in the root directory:

```python
import sys, os
import importlib.util

# Add the application directory to the Python path
INTERP = "/usr/bin/python3"
if sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)

# Path to your app
app_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, app_dir)

# Import your Flask app from the root directory
from app import app as application
```

## 5. Database Configuration

1. Since you're using SQLite3, ensure the database file and its directory are writable:
   ```
   chmod 755 /path/to/your/app/linkedin_crm/backend
   chmod 664 /path/to/your/app/linkedin_crm/backend/database.db
   ```

2. If the database doesn't exist yet, it will be created when the application runs (via `init_db()`)

## 6. Domain Setup

1. In cPanel, go to "Domains" or "Subdomains"
2. Add a subdomain:
   - Subdomain: 3rm
   - Domain: inlinkai.com
   - Document Root: /public_html/3rm (or wherever you placed your app)

3. Wait for DNS propagation (may take up to 24-48 hours)

## 7. Extension Configuration

Before deploying, update the API URL in your extension's `content.js` file:

1. Open `linkedin_crm/extension/content.js`
2. Find the line: `const apiUrl = '3rm/api/save_profile';`
3. Change it to: `const apiUrl = 'https://3rm.inlinkai.com/api/save_profile';`
4. Repackage your extension as described in the homepage instructions

## 8. Testing Your Deployment

1. Visit http://3rm.inlinkai.com
2. You should see the LinkedIn CRM homepage
3. If there are issues, check the error logs in cPanel (under "Logs" or "Error Log")

## 9. Common Issues and Solutions

### 500 Internal Server Error

- Check file permissions
- Check error logs
- Ensure Python version compatibility
- Make sure all dependencies are installed

### Extension Not Connecting

- Verify the API URL in content.js
- Check browser console for CORS errors
- Ensure https is used if your domain has SSL

### Database Issues

- Check if the database file is writable
- Ensure the database path in app.py is absolute or correctly relative

## 10. Security Considerations

1. Add proper authentication to your application
2. Consider setting up HTTPS (cPanel often provides Let's Encrypt)
3. Regularly backup your database
4. Don't expose your database file via the web (ensure it's outside public_html or protected)

## 11. Maintenance

- Regularly check for disk space usage (SQLite DB will grow over time)
- Set up automated backups of your database file
- Monitor error logs for any issues

For support, questions, or contributions, please contact: [your contact information] 