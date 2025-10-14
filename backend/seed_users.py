#!/usr/bin/env python3
"""
Seed users from users.json into the database
"""
import json
import sqlite3
import os
import sys

def seed_users():
    """Load users from users.json into database"""
    
    # Get paths
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    users_json_path = os.path.join(backend_dir, 'users.json')
    db_path = os.path.join(backend_dir, 'instance', 'church_voice.db')
    
    print(f"[SEED] Loading users from: {users_json_path}")
    print(f"[SEED] Database path: {db_path}")
    
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
    
    # Connect to database
    if not os.path.exists(db_path):
        print(f"[SEED] ERROR: Database not found at {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check how many users already exist
        cursor.execute("SELECT COUNT(*) FROM users")
        existing_count = cursor.fetchone()[0]
        print(f"[SEED] Currently {existing_count} users in database")
        
        # Only skip if we have at least 2 users (not just the default admin)
        if existing_count >= 2:
            print(f"[SEED] Found {existing_count} users, skipping seed")
            return True
        
        # If no users in JSON, create default admin
        if not users:
            print("[SEED] No users.json found, creating default admin")
            from werkzeug.security import generate_password_hash
            cursor.execute('''
                INSERT INTO users (username, password_hash, full_name, email, role, active)
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
        
        # Insert each user
        inserted = 0
        for username, user_data in users.items():
            cursor.execute('''
                INSERT INTO users 
                (username, password_hash, full_name, email, role, campus, active)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                username,
                user_data.get('password_hash', ''),
                user_data.get('full_name', username),
                user_data.get('email', ''),
                user_data.get('role', 'campus_pastor'),
                user_data.get('campus', ''),
                1 if user_data.get('active', True) else 0
            ))
            
            inserted += 1
            print(f"[SEED] Inserted user: {username} ({user_data.get('role', 'campus_pastor')})")
        
        conn.commit()
        print(f"[SEED] Successfully inserted {inserted} users")
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

