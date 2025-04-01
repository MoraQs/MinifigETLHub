import os
import requests
import time
import pandas as pd
from sqlalchemy import create_engine
from airflow import DAG
from airflow.operators.python import PythonOperator, BranchPythonOperator     # BranchPythonOperator to skip the ingestion process when already done
from datetime import datetime, timedelta
from dotenv import load_dotenv
import glob

# Load environment variables from .env file
load_dotenv()

## Check if the ingested files already exist. If yes, skip re-ingesting
def check_staging_files():
    """Check if staging files already exist."""
    staging_files = [
        './data/raw/inventory_tbl/inventories.csv',
        './data/raw/inventory_tbl/inventory_minifigs.csv',
        './data/raw/inventory_tbl/inventory_parts.csv',
        './data/raw/inventory_tbl/inventory_sets.csv',
        './data/raw/rebrickable_minifigs/minifigs.csv',
        './data/raw/parts_tbl/colors.csv',
        './data/raw/parts_tbl/elements.csv',
        './data/raw/parts_tbl/part_categories.csv',
        './data/raw/parts_tbl/part_relationships.csv',
        './data/raw/parts_tbl/parts.csv',
        './data/raw/sets_tbl/sets.csv',
        './data/raw/sets_tbl/themes.csv'
    ]
    
    for file in staging_files:
        if not os.path.exists(file):
            print(f"Staging file {file} does not exist. Ingestion is required.")
            return ["ingest_data_from_sql_db", "ingest_data_from_api"]  # Run ingestion tasks
    
    print("All staging files exist. Skipping ingestion.")
    return "Transformed_ingested_data"  # Skip ingestion and run transformation directly

# Ingest data from sql database
def ingest_sql_source():
    """Ingesting data from SQL Server database"""

    # Fetching the source environment variables
    DB_USER = os.getenv("POSTGRES_USER")
    DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
    DB_HOST = os.getenv("POSTGRES_HOST")
    DB_PORT = os.getenv("POSTGRES_PORT")
    DB_NAME = os.getenv("POSTGRES_DB")

    # Constructing the connection string
    DB_CONN_STRING = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}"
    print(f"Connection string: {DB_CONN_STRING}")

    try:
        # Creating a SQLAlchemy engine
        engine = create_engine(DB_CONN_STRING)
        
        # Test the connection
        with engine.connect() as conn:
            print("Connection to PostgreSQL database successful.")
            
            # Query to fetch data from inventories table
            category_query = """
            select * from (
                select 
                    table_name,
                    case 
                        when table_name in ('inventory_parts', 'inventories', 'inventory_minifigs', 'inventory_sets') then 'inventory_tbl'
                        when table_name in ('parts', 'part_relationships', 'part_categories', 'colors', 'elements') then 'parts_tbl'
                        when table_name in ('sets', 'themes') then 'sets_tbl'
                        else ''
                    end as "table_category"
                from information_schema.tables where table_type = 'BASE TABLE'
                ) subQ
            where table_category != ''
            """
            
            # Reading the data into a DataFrame
            tables = pd.read_sql(category_query, conn)

            # Define the path to the raw data folder
            data_folder = './data/raw'
            if not os.path.exists(data_folder):
                os.makedirs(data_folder)  # Create directory if it doesn't exist

            # Loop through each table, create category subfolder, and dump data
            for _, row in tables.iterrows():
                table = row['table_name']
                category = row['table_category']

                print(f"Fetching data from {table} in category {category}...")

                # Define the subfolder path based on the category
                category_folder = os.path.join(data_folder, category)
                if not os.path.exists(category_folder):
                    os.makedirs(category_folder)  # Create subfolder if it doesn't exist

                try:
                    # Query to select all data from the table
                    query = f"SELECT * FROM {table}"

                    # Read table data into a DataFrame
                    df = pd.read_sql(query, engine)

                    # Define the file path for the table's CSV file inside the category subfolder
                    csv_path = os.path.join(category_folder, f"{table}.csv")

                    # Save the DataFrame to CSV
                    df.to_csv(csv_path, index=False)
                    print(f"Data from {table} saved to {csv_path}")

                except Exception as e:
                    print(f"Error processing table {table}: {e}")

    except Exception as e:
        print(f"Error: Unable to connect to the database. {e}")

    finally:
        # Close the SQLAlchemy engine
        if 'engine' in locals():
            engine.dispose()
            print("SQLAlchemy engine closed.")

    print("Data ingestion complete!")

