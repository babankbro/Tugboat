import mysql.connector
from mysql.connector import Error
import json # Added for JSON functionality
from datetime import datetime # Added for timestamp conversion
from dotenv import load_dotenv
import os
import numpy as np
from flask import jsonify

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
            # Using dictionary=True to get results as dictionaries (column_name: value)
            cursor = conn.cursor(dictionary=True)
            
            # Updated queries to match the new database schema
            if table_name == 'Station':
                query = """
                    SELECT s.Id, s.Type, s.Name, s.Latitude, s.Longitude, s.DistanceKm, c.Name AS CustomerName
                    FROM Station AS s
                    LEFT JOIN Customer_Station AS cs ON cs.StationId = s.Id 
                    LEFT JOIN Customer AS c ON cs.CustomerId = c.Id
                """
            elif table_name == 'Carrier':
                query = """
                    SELECT c.Id, c.Name, o.Id AS OrderId, o.FromPoint, o.DestPoint
                    FROM Carrier AS c 
                    LEFT JOIN `Order` AS o ON c.Name = o.FromPoint OR c.Name = o.DestPoint
                """
            elif table_name == 'Tugboat':
                query = """
                    SELECT t.Id, t.Name, t.MaxCapacity, t.MaxBarge, t.MaxFuelCon, t.Type,
                           t.MinSpeed, t.MaxSpeed, t.EngineRpm, t.HorsePower, t.WaterStatus,
                           t.ReadyDateTime, t.StationId, s.Latitude, s.Longitude, s.DistanceKm
                    FROM Tugboat AS t
                    LEFT JOIN Station AS s ON t.StationId = s.Id
                """
            elif table_name == 'Barge':
                query = """
                    SELECT b.Id, b.Name, b.Weight, b.Capacity, b.WaterStatus, b.StationId,
                           b.SetupTime, b.ReadyDatetime, s.Latitude, s.Longitude, s.DistanceKm
                    FROM Barge AS b
                    LEFT JOIN Station AS s ON b.StationId = s.Id
                """
            elif table_name == 'Order':
                query = """
                    SELECT o.Id, o.Type, o.FromPoint, o.DestPoint, o.StartStationId, o.DestStationId,
                           o.ProductName, o.Demand, o.StartDateTime, o.DueDateTime, o.LoadingRate,
                           o.CR1, o.CR2, o.CR3, o.CR4, o.CR5, o.CR6, o.CR7,
                           o.TimeReadyCR1, o.TimeReadyCR2, o.TimeReadyCR3, o.TimeReadyCR4,
                           o.TimeReadyCR5, o.TimeReadyCR6, o.TimeReadyCR7
                    FROM `Order` AS o
                """
            else:
                query = f"SELECT * FROM `{table_name}`;"
                
            cursor.execute(query)
            results = cursor.fetchall()
            cursor.close()
            if results:
                json_output = json.dumps(results, indent=4, default=str)
                return json_output
            else:
                print(f"No data found in table {table_name}.")
                return json.dumps([])
    except Error as e:
        print(f"Error querying table '{table_name}' in database '{DATABASE_NAME}': {e}")
        return None
    finally:
        if conn and conn.is_connected():
            conn.close()

