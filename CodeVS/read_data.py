import pandas as pd
from config_problem import *
from connectdb import *

# Define the file path
file_path = FILE_INPUT_NAME

# Load the Excel file
# xls = pd.ExcelFile(file_path)
# Read specific sheets into DataFrames
#assigned_barge_df = xls.parse("assigned_barge")
def get_table_from_db(table_name, order_id=None):
    """
    Updated column mapping to match the actual database schema from the PDF
    """
    column_name_dict = {
        'Tugboat': {
            'Id': 'ID',
            'Name': 'NAME',
            'MaxCapacity': 'MAX CAP',
            'MaxBarge': 'MAX BARGE',
            'MaxFuelCon': 'MAX FUEL CON',
            'Type': 'TYPE',
            'MinSpeed': 'MIN SPEED',
            'MaxSpeed': 'MAX SPEED',
            'EngineRpm': 'RPM',
            'HorsePower': 'HP',
            'WaterStatus': 'STATUS',  # From database schema
            'StationId': 'STATION',   # From database schema
            'ReadyDateTime': 'READY DATETIME'
        },
        'Carrier': {
            'Id': 'ID',
            'Name': 'NAME'
        },
        'Barge': {
            'Id': 'ID', 
            'Name': 'NAME', 
            'Weight': 'WEIGHT', 
            'Capacity': 'CAP', 
            'WaterStatus': 'WATER STATUS',  # From database schema
            'StationId': 'STATION',         # From database schema
            'SetupTime': 'SETUP TIME', 
            'ReadyDatetime': 'READY DATETIME'
        },
        'Station': {
            'Id': 'ID', 
            'Name': 'NAME',  # Changed from 'StationName' to 'Name' per schema
            'Type': 'TYPE', 
            'Latitude': 'LAT', 
            'Longitude': 'LNG', 
            'DistanceKm': 'KM'
        },
        'Order': {
            'Id': 'ID',
            'Type': 'TYPE',
            'FromEntityId': 'START POINT',  # Map to existing column name
            'DestEntityId': 'DES POINT',    # Map to existing column name
            'StartStationId': 'START STATION ID',
            'DestStationId': 'DES STATION ID',
            'ProductName': 'PRODUCT',
            'Demand': 'DEMAND',
            'StartDateTime': 'START DATETIME',
            'DueDateTime': 'DUE DATETIME',
            'LoadingRate': 'LD+ULD RATE',
            'CR1': 'CRANE RATE1',
            'CR2': 'CRANE RATE2',
            'CR3': 'CRANE RATE3',
            'CR4': 'CRANE RATE4',
            'CR5': 'CRANE RATE5',
            'CR6': 'CRANE RATE6',
            'CR7': 'CRANE RATE7',
            'CR8': 'CRANE RATE8',  # Added CR8 and CR9 from schema
            'CR9': 'CRANE RATE9',
            'TimeReadyCR1': 'TIME READY CR1',
            'TimeReadyCR2': 'TIME READY CR2',
            'TimeReadyCR3': 'TIME READY CR3',
            'TimeReadyCR4': 'TIME READY CR4',
            'TimeReadyCR5': 'TIME READY CR5',
            'TimeReadyCR6': 'TIME READY CR6',
            'TimeReadyCR7': 'TIME READY CR7',
            'TimeReadyCR8': 'TIME READY CR8',  # Added these mappings
            'TimeReadyCR9': 'TIME READY CR9'
        },
        'Customer': {
            'Id': 'ID',
            'Name': 'NAME',
            'Email': 'EMAIL',
            'Address': 'ADDRESS',
            'StationId': 'STATION',
            'Latitude': 'LAT',
            'Longitude': 'LNG'
        },
        'Customer_Station': {
            'CustomerId': 'CUSTOMER_ID',
            'StationId': 'STATION_ID'
        }
    }
    
    # Get raw data from database
    if table_name == 'Station':
        # Updated query to match the new schema structure
        data_json = query_table_to_json_custom('Station', """
            SELECT s.Id, s.Type, s.Name, s.Latitude, s.Longitude, s.DistanceKm, s.StationType, c.Name AS CustomerName
            FROM Station AS s
            LEFT JOIN Customer AS c ON c.stationId = s.Id
        """)
        table = pd.read_json(data_json)
        # Add customer name mapping
        table = table.rename(columns={
            'Id': 'ID',
            'Name': 'NAME', 
            'Type': 'TYPE',
            'Latitude': 'LAT',
            'Longitude': 'LNG', 
            'DistanceKm': 'KM',
            'CustomerName': 'CUS'
        })
        
    elif table_name == 'Order':
    # Updated query to handle Order table with proper column mapping
        if order_id:
            try:
                data_json = query_table_to_json_custom('Order', f"""
                    SELECT Id, Type, FromEntityId, DestEntityId, StartStationId, DestStationId,
                        ProductName, Demand, StartDateTime, DueDateTime, LoadingRate,
                        CR1, CR2, CR3, CR4, CR5, CR6, CR7, CR8, CR9,
                        TimeReadyCR1, TimeReadyCR2, TimeReadyCR3, TimeReadyCR4, TimeReadyCR5, 
                        TimeReadyCR6, TimeReadyCR7, TimeReadyCR8, TimeReadyCR9
                    FROM `Order`
                    WHERE Id = '{order_id}'
                """)
                # Check if data_json is None or empty
                if not data_json:
                    raise ValueError("Empty or null result returned from database query")
                
                # Parse the JSON data
                try:
                    table = pd.read_json(data_json)
                except Exception as e:
                    print(f"Error parsing JSON data: {e}")
                    return None
                
                table = table.rename(columns=column_name_dict[table_name])
                
            except Exception as e:
                print(f"Error executing order query with order_id: {e}")
                return None
                
        else:
            try:
                data_json = query_table_to_json_custom('Order', """
                    SELECT Id, Type, FromEntityId, DestEntityId, StartStationId, DestStationId,
                        ProductName, Demand, StartDateTime, DueDateTime, LoadingRate,
                        CR1, CR2, CR3, CR4, CR5, CR6, CR7, CR8, CR9,
                        TimeReadyCR1, TimeReadyCR2, TimeReadyCR3, TimeReadyCR4, TimeReadyCR5, 
                        TimeReadyCR6, TimeReadyCR7, TimeReadyCR8, TimeReadyCR9
                    FROM `Order`
                """)
                # Check if data_json is None or empty
                if not data_json:
                    raise ValueError("Empty or null result returned from database query")
                
                # Parse the JSON data
                try:
                    table = pd.read_json(data_json)
                except Exception as e:
                    print(f"Error parsing JSON data: {e}")
                    return None
                
                table = table.rename(columns=column_name_dict[table_name])
                
            except Exception as e:
                print(f"Error executing order query: {e}")
                return None
    
    elif table_name == 'Customer':
        # Handle Customer table
        try:
            data_json = query_table_to_json_custom('Customer', """
                SELECT c.Id, c.Name, c.Email, c.Address, c.StationId, 
                       s.Latitude, s.Longitude
                FROM Customer AS c
                LEFT JOIN Station AS s ON c.StationId = s.Id
            """)
            
            # Check if data_json is None or empty
            if not data_json:
                raise ValueError("Empty or null result returned from database query")
            
            # Parse the JSON data
            try:
                table = pd.read_json(data_json)
            except Exception as e:
                print(f"Error parsing JSON data: {e}")
                return None
            
            table = table.rename(columns=column_name_dict[table_name])
            
            # Add LAT, LNG from station data if available
            if 'Latitude' in table.columns and 'Longitude' in table.columns:
                table['LAT'] = table['Latitude']
                table['LNG'] = table['Longitude']
                
        except Exception as e:
            print(f"Error executing customer query: {e}")
            return None
        
    elif table_name == 'Carrier':
        # Updated query to get carrier info with orders and location from start station
        # Get carrier info directly from Order table FromPoint/DestPoint with fallback logic
        try:
            # Try with start_station_id/des_station_id first
            data_json = query_table_to_json_custom('Carrier', """
                SELECT DISTINCT
                    o.carrier_id AS Id,
                    c.Name AS Name,
                    o.Id AS OrderId,
                    o.StartStationId,
                    o.DestEntityId,
                    o.Type AS OrderType,
                    CASE 
                        WHEN o.Type = 'IMPORT' THEN ss.Latitude
                        WHEN o.Type = 'EXPORT' THEN ds.Latitude
                        ELSE ss.Latitude
                    END AS Latitude,
                    CASE 
                        WHEN o.Type = 'IMPORT' THEN ss.Longitude
                        WHEN o.Type = 'EXPORT' THEN ds.Longitude
                        ELSE ss.Longitude
                    END AS Longitude
                FROM (
                    SELECT Id, Type, FromEntityId, DestEntityId, StartStationId, DestStationId,
                           CASE 
                               WHEN Type = 'IMPORT' THEN FromEntityId
                               WHEN Type = 'EXPORT' THEN DestEntityId
                               ELSE FromEntityId
                           END AS carrier_id
                    FROM `Order`
                ) AS o
                LEFT JOIN `Carrier` AS c ON o.carrier_id = c.Id
                LEFT JOIN `Station` AS ss ON o.StartStationId = ss.Id
                LEFT JOIN `Station` AS ds ON o.DestStationId = ds.Id
                WHERE c.Name IS NOT NULL AND c.Name != ''
            """)
            print("✓ Using carrier query with StartStationId/DestStationId")
            
        except Exception as e:
            print(f"Advanced carrier query failed: {e}")
            print("Using fallback carrier query...")
            
            # Fallback: Simple query with default coordinates
            data_json = query_table_to_json_custom('Carrier', """
                SELECT DISTINCT
                    o.carrier_id AS Id,
                    carrier_name AS Name,
                    o.Id AS OrderId,
                    o.FromPoint,
                    o.DestPoint,
                    o.Type AS OrderType,
                    13.7563 AS Latitude,
                    100.5018 AS Longitude
                FROM (
                    SELECT Id, Type, FromPoint, DestPoint,
                           CASE 
                               WHEN Type = 'IMPORT' THEN FromPoint
                               WHEN Type = 'EXPORT' THEN DestPoint
                               ELSE FromPoint
                           END AS carrier_name
                    FROM `Order`
                ) AS o
                WHERE carrier_name IS NOT NULL AND carrier_name != ''
            """)
            print("✓ Using simple carrier query with default coordinates")
        
        table = pd.read_json(data_json)
        table = table.rename(columns={
            'Id': 'ID',
            'Name': 'NAME',
            'OrderId': 'ORDER ID',
            'OrderType': 'ORDER TYPE',
            'Latitude': 'LAT',
            'Longitude': 'LNG'
        })
        # Note: Latitude and Longitude are not in the Carrier table per schema
        # You might need to add these fields or get them from another source
        
    elif table_name == 'Tugboat':
        # Updated query to get tugboat location from station
        data_json = query_table_to_json_custom('Tugboat', """
            SELECT t.Id, t.Name, t.MaxCapacity, t.MaxBarge, t.MaxFuelCon, t.Type,
                   t.MinSpeed, t.MaxSpeed, t.EngineRpm, t.HorsePower, t.WaterStatus,
                   t.ReadyDateTime, t.StationId, s.Latitude, s.Longitude, s.DistanceKm
            FROM Tugboat AS t
            LEFT JOIN Station AS s ON t.StationId = s.Id
        """)
        table = pd.read_json(data_json)
        table = table.rename(columns=column_name_dict[table_name])
        # Add LAT, LNG, KM from station data
        table['LAT'] = table.get('Latitude', 0)
        table['LNG'] = table.get('Longitude', 0) 
        table['KM'] = table.get('DistanceKm', 0)
        
    elif table_name == 'Barge':
        # Updated query to get barge location from station
        data_json = query_table_to_json_custom('Barge', """
            SELECT b.Id, b.Name, b.Weight, b.Capacity, b.WaterStatus, b.StationId,
                   b.SetupTime, b.ReadyDatetime, s.Latitude, s.Longitude, s.DistanceKm
            FROM Barge AS b
            LEFT JOIN Station AS s ON b.StationId = s.Id
        """)
        table = pd.read_json(data_json)
        table = table.rename(columns=column_name_dict[table_name])
        # Add LAT, LNG, KM from station data
        table['LAT'] = table.get('Latitude', 0)
        table['LNG'] = table.get('Longitude', 0)
        table['KM'] = table.get('DistanceKm', 0)
        
    elif table_name == 'Order':
    # Updated query to handle Order table with proper column mapping
        if order_id:
            data_json = query_table_to_json_custom('Order', f"""
                SELECT Id, Type, FromEntityId, DestEntityId, StartStationId, DestStationId,
                    ProductName, Demand, StartDateTime, DueDateTime, LoadingRate,
                    CR1, CR2, CR3, CR4, CR5, CR6, CR7, CR8, CR9,
                    TimeReadyCR1, TimeReadyCR2, TimeReadyCR3, TimeReadyCR4, TimeReadyCR5, 
                    TimeReadyCR6, TimeReadyCR7, TimeReadyCR8, TimeReadyCR9
                FROM `Order`
                WHERE Id = '{order_id}'
            """)
        else:
            data_json = query_table_to_json_custom('Order', """
                SELECT Id, Type, FromEntityId, DestEntityId, StartStationId, DestStationId,
                    ProductName, Demand, StartDateTime, DueDateTime, LoadingRate,
                    CR1, CR2, CR3, CR4, CR5, CR6, CR7, CR8, CR9,
                    TimeReadyCR1, TimeReadyCR2, TimeReadyCR3, TimeReadyCR4, TimeReadyCR5, 
                    TimeReadyCR6, TimeReadyCR7, TimeReadyCR8, TimeReadyCR9
                FROM `Order`
            """)
        
        table = pd.read_json(data_json)
        table = table.rename(columns=column_name_dict[table_name])
    
    # Filter by order_id if provided
    if order_id and 'ID' in table.columns:
        table = table[table['ID'] == order_id]
    
    return table

