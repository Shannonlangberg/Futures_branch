#!/usr/bin/env python3
"""
Safe script to add missing columns to persons table
This script checks if columns exist before adding them
"""
import sqlite3
import sys
import os

def get_db_path():
    """Get the database path from environment or default"""
    db_path = os.environ.get('DATABASE_URL', '').replace('sqlite:///', '')
    if not db_path:
        # Try common locations
        possible_paths = [
            'instance/futures_pulse.db',
            'futures_pulse.db',
            'backend/futures_pulse.db',
            'backend/instance/futures_pulse.db'
        ]
        for path in possible_paths:
            if os.path.exists(path):
                return path
    return db_path or 'instance/futures_pulse.db'

def column_exists(cursor, table_name, column_name):
    """Check if a column exists in a table"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    return column_name in columns

def add_column_if_missing(cursor, table_name, column_name, column_def):
    """Add a column if it doesn't exist"""
    if not column_exists(cursor, table_name, column_name):
        try:
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_def}")
            print(f"✓ Added column: {column_name}")
            return True
        except Exception as e:
            print(f"✗ Failed to add {column_name}: {e}")
            return False
    else:
        print(f"→ Column already exists: {column_name}")
        return False

def main():
    db_path = get_db_path()
    
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        print("Please set DATABASE_URL environment variable or ensure database exists")
        sys.exit(1)
    
    print(f"Connecting to database: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Columns to add (column_name: column_definition)
    columns_to_add = {
        'is_new_christian': 'INTEGER DEFAULT 0',
        'new_christian_date': 'DATE',
        'follow_up_status': 'TEXT',
        'service_attended': 'TEXT',
        'family_id': 'TEXT',
        'is_new_person': 'INTEGER DEFAULT 0',
        'new_person_date': 'DATE',
    }
    
    print("\nChecking and adding missing columns...")
    added_count = 0
    
    for column_name, column_def in columns_to_add.items():
        if add_column_if_missing(cursor, 'persons', column_name, column_def):
            added_count += 1
    
    # Create indexes
    indexes = [
        ("idx_persons_is_new_person", "CREATE INDEX IF NOT EXISTS idx_persons_is_new_person ON persons(is_new_person)"),
        ("idx_persons_new_person_date", "CREATE INDEX IF NOT EXISTS idx_persons_new_person_date ON persons(new_person_date)"),
        ("idx_persons_is_new_christian", "CREATE INDEX IF NOT EXISTS idx_persons_is_new_christian ON persons(is_new_christian)"),
        ("idx_persons_new_christian_date", "CREATE INDEX IF NOT EXISTS idx_persons_new_christian_date ON persons(new_christian_date)"),
        ("idx_persons_family_id", "CREATE INDEX IF NOT EXISTS idx_persons_family_id ON persons(family_id)"),
    ]
    
    print("\nCreating indexes...")
    for index_name, index_sql in indexes:
        try:
            cursor.execute(index_sql)
            print(f"✓ Index: {index_name}")
        except Exception as e:
            print(f"✗ Failed to create index {index_name}: {e}")
    
    conn.commit()
    conn.close()
    
    print(f"\n✓ Migration complete! Added {added_count} new column(s).")
    print("You can now use the 'Mark as New Person' and 'Mark as New Christian' features.")

if __name__ == '__main__':
    main()