# Ingest data from Rebrickable API
def ingest_api_data():
    """Ingesting data from Rebrickable REST API and saving it as CSV in the data folder in project root"""

    # Retrieve environment variables for API URL and key
    api_url = os.getenv('API_URL')
    api_key = os.getenv('API_KEY')

    # Log the API URL and key for debugging
    print(f"API URL: {api_url}")
    print(f"API Key: {api_key}")
    
    # Define headers with API key
    headers = {
        "Authorization": f"key {api_key}"
    }
    
    all_data = []  # List to store all records
    next_page_url = api_url  # Start with the initial API URL
    delay_time = 1  # Set delay time (in seconds)
    
    while next_page_url:
        response = requests.get(next_page_url, headers=headers)
        
        # Log the response status for debugging
        print(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()  # Convert API response to JSON
            
            # Append records to all_data list
            if "results" in data:
                all_data.extend(data["results"])  # Add new records
                
            # Check if there is a next page
            next_page_url = data.get("next")  # Get next page URL (if available)
            
            print(f"Fetched {len(all_data)} records so far...")  # Debugging output
    
            # Add delay before the next request
            time.sleep(delay_time)
    
        elif response.status_code == 429:
            # API rate limit hit: Wait and retry
            retry_after = int(response.headers.get("Retry-After", delay_time))
            print(f"Rate limit exceeded! Waiting for {retry_after} seconds before retrying...")
            time.sleep(retry_after)
            
        else:
            print(f"Failed to fetch data: {response.status_code}, {response.text}")
            break  # Stop if there's an error

    # After fetching all the data, check if any records were fetched
    if not all_data:
        print("❌ No data fetched from API.")
        return
    
    # Convert list to DataFrame
    df = pd.DataFrame(all_data)
    
    # Debugging: Print the first few rows of the DataFrame
    print(f"DataFrame Head:\n{df.head()}")
    
    # Define the path to the raw data folder
    data_folder = './data/raw'
    subfolder = 'rebrickable_minifigs'

    if not os.path.exists(data_folder):
        os.makedirs(data_folder)  # Create directory if it doesn't exist

    # Create the sub-folder if it doesn't exist
    subfolder_path = os.path.join(data_folder, subfolder)
    if not os.path.exists(subfolder_path):
        os.makedirs(subfolder_path)  # Create directory if it doesn't exist
    
    # Define the full CSV path
    csv_path = os.path.join(subfolder_path, "minifigs.csv")
    
    # Save the DataFrame as CSV
    df.to_csv(csv_path, index=False)
    
    print(f"Data saved to {csv_path}")


def transforming_data():
    """Load raw data, perform transformations, create dimensional modeling tables, and save them to './data/transformed'."""
    # Define the path to the raw data folder
    raw_data_dir = './data/raw'
    transformed_dir = './data/transformed'

    # Create the transformed directory if it doesn't exist
    if not os.path.exists(transformed_dir):
        os.makedirs(transformed_dir)  # Create directory if it doesn't exist

    # Find all .csv files in the raw folder and its subfolders
    csv_files = glob.glob(os.path.join(raw_data_dir, '**/*.csv'), recursive=True)

    # Print the list of found files
    print(f"Found {len(csv_files)} CSV files:")
    for file in csv_files:
        print(file)

    # Dictionary to store DataFrames
    dataframes = {}

    # Load each CSV file into a DataFrame
    for file in csv_files:
        # Extract the file name (without extension) and subfolder name
        relative_path = os.path.relpath(file, raw_data_dir)
        key = os.path.splitext(relative_path)[0]  # Remove .csv extension
        key = key.replace(os.path.sep, '_')  # Replace slashes with underscores

        # Load the CSV file into a DataFrame
        df = pd.read_csv(file)
        dataframes[key] = df

        print(f"Loaded {file} into DataFrame with key: {key}")

    # Extract individual DataFrames
    inventory_parts_df = dataframes['inventory_tbl_inventory_parts']
    part_relationship_df = dataframes['parts_tbl_part_relationships']
    colors_df = dataframes['parts_tbl_colors']
    parts_df = dataframes['parts_tbl_parts']
    part_categories_df = dataframes['parts_tbl_part_categories']
    sets_df = dataframes['sets_tbl_sets']
    themes_df = dataframes['sets_tbl_themes']
    inventories_df = dataframes['inventory_tbl_inventories']
    inventory_minifigs_df = dataframes['inventory_tbl_inventory_minifigs']
    minifigs_df = dataframes['rebrickable_minifigs_minifigs']
    inventory_sets_df = dataframes['inventory_tbl_inventory_sets']

    # Step 1: Aggregate part_relationships
    rel_type_mapping = {
        'P': 'Print',
        'R': 'Pair',
        'B': 'Sub-Part',
        'M': 'Mold',
        'T': 'Pattern',
        'A': 'Alternative'
    }

    # Combine both operations into one
    _summarized_part_relationship = (
        part_relationship_df
        # Add rel_type_desc based on rel_type
        .assign(rel_type_desc=lambda x: x['rel_type'].map(rel_type_mapping))
        # Group by parent_part_num and rel_type
        .groupby(['parent_part_num', 'rel_type', 'rel_type_desc'])
        .size()
        .reset_index(name='counting')
        # Group by parent_part_num and aggregate rel_type and rel_type_desc
        .groupby('parent_part_num')
        .agg({
            'rel_type': lambda x: ', '.join(x),
            'rel_type_desc': lambda x: ', '.join(x)
        })
        .reset_index()
    )

    ## inventories merged with sets and themes
    __summarizedinventories_df = (
        inventories_df.rename(columns={'id': 'inventory_id'})
        .merge(sets_df, how='left', on='set_num').rename(columns={'name': 'set_name', 'set_num': 'setnum', 'img_url': 'set_img_url', 'num_parts': 'numparts'})
        .merge(themes_df, how='left', left_on='theme_id', right_on='id').rename(columns={'id': 'themesid', 'name': 'themes_name'})
    )

    # Master dataset for inventory parts
    inventory_parts_master = (
        inventory_parts_df
        # .merge(__summarizedinventories_df, how='left', on='inventory_id')   # No direct relationship between these two
        .merge(parts_df, how='left', on='part_num').rename(columns={'part_num': 'part_num_id', 'name': 'part_name'})
        .merge(part_categories_df, how='left', left_on='part_cat_id', right_on='id').rename(columns={'id': 'part_categories_id', 'name': 'part_category_name'})
        .merge(colors_df, how='left', left_on='color_id', right_on='id')
        .merge(_summarized_part_relationship, how='left', left_on='part_num_id', right_on='parent_part_num')
    )

    # Master dataset for inventory minifigs
    inventory_minifigs_master = (
        inventory_minifigs_df
        .merge(minifigs_df, how='left', left_on='fig_num', right_on='set_num')
        .merge(__summarizedinventories_df, how='left', on='inventory_id')
    )

    # Change last_modified_dt from object to Timestamp
    inventory_minifigs_master['last_modified_dt'] = pd.to_datetime(inventory_minifigs_master['last_modified_dt'])

    # Master dataset for inventory sets
    inventory_sets_master = (
        inventory_sets_df
        .merge(sets_df, how='left', on='set_num').rename(columns={'name': 'set_name', 'set_num': 'setnum', 'img_url': 'set_img_url', 'num_parts': 'numparts'})
        .merge(themes_df, how='left', left_on='theme_id', right_on='id').rename(columns={'id': 'themesid', 'name': 'themes_name'})
    )

    ## Setting up Dimensional modeling (facts/dimension tables)
    # Dimension Sets table
    dimension_sets = sets_df[['set_num', 'name', 'year', 'theme_id', 'num_parts', 'img_url']] \
        .rename(columns={'set_num': 'setNum', 'name': 'setName', 'theme_id': 'themeId', 'num_parts': 'numParts', 'img_url': 'imageUrl'})

    # Dimension Colors table
    dimension_colors = colors_df[['id', 'name', 'rgb', 'is_trans', 'num_parts', 'num_sets', 'y1', 'y2']] \
        .rename(columns={'id': 'colorId', 'name': 'colorName', 'is_trans': 'isTransparent', 'num_parts': 'numParts', 'num_sets': 'numSets', 'y1': 'year1', 'y2': 'year2'}) \
        .drop_duplicates(subset='colorId')

    # Dimension Parts table
    dimension_parts = inventory_parts_master[['part_name', 'part_num_id', 'part_cat_id', 'part_category_name', 'part_material', 'rel_type', 'rel_type_desc']] \
        .rename(columns={'part_name': 'partName', 'part_num_id': 'partNumber', 'part_cat_id': 'partCategoryId', 'part_category_name': 'partCategoryName', 'part_material': 'partMaterial', \
            'rel_type': 'relationshipType', 'rel_type_desc': 'relationshipTypeDesc'}) \
        .drop_duplicates()

    # Facts inventory minifigs
    ft_inv_minifigs = inventory_minifigs_master[['inventory_id', 'fig_num', 'quantity', 'set_num', 'set_url', 'last_modified_dt']].rename(columns={'last_modified_dt': 'last_modified'})

    # Facts inventory sets
    ft_inv_sets = inventory_sets_master[['inventory_id', 'setnum', 'numparts', 'set_img_url', 'quantity']].rename(columns={'numparts': 'num_parts'})

    # Facts inventory parts
    ft_inv_parts = inventory_parts_master[['inventory_id', 'part_num_id', 'color_id', 'quantity', 'is_spare', 'img_url']]

    # Save the DataFrames to the transformed folder
    dimension_sets.to_csv(os.path.join(transformed_dir, 'dimension_sets.csv'), index=False)
    dimension_colors.to_csv(os.path.join(transformed_dir, 'dimension_colors.csv'), index=False)
    dimension_parts.to_csv(os.path.join(transformed_dir, 'dimension_parts.csv'), index=False)
    ft_inv_minifigs.to_csv(os.path.join(transformed_dir, 'ft_inv_minifigs.csv'), index=False)
    ft_inv_sets.to_csv(os.path.join(transformed_dir, 'ft_inv_sets.csv'), index=False)
    ft_inv_parts.to_csv(os.path.join(transformed_dir, 'ft_inv_parts.csv'), index=False)

    print(f"All fact and dimension tables saved to {transformed_dir}")

# Loading transformed data into the Analytics Database (PostgreSQL)
def load_to_postgres():
    """Loading transformed data into the destination PostgreSQL DB"""
    # Fetching the source environment variables
    DB_USER = os.getenv("POSTGRES_USER")
    DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
    DB_HOST = os.getenv("POSTGRES_HOST")
    DB_NAME = os.getenv("POSTGRES_DB")

    # Constructing the connection string
    DB_CONN_STRING = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}"
    print(f"Connection string: {DB_CONN_STRING}")

    engine = create_engine(DB_CONN_STRING)
    conn = engine.connect()

    # Define data path to write transformed data
    transformed_data_folder = './data/transformed'
    
    # Read transformed CSVs
    dimension_sets = pd.read_csv(f"{transformed_data_folder}/dimension_sets.csv")
    dimension_colors = pd.read_csv(f"{transformed_data_folder}/dimension_colors.csv")
    dimension_parts = pd.read_csv(f"{transformed_data_folder}/dimension_parts.csv")
    ft_inv_minifigs = pd.read_csv(f"{transformed_data_folder}/ft_inv_minifigs.csv")
    ft_inv_sets = pd.read_csv(f"{transformed_data_folder}/ft_inv_sets.csv")
    ft_inv_parts = pd.read_csv(f"{transformed_data_folder}/ft_inv_parts.csv")

    # Load Dimensions and Fact Tables (Upsert)
    dimension_sets.to_sql('sets_dim', con=engine, if_exists='replace', index=False)
    dimension_colors.to_sql('colors_dim', con=engine, if_exists='replace', index=False)
    dimension_parts.to_sql('parts_dim', con=engine, if_exists='replace', index=False)
    ft_inv_minifigs.to_sql('inventory_minifigs_ft', con=engine, if_exists='replace', index=False)
    ft_inv_sets.to_sql('inventory_sets_ft', con=engine, if_exists='replace', index=False)
    ft_inv_parts.to_sql('inventory_parts_ft', con=engine, if_exists='replace', index=False)

    print("Data loaded into PostgreSQL")
    conn.close()

