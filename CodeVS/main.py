import sys
import os

from click.decorators import R
from pandas.core.tools.datetimes import start_caching_at


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import timedelta, datetime
import pandas as pd
from read_data import *
from initialize_data import initialize_data, print_all_objects
from CodeVS.operations.assigned_barge import *
from CodeVS.operations.scheduling import *
from CodeVS.operations.transport_order import *
from CodeVS.operations.travel_helper import *
from CodeVS.components.solution import Solution
import warnings
warnings.filterwarnings(action='ignore')
import numpy as np

from pymoo.core.callback import Callback
from pymoo.optimize import minimize
from CodeVS.algorithm.AMIS import AMIS
from CodeVS.problems.tugboat_problem import TugboatProblem
from connectdb import update_database


from enum import Enum
class TestingResult(Enum):
    CRANE = 1
    ORDER = 2
    TUGBOAT = 3
    BARGE = 4
    COST = 5
    OTHER = 6
    NOTING = 7

# def test_tugboat(data):
#     tugboats = data['tugboats']
    
#     current_used_barge_list = assign_barges_to_orders(data['orders'], 
#                                 data['barges'], assigned_barge_df)
    
#     # Count and filter tugboats
#     total_tugboats = len(tugboats)
#     print(f"\nTotal Tugboats: {total_tugboats}")
    
#     sea_tugboats = {tugboat_id: tugboat for tugboat_id, tugboat in tugboats.items() if tugboat.tug_type == 'SEA'}
#     river_tugboats = {tugboat_id: tugboat for tugboat_id, tugboat in tugboats.items() if tugboat.tug_type == 'RIVER'}
    
#     print(f"Sea Tugboats: {len(sea_tugboats)}")
#     print(f"River Tugboats: {len(river_tugboats)}")

#     # Print sea tugboats
#     print("\nSea Tugboats:")
#     for tugboat_id, tugboat in sea_tugboats.items():
#         print(tugboat)

#     first_level_info = {
#         'type_transport': 'import',
#         "sea_tugboat" : sea_tugboats['tbs1'],
#         'river_tugboat' : river_tugboats['tbr1'],
#         "appoint_location" : 's2'
#     }

#     sea_tugboat1 = first_level_info["sea_tugboat"]
#     print("Speed Before load", sea_tugboat1.calculate_current_speed())
#     assign_barges_to_tugboat( sea_tugboat1, current_used_barge_list)
#     total_barge_weight = sea_tugboat1.get_total_weight_barge()
#     print("Affter load", sea_tugboat1.calculate_speed(0, 4, total_barge_weight))

#     print("1, tugboat to collect barge ----------------------------------")
#     result_step1 =  sea_tugboat1.calculate_collection_barge_time()
#     print(result_step1)
#     print("--------------------------------------------------------------")
#     print()
#     print("2. to carrier ------------------------------------------------")
#     last_location = result_step1['last_location']
#     result_step2 = sea_tugboat1.calculate_collection_product_time_with_crane_rate(last_location)
#     print(result_step2)
#     print("--------------------------------------------------------------")
#     print()

#     load_speed = sea_tugboat1.calculate_current_speed()
#     print("Speed After load", load_speed)
#     print("3. to carrier ------------------------------------------------")

# def test_assign_barge_to_order(data):
#     orders = data['orders']
#     barges = data['barges']
#     tugboats = data['tugboats']
    
#     assigned_barge_infos = assign_barges_to_single_order(orders['o1'], barges)
#     print(f"\nAssigning barges to Order {orders['o1'].order_id}... {len(assigned_barge_infos)} barges")
#     print("\nAssignment results:")
#     for barge_info in assigned_barge_infos:
#         barge = barge_info['barge']
#         distance = barge_info['distance']
#         print(f"Barge {barge.barge_id} assigned to Order {barge.current_order.order_id}")
#         print(f"  - Load: {barge.load}")
#         print(f"  - Distance: {distance} km: {barge.crane_rate}")
    
#     sea_tugboats = {tugboat_id: tugboat for tugboat_id, tugboat in tugboats.items() if tugboat.tug_type == 'SEA'}
    
#     assigned_barges = [barge_info['barge'] for barge_info in assigned_barge_infos]
#     assigned_tugboats = assign_barges_to_tugboats(orders['o1'],sea_tugboats, assigned_barges)

    
#     print("\nTesting all orders assignment...")
#     for tugboat in assigned_tugboats:
#         print(f"\nAssigning barges to Tugboat {tugboat.tugboat_id}... {len(tugboat.assigned_barges)} barges")
#         print(f"Total Weight: {tugboat.get_total_load()} tugboat capacity: {tugboat.max_capacity}")
#         print("\nAssignment results:")
#         for barge in tugboat.assigned_barges:
#             print(f"Barge {barge.barge_id} assigned to Tugboat {tugboat.tugboat_id}")
#             print(f"  - Load: {barge.load}")
#             print(f"  - Distance: {barge.used_end - barge.used_start} km: {barge.crane_rate}")

   
#     # result = schedule_order_single_tugboat(orders['o1'], assigned_tugboats[0])
#     # crane_schedule = result['crane_schedule']
#     # barge_schedule = result['barge_schedule']
#     # tugboat_schedule = result['tugboat_schedule']
#     # print("\nCrane Schedule:")
#     # for crane in crane_schedule:
#     #     print(crane)
#     # print("\nBarge Schedule:")
#     # for barge in barge_schedule:
#     #     print(barge)
#     # print("\nTugboat Schedule:")
#     # for tugboat in tugboat_schedule:
#     #     print(tugboat)
    
    
#     for tugboat in assigned_tugboats:
#         print(f"\nAssigning barges to Tugboat EE {tugboat.tugboat_id}... {len(tugboat.assigned_barges)} barges")
    
#     results = schedule_carrier_order_tugboats(orders['o1'], assigned_tugboats, [0, 0, 20,  30])
#     for result in results:
#         print("\nSchedule for Tugboat", result['tugboat_schedule']['tugboat_id'])
#         crane_schedule = result['crane_schedule']
#         barge_schedule = result['barge_schedule']    
#         tugboat_schedule = result['tugboat_schedule']
#         print("\nCrane Schedule:")
#         for crane in crane_schedule:
#             print(crane)    
#         print("\nBarge Schedule:")          
#         for barge in barge_schedule:
#             print(barge)
#         print("\nTugboat Schedule:")
        
#         print(tugboat_schedule)

def test_transport_order(data, testing=False, testing_result=TestingResult.CRANE):
    # orders = data['orders']
    # barges = data['barges']
    # tugboats = data['tugboats']
    # order = orders['o1']
    
    
    solution = Solution(data)
    
    
    # cost_results, tugboat_df, barge_df, cost_df = solution.calculate_cost()
    # print(cost_results)
    # print(barge_df)
    return solution.calculate_cost()
#     print(tugboat_df)
#     print(cost_df)
    
    
    
# #     filtered_df = tugboat_df[
# #                             ((tugboat_df['tugboat_id'] == 'tbs1') | (tugboat_df['tugboat_id'] == 'tbr5')) 
# #                            # &  ((tugboat_df['order_id'] == 'o1') | (tugboat_df['order_id'] == 'o1'))
# #                             &  ((tugboat_df['order_id'] == 'o1') )
# #                            # & (tugboat_df['order_trip'] == 1)
# #                             #& (tugboat_df['distance'] > 60)
# #                             #(tugboat_df['distance'] > 60)
# #                             ]
# #     temp_df = filtered_df[['ID', 'type', 'name', 'enter_datetime', 'exit_datetime', 
# #                            'tugboat_id','distance', 'time', 'speed','order_trip',
# #                       # 'distance', 'time', 'speed', 'order_trip', 'total_load', 'barge_ids'
# #                       'total_load', 'barge_ids',
# #        #'order_distance', 'order_time', 'barge_speed', 'order_arrival_time',
# #        #'tugboat_id', 'order_id', 'water_type'
# #        ]]
    
