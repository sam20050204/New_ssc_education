import os
import sqlite3
from pathlib import Path

# Path to database
db_path = "db.sqlite3"

# Create a recovery script
recovery_script = """
PRAGMA writable_schema = ON;
DELETE FROM sqlite_master WHERE type='table' AND name LIKE 'sqlite_%';
PRAGMA writable_schema = OFF;
PRAGMA integrity_check;
"""

# Try to open and check database
try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print("=== Database Tables ===")
    for table in tables:
        print(f"  - {table[0]}")
    
    # Check AdmittedStudent table
    cursor.execute("SELECT COUNT(*) FROM core_admittedstudent;")
    count = cursor.fetchone()[0]
    print(f"\n=== AdmittedStudent Count: {count} ===")
    
    if count > 0:
        print("\nFirst 5 students:")
        cursor.execute("""
            SELECT id, full_name, admission_date 
            FROM core_admittedstudent 
            LIMIT 5
        """)
        for row in cursor.fetchall():
            print(f"  {row}")
    
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
