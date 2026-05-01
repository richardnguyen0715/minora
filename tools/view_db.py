import sqlite3
import sys
from pathlib import Path


def visualize_database():
    """Reads the local SQLite database and prints out its contents in a readable format."""
    db_path = Path("data/minora.db")

    if not db_path.exists():
        print(f"❌ Database not found at {db_path.absolute()}")
        print("Please make sure the application has run and created the database.")
        sys.exit(1)

    print(f"📊 Analyzing database at {db_path}...\n")
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row["name"] for row in cursor.fetchall()]
        
        print(f"Found {len(tables)} tables: {', '.join(tables)}\n")

        for table in tables:
            print("=" * 100)
            print(f"📋 Table: {table.upper()}")
            print("=" * 100)
            
            # Get columns
            cursor.execute(f"PRAGMA table_info({table});")
            columns = [col["name"] for col in cursor.fetchall()]
            
            # Format header
            header = " | ".join(f"{col:<20}" for col in columns)
            print(header)
            print("-" * len(header))
            
            # Get rows
            cursor.execute(f"SELECT * FROM {table} LIMIT 100;")
            rows = cursor.fetchall()
            
            if not rows:
                print("   (Empty table)")
            else:
                for row in rows:
                    # Truncate values if they are too long for terminal viewing
                    formatted_row = " | ".join(f"{str(row[col])[:20]:<20}" for col in columns)
                    print(formatted_row)
                
                if len(rows) == 100:
                    print("... (showing first 100 rows)")
            
            print()

    except sqlite3.Error as e:
        print(f"❌ Error reading database: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()


if __name__ == "__main__":
    visualize_database()
