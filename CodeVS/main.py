import sys
import os

from click.decorators import R


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

    carrier_df, barge_df, tugboat_df, station_df, order_df = get_data_from_db()
    #order_df = order_df[order_df['ID']=='o1']
    # print(carrier_df)
    # eed
    
    data = initialize_data(carrier_df, barge_df, tugboat_df, station_df, order_df)
    
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
    tugboat_df, barge_df = solution.generate_schedule(order_ids)
    
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

    
    order_ids = [ order_id for order_id in data['orders'].keys() if data['orders'][order_id].order_type == TransportType.EXPORT]
    order_ids = order_ids[:1]
    solution = Solution(data)
    tugboat_df, barge_df = solution.generate_schedule(order_ids)
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
    carrier_df, barge_df, tugboat_df, station_df, order_df  , customer_df = get_data_from_db()
    data = initialize_data(carrier_df, barge_df, 
                           tugboat_df, station_df, order_df, customer_df)
    
    if TravelHelper._instance is None:
        TravelHelper()
    
    TravelHelper._set_data(TravelHelper._instance,  data)
    # print_all_objects(data)

    order_ids = [ order_id for order_id in data['orders'].keys() ]
    order_ids = order_ids[:]
    solution = Solution(data)
    tugboat_df, barge_df = solution.generate_schedule(order_ids)
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
    order_ids = order_ids[:1]
    solution = Solution(data)
    tugboat_df, barge_df = solution.generate_schedule(order_ids)
    
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
    
def test_algorithm(order_input_ids = None):
    
    carrier_df, barge_df, tugboat_df, station_df, order_df  , customer_df = get_data_from_db()
    print()
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
    if order_input_ids is not None:
        order_ids = order_input_ids
    else  :
        order_ids = order_ids[:]
    print("Order\n", order_df)
    for order_id in order_ids:
        print(order_id, orders[order_id])
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
        max_iter = 5,
        #dither="vector",
        #jitter=False
    )
    algorithm.iterate()
    columns_of_interest = ['ID', 'type', 'name', 'enter_datetime', 'exit_datetime', 'distance',
       'time', 'speed', 'type_point', 'barge_speed', 'tugboat_id', 'order_id',
       'water_type']
    
    solution = Solution(data)
    tugboat_df, barge_df = solution.generate_schedule(order_ids, xs=algorithm.bestX)
    cost_results, tugboat_df_o, barge_df, tugboat_df_grouped = solution.calculate_cost(tugboat_df, barge_df)
    
    tugboat_dfx = tugboat_df[(tugboat_df['tugboat_id'] == 'SeaTB_05') & (tugboat_df['order_id'] == 'ODR_001')]
    #tugboat_dfx = tugboat_df
    
    print(tugboat_dfx[columns_of_interest])
    order = data['orders'][order_ids[0]]
    station_start = order.start_object.station
    station_end = order.des_object.station
    
    print(order)
    print(station_start)
    print(station_end)
    print(tugboat_df['tugboat_id'].unique())
    print(len(tugboat_df))
    print(cost_results)
    
    
    print(tugboat_df_grouped)
    print("Total Cost", np.sum(tugboat_df_grouped['cost']))
    

if __name__ == "__main__":
    #result_df = main(testing=False, testing_result=TestingResult.TUGBOAT)
    #test_read_data()
    #test_generate_codes()
    #test_import()
    test_algorithm(["ODR_001", "ODR_002", "ODR_003", "ODR_004", 
                    "ODR_005", "ODR_006", "ODR_007", "ODR_008",
                    "ODR_009", "ODR_010", "ODR_011", "ODR_012", 
                    "ODR_013", "ODR_014", 
                    ])

