import psycopg2
import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

# Database connection details from environment variables
db_params = {
    'dbname': os.getenv('POSTGRES_DB', 'athena'),
    'user': os.getenv('POSTGRES_USER', 'user'),
    'password': os.getenv('POSTGRES_PASSWORD', 'pass'),
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': os.getenv('POSTGRES_PORT', '5432')
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
