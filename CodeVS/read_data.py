import pandas as pd
from config_problem import *

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