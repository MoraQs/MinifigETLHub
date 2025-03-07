import os
from sqlalchemy import create_engine
import pandas as pd

# Fetching the environment variables
DB_USER = os.getenv("POSTGRES_USER_DEST")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD_DEST")
DB_HOST = os.getenv("POSTGRES_HOST_DEST")
DB_PORT = os.getenv("POSTGRES_PORT_DEST")
DB_NAME = os.getenv("POSTGRES_DB_DEST")

# Constructing the connection string
DB_CONN_STRING = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
print(f"Connection string: {DB_CONN_STRING}")

try:
    # Creating a SQLAlchemy engine
    engine = create_engine(DB_CONN_STRING)
    
    # Test the connection
    with engine.connect() as conn:
        print("Connection to PostgreSQL database successful.")
        
        # Query to fetch data from inventories table
        category_query = """SELECT * FROM inventories"""
        
        # Reading the data into a DataFrame
        tables = pd.read_sql(category_query, conn)
        print(tables.head())  # Display the first few rows of the table

except Exception as e:
    print(f"Error: Unable to connect to the database. {e}")

finally:
    # Dispose of the engine to close all connections
    if 'engine' in locals():
        engine.dispose()
        print("Connection closed.")