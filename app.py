import sqlite3
import json
from flask import Flask, request, jsonify, render_template, g, send_file
from flask_cors import CORS
import datetime
import re # Import regex for parsing
import os
import shutil
import tempfile

# Change the template folder to point to the backend/templates directory
template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'linkedin_crm/backend/templates')
app = Flask(__name__, template_folder=template_dir)
# Allow requests from the Chrome extension's origin
# CORS(app, resources={r"/api/*": {"origins": "chrome-extension://*"}}) # Original line
CORS(app) # Allow all origins for debugging

# Set the database path to the backend directory
DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'linkedin_crm/backend/database.db')

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys = ON") # Enforce foreign key constraints
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    """Initializes the database with the new schema."""
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        print("Initializing database schema...")

        # Drop existing tables if they exist (for easier re-initialization)
        # Use with caution in production
        # cursor.execute("DROP TABLE IF EXISTS featured;")
        # cursor.execute("DROP TABLE IF EXISTS recommendations;")
        # cursor.execute("DROP TABLE IF EXISTS skills;")
        # cursor.execute("DROP TABLE IF EXISTS education;")
        # cursor.execute("DROP TABLE IF EXISTS experience;")
        # cursor.execute("DROP TABLE IF EXISTS profiles;")

        # Profiles Table (Core Info)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            linkedin_url TEXT UNIQUE NOT NULL,
            name TEXT,
            headline TEXT,
            location TEXT,
            about TEXT,
            profile_pic_url TEXT,
            banner_pic_url TEXT,
            followers TEXT,
            connections TEXT,
            website TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """)
        print("Created profiles table.")

        # Experience Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS experience (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_id INTEGER NOT NULL,
            title TEXT,
            company_name TEXT,
            company_linkedin_url TEXT,
            employment_type TEXT, -- e.g., Full-time, Part-time, Self-employed
            location TEXT,
            start_date TEXT,
            end_date TEXT,
            duration TEXT,
            description TEXT,
            is_multi_role INTEGER DEFAULT 0, -- Flag if part of a multi-role entry
            parent_experience_id INTEGER, -- Link sub-roles to main company entry
            FOREIGN KEY (profile_id) REFERENCES profiles (id) ON DELETE CASCADE
        );
        """)
        print("Created experience table.")

        # Education Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS education (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_id INTEGER NOT NULL,
            school_name TEXT,
            school_linkedin_url TEXT,
            degree_name TEXT,
            field_of_study TEXT,
            start_date TEXT,
            end_date TEXT,
            grade TEXT,
            activities TEXT,
            description TEXT,
            FOREIGN KEY (profile_id) REFERENCES profiles (id) ON DELETE CASCADE
        );
        """)
        print("Created education table.")

        # Skills Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_id INTEGER NOT NULL,
            skill_name TEXT NOT NULL,
            UNIQUE(profile_id, skill_name), -- Avoid duplicate skills per profile
            FOREIGN KEY (profile_id) REFERENCES profiles (id) ON DELETE CASCADE
        );
        """)
        print("Created skills table.")

        # Recommendations Table (Received)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS recommendations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_id INTEGER NOT NULL,
            recommender_name TEXT,
            recommender_headline TEXT,
            recommender_linkedin_url TEXT,
            relationship TEXT,
            recommendation_text TEXT,
            FOREIGN KEY (profile_id) REFERENCES profiles (id) ON DELETE CASCADE
        );
        """)
        print("Created recommendations table.")

         # Featured Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS featured (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_id INTEGER NOT NULL,
            title TEXT,
            link TEXT,
            description TEXT,
            image_url TEXT,
            type TEXT, -- e.g., Link, Post, Article
            FOREIGN KEY (profile_id) REFERENCES profiles (id) ON DELETE CASCADE
        );
        """)
        print("Created featured table.")

        db.commit()
        print("Database initialized successfully.")

@app.route('/')
def index():
    """Show minimal list of saved profiles."""
    db = get_db()
    profiles_data = []
    try:
        # Fetch all profiles with minimal data (remove industry column which doesn't exist)
        profiles_cursor = db.execute('SELECT id, name, headline, location, linkedin_url, profile_pic_url, banner_pic_url, timestamp FROM profiles ORDER BY timestamp DESC')
        profiles = profiles_cursor.fetchall()
        profiles_data = [dict(profile) for profile in profiles]
    except sqlite3.Error as e:
        print(f"Database error fetching profiles: {e}")
        return render_template('index.html', profiles=[], error=f"Database Error: {e}")

    return render_template('index.html', profiles=profiles_data)

