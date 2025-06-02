import pandas as pd
from config_problem import *
from connectdb import *

# Define the file path
file_path = FILE_INPUT_NAME

# Load the Excel file
xls = pd.ExcelFile(file_path)

# Read specific sheets into DataFrames
carrier_df = xls.parse("carrier")
barge_df = xls.parse("barge")
tugboat_df = xls.parse("tugboat")
station_df = xls.parse("station")
order_df = xls.parse("order")
#assigned_barge_df = xls.parse("assigned_barge")






def print_df():
    print("Carrier:")
    print(carrier_df.head())
    print("\nBarge:")
    print(barge_df.head())
    print("\nTugboat:")
    print(tugboat_df.head())
    print("\nStation:")
    print(station_df.head())
    print("\nOrder:")
    print(order_df.head())
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
    schedule_json = query_table_to_json('Schedule')
    schedule_dfv2 = pd.read_json(schedule_json)
    print(schedule_dfv2.columns)
    print(schedule_dfv2.head())
    
    # pandas read excel sheet Summary file
    schedule_xls = pd.ExcelFile('CodeVS/data/output/tugboat_schedule.xlsx')
    schedule_dfv3 = pd.read_excel(schedule_xls, sheet_name='Summary')
    print(schedule_dfv3.columns)
    print(schedule_dfv3.head())
    
    #convert schedule_dfv3 to json
    schedule_jsonv3 = schedule_dfv3.to_json(orient='records')
    print(schedule_jsonv3)
    
    insert_data_into_schedule(schedule_jsonv3)
    
    