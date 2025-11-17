#!/usr/bin/env python3
"""
Seed users from users.json into the database
"""
import json
import sqlite3
import os
import sys

def seed_users(db_path=None):
    """Load users from users.json into database"""
    
    # Get paths
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    users_json_path = os.path.join(backend_dir, 'users.json')
    
    # Use provided db_path or use the same path as app.py (CHURCH_VOICE_DB_PATH)
    if not db_path:
        # Default to the same path as authentication uses (CHURCH_VOICE_DB_PATH)
        db_path = os.path.join(backend_dir, 'instance', 'church_voice.db')
        
        # On Railway, the database might be at /data/futures_link.db
        # Check DATABASE_URL and if it points to a mounted volume, use that
        database_url = os.getenv('DATABASE_URL', '')
        if database_url and database_url.startswith('sqlite:///'):
            # Extract path from DATABASE_URL (handles both sqlite:/// and sqlite:////)
            potential_path = database_url.replace('sqlite:///', '')
            # Handle 4 slashes (sqlite:////) - remove one more slash
            if potential_path.startswith('/'):
                # This is an absolute path (Railway mounted volume)
                # Check if users table exists there - if so, use it
                import sqlite3
                try:
                    test_conn = sqlite3.connect(potential_path)
                    test_cursor = test_conn.cursor()
                    test_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
                    if test_cursor.fetchone():
                        # Users table exists in this database, use it
                        db_path = potential_path
                        print(f"[SEED] Found users table in DATABASE_URL database, using: {db_path}")
                    test_conn.close()
                except:
                    pass  # Fall back to default
    
    print(f"[SEED] Ensuring admin user exists")
    print(f"[SEED] Database path: {db_path}")
    
    # Ensure database directory exists (SQLite will create the file if it doesn't exist)
    db_dir = os.path.dirname(db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    
    # Connect to database (SQLite will create the file if it doesn't exist)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if users table exists (migrations should create it, but handle gracefully)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if not cursor.fetchone():
            print(f"[SEED] WARNING: users table does not exist yet. Migrations may not have run.")
            print(f"[SEED] Users table should be created by migration 012_users_table.sql")
            conn.close()
            return False
        
        # Check if admin user exists
        cursor.execute("SELECT id FROM users WHERE username = ?", ('admin',))
        admin_exists = cursor.fetchone()
        
        # Always ensure admin user exists with correct password
        from werkzeug.security import generate_password_hash
        admin_password_hash = generate_password_hash('futures2025')
        
        if admin_exists:
            # Update existing admin to ensure password is correct
            cursor.execute('''
                UPDATE users 
                SET password_hash = ?, full_name = ?, email = ?, role = ?, active = 1
                WHERE username = ?
            ''', (
                admin_password_hash,
                'Administrator',
                'admin@futures.church',
                'admin',
                'admin'  # WHERE username = ?
            ))
            print("[SEED] Updated admin user (username: admin, password: futures2025)")
        else:
            # Create admin user
            cursor.execute('''
                INSERT INTO users (username, password_hash, full_name, email, role, campus, active)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                'admin',
                admin_password_hash,
                'Administrator',
                'admin@futures.church',
                'admin',
                'all_campuses',
                1
            ))
            print("[SEED] Created default admin user (username: admin, password: futures2025)")
        
        conn.commit()
        print("[SEED] Admin user ensured successfully")
        return True
        
    except Exception as e:
        print(f"[SEED] ERROR: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == '__main__':
    success = seed_users()
    sys.exit(0 if success else 1)