def query_table_to_json_custom(table_name, custom_query):
    """
    Execute a custom query and return results as JSON.
    Added to support complex queries with joins.
    """
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
            cursor = conn.cursor(dictionary=True)
            cursor.execute(custom_query)
            results = cursor.fetchall()
            cursor.close()
            if results:
                return json.dumps(results, indent=4, default=str)
            else:
                print(f"No data found for custom query on {table_name}.")
                return json.dumps([])
    except Error as e:
        print(f"Error executing custom query for '{table_name}': {e}")
        return None
    finally:
        if conn and conn.is_connected():
            conn.close()

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

  
def update_database(order_ids, tugboat_df, cost_df, barge_cost_df):
    
    print("Updating database", tugboat_df.columns)
    try:
        # Connect to MySQL database
        conn = mysql.connector.connect(
                host=HOST,
                port=PORT,
                user=USER,
                password=PASSWORD,
                database=DATABASE_NAME
            )
    
        if conn.is_connected():
            print("Connected to DB Successfully")
            cursor = conn.cursor()
            
            # Clear all results in Schedule and Cost tables before calculating new schedules
            query_clear_schedule = "DELETE FROM `Schedule`"
            query_clear_cost = "DELETE FROM `Cost`"
            query_clear_barge_cost = "DELETE FROM `cost_barge`"
            cursor.execute(query_clear_schedule)
            cursor.execute(query_clear_cost)
            cursor.execute(query_clear_barge_cost)
            print("All previous schedule and cost records cleared")
            
            # Filter order_ids that were successfully processed
            valid_order_ids = [order_id for order_id in order_ids if order_id in tugboat_df["order_id"].unique()]
            
            if valid_order_ids:
                # No need to delete specific records as we've cleared all tables already
                
                # Prepare batch inserts for Schedule table
                insert_schedule_query = """
                    INSERT INTO `Schedule`(`ID`, `type`, `name`, `station_id`,  `enter_datetime`, 
                        `exit_datetime`, `rest_time`,  `distance`, `time`, `speed`, `type_point`, `order_trip`, 
                        `total_load`, `barge_ids`, `order_distance`, `order_time`,  `barge_speed`, order_arrival_time,
                        `tugboat_id`, `order_id`, `water_type`) 
                    VALUES (%s,%s,%s,%s,%s,
                            %s,%s,%s,%s,%s,%s,%s,
                            %s,%s,%s,%s,%s,%s,
                            %s,%s,%s)"""
                
                
                # Filter and prepare all schedule records
                schedule_records = []
                for order_id in valid_order_ids:
                    temp_tugboat_df = tugboat_df[tugboat_df["order_id"]==order_id]
                    temp_tugboat_df = temp_tugboat_df.replace([np.nan], [None])
                    # Before your batch insert, check for null time values
                    
                    
                    for _, row in temp_tugboat_df.iterrows():
                        
                        schedule_records.append((
                            row['ID'] if row["ID"] else None,
                            row['type'] if row["type"] else None,
                            row['name'] if row["name"] else None,
                            row['station_id'] if row["station_id"] else None,
                            row['enter_datetime'] if row["enter_datetime"] else None,
                            row['exit_datetime'] if row["exit_datetime"] else None,
                            row['rest_time'] if row["rest_time"] else 0,
                            row['distance'] if row["distance"] is not None else 0.0,
                            row['time'] if row["time"] is not None else 0.0,
                            row['speed'] if row["speed"] is not None else 0.0,
                            row['type_point'] if row["type_point"] else None,
                            row['order_trip'] if row["order_trip"] else 1,
                            row['total_load'] if row["total_load"] is not None else 0.0,
                            row['barge_ids'] if row["barge_ids"] else '',
                            row['order_distance'] if row["order_distance"] is not None else 0.0,
                            row['order_time'] if row["order_time"] is not None else 0.0,
                            row['barge_speed'] if row["barge_speed"] is not None else 0.0,
                            # order_arrival_time is datetime how to convert to database 
                            row['order_arrival_time'] if row["order_arrival_time"] else None,
                            
                            row['tugboat_id'] if row["tugboat_id"] else None,
                            row['order_id'] if row["order_id"] else None,
                            row['water_type'] if row["water_type"] else None,
                        ))
                        if _ == 0:
                            print(row)
                            print(insert_schedule_query % schedule_records[0])
                
                # Batch insert schedule records
                if schedule_records:
                    if schedule_records:
                        print(f"Number of columns in data tuple: {len(schedule_records[0])}")
                        print(schedule_records[0])
                        # print(f"First data record: {schedule_records[0]}") # Optional: see the actual data
                    else:
                        print("Schedule records list is empty, nothing to insert.")
                    cursor.executemany(insert_schedule_query, schedule_records)
                
                # Prepare batch inserts for Cost table
                insert_cost_query = """
                    INSERT INTO `Cost`(`TugboatId`, `OrderId`, `Time`, `Distance`, 
                        `ConsumptionRate`, `Cost`, `TotalLoad`, `StartDatetime`, `StartPointDatetime`, 
                        `FinishDatetime`, `StartStationId`, `StartPointStationId`, `EndPointStationId`, 
                        `UnloadLoadTime`, `ParkingTime`, `MoveTime`, `OrderTrip`, `AllTime`) 
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """
                # StartDatetime  StartPointDatetime          FinishDatetime StartStationId StartPointStationId EndPointStationId  UnloadLoadTime  ParkingTime   MoveTime     AllTime
                # Filter and prepare all cost records
                cost_records = []
                for order_id in valid_order_ids:
                    temp_cost_df = cost_df[cost_df["OrderId"]==order_id]
                    temp_cost_df = temp_cost_df.replace([np.nan], [None])
                    
                    for _, row in temp_cost_df.iterrows():
                        cost_records.append((
                            row['TugboatId'] if row["TugboatId"] else None,
                            row['OrderId'] if row["OrderId"] else None,
                            row['Time'] if row["Time"] is not None else 0.0,
                            row['Distance'] if row["Distance"] is not None else 0.0,
                            row['ConsumptionRate'] if row["ConsumptionRate"] is not None else 0.0,
                            row['Cost'] if row["Cost"] is not None else 0.0,
                            row['TotalLoad'] if row["TotalLoad"] is not None else 0.0,
                            row['StartDatetime'] if row["StartDatetime"] else None,
                            row['StartPointDatetime'] if row["StartPointDatetime"] else None,
                            row['FinishDatetime'] if row["FinishDatetime"] else None,
                            row['StartStationId'] if row["StartStationId"] else None,
                            row['StartPointStationId'] if row["StartPointStationId"] else None,
                            row['EndPointStationId'] if row["EndPointStationId"] else None,
                            row['UnloadLoadTime'] if row["UnloadLoadTime"] else 0,
                            row['ParkingTime'] if row["ParkingTime"] else 0,
                            row['MoveTime'] if row["MoveTime"] else 0,
                            row['OrderTrip'] if row["OrderTrip"] else 1,
                            row['AllTime'] if row["AllTime"] else None,
                        ))
                
                #print(insert_cost_query.format(cost_records[0]))
                
                # Batch insert cost records
                if cost_records:
                    cursor.executemany(insert_cost_query, cost_records)
                    
                    
                #do insert barge cost
                 #create pandas df with 
                # columns = [
                #     "BargeId",
                #     "TugboatId",
                #     "OrderId",
                #     "Time",
                #     "Distance",
                #     "Cost",
                #     "Load",
                #     "StartDatetime",
                #     "StartPointDatetime",
                #     "FinishDatetime",
                #     "StartStationId",
                #     "StartPointStationId",
                #     "EndPointStationId",
                #     "UnloadLoadTime",
                #     "ParkingTime",
                #     "MoveTime",
                #     "OrderTrip",
                #     "AllTime",
                # ]
                # Insert barge cost data
                insert_barge_cost_query = """
                    INSERT INTO `cost_barge`(`BargeId`, `TugboatId`, `OrderId`, `Time`, `Distance`, 
                        `Cost`, `Load`, `StartDatetime`, `StartPointDatetime`, `FinishDatetime`, 
                        `StartStationId`, `StartPointStationId`, `EndPointStationId`, `UnloadLoadTime`, 
                        `ParkingTime`, `MoveTime`, `OrderTrip`, `AllTime`) 
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """

                barge_cost_records = []
                for order_id in valid_order_ids:
                    temp_barge_df = barge_cost_df[barge_cost_df["OrderId"]==order_id]
                    temp_barge_df = temp_barge_df.replace([np.nan], [None])
                    
                    for _, row in temp_barge_df.iterrows():
                        temp_row_data = (
                            row['BargeId'] if row["BargeId"] else None,
                            row['TugboatId'] if row["TugboatId"] else None,
                            row['OrderId'] if row["OrderId"] else None,
                            row['Time'] if row["Time"] is not None else 0.0,
                            row['Distance'] if row["Distance"] is not None else 0.0,
                            row['Cost'] if row["Cost"] is not None else 0.0,
                            row['Load'] if row["Load"] is not None else 0.0,
                            row['StartDatetime'] if row["StartDatetime"] else None,
                            row['StartPointDatetime'] if row["StartPointDatetime"] else None,
                            row['FinishDatetime'] if row["FinishDatetime"] else None,
                            row['StartStationId'] if row["StartStationId"] else None,
                            row['StartPointStationId'] if row["StartPointStationId"] else None,
                            row['EndPointStationId'] if row["EndPointStationId"] else None,
                            row['UnloadLoadTime'] if row["UnloadLoadTime"] else 0,
                            row['ParkingTime'] if row["ParkingTime"] else 0,
                            row['MoveTime'] if row["MoveTime"] else 0,
                            row['OrderTrip'] if row["OrderTrip"] else 1,
                            row['AllTime'] if row["AllTime"] else None,
                        )
                        if temp_row_data[0] is None:
                            print("Error---------------------------------------------------------------")
                            print("temp_row_data", temp_row_data)
                        barge_cost_records.append(temp_row_data)

                # Batch insert barge cost records
                if barge_cost_records:
                    cursor.executemany(insert_barge_cost_query, barge_cost_records)
                    
                
                conn.commit()
            
            cursor.close()
            print(f"{cursor.rowcount} records inserted successfully into 'Cost' table.")

   
    finally:
        if conn and conn.is_connected():
            conn.close()
            print(f'MySQL connection for inserting data into Schedule table in {DATABASE_NAME} is closed')