@app.route('/profile/<int:profile_id>')
def view_profile(profile_id):
    """Show detailed view of a single profile."""
    db = get_db()
    try:
        # Fetch the profile
        profile_cursor = db.execute('SELECT * FROM profiles WHERE id = ?', (profile_id,))
        profile = profile_cursor.fetchone()
        
        if not profile:
            return render_template('index_detailed.html', profiles=[], error=f"Profile not found")
        
        profile_dict = dict(profile)
        
        # Fetch related data for the profile
        exp_cursor = db.execute('SELECT * FROM experience WHERE profile_id = ? ORDER BY id', (profile_id,))
        profile_dict['experience'] = [dict(row) for row in exp_cursor.fetchall()]

        edu_cursor = db.execute('SELECT * FROM education WHERE profile_id = ? ORDER BY id', (profile_id,))
        profile_dict['education'] = [dict(row) for row in edu_cursor.fetchall()]

        skills_cursor = db.execute('SELECT * FROM skills WHERE profile_id = ? ORDER BY skill_name', (profile_id,))
        profile_dict['skills'] = [dict(row) for row in skills_cursor.fetchall()]

        rec_cursor = db.execute('SELECT * FROM recommendations WHERE profile_id = ? ORDER BY id', (profile_id,))
        profile_dict['recommendations'] = [dict(row) for row in rec_cursor.fetchall()]

        feat_cursor = db.execute('SELECT * FROM featured WHERE profile_id = ? ORDER BY id', (profile_id,))
        profile_dict['featured'] = [dict(row) for row in feat_cursor.fetchall()]

        return render_template('index_detailed.html', profiles=[profile_dict])
        
    except sqlite3.Error as e:
        print(f"Database error fetching profile: {e}")
        return render_template('index_detailed.html', profiles=[], error=f"Database Error: {e}")

