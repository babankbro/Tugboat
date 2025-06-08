import mysql.connector
from mysql.connector import Error
import json # Added for JSON functionality
from datetime import datetime # Added for timestamp conversion
from dotenv import load_dotenv
import os

load_dotenv()

HOST=os.getenv('HOST')
PORT=os.getenv('PORT')
USER=os.getenv('USERDB')
PASSWORD=os.getenv('PASSWORD')
DATABASE_NAME=os.getenv('DATABASE_NAME')

# print(f"{HOST} {PORT} {USER} {PASSWORD} {DATABASE_NAME}")
def connect_to_mysql_and_list_databases():
    """ Connect to MySQL server and list all databases """
    conn = None
    try:
        conn = mysql.connector.connect(
            host=HOST,
            port=PORT,  # Standard MySQL port, change if different
            user=USER,
            password=PASSWORD
        )
        if conn.is_connected():
            
            cursor = conn.cursor()
            print("Executing SHOW DATABASES;")
            cursor.execute("SHOW DATABASES;")
            databases = cursor.fetchall()
            print("Databases found:")
            if databases:
                for db_name_tuple in databases:
                    print(db_name_tuple[0])
            else:
                print("No databases found or no permission to list them.")
            cursor.close()
    except Error as e:
        print(f"Error connecting to MySQL server: {e}")
        print("Please check server status, port (3306 or 18080), and firewall.")
    finally:
        if conn and conn.is_connected():
            conn.close()
            print('MySQL server connection is closed')

def list_tables_in_database():
    """ Connect to a specific MySQL database and list its tables """
    conn = None
    try:
        conn = mysql.connector.connect(
            host=HOST,
            port=PORT,  # Standard MySQL port
            user=USER,
            password=PASSWORD,
            database=DATABASE_NAME
        )
        if conn.is_connected():
            print(f'Connected to MySQL database: {DATABASE_NAME} at {HOST}')
            cursor = conn.cursor()
            print(f"Executing SHOW TABLES; in {DATABASE_NAME}")
            cursor.execute("SHOW TABLES;")
            tables = cursor.fetchall()
            print(f"Tables found in {DATABASE_NAME}:")
            if tables:
                for table_name_tuple in tables:
                    print(table_name_tuple[0])
            else:
                print(f"No tables found in {DATABASE_NAME} or no permission to list them.")
            cursor.close()
    except Error as e:
        print(f"Error connecting to database '{DATABASE_NAME}': {e}")
        print("Please check if the database exists and the user has permissions.")
    finally:
        if conn and conn.is_connected():
            conn.close()
            print(f'MySQL connection to {DATABASE_NAME} is closed')

def query_table_to_json(table_name):
    """ Connects to a specific MySQL database, queries a table, and returns results as JSON. """
    conn = None
    try:
        conn = mysql.connector.connect(
            host=HOST,
            port=PORT,  # Standard MySQL port
            user=USER,
            password=PASSWORD,
            database=DATABASE_NAME
        )
        if conn.is_connected():
            # print(f'Connected to database: {DATABASE_NAME} to query table: {table_name}')
            # Using dictionary=True to get results as dictionaries (column_name: value)
            cursor = conn.cursor(dictionary=True)
            if table_name == 'Station':
                query = """
                            SELECT s.Id, s.Type, s.Name AS StationName, s.Latitude, s.Longitude, s.DistanceKm, c.Name 
                            FROM `Station` AS s
                                LEFT JOIN `Customer_Station` AS cs ON cs.`StationId` = s.`Id` 
                                LEFT JOIN `Customer` AS c ON cs.`CustomerId` = c.`Id`;
                        """
            elif table_name == 'Carrier':
                query = """
                            SELECT c.Id, c.Name, c.Latitude, c.Longitude, o.Id AS Order_id
                            FROM
                                `Carrier` AS c LEFT JOIN
                                `Order` AS o ON c.Name=o.FromPoint;
                        """
            else:
                query = f"SELECT * FROM `{table_name}`;" # Be cautious with unescaped table names in production
            # print(f"Executing query: {query}")
            cursor.execute(query)
            results = cursor.fetchall()
            cursor.close()
            if results:
                # Convert list of dictionaries to JSON string
                # default=str handles non-serializable types like datetime
                json_output = json.dumps(results, indent=4, default=str)
                # print(f"Data from {table_name} (JSON format):")
                # print(json_output) # Optionally print here or just return
                return json_output
            else:
                print(f"No data found in table {table_name}.")
                return json.dumps([]) # Return an empty JSON array string
    except Error as e:
        print(f"Error querying table '{table_name}' in database '{DATABASE_NAME}': {e}")
        return None # Indicate failure
    finally:
        if conn and conn.is_connected():
            conn.close()
            # print(f'MySQL connection for querying {table_name} in {DATABASE_NAME} is closed')


