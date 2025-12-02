#!/usr/bin/env python3
"""
Password reset utility for Futures Pulse app
Usage: python reset_password.py <email> <new_password>
"""
import sys
import os
import sqlite3
from werkzeug.security import generate_password_hash

def reset_password(email, new_password):
    """Reset user password"""
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(backend_dir, 'instance', 'church_voice.db')
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at: {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if user exists
    cursor.execute("SELECT id, username, email FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    
    if not user:
        print(f"❌ User with email '{email}' not found")
        conn.close()
        return False
    
    user_id, username, user_email = user
    print(f"✅ Found user: {username} ({user_email})")
    
    # Generate password hash
    password_hash = generate_password_hash(new_password)
    
    # Update password
    cursor.execute("UPDATE users SET password_hash = ? WHERE email = ?", (password_hash, email))
    conn.commit()
    
    print(f"✅ Password reset successfully for {email}")
    print(f"   New password: {new_password}")
    
    conn.close()
    return True

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python reset_password.py <email> <new_password>")
        print(f"\nExample:")
        print(f"  python reset_password.py shannon.langberg@futures.church mynewpassword")
        sys.exit(1)
    
    email = sys.argv[1]
    new_password = sys.argv[2]
    
    reset_password(email, new_password)

