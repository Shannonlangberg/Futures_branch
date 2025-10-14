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
        
        # Insert each user (INSERT OR IGNORE to avoid duplicates)
        inserted = 0
        for user_key, user_data in users.items():
            # Use the actual username from user_data, not the dictionary key
            actual_username = user_data.get('username', user_key)
            cursor.execute('''
                INSERT OR IGNORE INTO users 
                (username, password_hash, full_name, email, role, campus, active)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                actual_username,
                user_data.get('password_hash', ''),
                user_data.get('full_name', actual_username),
                user_data.get('email', ''),
                user_data.get('role', 'campus_pastor'),
                user_data.get('campus', ''),
                1 if user_data.get('active', True) else 0
            ))
            
            inserted += 1
            print(f"[SEED] Inserted user: {actual_username} ({user_data.get('role', 'campus_pastor')})")
        
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

