import pandas as pd
from config_problem import *
from connectdb import *

# Define the file path
file_path = FILE_INPUT_NAME

# Load the Excel file
# xls = pd.ExcelFile(file_path)

# Read specific sheets into DataFrames

#assigned_barge_df = xls.parse("assigned_barge")

def get_table_from_db(table_name, order_id=False):
    column_name_dict = {
        'Tugboat':{
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
        },
        'Carrier':{'Id':'ID',
                    'Name':'NAME', 
                    'Order_id':'ORDER ID',
                    'Latitude':'LAT', 
                    'Longitude':'LNG'},

        'Barge':{'Id':'ID', 
                 'Name':'NAME', 
                 'Weight':'WEIGHT', 
                 'Capacity':'CAP', 
                 'Latitude':'LAT', 
                 'Longitude':'LNG',
                 'WaterStatus':'WATER STATUS', 
                 'StationId':'STATION', 
                 'DistanceKm':'KM', 
                 'SetupTime':'SETUP TIME', 
                 'ReadyDatetime':'READY DATETIME'},

        'Station':{'Id':'ID', 
                   'StationName':'NAME', 
                   'Type':'TYPE', 
                   'Latitude':'LAT', 
                   'Longitude':'LNG', 
                   'DistanceKm':'KM',
                   'Name':'CUS'},

        'Order':{'Id':'ID', 
                 'Type':'TYPE', 
                 'FromPoint':'START POINT', 
                 'DestPoint':'DES POINT', 
                 'ProductName':'PRODUCT', 
                 'Demand':'DEMAND',
                 'StartDateTime':'START DATETIME', 
                 'DueDateTime':'DUE DATETIME', 
                 'LoadingRate':'LD+ULD RATE', 
                 'CR1':'CRANE RATE1', 
                 'CR2':'CRANE RATE2', 
                 'CR3':'CRANE RATE3',
                 'CR4':'CRANE RATE4', 
                 'CR5':'CRANE RATE5', 
                 'CR6':'CRANE RATE6', 
                 'CR7':'CRANE RATE7', 
                 'TimeReadyCR1':'TIME READY CR1', 
                 'TimeReadyCR2':'TIME READY CR2',
                 'TimeReadyCR3':'TIME READY CR3', 
                 'TimeReadyCR4':'TIME READY CR4', 
                 'TimeReadyCR5':'TIME READY CR5', 
                 'TimeReadyCR6':'TIME READY CR6',
                 'TimeReadyCR7':'TIME READY CR7'}

    }
    data_json = query_table_to_json(table_name)
    table = pd.read_json(data_json)
    
    table = table.rename(columns=column_name_dict[table_name])
    # print(table)
    # if order_id:
    #     table = table[table['ID']==order_id]
    # print(table)
    # eeeeee
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


        # print(station_df.columns)
        order_df = get_table_from_db('Order',order_id=order_id)
        # print(order_df)
        # print(order_df.columns)
        return (carrier_df, barge_df, tugboat_df, station_df, order_df)
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
    
# if __name__ == "__main__":
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
    
    