@app.route('/api/save_profile', methods=['POST'])
def save_profile():
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.get_json()
    # print("Received data:", json.dumps(data, indent=2)) # Extensive Debugging

    required_fields = ['name', 'headline', 'linkedin_url']
    if not all(field in data and data[field] is not None for field in required_fields):
        missing = [field for field in required_fields if not (field in data and data[field] is not None)]
        print(f"Missing required fields: {missing}")
        return jsonify({"error": "Missing required fields", "missing": missing}), 400

    db = get_db()
    cursor = db.cursor()
    profile_id = None

    try:
        # --- Start Transaction ---
        cursor.execute("BEGIN")

        # 1. Insert or Update Profile (Base Info)
        profile_base_sql = '''
            INSERT INTO profiles (linkedin_url, name, headline, location, about, profile_pic_url, banner_pic_url, followers, connections, website, timestamp)
            VALUES (:linkedin_url, :name, :headline, :location, :about, :profile_pic_url, :banner_pic_url, :followers, :connections, :website, CURRENT_TIMESTAMP)
            ON CONFLICT(linkedin_url) DO UPDATE SET
                name=excluded.name,
                headline=excluded.headline,
                location=excluded.location,
                about=excluded.about,
                profile_pic_url=excluded.profile_pic_url,
                banner_pic_url=excluded.banner_pic_url,
                followers=excluded.followers,
                connections=excluded.connections,
                website=excluded.website,
                timestamp=CURRENT_TIMESTAMP;
        '''
        profile_base_data = {
            'linkedin_url': data.get('linkedin_url'),
            'name': data.get('name'),
            'headline': data.get('headline'),
            'location': data.get('location'),
            'about': data.get('about'),
            'profile_pic_url': data.get('profile_pic_url'),
            'banner_pic_url': data.get('banner_pic_url'),
            'followers': data.get('followers'),
            'connections': data.get('connections'),
            'website': data.get('website')
        }
        cursor.execute(profile_base_sql, profile_base_data)

        # Get the ID of the inserted/updated profile
        cursor.execute("SELECT id FROM profiles WHERE linkedin_url = ?", (data['linkedin_url'],))
        profile_row = cursor.fetchone()
        if not profile_row:
             raise Exception("Failed to retrieve profile ID after insert/update.")
        profile_id = profile_row['id']
        print(f"Profile ID: {profile_id}")

        # 2. Clear existing related data for this profile_id
        cursor.execute("DELETE FROM experience WHERE profile_id = ?", (profile_id,))
        cursor.execute("DELETE FROM education WHERE profile_id = ?", (profile_id,))
        cursor.execute("DELETE FROM skills WHERE profile_id = ?", (profile_id,))
        cursor.execute("DELETE FROM recommendations WHERE profile_id = ?", (profile_id,))
        cursor.execute("DELETE FROM featured WHERE profile_id = ?", (profile_id,))
        print("Cleared old related data.")

        # 3. Insert Experience
        exp_sql = '''INSERT INTO experience (profile_id, title, company_name, company_linkedin_url, employment_type, location, start_date, end_date, duration, description, is_multi_role, parent_experience_id)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'''
        if data.get('experience'):
            for exp in data['experience']:
                # Simple check for required fields in experience entry
                if exp.get('title') and exp.get('company_name'):
                    cursor.execute(exp_sql, (
                        profile_id,
                        exp.get('title'),
                        exp.get('company_name'),
                        exp.get('company_linkedin_url'),
                        exp.get('employment_type'),
                        exp.get('location'),
                        exp.get('start_date'),
                        exp.get('end_date'),
                        exp.get('duration'),
                        exp.get('description'),
                        exp.get('is_multi_role', 0),
                        exp.get('parent_experience_id') # This needs careful handling in scraping logic
                    ))
            print(f"Inserted {len(data['experience'])} experience entries.")

        # 4. Insert Education
        edu_sql = '''INSERT INTO education (profile_id, school_name, school_linkedin_url, degree_name, field_of_study, start_date, end_date, grade, activities, description)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'''
        if data.get('education'):
             for edu in data['education']:
                 if edu.get('school_name'): # Basic check
                     cursor.execute(edu_sql, (
                         profile_id,
                         edu.get('school_name'),
                         edu.get('school_linkedin_url'),
                         edu.get('degree_name'),
                         edu.get('field_of_study'),
                         edu.get('start_date'),
                         edu.get('end_date'),
                         edu.get('grade'),
                         edu.get('activities'),
                         edu.get('description')
                     ))
             print(f"Inserted {len(data['education'])} education entries.")

        # 5. Insert Skills
        skill_sql = 'INSERT INTO skills (profile_id, skill_name) VALUES (?, ?)'
        if data.get('skills'):
            for skill in data['skills']:
                if isinstance(skill, str) and skill: # Ensure it's a non-empty string
                     # Use INSERT OR IGNORE to handle potential duplicates from UNIQUE constraint
                     cursor.execute('INSERT OR IGNORE INTO skills (profile_id, skill_name) VALUES (?, ?)', (profile_id, skill))
            print(f"Inserted/ignored {len(data['skills'])} skill entries.")

        # 6. Insert Recommendations (Received)
        rec_sql = '''INSERT INTO recommendations (profile_id, recommender_name, recommender_headline, recommender_linkedin_url, relationship, recommendation_text)
                     VALUES (?, ?, ?, ?, ?, ?)'''
        if data.get('recommendations'):
             for rec in data['recommendations']:
                 if rec.get('recommender_name') and rec.get('recommendation_text'): # Basic check
                     cursor.execute(rec_sql, (
                         profile_id,
                         rec.get('recommender_name'),
                         rec.get('recommender_headline'),
                         rec.get('recommender_linkedin_url'),
                         rec.get('relationship'),
                         rec.get('recommendation_text')
                     ))
             print(f"Inserted {len(data['recommendations'])} recommendation entries.")

        # 7. Insert Featured
        feat_sql = '''INSERT INTO featured (profile_id, title, link, description, image_url, type)
                      VALUES (?, ?, ?, ?, ?, ?)'''
        if data.get('featured'):
            for feat in data['featured']:
                if feat.get('title') or feat.get('description'): # Basic check
                    cursor.execute(feat_sql, (
                        profile_id,
                        feat.get('title'),
                        feat.get('link'),
                        feat.get('description'),
                        feat.get('image_url'),
                        feat.get('type')
                    ))
            print(f"Inserted {len(data['featured'])} featured entries.")


        # --- Commit Transaction ---
        db.commit()
        print("Transaction committed.")
        return jsonify({"success": True, "message": "Profile saved/updated successfully.", "profile_id": profile_id}), 201

    except sqlite3.Error as e:
        db.rollback() # Rollback on error
        print(f"Database error during save: {e}")
        print(f"Failed SQL Data (example): {profile_base_data if 'profile_base_data' in locals() else 'N/A'}")
        return jsonify({"error": "Database error", "details": str(e)}), 500
    except Exception as e:
        db.rollback() # Rollback on unexpected error
        print(f"An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "An unexpected server error occurred", "details": str(e)}), 500

@app.route('/download-extension')
def download_extension():
    """Create a zip file of the extension directory and send it for download."""
    extension_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'linkedin_crm/extension')
    
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(temp_dir, 'linkedin_crm_extension.zip')
    
    # Create a zip file of the extension directory
    shutil.make_archive(os.path.splitext(zip_path)[0], 'zip', extension_dir)
    
    return send_file(zip_path, as_attachment=True, download_name='linkedin_crm_extension.zip')

if __name__ == '__main__':
    init_db() # Initialize DB schema
    app.run(host='0.0.0.0', port=5000, debug=False)