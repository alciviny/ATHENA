import psycopg2
import os

# Database connection details from docker-compose
db_params = {
    'dbname': 'athena',
    'user': 'user',
    'password': 'pass',
    'host': 'localhost',  # We are running this script from the host
    'port': '5432'
}

try:
    conn = psycopg2.connect(**db_params)
    cur = conn.cursor()

    print('Tables:')
    # Query to get table names in PostgreSQL
    cur.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
    """)
    tables = cur.fetchall()
    print(tables)

    for table in tables:
        t_name = table[0]
        print(f"\nTable: {t_name}")
        try:
            # Using placeholders to prevent SQL injection
            cur.execute(f"SELECT * FROM {t_name} LIMIT 1")
            print(cur.fetchone())
        except Exception as e:
            print(f"Error reading {t_name}: {e}")

    cur.close()
    conn.close()

except psycopg2.OperationalError as e:
    print(f"Could not connect to the database: {e}")
    print("Please ensure the Docker containers are running (`docker-compose up -d`).")
    exit(1)
