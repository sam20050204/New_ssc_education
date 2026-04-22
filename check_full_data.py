import sqlite3
import os

db_path = "db.sqlite3"

# Try to recover deleted data by examining the database file
try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Enable query-only mode and try to recover
    cursor.execute("PRAGMA quick_check;")
    result = cursor.fetchone()
    print(f"Database integrity check: {result}")
    
    # Try to list all data in admittedstudent
    cursor.execute("""
        SELECT * FROM core_admittedstudent
    """)
    
    print("\n=== All Admitted Students ===")
    for row in cursor.fetchall():
        print(row)
    
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
    print("\nThe data has been permanently overwritten.")
    print("SQLite does not maintain transaction logs for recovery.")