# #     if testing:
# #         if testing_result == TestingResult.CRANE:
# #             filtered_df = tugboat_df[
# #                             #((tugboat_df['tugboat_id'] == 'tbs1') | (tugboat_df['tugboat_id'] == 'tbr5')) 
# #                            # &  ((tugboat_df['order_id'] == 'o1') | (tugboat_df['order_id'] == 'o1'))
# #                            #((tugboat_df['order_id'] == 'o1') )
# #                            # & (tugboat_df['order_trip'] == 1)
# #                             #& (tugboat_df['distance'] > 60)
# #                             #(tugboat_df['distance'] > 60)
# #                             (tugboat_df['name'].str.contains('cr1', case=False, na=False))
# #                             ]
# #             temp_df = filtered_df[['ID', 'type', 'name', 'enter_datetime', 'exit_datetime', 
# #                                 'tugboat_id','distance', 'time', 'speed','order_trip',
# #                             # 'distance', 'time', 'speed', 'order_trip', 'total_load', 'barge_ids'
# #                             'total_load', 'barge_ids',
# #                             ]]
# #             print(temp_df)
# #         if testing_result == TestingResult.TUGBOAT:
# #             filtered_df = tugboat_df[
# #                             ((tugboat_df['tugboat_id'] == 'tbr1') | (tugboat_df['tugboat_id'] == 'tbr1')) 
# #                             &  ((tugboat_df['order_id'] == 'o1') | (tugboat_df['order_id'] == 'o1')| (tugboat_df['order_id'] == 'o1'))
# #                            #((tugboat_df['order_id'] == 'o1') )
# #                            # & (tugboat_df['order_trip'] == 1)
# #                             #& (tugboat_df['distance'] > 60)
# #                             #(tugboat_df['distance'] > 60)
# #                             #(tugboat_df['name'].str.contains('cr1', case=False, na=False))
# #                             ]
# #             temp_df = filtered_df[['ID', 'type', 'name', 'enter_datetime', 'exit_datetime', 
# #                                 'tugboat_id','distance', 'time', 'speed','order_trip',
# #                             # 'distance', 'time', 'speed', 'order_trip', 'total_load', 'barge_ids'
# #                             'total_load', 'barge_ids',
# #                             ]]
# #             print(temp_df.head(55))
        
# #         if testing_result == TestingResult.BARGE:
# #             #check barge_id not contains ','
# #             filtered_df = tugboat_df[~tugboat_df['barge_ids'].str.contains(',')]
           
# #             temp_df = filtered_df[['ID', 'type', 'name', 'enter_datetime', 'exit_datetime', 
# #                                 'tugboat_id','distance', 'time', 'speed','order_trip',
# #                             # 'distance', 'time', 'speed', 'order_trip', 'total_load', 'barge_ids'
# #                             'total_load', 'barge_ids',
# #                             ]]
# #             print(np.unique(temp_df['barge_ids']))
# #             print("Number of used barges", len(np.unique(temp_df['barge_ids'])))
# #             print("Number of all barges", len(data['barges']))
            
# #             # use the regular machine exacly b4 not b41
            
# #             filtered_df = tugboat_df[tugboat_df['barge_ids'].str.contains(r'\bb11\b', regex=True)]
# #             temp_df = filtered_df[['ID', 'type', 'name', 'enter_datetime', 'exit_datetime', 
# #                                 'tugboat_id','distance', 'time', 'speed','order_trip',
# #                             # 'distance', 'time', 'speed', 'order_trip', 'total_load', 'barge_ids'
# #                             'total_load', 'barge_ids',
# #                             ]]
# #             print(temp_df)
    
# # #     filtered_df = tugboat_df[
# # #                             ((tugboat_df['tugboat_id'] == 'tbr1') | (tugboat_df['tugboat_id'] == 'tbr1')) 
# # #                             #((tugboat_df['order_id'] == 'o1') | (tugboat_df['order_id'] == 'o2'))
# # #                             #& (tugboat_df['order_trip'] == 1) 
# # #                             #& ((tugboat_df['type'] == 'Loader-Customer') | (tugboat_df['type'] == 'Crane-Carrier') | 
# # #                             #   (tugboat_df['type'] == 'Customer Station')| (tugboat_df['type'] == 'Start Order Carrier'))
# # #                             #& (tugboat_df['distance'] > 60)
# # #                             #(tugboat_df['distance'] > 60)
# # #                             #(tugboat_df['name'].str.contains('ld1', case=False, na=False))
# # #     ]
    
    
    
# # #     temp_df = filtered_df[['ID', 'type', 'name', 'enter_datetime', 'exit_datetime',
# # #                             'tugboat_id','distance', 'speed','order_trip'
# # #                       # 'distance', 'time', 'speed', 'order_trip', 'total_load', 'barge_ids'
# # #        #'order_distance', 'order_time', 'barge_speed', 'order_arrival_time',
# # #        #'tugboat_id', 'order_id', 'water_type'
# # #        ]]
# # #     # print(temp_df)
    
    

# # #     filtered_df = tugboat_df[
# # #                             (
# # #                             #& (tugboat_df['order_trip'] == 1) 
# # #                             (tugboat_df['type'] == 'Customer Station'))
# # #                             #(tugboat_df['type'] == 'Appointment'))
# # #                             #& (tugboat_df['distance'] > 60)
# # #                             #(tugboat_df['distance'] > 60)
# # #     ]
# # #     temp_df = filtered_df[['ID', 'type', 'name', 'enter_datetime',  'total_load', 'order_id',
# # #                            'exit_datetime', 'tugboat_id','distance', 'time', 'speed','order_trip'
# # #                       # 'distance', 'time', 'speed', 'order_trip', 'total_load', 'barge_ids'
# # #        #'order_distance', 'order_time', 'barge_speed', 'order_arrival_time',
# # #        #'tugboat_id', 'order_id', 'water_type'
# # #        ]]
# # #     #print(temp_df)
# # #     #demand_load = sum(order_df['DEMAND'])
# # #     #print("Total Load",  sum(temp_df['total_load']), demand_load)
    
# # #     grouped_df = temp_df.groupby('order_id')['total_load'].sum().reset_index()
# # # # Now you can print the grouped data
# # #     #print(grouped_df)
# # #     grouped_df = order_df.groupby('ID')['DEMAND'].sum().reset_index()
# # # # Now you can print the grouped data
# # #     #print(grouped_df)

# # #     #print("customer_river_time_lates", customerso_river_time_lates, list_lates)


# # #     # for order_id, order_barge_info in lookup_order_barges.items():
# # #     #     print(order_barge_info)
        
        
# # #     # #print('-------------------------- Tugboat')
# # #     # for tugboat_id, results in lookup_river_tugboat_results.items( ):
# # #     #     print(tugboat_id, results['data_points'][1]['exit_datetime'])

#     # if not testing:
#     #     solution.save_schedule_to_csv(tugboat_df, barge_df,
#     #                                 tugboat_path='CodeVS/data/output/tugboat_schedule.xlsx',
#     #                                 barge_path='CodeVS/data/output/barge_schedule.xlsx')
#     #     print("Schedule Created")
#     return tugboat_df
    
