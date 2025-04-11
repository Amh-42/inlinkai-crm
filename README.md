# LinkedIn CRM Deployment Guide

This guide will walk you through deploying the LinkedIn CRM application on a cPanel hosting environment.

## Deployment Overview

- **Database**: inlinkff_crm
- **Domain**: 3rm3.inlinkai.com

## 1. Prerequisites

- cPanel hosting account with Python application support
- SSH access to your hosting (recommended)
- MySQL database access
- Domain/subdomain already pointing to your hosting

## 2. File Preparation

1. Download your LinkedIn CRM application as a ZIP file
2. Extract the files locally
3. Modify the database configuration in `linkedin_crm/backend/app.py`:

```python
# Replace SQLite with MySQL
import pymysql

# Replace the existing DATABASE line
# DATABASE = 'database.db'

# MySQL Configuration
MYSQL_HOST = 'localhost'
MYSQL_USER = 'inlinkff_crmuser'  # Create this user in cPanel
MYSQL_PASSWORD = 'your_secure_password'  # Use a secure password
MYSQL_DB = 'inlinkff_crm'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = pymysql.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DB,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()
```

4. Update the schema to work with MySQL by modifying the `init_db()` function in `app.py`:

```python
def init_db():
    """Initializes the database with the schema for MySQL."""
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        print("Initializing database schema...")

        # MySQL version of the schema
        # Note: Change autoincrement syntax and some data types
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS profiles (
            id INT AUTO_INCREMENT PRIMARY KEY,
            linkedin_url VARCHAR(255) UNIQUE NOT NULL,
            name VARCHAR(255),
            headline TEXT,
            location VARCHAR(255),
            about TEXT,
            profile_pic_url TEXT,
            banner_pic_url TEXT,
            followers VARCHAR(50),
            connections VARCHAR(50),
            website TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """)
        print("Created profiles table.")

        # Repeat similar changes for other tables (experience, education, skills, etc.)
        # Remember to change:
        # - INTEGER PRIMARY KEY AUTOINCREMENT to INT AUTO_INCREMENT PRIMARY KEY
        # - TEXT to TEXT or VARCHAR as appropriate
        # - DATETIME DEFAULT CURRENT_TIMESTAMP stays the same

        db.commit()
        print("Database initialized successfully.")
```

5. Update the extension's API endpoint in `linkedin_crm/extension/content.js`:

```javascript
// Change this line to point to your domain
const apiUrl = 'https://3rm3.inlinkai.com/api/save_profile';
```

## 3. Database Setup

1. Log in to cPanel
2. Navigate to "MySQL Databases"
3. Create a new database named `inlinkff_crm`
4. Create a new user (e.g., `inlinkff_crmuser`) with a secure password
5. Add the user to the database with "All Privileges"
6. Make note of the database name, username, and password

## 4. Domain Configuration

1. Log in to cPanel
2. Navigate to "Domains" or "Subdomains"
3. Set up the subdomain `3rm3.inlinkai.com` if not already created
4. Point the subdomain to the directory where you'll upload the application (e.g., `public_html/linkedin_crm`)

## 5. Application Upload

1. Log in to cPanel
2. Navigate to "File Manager"
3. Go to the directory where your subdomain points (e.g., `public_html`)
4. Create a new folder called `linkedin_crm`
5. Upload your application files to this folder
6. Set the correct permissions:
   - Directories: 755 (`drwxr-xr-x`)
   - Files: 644 (`-rw-r--r--`)
   - Set `app.py` to 755 (`-rwxr-xr-x`) if needed

## 6. Python Environment Setup

1. Log in to your server via SSH:
   ```
   ssh username@your-cpanel-server.com
   ```

2. Navigate to your application directory:
   ```
   cd public_html/linkedin_crm
   ```

3. Create a virtual environment:
   ```
   python3 -m venv venv
   ```

4. Activate the virtual environment:
   ```
   source venv/bin/activate
   ```

5. Install required packages:
   ```
   pip install flask flask-cors pymysql gunicorn
   pip install -r requirements.txt
   ```

## 7. WSGI Configuration

1. Create a file named `passenger_wsgi.py` in your application directory with the following content:

```python
import sys, os

# Add the application directory to the Python path
INTERP = os.path.join(os.getcwd(), 'venv', 'bin', 'python')
if sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)

# Adjust the path to your application
sys.path.append(os.getcwd() + '/linkedin_crm')

# Import your Flask app
from linkedin_crm.backend.app import app as application
```

2. Create a `.htaccess` file in the same directory:

```
RewriteEngine On
RewriteCond %{REQUEST_FILENAME} !-f
RewriteRule ^(.*)$ /passenger_wsgi.py/$1 [QSA,L]
```

## 8. Initialize the Database

1. SSH into your server and navigate to your application directory
2. Activate the virtual environment:
   ```
   source venv/bin/activate
   ```
3. Run the Python shell:
   ```
   python
   ```
4. Initialize the database:
   ```python
   from linkedin_crm.backend.app import init_db
   init_db()
   exit()
   ```

## 9. Application Restart

1. In cPanel, navigate to "Setup Python App"
2. Restart your Python application if necessary
3. Alternatively, in some cPanel setups, you might need to run:
   ```
   touch tmp/restart.txt
   ```

## 10. Browser Extension Setup

1. Download the browser extension from your deployed site at `https://3rm3.inlinkai.com/download-extension`
2. Unzip the extension file
3. Open Chrome and go to `chrome://extensions/`
4. Enable "Developer mode" (toggle in the top-right corner)
5. Click "Load unpacked" and select the unzipped extension folder
6. The LinkedIn CRM extension icon should appear in your browser toolbar

## 11. Testing Your Deployment

1. Open a web browser and navigate to `https://3rm3.inlinkai.com`
2. Verify that the LinkedIn CRM interface loads correctly
3. Test the extension by visiting a LinkedIn profile and clicking the extension icon
4. Verify that profiles are being saved to your CRM

## Troubleshooting

### Application Not Loading
- Check the server error logs in cPanel
- Verify file permissions
- Ensure the Python application is running

### Database Connection Issues
- Verify database credentials
- Check if the MySQL user has correct permissions
- Ensure the database exists and is accessible

### Extension Not Working
- Check that the backend URL in the extension's configuration is correct
- Verify CORS settings in your Flask application
- Check browser console for any errors

## Maintenance

- Regularly backup your database through cPanel
- Keep Python packages updated using pip
- Monitor server logs for any errors or performance issues

## Security Considerations

- Use HTTPS for your domain
- Keep passwords secure and complex
- Regularly update the application and dependencies
- Restrict file permissions appropriately