# Airflow DAG Configuration
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2025, 3, 3),
    'retries': 3,
    'retry_delay': timedelta(minutes=2),
}

dag = DAG(
    dag_id='full_etl',
    default_args=default_args,
    schedule_interval='@daily',
    catchup=False,
    tags=['ETL', 'SQL_API', 'Postgres']
)

# Task to check if staging files exist
check_staging_task = BranchPythonOperator(
    task_id = "check_staging_files",
    python_callable = check_staging_files,
    provide_context = True,
    dag = dag
)

# Define Airflow tasks
ingest_sql_task = PythonOperator(
    task_id = "ingest_data_from_sql_db",
    python_callable = ingest_sql_source,
    dag = dag
)

ingest_api_task = PythonOperator(
    task_id = "ingest_data_from_api",
    python_callable = ingest_api_data,
    dag = dag
)

transformed_data_task = PythonOperator(
    task_id = "Transformed_ingested_data",
    python_callable = transforming_data,
    dag = dag
)

load_data_to_warehouse = PythonOperator(
    task_id = "Load_transformed_data_to_data_warehouse",
    python_callable = load_to_postgres,
    dag = dag
)

# Set task dependencies
check_staging_task >> [ingest_sql_task, ingest_api_task]  
check_staging_task >> transformed_data_task >> load_data_to_warehouse