def get_data_from_db(table_name=False, order_id=False):
    if not table_name:
        carrier_df = get_table_from_db('Carrier')
        # print(carrier_df)

        # print(carrier_df.columns)
        barge_df = get_table_from_db('Barge')
        # print(barge_df.columns)
        tugboat_df = get_table_from_db('Tugboat')
        # print(tugboat_df)
        station_df = get_table_from_db('Station')
        # print(station_df)
        customer_df = get_table_from_db('Customer')
        # print(customer_df)

        # print(station_df.columns)
        order_df = get_table_from_db('Order',order_id=order_id)
        # print(order_df)
        # print(order_df.columns)
        return (carrier_df, barge_df, tugboat_df, station_df, order_df, customer_df)
    elif table_name:
        return get_table_from_db(table_name)
        # print("Table not found.")

# def print_df():
#     print("Carrier:")
#     print(carrier_df.head())
#     print("\nBarge:")
#     print(barge_df.head())
#     print("\nTugboat:")
#     print(tugboat_df.head())
#     print("\nStation:")
#     print(station_df.head())
#     print("\nOrder:")
#     print(order_df.head())
    #print("\nAssigned Barge:")
    #print(assigned_barge_df.head())
    
    
def test_read_data():
    tugboat_json = query_table_to_json('Tugboat')   
    print(tugboat_json)
    # json to pandas
    tugboat_dfv2 = pd.read_json(tugboat_json)

    # Define the column mapping
    column_mapping = {
        'Id': 'ID',
        'Name': 'NAME',
        'MaxCapacity': 'MAX CAP',
        'MaxBarge': 'MAX BARGE',
        'MaxFuelCon': 'MAX FUEL CON',
        'Type': 'TYPE',
        'MinSpeed': 'MIN SPEED',
        'MaxSpeed': 'MAX SPEED',
        'EngineRpm': 'RPM',
        'HorsePower': 'HP',
        'Latitude': 'LAT',
        'Longitude': 'LNG',
        'WaterStatus': 'STATUS',
        'DistanceKm': 'KM',
        'ReadyDateTime': 'READY DATETIME'
    }
    # Rename the columns
    tugboat_dfv2 = tugboat_dfv2.rename(columns=column_mapping)
    print("tugboat_dfv2 columns after renaming:")
    print(tugboat_dfv2.columns)
    print(tugboat_dfv2.head())
    print(tugboat_df.columns)
    print(tugboat_df.head())
    
    
    
    
    print("Are tugboat_dfv2 and tugboat_df equal?")
    print(tugboat_dfv2.equals(tugboat_df))
    
