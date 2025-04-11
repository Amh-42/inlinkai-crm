CREATE TABLE IF NOT EXISTS profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    profile_pic_url TEXT,
    banner_pic_url TEXT,
    headline TEXT,
    summary TEXT,
    experience TEXT,
    featured TEXT,
    industry TEXT,
    linkedin_url TEXT UNIQUE,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
); 