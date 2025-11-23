#!/usr/bin/env python3
"""
Copy users from beta database to main database
This script exports users from beta and imports them to main
"""
import sqlite3
import os
import sys
import json

def get_database_path(service_name="main"):
    """
    Get database path using the same logic as app.py
    service_name: "main" or "beta" - just for logging
    """
    # Check DATABASE_URL first
    database_url = os.getenv('DATABASE_URL', '').strip()
    
    if database_url and database_url.startswith('sqlite:///'):
        potential_path = database_url.replace('sqlite:///', '')
        if potential_path.startswith('/'):
            print(f"[{service_name.upper()}] Using DATABASE_URL path: {potential_path}")
            return potential_path
    
    # Check for Railway volumes
    volume_paths = [
        '/data',  # Common Railway volume path (RECOMMENDED)
        '/app/backend/instance',  # Alternative Railway volume path
        '/app/data',  # Another common path
    ]
    
    for volume_path in volume_paths:
        if os.path.exists(volume_path) and os.path.isdir(volume_path):
            db_file = os.path.join(volume_path, 'futures_link.db')
            if os.path.exists(db_file):
                print(f"[{service_name.upper()}] Found volume at {volume_path}, using: {db_file}")
                return db_file
    
    # Fallback to local development path
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    instance_path = os.path.join(backend_dir, 'instance', 'futures_link.db')
    if os.path.exists(instance_path):
        print(f"[{service_name.upper()}] Using local instance path: {instance_path}")
        return instance_path
    
    # Last resort
    backend_path = os.path.join(backend_dir, 'futures_link.db')
    print(f"[{service_name.upper()}] Using fallback path: {backend_path}")
    return backend_path

def export_users_from_beta():
    """Export all users from beta database to a JSON file"""
    print("\n=== EXPORTING USERS FROM BETA ===")
    
    # Get beta database path
    beta_db_path = get_database_path("beta")
    
    if not os.path.exists(beta_db_path):
        print(f"ERROR: Beta database not found at: {beta_db_path}")
        print("Make sure you're running this on the beta service or have access to the beta database")
        return None
    
    try:
        conn = sqlite3.connect(beta_db_path)
        cursor = conn.cursor()
        
        # Check if users table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if not cursor.fetchone():
            print("ERROR: users table does not exist in beta database")
            conn.close()
            return None
        
        # Get all users
        cursor.execute("""
            SELECT id, username, password_hash, full_name, email, role, campus, active, 
                   created_at, last_login
            FROM users
        """)
        
        users = []
        for row in cursor.fetchall():
            user = {
                'id': row[0],
                'username': row[1],
                'password_hash': row[2],
                'full_name': row[3],
                'email': row[4],
                'role': row[5],
                'campus': row[6],
                'active': row[7],
                'created_at': row[8] if row[8] else None,
                'last_login': row[9] if row[9] else None
            }
            users.append(user)
        
        conn.close()
        
        print(f"✅ Exported {len(users)} users from beta database")
        
        # Save to JSON file
        export_file = os.path.join(os.path.dirname(__file__), 'users_export_from_beta.json')
        with open(export_file, 'w') as f:
            json.dump({'users': users}, f, indent=2)
        
        print(f"✅ Saved users to: {export_file}")
        return export_file
        
    except Exception as e:
        print(f"ERROR exporting users: {e}")
        import traceback
        traceback.print_exc()
        return None

def import_users_to_main(export_file=None):
    """Import users from export file to main database"""
    print("\n=== IMPORTING USERS TO MAIN ===")
    
    # Get main database path
    main_db_path = get_database_path("main")
    
    if not os.path.exists(main_db_path):
        print(f"ERROR: Main database not found at: {main_db_path}")
        print("Make sure you're running this on the main service or have access to the main database")
        return False
    
    # Load users from export file
    if not export_file:
        export_file = os.path.join(os.path.dirname(__file__), 'users_export_from_beta.json')
    
    if not os.path.exists(export_file):
        print(f"ERROR: Export file not found: {export_file}")
        print("Run export first or provide the export file path")
        return False
    
    try:
        with open(export_file, 'r') as f:
            data = json.load(f)
            users = data.get('users', [])
        
        if not users:
            print("ERROR: No users found in export file")
            return False
        
        print(f"Loading {len(users)} users from export file")
        
        # Connect to main database
        conn = sqlite3.connect(main_db_path)
        cursor = conn.cursor()
        
        # Check if users table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if not cursor.fetchone():
            print("ERROR: users table does not exist in main database")
            print("Run migrations first!")
            conn.close()
            return False
        
        # Import users
        imported = 0
        updated = 0
        skipped = 0
        
        for user in users:
            username = user.get('username')
            if not username:
                skipped += 1
                continue
            
            # Check if user already exists
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            exists = cursor.fetchone()
            
            if exists:
                # Update existing user (preserve their ID)
                cursor.execute("""
                    UPDATE users 
                    SET password_hash = ?, full_name = ?, email = ?, role = ?, campus = ?, active = ?,
                        last_login = ?
                    WHERE username = ?
                """, (
                    user.get('password_hash', ''),
                    user.get('full_name', username),
                    user.get('email', ''),
                    user.get('role', 'pastor'),
                    user.get('campus', 'all_campuses'),
                    1 if user.get('active', True) else 0,
                    user.get('last_login'),
                    username
                ))
                updated += 1
                print(f"  Updated: {username} ({user.get('role', 'pastor')})")
            else:
                # Insert new user
                cursor.execute("""
                    INSERT INTO users (username, password_hash, full_name, email, role, campus, active, last_login)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    username,
                    user.get('password_hash', ''),
                    user.get('full_name', username),
                    user.get('email', ''),
                    user.get('role', 'pastor'),
                    user.get('campus', 'all_campuses'),
                    1 if user.get('active', True) else 0,
                    user.get('last_login')
                ))
                imported += 1
                print(f"  Imported: {username} ({user.get('role', 'pastor')})")
        
        conn.commit()
        conn.close()
        
        print(f"\n✅ Successfully imported {imported} new users and updated {updated} existing users")
        if skipped > 0:
            print(f"⚠️  Skipped {skipped} users (missing username)")
        
        return True
        
    except Exception as e:
        print(f"ERROR importing users: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function - handles command line arguments"""
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'export':
            # Export from beta
            export_file = export_users_from_beta()
            if export_file:
                print(f"\n✅ Export complete! File saved: {export_file}")
                print("Next step: Run 'python copy_users_beta_to_main.py import' on main service")
            else:
                sys.exit(1)
        
        elif command == 'import':
            # Import to main
            export_file = sys.argv[2] if len(sys.argv) > 2 else None
            success = import_users_to_main(export_file)
            if success:
                print("\n✅ Import complete! Users are now in main database")
            else:
                sys.exit(1)
        
        else:
            print("Usage:")
            print("  Export from beta: python copy_users_beta_to_main.py export")
            print("  Import to main:  python copy_users_beta_to_main.py import [export_file.json]")
            sys.exit(1)
    else:
        print("Usage:")
        print("  Export from beta: python copy_users_beta_to_main.py export")
        print("  Import to main:  python copy_users_beta_to_main.py import [export_file.json]")
        print("\nThis script requires two steps:")
        print("1. Run 'export' on the beta service to export users")
        print("2. Run 'import' on the main service to import users")
        sys.exit(1)

if __name__ == '__main__':
    main()

