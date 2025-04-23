import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
DATABASE = {
    "dbname": os.getenv("DB_NAME", "compliance_bot"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "anas"),
    "host": os.getenv("DB_HOST", "localhost"),
    # "port": os.getenv("DB_PORT", "8502"),  
}

# def get_db_connection():
#     """
#     Create and return a connection to the PostgreSQL database
#     """
#     try:
#         conn = psycopg2.connect(
#             dbname=DATABASE["dbname"],
#             user=DATABASE["user"],
#             password=DATABASE["password"],
#             host=DATABASE["host"],
#             port=DATABASE["port"]
#         )
#         print("Database conn:", conn)
#         return conn
#     except Exception as e:
#         print(f"Database connection error: {e}")
#         return None

def get_db_connection():
    print("→ DB host:", DATABASE["host"])
    try:
        conn = psycopg2.connect(
            dbname=DATABASE["dbname"],
            user=DATABASE["user"],
            password=DATABASE["password"],
            host=DATABASE["host"]
            # port=DATABASE["port"]
        )
        print("Database conn:", conn)
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

# get_db_connection()