def drop_table(table_name):
    """ Connects to a specific MySQL database and drops a table. """
    conn = None
    try:
        conn = mysql.connector.connect(
            host=HOST,
            port=PORT,
            user=USER,
            password=PASSWORD,
            database=DATABASE_NAME
        )
        if conn.is_connected():
            cursor = conn.cursor()
            # Using IF EXISTS to avoid error if table doesn't exist
            query = f"DROP TABLE IF EXISTS {table_name}" 
            print(f"Executing query: {query} in database {DATABASE_NAME}")
            cursor.execute(query)
            conn.commit() # Important to commit changes for DDL statements like DROP TABLE
            print(f"Table '{table_name}' dropped successfully from database '{DATABASE_NAME}'.")
            cursor.close()
    except Error as e:
        print(f"Error dropping table '{table_name}' from database '{DATABASE_NAME}': {e}")
    finally:
        if conn and conn.is_connected():
            conn.close()
            print(f'MySQL connection for dropping table {table_name} in {DATABASE_NAME} is closed')


def create_schedule_table():
    """ Connects to a specific MySQL database and creates the Schedule table. """
    conn = None
    try:
        conn = mysql.connector.connect(
            host=HOST,
            port=PORT,
            user=USER,
            password=PASSWORD,
            database=DATABASE_NAME
        )
        if conn.is_connected():
            cursor = conn.cursor()
            create_table_query = """
            CREATE TABLE IF NOT EXISTS Schedule (
                ID VARCHAR(255),
                type VARCHAR(255),
                name VARCHAR(255),
                enter_datetime DATETIME,
                exit_datetime DATETIME,
                distance DECIMAL(10, 2),
                time DECIMAL(10, 4),
                speed DECIMAL(10, 2),
                type_point VARCHAR(255),
                order_trip VARCHAR(255),
                total_load DECIMAL(10, 2),
                barge_ids TEXT,
                order_distance DECIMAL(10, 2),
                order_time DECIMAL(10, 4),
                barge_speed DECIMAL(10, 2),
                order_arrival_time DATETIME,
                tugboat_id VARCHAR(255),
                order_id VARCHAR(255),
                water_type VARCHAR(50)
            )
            """
            print(f"Executing query: CREATE TABLE Schedule in database {DATABASE_NAME}")
            cursor.execute(create_table_query)
            conn.commit()
            print(f"Table 'Schedule' created successfully or already exists in database '{DATABASE_NAME}'.")
            cursor.close()
    except Error as e:
        print(f"Error creating table 'Schedule' in database '{DATABASE_NAME}': {e}")
    finally:
        if conn and conn.is_connected():
            conn.close()
            print(f'MySQL connection for creating Schedule table in {DATABASE_NAME} is closed')