def get_water_level_data(table_type='level_up'):
    """
    Load water level data from database.
    
    Args:
        table_type: 'level_up' or 'level_down' to specify which water level data to load
        
    Returns:
        pandas.DataFrame: Water level data or None if not found
    """
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
            cursor = conn.cursor(dictionary=True)
            
            # Try different possible table names for water level data
            possible_queries = [
               # f"SELECT * FROM water_{table_type}",
                #f"SELECT * FROM {table_type}",
                #f"SELECT * FROM WaterLevel WHERE type = '{table_type}'",
                #"SELECT * FROM WaterLevel",
                #"SHOW TABLES LIKE '%water%'",
                #"SHOW TABLES LIKE '%level%'",
                f"SELECT * FROM {table_type}_status"
            ]
            
            water_df = None
            
            for query in possible_queries:
                try:
                    print(f"Trying query: {query}")
                    cursor.execute(query)
                    
                    if query.startswith("SHOW TABLES"):
                        # List available tables for debugging
                        tables = cursor.fetchall()
                        print(f"Available tables matching pattern: {tables}")
                        continue
                        
                    results = cursor.fetchall()
                    
                    if results:
                        import pandas as pd
                        water_df = pd.DataFrame(results)
                        print(f"Successfully loaded data with query: {query}")
                        #print(f"Data shape: {water_df.shape}")
                        #print(f"Columns: {list(water_df.columns)}")
                        break
                        
                except Error as e:
                    print(f"Query failed: {query} - Error: {e}")
                    continue
            
            cursor.close()
            
            if water_df is not None and not water_df.empty:
                # Process the data to match expected format
                if 'DATETIME' not in water_df.columns:
                    # Look for datetime-like columns
                    datetime_cols = [col for col in water_df.columns if 'time' in col.lower() or 'date' in col.lower()]
                    if datetime_cols:
                        water_df = water_df.rename(columns={datetime_cols[0]: 'DATETIME'})
                
                print(f"Water level data loaded successfully from database")
                return water_df
            else:
                print(f"No water level data found in database.")
                return None
                    
    except Error as e:
        print(f"Database connection error: {e}")
        return None
        
    finally:
        if conn and conn.is_connected():
            conn.close()
            
    return None

if __name__ == '__main__':
    #connect_to_mysql_and_list_databases() # Lists all databases
    #list_tables_in_database('spinterdb') # Initial list if needed

    #print("\   nAttempting to drop 'Schedule' table (if it exists)...")
    #drop_table('Schedule')
    
    #print("\nAttempting to create 'Schedule' table...")
    #create_schedule_table()
    
    print("\nListing tables in 'spinterdb' after operations:")
    #list_tables_in_database()
    water_df = get_water_level_data('level_up')
    print(water_df.head())
    print(water_df.shape)
    print("---------")
    water_df = get_water_level_data('level_down')
    print(water_df.head())
    print(water_df.shape)
    print(water_df.shape)

    # Example usage for query_table_to_json:
    # table_data_json = query_table_to_json('spinterdb', 'Schedule') 
    # if table_data_json:
    #     print("--- JSON Output from Schedule table --- ")
    #     print(table_data_json)
    # else:
    #     print("Failed to retrieve data as JSON from Schedule table.")
