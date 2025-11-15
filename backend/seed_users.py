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
    
    # Use provided db_path or fall back to extracting from DATABASE_URL
    if not db_path:
        import os
        from urllib.parse import urlparse
        database_url = os.getenv('DATABASE_URL', '')
        if database_url and database_url.startswith('sqlite:///'):
            db_path = database_url.replace('sqlite:///', '')
            # Handle 4 slashes for absolute paths
            if not db_path.startswith('/'):
                db_path = os.path.join(backend_dir, db_path)
        else:
            # Fallback to default
            db_path = os.path.join(backend_dir, 'instance', 'church_voice.db')
    
    print(f"[SEED] Loading users from: {users_json_path}")
    print(f"[SEED] Database path: {db_path}")
    
    # Ensure database directory exists (SQLite will create the file if it doesn't exist)
    db_dir = os.path.dirname(db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    
    # Load users.json
    if not os.path.exists(users_json_path):
        print(f"[SEED] WARNING: users.json not found at {users_json_path}")
        print(f"[SEED] Will create default admin user")
        users = {}
    else:
        with open(users_json_path, 'r') as f:
            data = json.load(f)
        users = data.get('users', {})
    
    print(f"[SEED] Found {len(users)} users in JSON file")
    
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
        
        # Always ensure we have the expected users from users.json
        cursor.execute("SELECT COUNT(*) FROM users")
        existing_count = cursor.fetchone()[0]
        print(f"[SEED] Currently {existing_count} users in database")
        
        # If we have 5+ users, verify they're the correct ones
        if existing_count >= 5:
            cursor.execute("SELECT username FROM users ORDER BY id LIMIT 5")
            existing_usernames = [row[0] for row in cursor.fetchall()]
            expected_usernames = list(users.keys()) if users else []
            
            # Check if we have the right users
            has_correct_users = any(users[key].get('username', key) in existing_usernames for key in expected_usernames[:3])
            
            if has_correct_users:
                print(f"[SEED] Found {existing_count} users with correct data, skipping seed")
                return True
            else:
                print(f"[SEED] Found {existing_count} users but they appear to be wrong, re-seeding")
                cursor.execute("DELETE FROM users")
                conn.commit()
        
        # If no users in JSON, create default admin
        if not users:
            print("[SEED] No users.json found, creating default admin")
            from werkzeug.security import generate_password_hash
            cursor.execute('''
                INSERT OR IGNORE INTO users (username, password_hash, full_name, email, role, active)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                'admin',
                generate_password_hash('futures2025'),
                'Administrator',
                'admin@futureschurch.com',
                'admin',
                1
            ))
            conn.commit()
            print("[SEED] Created default admin user (username: admin, password: futures2025)")
            return True
        
        # Insert or update each user
        inserted = 0
        updated = 0
        from werkzeug.security import generate_password_hash
        
        for user_key, user_data in users.items():
            # Use the actual username from user_data, not the dictionary key
            # Strip whitespace to prevent login issues
            actual_username = user_data.get('username', user_key).strip()
            full_name = user_data.get('full_name', actual_username).strip()
            
            # Get password hash - use from JSON, or generate default for admin
            password_hash = user_data.get('password_hash', '')
            if not password_hash and actual_username.lower() == 'admin':
                # Ensure admin has a known password if hash is missing
                password_hash = generate_password_hash('futures2025')
                print(f"[SEED] Generated password hash for admin user")
            
            # Check if user already exists
            cursor.execute('SELECT id FROM users WHERE username = ?', (actual_username,))
            existing = cursor.fetchone()
            
            if existing:
                # Update existing user (including password hash to ensure it's correct)
                cursor.execute('''
                    UPDATE users 
                    SET password_hash = ?, full_name = ?, email = ?, role = ?, campus = ?, active = ?
                    WHERE username = ?
                ''', (
                    password_hash,
                    full_name,
                    user_data.get('email', ''),
                    user_data.get('role', 'campus_pastor'),
                    user_data.get('campus', ''),
                    1 if user_data.get('active', True) else 0,
                    actual_username
                ))
                updated += 1
                print(f"[SEED] Updated user: {actual_username} ({user_data.get('role', 'campus_pastor')})")
            else:
                # Insert new user
                cursor.execute('''
                    INSERT INTO users 
                    (username, password_hash, full_name, email, role, campus, active)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    actual_username,
                    password_hash,
                    full_name,
                    user_data.get('email', ''),
                    user_data.get('role', 'campus_pastor'),
                    user_data.get('campus', ''),
                    1 if user_data.get('active', True) else 0
                ))
                inserted += 1
                print(f"[SEED] Inserted user: {actual_username} ({user_data.get('role', 'campus_pastor')})")
        
        conn.commit()
        print(f"[SEED] Successfully inserted {inserted} users, updated {updated} users")
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

