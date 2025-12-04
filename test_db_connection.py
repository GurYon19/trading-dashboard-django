import os
import django
from django.db import connections
from django.db.utils import OperationalError
from decouple import config

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def check_db_connection():
    db_conn = connections['default']
    print(f"Attempting to connect to: {db_conn.settings_dict['NAME']} on {db_conn.settings_dict['HOST']}:{db_conn.settings_dict['PORT']} as {db_conn.settings_dict['USER']}")
    try:
        db_conn.cursor()
        print("Database connection successful!")
    except OperationalError as e:
        print(f"Database connection failed: {e}")

if __name__ == "__main__":
    check_db_connection()