def main(testing=False, testing_result=TestingResult.CRANE):
    # Initialize data structures

    data_df = get_data_from_db()
    #order_df = order_df[order_df['ID']=='o1']
    # print(carrier_df)
    # eed
    
    data = initialize_data(data_df)
    
    if TravelHelper._instance is None:
        TravelHelper()
        
    TravelHelper._set_data(TravelHelper._instance,  data)
    
    #print(f"Data Type: {type(data)}")
    #for key, value in data.items():
    #    print(key, value, "\n")
    # print(data)
    # eeeee
    # TravelHelper()
    # print("========================================")
    # print(f"Type {type(TravelHelper._instance)}")
    # print("========================================")
    # TravelHelper._set_data(TravelHelper._instance,  data)
    
    
    # Print all objects (optional)
    #print_all_objects(data)
    
    # Run tests
    #test_assign_barge_to_order(data)
    
    cost_results, tugboat_df, barge_df, cost_df = test_transport_order(data, testing, testing_result)
    # print(Travel_Helper.get_next_station(TransportType.IMPORT, 11))
    # print(Travel_Helper.get_next_station(TransportType.IMPORT, 15))
    # print(Travel_Helper.get_next_station(TransportType.EXPORT, 15))
    print(testing, testing_result)
    
    filtered_df = tugboat_df[
                        ((tugboat_df['tugboat_id'] == 'tbs01') | (tugboat_df['tugboat_id'] == 'tbr05x')) 
                        # &  ((tugboat_df['order_id'] == 'o1') | (tugboat_df['order_id'] == 'o1'))
                        &  ((tugboat_df['order_id'] == 'o1') )
                        # & (tugboat_df['order_trip'] == 1)
                        #& (tugboat_df['distance'] > 60)
                        #(tugboat_df['distance'] > 60)
                        ]
    
    temp_df = filtered_df[['ID', 'type', 'name', 'enter_datetime', 'exit_datetime', 
                           'tugboat_id','distance', 'time', 'speed','order_trip',
                      # 'distance', 'time', 'speed', 'order_trip', 'total_load', 'barge_ids'
                     # 'total_load', 'barge_ids',
       #'order_distance', 'order_time', 'barge_speed', 'order_arrival_time',
       #'tugboat_id', 'order_id', 'water_type'
       ]]
    
    print(temp_df)
    print("order_df", order_df.columns)
    print("order_df", order_df[['ID', 'TYPE', 'START POINT', 'DES POINT', 'START STATION ID',
       'DES STATION ID', 'PRODUCT', 'DEMAND', 'START DATETIME', 'DUE DATETIME',
       #'LD+ULD RATE', 'CRANE RATE1', 'CRANE RATE2', 'CRANE RATE3',
       #'CRANE RATE4', 'CRANE RATE5', 'CRANE RATE6', 'CRANE RATE7',
       #'TIME READY CR1', 'TIME READY CR2', 'TIME READY CR3', 'TIME READY CR4',
       #'TIME READY CR5', 'TIME READY CR6', 'TIME READY CR7'
       ]])
    
    return tugboat_df

def test_read_data():
  
    carrier_df, barge_df, tugboat_df, station_df, order_df  , customer_df = get_data_from_db()
    
    # print(carrier_df)
    # print(barge_df)
    # print(tugboat_df)
    # print(station_df)
    # print(order_df)
    # print(customer_df)
    
    data = initialize_data(carrier_df, barge_df, 
                           tugboat_df, station_df, order_df, customer_df)
    
    if TravelHelper._instance is None:
        TravelHelper()
    
    TravelHelper._set_data(TravelHelper._instance,  data)
    # print_all_objects(data)

    
    order_ids = [ order_id for order_id in data['orders'].keys() if data['orders'][order_id].order_type == TransportType.IMPORT]
    order_ids = order_ids[:]
    
    solution = Solution(data)
    is_success, tugboat_df, barge_df = solution.generate_schedule(order_ids)
    
    #print(tugboat_df)
    columns_of_interest = ['tugboat_id', 'type', 'name', 'enter_datetime', 'exit_datetime', 
                      'distance', 'time', 'speed', 'total_load', 'barge_ids', 'type_point']

    
    multiple_combos = tugboat_df[
        ((tugboat_df['tugboat_id'] == 'RiverTB_02') & (tugboat_df['order_id'] == 'ODR_001')) |
        ((tugboat_df['tugboat_id'] == 'RiverTB_02') & (tugboat_df['order_id'] == 'ODR_001'))
    ]
    multiple_combos = tugboat_df
    print("\nData for SeaTB_01-ODR_001 and RiverTB_09-ODR_001:")
    print(multiple_combos[columns_of_interest].head(20))
    print(len(multiple_combos))
    
def test_export():
    data_df = get_data_from_db()
    
    # print(carrier_df)
    # print(barge_df)
    # print(tugboat_df)
    # print(station_df)
    # print(order_df)
    # print(customer_df)
    
    data = initialize_data(data_df)
    
    if TravelHelper._instance is None:
        TravelHelper()
    
    TravelHelper._set_data(TravelHelper._instance,  data)
    # print_all_objects(data)

    
    order_ids = [ order_id for order_id in data['orders'].keys() if data['orders'][order_id].order_type == TransportType.EXPORT]
    order_ids = order_ids[:1]
    solution = Solution(data)
    is_success, tugboat_df, barge_df = solution.generate_schedule(order_ids)
    columns_of_interest = ['ID', 'type', 'name', 'enter_datetime', 'exit_datetime', 'distance',
       'time', 'speed', 'type_point', 'barge_speed', 'tugboat_id', 'order_id',
       'water_type']
    
    #filter tugboat_df
    tugboat_dfx = tugboat_df[(tugboat_df['tugboat_id'] == 'RiverTB_01') | (tugboat_df['tugboat_id'] == 'SeaTB_06')]
    
    print(tugboat_dfx[columns_of_interest])
    order = data['orders'][order_ids[0]]
    station_start = order.start_object.station
    station_end = order.des_object.station
    
    print(order)
    print(station_start)
    print(station_end)
    print(tugboat_df['tugboat_id'].unique())
    print(len(tugboat_df))
    
def test_mixed():
    data_df = get_data_from_db()
    data = initialize_data(data_df)
    
    if TravelHelper._instance is None:
        TravelHelper()
    
    TravelHelper._set_data(TravelHelper._instance,  data)
    # print_all_objects(data)

    order_ids = [ order_id for order_id in data['orders'].keys() ]
    order_ids = order_ids[:]
    solution = Solution(data)
    is_success, tugboat_df, barge_df = solution.generate_schedule(order_ids)
    columns_of_interest = ['ID', 'type', 'name', 'enter_datetime', 'exit_datetime', 'distance',
       'time', 'speed', 'type_point', 'barge_speed', 'tugboat_id', 'order_id',
       'water_type']
    
    #filter tugboat_df
    tugboat_dfx = tugboat_df[(tugboat_df['tugboat_id'] == 'RiverTB_01') | (tugboat_df['tugboat_id'] == 'SeaTB_06')]
    
    print(tugboat_dfx[columns_of_interest])
    order = data['orders'][order_ids[0]]
    station_start = order.start_object.station
    station_end = order.des_object.station
    
    print(order)
    print(station_start)
    print(station_end)
    print(tugboat_df['tugboat_id'].unique())
    print(len(tugboat_df))
     
def test_import():
    data_df = get_data_from_db()
    
    # print(carrier_df)
    # print(barge_df)
    # print(tugboat_df)
    # print(station_df)
    # print(order_df)
    # print(customer_df)
    
    data = initialize_data(data_df)
    
    if TravelHelper._instance is None:
        TravelHelper()
    
    TravelHelper._set_data(TravelHelper._instance,  data)
    # print_all_objects(data)

    
    order_ids = [ order_id for order_id in data['orders'].keys() if data['orders'][order_id].order_type == TransportType.IMPORT]
    order_ids = order_ids[:1]
    solution = Solution(data)
    is_success, tugboat_df, barge_df = solution.generate_schedule(order_ids)
    
    #save csv
    tugboat_df.to_csv('tugboat_df.csv', index=False)
    barge_df.to_csv('barge_df.csv', index=False)