def insert_data_into_schedule(json_data_string):
    """ Connects to MySQL, parses JSON data, and inserts it into the Schedule table. """
    conn = None
    try:
        records = json.loads(json_data_string)
        if not records:
            print("No data provided in JSON string to insert.")
            return

        conn = mysql.connector.connect(
            host=HOST,
            port=PORT,
            user=USER,
            password=PASSWORD,
            database=DATABASE_NAME
        )
        if conn.is_connected():
            cursor = conn.cursor()
            
            columns = [
                'ID', 'type', 'name', 'enter_datetime', 'exit_datetime', 'distance',
                'time', 'speed', 'type_point', 'order_trip', 'total_load', 'barge_ids',
                'order_distance', 'order_time', 'barge_speed', 'order_arrival_time',
                'tugboat_id', 'order_id', 'water_type'
            ]
            datetime_cols = ['enter_datetime', 'exit_datetime', 'order_arrival_time']
            
            value_placeholders = ", ".join(["%s"] * len(columns))
            insert_query = f"INSERT INTO Schedule ({', '.join(columns)}) VALUES ({value_placeholders})"
            
            data_to_insert = []
            for record in records:
                row_values = []
                for col in columns:
                    value = record.get(col) 
                    
                    if col in datetime_cols and value is not None:
                        if isinstance(value, (int, float)):
                            try:
                                # Assume timestamp is in milliseconds
                                value = datetime.fromtimestamp(value / 1000).strftime('%Y-%m-%d %H:%M:%S')
                            except (ValueError, TypeError, OverflowError):
                                print(f"Warning: Could not convert numeric value '{value}' for datetime column '{col}'. Storing as NULL.")
                                value = None
                        elif isinstance(value, str):
                            if value.isdigit(): # Check if string is all digits
                                try:
                                    numeric_value = float(value)
                                    # Heuristic: if it's long, assume ms, otherwise it might be a year or something else
                                    if len(value) >= 10: # Typically 13 digits for ms, 10 for seconds
                                        value = datetime.fromtimestamp(numeric_value / 1000).strftime('%Y-%m-%d %H:%M:%S')
                                    # Else, leave as is for MySQL to validate if it's a different string format (e.g. 'YYYY')
                                except (ValueError, TypeError, OverflowError):
                                    print(f"Warning: Could not convert string of digits '{value}' for datetime column '{col}'. Storing as NULL.")
                                    value = None
                            elif value == 'NaT': # Handle Pandas NaT string
                                value = None
                        # If value is already a correctly formatted datetime string, it will pass through
                    
                    if col == 'barge_ids' and isinstance(value, list):
                        value = json.dumps(value)
                    
                    # General NaN handling for non-datetime columns
                    if isinstance(value, float) and value != value: # value != value is true for NaN
                        value = None
                        
                    row_values.append(value)
                data_to_insert.append(tuple(row_values))
            
            cursor.executemany(insert_query, data_to_insert)
            conn.commit()
            print(f"{cursor.rowcount} records inserted successfully into 'Schedule' table.")
            cursor.close()

    except Error as e:
        print(f"Error inserting data into 'Schedule' table: {e}")
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON string: {e}")
    finally:
        if conn and conn.is_connected():
            conn.close()
            print(f'MySQL connection for inserting data into Schedule table in {DATABASE_NAME} is closed')


if __name__ == '__main__':
    #connect_to_mysql_and_list_databases() # Lists all databases
    #list_tables_in_database('spinterdb') # Initial list if needed

    print("\nAttempting to drop 'Schedule' table (if it exists)...")
    drop_table('Schedule')
    
    print("\nAttempting to create 'Schedule' table...")
    create_schedule_table()
    
    print("\nListing tables in 'spinterdb' after operations:")
    list_tables_in_database()

    # Example usage for query_table_to_json:
    # table_data_json = query_table_to_json('spinterdb', 'Schedule') 
    # if table_data_json:
    #     print("--- JSON Output from Schedule table --- ")
    #     print(table_data_json)
    # else:
    #     print("Failed to retrieve data as JSON from Schedule table.")