if __name__ == "__main__":
    # tugboat_df = get_table_from_db('Tugboat')
    # print(tugboat_df.head())
    # station_df = get_table_from_db('Station')
    # print(station_df.head())
    # carrier_df = get_table_from_db('Carrier')
    # print(carrier_df.head())
    # barge_df = get_table_from_db('Barge')
    # print(barge_df.head())
    # order_df = get_table_from_db('Order')
    # print(order_df.head())
    carrier_df, barge_df, tugboat_df, station_df, order_df, customer_df = get_data_from_db()
    print(carrier_df.head())
    print(barge_df.head())
    print(tugboat_df.head())
    print(station_df.head())    
    print(order_df.head())
    print(customer_df.head())
#     schedule_json = query_table_to_json('Schedule')
#     schedule_dfv2 = pd.read_json(schedule_json)
#     print(schedule_dfv2.columns)
#     print(schedule_dfv2.head())

    
#     # pandas read excel sheet Summary file
#     schedule_xls = pd.ExcelFile('CodeVS/data/output/tugboat_schedule.xlsx')
#     schedule_dfv3 = pd.read_excel(schedule_xls, sheet_name='Summary')
#     print(schedule_dfv3.columns)
#     print(schedule_dfv3.head())
    
#     #convert schedule_dfv3 to json
#     schedule_jsonv3 = schedule_dfv3.to_json(orient='records')
#     print(schedule_jsonv3)
    
#     insert_data_into_schedule(schedule_jsonv3)
    
    