def test_generate_codes():
    
    carrier_df, barge_df, tugboat_df, station_df, order_df  , customer_df = get_data_from_db()
    
    data = initialize_data(carrier_df, barge_df, 
                           tugboat_df, station_df, order_df, customer_df)
    
    if TravelHelper._instance is None:
        TravelHelper()
    
    TravelHelper._set_data(TravelHelper._instance,  data)
    # print_all_objects(data)

    barges = data['barges']
    stations = data['stations']
    orders = data['orders']
    tugboats = data['tugboats']
    
    order_ids = [ order_id for order_id in orders.keys() ]
    order_ids = order_ids[:]
    
    #total demand of order_ids
    total_demand = sum(orders[order_id].demand for order_id in order_ids)
    
    average_capacity_barge = sum(b.capacity for b in barges.values()) / len(barges.values())
    average_tugboat_capacity = sum(t.max_capacity for t in tugboats.values()) / len(tugboats.values())
    print("Average Capacity Barge", average_capacity_barge)
    print("Total Demand", total_demand//(average_capacity_barge), len(barges))
    print("Average Capacity Tugboat", average_tugboat_capacity)
    print("Total Demand", total_demand//(average_tugboat_capacity), len(tugboats))
    
    Number_Code_Tugboat = int(2*total_demand//(average_tugboat_capacity)) #for barge and tugboat
    print("Number Code Tugboat", Number_Code_Tugboat)
    
    
    order_start = orders[order_ids[0]].start_datetime
    order_end = orders[order_ids[0]].due_datetime
    days = 4
    
    
    MAX_DISTANCE  = max(station.km for station in stations.values())
    MAX_SPEED = max(tugboat.max_speed for tugboat in tugboats.values())
    MAX_FUEL_CON = max(tugboat.max_fuel_con for tugboat in tugboats.values())
    
    BASED_VALUE = MAX_DISTANCE * MAX_FUEL_CON / MAX_SPEED
    
    solution = Solution(data)
    #start_station = stations[config_problem.APPOINTMENT_STATION_BASE_REFERENCE_ID]
    start_station = stations['ST_001']
    available_barges = [
            b for b in barges.values() 
            #if (self.get_ready_barge(b)is None or self.get_ready_barge(b) < order_end - timedelta(days=4) ) 
            if (solution.get_ready_barge(b)is None or solution.get_ready_barge(b) < order_start + timedelta(days=days)) 
        ]
    
    available_tugboats = [
            t for t in tugboats.values() 
            #if (self.get_ready_tugboat(t)is None or self.get_ready_tugboat(t) < order_end - timedelta(days=4) ) 
            if (solution.get_ready_time_tugboat(t)is None or solution.get_ready_time_tugboat(t) < order_start + timedelta(days=days)) 
        ]
    
    
    def get_distance_barge(b: Barge):
        delta = stations[solution.get_station_id_barge(b)].km - start_station.km
        distance = abs(delta)
        if stations[solution.get_station_id_barge(b)].water_type == WaterBody.RIVER and start_station.water_type == WaterBody.RIVER:
            pass
        elif start_station.water_type == WaterBody.SEA and stations[solution.get_station_id_barge(b)].water_type == WaterBody.RIVER:
            distance = stations[solution.get_station_id_barge(b)].km + start_station.km
        elif start_station.water_type == WaterBody.RIVER and stations[solution.get_station_id_barge(b)].water_type == WaterBody.SEA:
            distance = abs(stations[solution.get_station_id_barge(b)].km - start_station.km)
        else:
            distance = abs(stations[solution.get_station_id_barge(b)].km - start_station.km)
        
        return distance
    
    def get_distance_tugboat(t: Tugboat):
        delta = stations[solution.get_station_id_tugboat(t)].km - start_station.km
        distance = abs(delta)
        if stations[solution.get_station_id_tugboat(t)].water_type == WaterBody.RIVER and start_station.water_type == WaterBody.RIVER:
            pass
        elif start_station.water_type == WaterBody.SEA and stations[solution.get_station_id_tugboat(t)].water_type == WaterBody.RIVER:
            distance = stations[solution.get_station_id_tugboat(t)].km + start_station.km
        elif start_station.water_type == WaterBody.RIVER and stations[solution.get_station_id_tugboat(t)].water_type == WaterBody.SEA:
            distance = abs(stations[solution.get_station_id_tugboat(t)].km - start_station.km)
        else:
            distance = abs(stations[solution.get_station_id_tugboat(t)].km - start_station.km)
        
        return distance
    
    
    def sorted_barges(b: Barge):
        return get_distance_barge(b)/MAX_DISTANCE
    
    def sorted_tugboats(t: Tugboat):
        distance = get_distance_tugboat(t)
        speed = t.max_speed
        consumption = t.max_fuel_con
        return (distance * consumption / speed )/BASED_VALUE
    
    
    #random array xs Number_Code_Tugboat
    np.random.seed(0)
    xs = np.random.rand(Number_Code_Tugboat)
    #random array xs based on seed numpy array len available_tugboats
    np.random.seed(int(xs[0]*100000000))
    rxs_tugboats = np.random.rand(len(available_tugboats))
    np.random.seed(int(xs[1]*100000000))
    rxs_barges = np.random.rand(len(available_barges))
    
    
    
    
    # For tugboats
    tugboat_values = np.fromiter((sorted_tugboats(t) for t in available_tugboats), dtype=float)
    sorted_tugboat_indices = np.argsort(tugboat_values )
    sorted_tugboats_list = np.array(available_tugboats, dtype=object)[sorted_tugboat_indices].tolist()

    # For barges
    barge_values = np.fromiter((sorted_barges(b) for b in available_barges), dtype=float)
    sorted_barge_indices = np.argsort(barge_values)
    sorted_barges_list = np.array(available_barges, dtype=object)[sorted_barge_indices].tolist()
    
    print("Start Station", start_station.station_id)
    for barge in sorted_barges_list:
        barge_station = stations[solution.get_station_id_barge(barge)]
        # print(barge.barge_id, solution.get_ready_barge(barge), barge_station.station_id, 
        #       barge_station.water_type, barge_station.km)
    
    #
    for tugboat in sorted_tugboats_list:
        tugboat_station = stations[solution.get_station_id_tugboat(tugboat)]
        #print(tugboat)
        print(tugboat.tugboat_id, solution.get_ready_time_tugboat(tugboat), tugboat_station.station_id, 
              tugboat_station.water_type, tugboat_station.km, tugboat.max_fuel_con, tugboat.min_speed)
    
    
    print("Sorted Tugboats", [t.tugboat_id for t in sorted_tugboats_list])
    print("Sorted Value Tugboats", tugboat_values[sorted_tugboat_indices])
    print()
    print("Sorted Barges", [b.barge_id for b in sorted_barges_list][:10])
    print("Sorted Value Barges", barge_values[sorted_barge_indices][:10])
    
    FACTOR = 0.01
    sorted_tugboat_indices = np.argsort(tugboat_values + rxs_tugboats*FACTOR)
    sorted_tugboats_list = np.array(available_tugboats, dtype=object)[sorted_tugboat_indices].tolist()
    sorted_barge_indices = np.argsort(barge_values + rxs_barges*FACTOR)
    sorted_barges_list = np.array(available_barges, dtype=object)[sorted_barge_indices].tolist()
    print("--------------------------------------------------------------------")
    print("After Sorted Tugboats", [t.tugboat_id for t in sorted_tugboats_list])
    print("After Sorted Value Tugboats", tugboat_values[sorted_tugboat_indices])
    print()
    print("After Sorted Barges", [b.barge_id for b in sorted_barges_list][:10])
    print("After Sorted Value Barges", barge_values[sorted_barge_indices][:10])
    
def test_algorithm(order_input_ids = None, name='v3'):
    
    data_df = get_data_from_db()
    order_df = data_df['order']
    print()
    data = initialize_data(data_df)
    
    if TravelHelper._instance is None:
        TravelHelper()
    
    TravelHelper._set_data(TravelHelper._instance,  data)
    # print_all_objects(data)

    barges = data['barges']
    stations = data['stations']
    orders = data['orders']
    tugboats = data['tugboats']
    
    order_ids = [ order_id for order_id in orders.keys() ]
    if order_input_ids is not None:
        order_ids = order_input_ids
    else  :
        order_ids = order_ids[:]
    print("Order\n", order_df)
    #for order_id in order_ids:
    #    print(order_id, orders[order_id])
    #total demand of order_ids
    total_demand = sum(orders[order_id].demand for order_id in order_ids)
    print("Total Demand", total_demand)
    print("Average Demand", order_ids)
    
    average_capacity_barge = sum(b.capacity for b in barges.values()) / len(barges.values())
    average_tugboat_capacity = sum(t.max_capacity for t in tugboats.values()) / len(tugboats.values())
    print("Average Capacity Barge", average_capacity_barge)
    print("Total Demand", total_demand//(average_capacity_barge), len(barges))
    print("Average Capacity Tugboat", average_tugboat_capacity)
    print("Total Demand", total_demand//(average_tugboat_capacity), len(tugboats))
    
    Number_Code_Tugboat = 4*int(2*max(total_demand//(average_tugboat_capacity), 20)) #for barge and tugboat
    print("Number Code Tugboat", Number_Code_Tugboat)

    
    solution = Solution(data)
    
    np.random.seed(1)
    xs = np.random.rand(Number_Code_Tugboat)
    
    #tugboat_df, barge_df = solution.generate_schedule(order_ids, xs=xs)
    #tugboat_df, barge_df = solution.generate_schedule(order_ids)
    #cost_results, tugboat_df_o, barge_df, tugboat_df_grouped = solution.calculate_cost(tugboat_df, barge_df)
    
    
    problem = TugboatProblem(order_ids, data, solution, Number_Code_Tugboat)
    #np.random.seed(0)

    algorithm = AMIS(problem,
        pop_size=5,
        CR=0.3,
        max_iter = 1,
        #dither="vector",
        #jitter=False
    )
    algorithm.iterate()

    
    solution = Solution(data)
    is_success, tugboat_df, barge_df = solution.generate_schedule(order_ids, xs=algorithm.bestX)
    if not is_success:
        print("Failed to generate schedule")
        exit()
    

    cost_results, tugboat_df_o, barge_df, tugboat_df_grouped = solution.calculate_cost(tugboat_df, barge_df)
    tugboat_df_grouped = solution.calculate_full_cost(tugboat_df, barge_df)
    barge_cost_df = solution.calculate_full_barge_cost(tugboat_df)
        
        
    #cost_results, tugboat_df_o, barge_df, tugboat_df_grouped = solution.calculate_full_cost(tugboat_df, barge_df)
    
    tugboat_df.to_excel(f'{config_problem.OUTPUT_FOLDER}/tugboat_schedule_algorithm_{name}.xlsx', index=False)
    
    
    tugboat_dfx = tugboat_df[(tugboat_df['tugboat_id'] == 'SeaTB_05') & (tugboat_df['order_id'] == 'ODR_001')]
    #tugboat_dfx = tugboat_df
    
    print(tugboat_dfx[  COLUMN_OF_INTEREST])
    order = data['orders'][order_ids[0]]
    station_start = order.start_object.station
    station_end = order.des_object.station
    
    print(order)
    print(station_start)
    print(station_end)
    print(tugboat_df['tugboat_id'].unique())
    print(len(tugboat_df))
    print(cost_results)
    
    
    
    print("Total Cost", np.sum(tugboat_df_grouped['Cost']))
    #filter tugboat_df_grouped by not cost is zero
    tugboat_df_grouped = tugboat_df_grouped[tugboat_df_grouped['Cost'] != 0]
    print(tugboat_df_grouped)
    tugboat_df = tugboat_df_grouped[tugboat_df_grouped['TugboatId'].str.contains("Sea")]
    print("Total Load Sea", np.sum(tugboat_df['TotalLoad']))
    tugboat_df = tugboat_df_grouped[tugboat_df_grouped['TugboatId'].str.contains("River")]
    print("Total Load River", np.sum(tugboat_df['TotalLoad']))
    
    tugboat_df_o.to_csv(f'{config_problem.OUTPUT_FOLDER}/tugboat_schedule_{name}.csv', index=False)
    update_database(order_ids, tugboat_df_o, tugboat_df_grouped, barge_cost_df)
    
    tb = tugboat_df_o[(tugboat_df_o['tugboat_id'] == 'RiverTB_11') & (tugboat_df_o['order_id'] == 'ODR_015')]
    #sort by enter_datetime
    tb = tb.sort_values(by='enter_datetime')
    print(tb)
    
    
    
    
def test_single_solution(order_input_ids = None, name='v3'):
    data_df = get_data_from_db()
    order_df = data_df['order']
    print()
    data = initialize_data(data_df)
 
    
    order_ids, cost_df_result, tugboat_df, tugboat_df_o, barge_df, tugboat_df_grouped, barge_cost_df = _init_test(data, order_df, order_input_ids)
    #tugboat_df.to_csv(f'{config_problem.OUTPUT_FOLDER}/tugboat_schedule_v2.csv', index=False)
    # save as excel
    tugboat_df.to_excel(f'{config_problem.OUTPUT_FOLDER}/tugboat_schedule_{name}.xlsx', index=False)
    
    
    print(tugboat_df)
    
    # tugboat_dfx = tugboat_df[
    #         ((tugboat_df['tugboat_id'] == 'SeaTB_02') | (tugboat_df['tugboat_id'] == 'SeaTB_02')) 
    #         &(tugboat_df['order_id'] == 'ODR_001')
    #     ]
    #filter type ="Barge Step Collection"
    #tugboat_dfx = tugboat_df[tugboat_df['type'].str.contains("Barge Step Collection")]
    #tugboat_dfx = tugboat_df
    
    #filter tugboat_df by contain "Sea" Word in barge id
    #tugboat_dfx = tugboat_df[tugboat_df['barge_ids'].str.contains("B_084")]
    
    #print(tugboat_df)
   
    
    
    
    
    #print(np.unique(tugboat_df['type']))
    
    order = data['orders'][order_ids[0]]
    station_start = order.start_object.station
    station_end = order.des_object.station
    
    #print(order)
    #print(station_start)
    #print(station_end)
    #print(tugboat_df['tugboat_id'].unique())
    #print(len(tugboat_df))
    #print(cost_results)
    
 
    tugboat_dfx = tugboat_df[(tugboat_df['tugboat_id'].str.contains("Sea")) & (tugboat_df['order_id'] == 'ODR_008')]
    print(tugboat_dfx[COLUMN_OF_INTEREST].head(20))
    
    
    
    #filter tugboat_df by contain "Sea" Word in tugboat id
    
    
    # #group tugboat_df by order_id and sum total_load
    # tugboat_df_grouped = tugboat_df.groupby('order_id').sum()
    # print(tugboat_df_grouped)
    print("Total Cost", np.sum(tugboat_df_grouped['Cost']))
    #filter tugboat_df_grouped by not cost is zero
    tugboat_df_grouped = tugboat_df_grouped[tugboat_df_grouped['Cost'] != 0]
    print(tugboat_df_grouped)
    tugboat_df = tugboat_df_grouped[tugboat_df_grouped['TugboatId'].str.contains("Sea")]
    print("Total Load Sea", np.sum(tugboat_df['TotalLoad']))
    tugboat_df = tugboat_df_grouped[tugboat_df_grouped['TugboatId'].str.contains("River")]
    print("Total Load River", np.sum(tugboat_df['TotalLoad']))
    
    # for order_id in order_ids:
    #     #print(order_id, data['orders'][order_id])
    #     #filter tugboat_df by order_id
    #     tugboat_dfxt = tugboat_df[(tugboat_df['order_id'] == order_id)
    #                              & (tugboat_df['tugboat_id'].str.contains("RiverTB_02"))
    #                              #& (tugboat_df['type'].str.contains("Barge Collection"))
    #                              ]
    #     order = data['orders'][order_id]
    #     print("Order", order_id, order.start_datetime)
    #     #print(tugboat_dfx)
    #     for index, row in tugboat_dfxt.iterrows():
    #         #check if row['enter_datetime'] is less than order.start_datetime
    #         # row['enter_datetime'] string to datetime TypeError: strptime() argument 1 must be str, not Timestamp
    #         #temp_enter = row['enter_datetime'].strftime('%Y-%m-%d %H:%M:%S')
    #         #order_start_datetime= order.start_datetime.strftime('%Y-%m-%d %H:%M:%S')
    #         # print(row['enter_datetime'], order.start_datetime)
    #         # temp_enter = datetime.strptime(row['enter_datetime'], '%Y-%m-%d %H:%M:%S')
    #         # order_start_datetime = datetime.strptime(order.start_datetime, '%Y-%m-%d %H:%M:%S')
    #         #delta time
    #         delta_time = row['enter_datetime'] - order.start_datetime
    #         if delta_time.total_seconds()/3600 > 24*0:
    #             print("Tugboat", row['tugboat_id'], "is late",row['enter_datetime'], order.start_datetime )
    #     print("Tugboat++++++++++++++++++++++++++++")
    #     for tugboat_id, tugboat in data['tugboats'].items():
    #         #if tugboat._ready_time < order.start_datetime and "Sea" in tugboat.name:
    #         print("Tugboat", tugboat_id, "is late", tugboat._ready_time, order.start_datetime)
    
    
    
    print(cost_df_result)
    
    #save to csv
    update_database(order_ids, tugboat_df_o, tugboat_df_grouped, barge_cost_df)
    
    #barge_df.to_csv('barge_df.csv', index=False)
    # unique tugboat_id
    print(tugboat_df_o['tugboat_id'].unique())
    print(tugboat_df_o[(tugboat_df_o['tugboat_id'] == "RiverTB_11") |
                       (tugboat_df_o['order_id'] == "ODR_015")][COLUMN_OF_INTEREST].head(40))

COLUMN_OF_INTEREST = ['ID',"station_id" , 'type', 'name', 'enter_datetime', 'exit_datetime', 'start_arrival_datetime', 'rest_time', 'distance',
       'time', 'speed', 'type_point', 'barge_speed', 'tugboat_id', 'order_id', 
       'water_type']

def _init_test(data, order_df, order_input_ids):
    
    if TravelHelper._instance is None:
        TravelHelper()
    
    TravelHelper._set_data(TravelHelper._instance,  data)
    # print_all_objects(data)

    barges = data['barges']
    stations = data['stations']
    orders = data['orders']
    tugboats = data['tugboats']
    
    order_ids = [ order_id for order_id in orders.keys() ]
    if order_input_ids is not None:
        order_ids = order_input_ids
    else  :
        order_ids = order_ids[:]
    print("Order\n", order_df)
    #for order_id in order_ids:
    #    print(order_id, orders[order_id])
    #total demand of order_ids
    total_demand = sum(orders[order_id].demand for order_id in order_ids)
    print("Total Demand", total_demand)
    print("Average Demand", order_ids)
    
    average_capacity_barge = sum(b.capacity for b in barges.values()) / len(barges.values())
    average_tugboat_capacity = sum(t.max_capacity for t in tugboats.values()) / len(tugboats.values())
    print("Average Capacity Barge", average_capacity_barge)
    print("Total Demand", total_demand//(average_capacity_barge), len(barges))
    print("Average Capacity Tugboat", average_tugboat_capacity)
    print("Total Demand", total_demand//(average_tugboat_capacity), len(tugboats))
    
    Number_Code_Tugboat = 4*int(2*max(total_demand//(average_tugboat_capacity), 20)) #for barge and tugboat
    print("Number Code Tugboat", Number_Code_Tugboat)
    
    
  
    
    np.random.seed(1)
    xs = np.random.rand(Number_Code_Tugboat)
    
    #tugboat_df, barge_df = solution.generate_schedule(order_ids, xs=xs)
    #tugboat_df, barge_df = solution.generate_schedule(order_ids)
    #cost_results, tugboat_df_o, barge_df, tugboat_df_grouped = solution.calculate_cost(tugboat_df, barge_df)
    
    
    
    
    solution = Solution(data)
    is_success, tugboat_df, barge_df = solution.generate_schedule_v2(order_ids, xs=xs)
    if not is_success:
        print("Failed to generate schedule")
        exit()
    cost_results, tugboat_df_o, barge_df, cost_df = solution.calculate_cost(tugboat_df, barge_df)
    cost_df_result = solution.calculate_full_cost(tugboat_df, barge_df)
    barge_cost_df = solution.calculate_full_barge_cost(tugboat_df)
    return order_ids, cost_results, tugboat_df, tugboat_df_o, barge_df, cost_df_result, barge_cost_df 

def test_step_travel():
    data_df = get_data_from_db()
    order_df = data_df['order']
    data = initialize_data(data_df)
    
    if TravelHelper._instance is None:
        TravelHelper()
    
    TravelHelper._set_data(TravelHelper._instance,  data)
    # print_all_objects(data)

    order = data['orders']['ODR_001']
    station_start = data['stations']["ST_024"]
    station_end = data['stations']["ST_025"]
    base_speed = 8.22
    distance = 21
    travel_info = TravelInfo((station_start.lat, station_start.lng), 
                             (station_end.lat, station_end.lng), 
                             base_speed, 
                             station_start.km, station_end.km)
    travel_step = TravelStep(data, (station_start.lat, station_start.lng), 
                             (station_end.lat, station_end.lng), 
                             station_start.station_id, 
                             station_end.station_id, distance, base_speed)
    # convert string 2025-01-01 02:00 to datetime
    travel_info.start_time = datetime.strptime("2025-02-10 08:04", "%Y-%m-%d %H:%M")
    travel_step.update_travel_step_move(travel_info.start_time)
    print(travel_step)
    print("--------------------------------")
    travel_info.start_time = datetime.strptime("2025-02-10 12:05", "%Y-%m-%d %H:%M")
    travel_step.update_travel_step_move(travel_info.start_time)
    print(travel_step)

def test_result_travel_sea_have_break(order_input_ids):
    data_df = get_data_from_db()
    order_df = data_df['order']
    print()
    data = initialize_data(data_df)
    
    order_ids, cost_results, tugboat_df, barge_df, tugboat_df_grouped, barge_cost_df = _init_test(data, order_df, order_input_ids)
    #tugboat_dfx = tugboat_df[(tugboat_df['tugboat_id'] == 'SeaTB_05') & (tugboat_df['order_id'] == 'ODR_001')]
    tugboat_dfx = tugboat_df
    
    
    print(tugboat_dfx[COLUMN_OF_INTEREST])
    
    tugboat_dfx = tugboat_df[(tugboat_df['name'] == 'ST_001 to ST_005') 
                             #& tugboat_df['name'] == 'ST001 to ST005']
    ]
    #tugboat_dfx = tugboat_df
    
    print(tugboat_dfx[columns_of_interest])
    order = data['orders'][order_ids[0]]
    station_start = order.start_object.station
    station_end = order.des_object.station

def test_result_barge_start_collection_is_dash(order_input_ids):
    data_df = get_data_from_db()
    order_df = data_df['order']
    print()
    data = initialize_data(data_df)
    
    order_ids, cost_results, tugboat_df, barge_df, tugboat_df_grouped, barge_cost_df = _init_test(data, order_df, order_input_ids)
    #tugboat_dfx = tugboat_df[(tugboat_df['tugboat_id'] == 'SeaTB_05') & (tugboat_df['order_id'] == 'ODR_001')]
    tugboat_dfx = tugboat_df
    
    columns_of_interest = ['ID', 'type', 'name', 'enter_datetime', 'exit_datetime', 'start_arrival_datetime', 'rest_time', 'distance',
       'time', 'speed', 'type_point', 'barge_speed', 'tugboat_id', 'order_id', 
       'water_type']
    print(tugboat_dfx[columns_of_interest])
    
    #check string is in name
    tugboat_dfx = tugboat_df[tugboat_df['name'].str.contains('- to ST_001') & (tugboat_df['type'] == 'Barge Step Collection')]
    #tugboat_dfx = tugboat_df
    
    print(tugboat_dfx[columns_of_interest])
    order = data['orders'][order_ids[0]]
    station_start = order.start_object.station
    station_end = order.des_object.station
    
def use_barge_ready_after_order_start(order_input_ids):
    data_df = get_data_from_db()
    order_df = data_df['order']
    print()
    data = initialize_data(data_df)
    
    order_ids, cost_results, tugboat_df, barge_df, tugboat_df_grouped, barge_cost_df = _init_test(data, order_df, order_input_ids)
    
    for order_id in order_ids:
        odrder_results = tugboat_df[tugboat_df['order_id'] == order_id]
        order = data['orders'][order_id]
        #print(order_id)
        #print(odrder_results)
        list_barge_ids = []
        for index, row in odrder_results.iterrows():
            list_barge_ids.extend(row['barge_ids'].split(','))
        print(order_id,   order.start_datetime, order.due_datetime, "Barge_ids:", set(list_barge_ids))
        set_barge_ids = set(list_barge_ids)
        for barge_id in set_barge_ids:
            if order.due_datetime < data['barges'][barge_id]._ready_time:
                print(order.due_datetime, data['barges'][barge_id]._ready_time)
                break
        
def check_delay_out_after_finish_crane_load(order_input_ids):
    data_df = get_data_from_db()
    order_df = data_df['order']
    print()
    data = initialize_data(data_df)
    
    order_ids, cost_results, tugboat_df, barge_df, tugboat_df_grouped, barge_cost_df = _init_test(data, order_df, order_input_ids)
    #tugboat_dfx = tugboat_df[(tugboat_df['tugboat_id'] == 'SeaTB_05') & (tugboat_df['order_id'] == 'ODR_001')]
    tugboat_dfx = tugboat_df
    
    columns_of_interest = ['ID', 'type', 'name', 'enter_datetime', 'exit_datetime', 'start_arrival_datetime', 'rest_time', 'distance',
       'time', 'speed', 'type_point', 'barge_speed', 'tugboat_id', 'order_id', 
       'water_type']
    print(tugboat_dfx[columns_of_interest])
    
    tugboat_dfx = tugboat_df[(tugboat_df['tugboat_id'] == 'SeaTB_04') 
                             #& tugboat_df['name'] == 'ST001 to ST005']
    ]
    #tugboat_dfx = tugboat_df
    
    print(tugboat_dfx[columns_of_interest].head(20))
    order = data['orders'][order_ids[0]]
    station_start = order.start_object.station
    station_end = order.des_object.station
    
def check_all_start_arrival_time(order_input_ids):
    data_df = get_data_from_db()
    order_df = data_df['order']
    print()
    data = initialize_data(data_df)
    
    order_ids, cost_results, tugboat_df, barge_df, tugboat_df_grouped, barge_cost_df = _init_test(data, order_df, order_input_ids)
        
    columns_of_interest = ['ID', 'type', 'name', 'enter_datetime', 'exit_datetime', 'start_arrival_datetime', 'rest_time', 'distance',
       'time', 'speed', 'type_point', 'barge_speed', 'tugboat_id', 'order_id', 
       'water_type']
    print(tugboat_df[columns_of_interest])
    for index, row in tugboat_df.iterrows():
        if row['start_arrival_datetime'] > row['exit_datetime']:
            print(row)
            print("Error Time start_arrival_datetime > exit_datetime", index)
            break
        if row['start_arrival_datetime'] < row['enter_datetime']:
            print(row)
            print("Error Time start_arrival_datetime < enter_datetime", index)
            break

def test_after_prosess():
    import pandas as pd
    from pathlib import Path
    # ---- Example usage ----

    # 1) Read your file
    excel_path = Path("data/output/tugboat_schedule_v4.xlsx")  # <- your uploaded file
    # If your data is on a specific sheet, set sheet_name="Sheet1" (or the correct sheet)
    df = pd.read_excel(excel_path)  # , sheet_name="Sheet1"

    # 2) Insert stop rows
    df_with_stops = insert_stop_rows(
        df,
        travel_col="name",      # change if your column is named differently
        type_col="type",
        rest_col="rest_time",
        speed_col="speed",        # set to None if you don't have a speed column
        valid_travel_values=("Sea-River", "River-River", "River-Sea"),
        stop_type_value="stop",
        keep_rest_time_in_stop=True,  # True: keep same rest_time in the new stop row; False: set to 0
        stop_speed_value=0,           # set what speed the stop row should have (e.g., 0)
    )
    print(df_with_stops[((df_with_stops['type'].str.contains("stop")) | (df_with_stops['type'] == 'River-River')) & 
                        (df_with_stops['tugboat_id'] == 'RiverTB_02')].head(50))

def insert_stop_rows(
    df: pd.DataFrame,
    travel_col: str = "travel",
    type_col: str = "type",
    rest_col: str = "rest_time",
    speed_col: str | None = "speed",
    valid_travel_values: tuple[str, ...] = ("Sea-River", "River-River", "River-Sea"),
    stop_type_value: str = "stop",
    keep_rest_time_in_stop: bool = True,
    stop_speed_value: int | float | None = 0,
) -> pd.DataFrame:
    """
    Insert a 'stop' row after any row satisfying:
      rest_time > 0 and travel in valid_travel_values.
    The inserted row copies all columns by default, then overrides:
      - type -> stop_type_value
      - (optional) speed -> stop_speed_value
      - rest_time -> keep or clear (based on keep_rest_time_in_stop)
    """

    # Work on a copy
    df = df.copy()

    # Ensure required columns exist
    required = {travel_col, type_col, rest_col}
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # Build condition mask
    mask = (
        df[rest_col].fillna(0).astype(float).gt(0)
        & df[type_col].isin(valid_travel_values)
    )
    print(df[df['tugboat_id'] == 'RiverTB_02'][mask].head(50))
    # Rows that need a stop inserted
    original_rows = df[mask]
    to_insert = original_rows.copy()

    if to_insert.empty:
        # Nothing to insert — return original as-is
        return df.reset_index(drop=True)

    # Prepare the stop rows by copying matched rows, then overriding fields
    stop_rows = to_insert.copy()

    # Set 'type' to stop
  
    first_token = (
    df[travel_col]
      .fillna("")                # avoid NaN -> "nan"
      .astype(str)
      .str.strip()
      .str.split()
      .str.get(0)                # first word or NaN if empty
      .fillna("")                # back to empty string if missing
    )
    df.loc[mask, travel_col] = stop_type_value + " at " + first_token[mask]
    df.loc[mask, 'distance'] = 0
    df.loc[mask, 'time'] = 0
    df.loc[mask, 'speed'] = 0
    df.loc[mask, 'exit_datetime'] = df[mask]['start_arrival_datetime']

    # Optionally set speed
    if speed_col is not None and speed_col in df.columns:
        stop_rows[speed_col] = stop_speed_value

    stop_rows[rest_col] = 0
    stop_rows['enter_datetime'] = stop_rows['start_arrival_datetime']

    # If you want the stop row to keep only certain columns, modify here.
    # For now, we keep all columns and only override fields above.

    # We’ll interleave: original rows keep integer order;
    # new stop rows get order + 0.5 to come right after the originals.
    df = df.reset_index(drop=False).rename(columns={"index": "_orig_pos"})
    to_insert_pos = df.loc[mask, ["_orig_pos"]]  # original positions for matched rows

    stop_rows = stop_rows.merge(
        to_insert_pos,
        left_index=True,
        right_index=True,
        how="left"
    )

    # Create order keys
    df["_order_key"] = df["_orig_pos"].astype(float)
    stop_rows["_order_key"] = stop_rows["_orig_pos"].astype(float) + 0.5

    # Align columns (in case stop_rows is missing some cols)
    stop_rows = stop_rows[df.columns.intersection(stop_rows.columns)]
    # And also add any missing columns to stop_rows with NaN so concat aligns
    for col in df.columns:
        if col not in stop_rows.columns:
            stop_rows[col] = pd.NA
    # Reorder columns like df
    stop_rows = stop_rows[df.columns]

    # Combine and sort
    out = pd.concat([df, stop_rows], ignore_index=True)
    out = out.sort_values("_order_key", kind="mergesort").drop(columns=["_orig_pos", "_order_key"])
    out = out.reset_index(drop=True)
    return out

def test_generate_all_cost():
    import pandas as pd
    from pathlib import Path
    # 1) Read your file
    excel_path = Path("data/output/tugboat_schedule_algorithm.xlsx")  # <- your uploaded file
    # If your data is on a specific sheet, set sheet_name="Sheet1" (or the correct sheet)
    df = pd.read_excel(excel_path)  # , sheet_name="Sheet1"
    
    data_df = get_data_from_db()
    order_df = data_df['order']
    print()
    data = initialize_data(data_df)
    
    if TravelHelper._instance is None:
        TravelHelper()
    
    TravelHelper._set_data(TravelHelper._instance,  data)
    solution = Solution(data)
    cost_df = solution.calculate_full_cost(df)
    cost_results, tugboat_df_o, barge_df, tugboat_df_grouped=  solution.calculate_cost(df, None)
    print("Original Total Load: ", tugboat_df_grouped['total_load'].sum())
    print("Original Total Distance: ", tugboat_df_grouped['distance'].sum())
    print("Original Total Time: ", tugboat_df_grouped['time'].sum())
    print("Original Total Cost: ", tugboat_df_grouped['cost'].sum())
    
    print("Custom Total Load: ", cost_df['TotalLoad'].sum())
    print("Total Cost", np.sum(cost_df['Cost']))
    #filter tugboat_df_grouped by not cost is zero
    cost_df = cost_df[cost_df['Cost'] != 0]
    print(cost_df)
    tugboat_df = cost_df[cost_df['TugboatId'].str.contains("Sea")]
    print("Total Load Sea", np.sum(tugboat_df['TotalLoad']))
    tugboat_df = cost_df[cost_df['TugboatId'].str.contains("River")]
    print("Total Load River", np.sum(tugboat_df['TotalLoad']))
    
def test_generate_all_barge_cost():
    import pandas as pd
    from pathlib import Path
    # 1) Read your file
    excel_path = Path("data/output/tugboat_schedule_algorithm_v2.xlsx")  # <- your uploaded file
    # If your data is on a specific sheet, set sheet_name="Sheet1" (or the correct sheet)
    df = pd.read_excel(excel_path)  # , sheet_name="Sheet1"
    
    data_df = get_data_from_db()
    order_df = data_df['order']
    print()
    data = initialize_data(data_df)
    
    if TravelHelper._instance is None:
        TravelHelper()
    
    TravelHelper._set_data(TravelHelper._instance,  data)
    solution = Solution(data)
    output_df = solution.calculate_full_barge_cost(df)
    print(output_df.head(40))
    
def generate_test_result():
    
    order_list = [
        "ODR_001", "ODR_002", "ODR_003", "ODR_004", 
        "ODR_005", "ODR_006", "ODR_007", "ODR_008",
        "ODR_009", "ODR_010", "ODR_011", "ODR_012", 
        "ODR_013", "ODR_014", "ODR_015", 
        'ODR_016', 
        'ODR_020', 'ODR_021', 'ODR_022', 
                        ]
    
    for order_name in order_list:
        test_algorithm([order_name], name=order_name)
    
    
    test_algorithm(["ODR_020", 'ODR_021', 'ODR_022',
                        ], name='ORDER_20_21_22')


if __name__ == "__main__":
    
    #result_df = main(testing=False, testing_result=TestingResult.TUGBOAT)
    #test_read_data()
    #test_generate_codes()
    #test_import()
    #test_algorithm([ "ODR_009"])
    
    #test_step_travel()
    
    # test_single_solution(["ODR_001", "ODR_002", "ODR_003", "ODR_004", 
    #                 "ODR_005", "ODR_006", "ODR_007", "ODR_008",
    #                 "ODR_009", "ODR_010", "ODR_011", "ODR_012", 
    #                 "ODR_013", "ODR_014", 
    #                 ])
    #test_single_solution(["ODR_001"])
    
    # test_single_solution(["ODR_001", "ODR_002", "ODR_003", "ODR_004", 
    #                 "ODR_005", "ODR_006", "ODR_007",
    #                 #"ODR_008",
    #                 #"ODR_009", "ODR_010", "ODR_011", "ODR_012", 
    #                 #"ODR_013", "ODR_014", 
    #                 ])
    
    #test_single_solution
    
    #test_single_solution([ "ODR_015"], name='_order_15_v2')
    #test_algorithm([ "ODR_001", "ODR_005", 'ODR_015'], name='_3order')
    #test_algorithm([ "ODR_001", "ODR_005", 'ODR_015', 'Orid16'], name='_3order')
    #test_algorithm
    
    #generate_test_result()
    #test_single_solution(["ODR_022"], name='ORDER_22')
    
    #test_algorithm(["ODR_001", "ODR_002", "ODR_003","ODR_022"], name='ORDER_1_2_3_22')
    
    
    test_single_solution(["ODR_001", "ODR_002", "ODR_003", "ODR_004", 
                         "ODR_005", "ODR_006", "ODR_007", "ODR_008",
                         "ODR_009", "ODR_010", "ODR_011", "ODR_012", 
                         "ODR_013",
                         "ODR_014", 'ODR_015', 'ODR_016',
                          'ODR_020', 'ODR_021', 'ODR_022'], name='ORDER_1_22')
    
    #test_algorithm(["ODR_022"], name='ORDER_22')
    
    # test_algorithm(["ODR_020", 'ODR_021', 'ODR_022'
    #                     ], name='ORDER_20_21_22')
    
    
    
    
    # test_algorithm([
    #     "ODR_001", "ODR_002", "ODR_003", "ODR_004", 
    #                     "ODR_005", "ODR_006", "ODR_007", "ODR_008",
    #                     "ODR_009", "ODR_010", "ODR_011", "ODR_012", 
    #                     "ODR_013",
    #                     "ODR_014", 'ODR_015', 'ODR_016'
    #                     ], name='v4')
    #test_after_prosess()
    #test_generate_all_barge_cost()
