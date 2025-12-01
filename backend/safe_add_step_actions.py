#!/usr/bin/env python3
"""
Safely add step_actions column to discipleship_pathway_steps table if it doesn't exist
"""
import sqlite3
import os
import sys

def get_database_path():
    """Get the database path from environment or default"""
    db_path = os.environ.get('DATABASE_URL', 'futures_link.db')
    # Remove sqlite:/// prefix if present
    if db_path.startswith('sqlite:///'):
        db_path = db_path[10:]
    # Handle Railway volume path
    if '/data/' in db_path or db_path.startswith('/data/'):
        return db_path
    # Try data directory first
    data_path = os.path.join(os.path.dirname(__file__), 'data', 'futures_link.db')
    if os.path.exists(data_path):
        return data_path
    # Fallback to backend directory
    return os.path.join(os.path.dirname(__file__), db_path)

def add_step_actions_column():
    """Add step_actions column if it doesn't exist"""
    db_path = get_database_path()
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at: {db_path}")
        return False
    
    print(f"📁 Database path: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if column exists
        cursor.execute("PRAGMA table_info(discipleship_pathway_steps)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'step_actions' in columns:
            print("✅ step_actions column already exists")
            conn.close()
            return True
        
        print("➕ Adding step_actions column...")
        
        # Add the column
        cursor.execute("""
            ALTER TABLE discipleship_pathway_steps 
            ADD COLUMN step_actions TEXT DEFAULT '[]'
        """)
        
        # Update existing rows to have empty array
        cursor.execute("""
            UPDATE discipleship_pathway_steps 
            SET step_actions = '[]' 
            WHERE step_actions IS NULL
        """)
        
        conn.commit()
        conn.close()
        
        print("✅ Successfully added step_actions column")
        return True
        
    except sqlite3.OperationalError as e:
        if 'duplicate column' in str(e).lower() or 'already exists' in str(e).lower():
            print("✅ step_actions column already exists (detected via error)")
            return True
        print(f"❌ Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == '__main__':
    success = add_step_actions_column()
    sys.exit(0 if success else 1)


