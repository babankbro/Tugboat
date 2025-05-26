import sys
import os


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import timedelta, datetime
import pandas as pd
from read_data import *
from initialize_data import initialize_data, print_all_objects
from CodeVS.operations.assigned_barge import *
from CodeVS.operations.scheduling import *
from CodeVS.operations.transport_order import *
from CodeVS.operations.travel_helper import *
from CodeVS.compoents.solution import Solution
import warnings
warnings.filterwarnings(action='ignore')

def test_tugboat(data):
    tugboats = data['tugboats']
    
    current_used_barge_list = assign_barges_to_orders(data['orders'], 
                                data['barges'], assigned_barge_df)
    
    # Count and filter tugboats
    total_tugboats = len(tugboats)
    print(f"\nTotal Tugboats: {total_tugboats}")
    
    sea_tugboats = {tugboat_id: tugboat for tugboat_id, tugboat in tugboats.items() if tugboat.tug_type == 'SEA'}
    river_tugboats = {tugboat_id: tugboat for tugboat_id, tugboat in tugboats.items() if tugboat.tug_type == 'RIVER'}
    
    print(f"Sea Tugboats: {len(sea_tugboats)}")
    print(f"River Tugboats: {len(river_tugboats)}")

    # Print sea tugboats
    print("\nSea Tugboats:")
    for tugboat_id, tugboat in sea_tugboats.items():
        print(tugboat)

    first_level_info = {
        'type_transport': 'import',
        "sea_tugboat" : sea_tugboats['tbs1'],
        'river_tugboat' : river_tugboats['tbr1'],
        "appoint_location" : 's2'
    }

    sea_tugboat1 = first_level_info["sea_tugboat"]
    print("Speed Before load", sea_tugboat1.calculate_current_speed())
    assign_barges_to_tugboat( sea_tugboat1, current_used_barge_list)
    total_barge_weight = sea_tugboat1.get_total_weight_barge()
    print("Affter load", sea_tugboat1.calculate_speed(0, 4, total_barge_weight))

    print("1, tugboat to collect barge ----------------------------------")
    result_step1 =  sea_tugboat1.calculate_collection_barge_time()
    print(result_step1)
    print("--------------------------------------------------------------")
    print()
    print("2. to carrier ------------------------------------------------")
    last_location = result_step1['last_location']
    result_step2 = sea_tugboat1.calculate_collection_product_time_with_crane_rate(last_location)
    print(result_step2)
    print("--------------------------------------------------------------")
    print()

    load_speed = sea_tugboat1.calculate_current_speed()
    print("Speed After load", load_speed)
    print("3. to carrier ------------------------------------------------")

def test_assign_barge_to_order(data):
    orders = data['orders']
    barges = data['barges']
    tugboats = data['tugboats']
    
    assigned_barge_infos = assign_barges_to_single_order(orders['o1'], barges)
    print(f"\nAssigning barges to Order {orders['o1'].order_id}... {len(assigned_barge_infos)} barges")
    print("\nAssignment results:")
    for barge_info in assigned_barge_infos:
        barge = barge_info['barge']
        distance = barge_info['distance']
        print(f"Barge {barge.barge_id} assigned to Order {barge.current_order.order_id}")
        print(f"  - Load: {barge.load}")
        print(f"  - Distance: {distance} km: {barge.crane_rate}")
    
    sea_tugboats = {tugboat_id: tugboat for tugboat_id, tugboat in tugboats.items() if tugboat.tug_type == 'SEA'}
    
    assigned_barges = [barge_info['barge'] for barge_info in assigned_barge_infos]
    assigned_tugboats = assign_barges_to_tugboats(orders['o1'],sea_tugboats, assigned_barges)

    
    print("\nTesting all orders assignment...")
    for tugboat in assigned_tugboats:
        print(f"\nAssigning barges to Tugboat {tugboat.tugboat_id}... {len(tugboat.assigned_barges)} barges")
        print(f"Total Weight: {tugboat.get_total_load()} tugboat capacity: {tugboat.max_capacity}")
        print("\nAssignment results:")
        for barge in tugboat.assigned_barges:
            print(f"Barge {barge.barge_id} assigned to Tugboat {tugboat.tugboat_id}")
            print(f"  - Load: {barge.load}")
            print(f"  - Distance: {barge.used_end - barge.used_start} km: {barge.crane_rate}")

   
    # result = schedule_order_single_tugboat(orders['o1'], assigned_tugboats[0])
    # crane_schedule = result['crane_schedule']
    # barge_schedule = result['barge_schedule']
    # tugboat_schedule = result['tugboat_schedule']
    # print("\nCrane Schedule:")
    # for crane in crane_schedule:
    #     print(crane)
    # print("\nBarge Schedule:")
    # for barge in barge_schedule:
    #     print(barge)
    # print("\nTugboat Schedule:")
    # for tugboat in tugboat_schedule:
    #     print(tugboat)
    
    
    for tugboat in assigned_tugboats:
        print(f"\nAssigning barges to Tugboat EE {tugboat.tugboat_id}... {len(tugboat.assigned_barges)} barges")
    
    results = schedule_carrier_order_tugboats(orders['o1'], assigned_tugboats, [0, 0, 20,  30])
    for result in results:
        print("\nSchedule for Tugboat", result['tugboat_schedule']['tugboat_id'])
        crane_schedule = result['crane_schedule']
        barge_schedule = result['barge_schedule']    
        tugboat_schedule = result['tugboat_schedule']
        print("\nCrane Schedule:")
        for crane in crane_schedule:
            print(crane)    
        print("\nBarge Schedule:")          
        for barge in barge_schedule:
            print(barge)
        print("\nTugboat Schedule:")
        
        print(tugboat_schedule)

def test_transport_order(data, testing=False):
    orders = data['orders']
    barges = data['barges']
    tugboats = data['tugboats']
    order = orders['o1']
    
    
    solution = Solution(data)
    
    tugboat_df, barge_df = solution.generate_schedule()
    
    
    
    filtered_df = tugboat_df[
                            ((tugboat_df['tugboat_id'] == 'tbs1') | (tugboat_df['tugboat_id'] == 'tbr1')) 
                           # &  ((tugboat_df['order_id'] == 'o1') | (tugboat_df['order_id'] == 'o1'))
                            &  ((tugboat_df['order_id'] == 'o1') )
                           # & (tugboat_df['order_trip'] == 1)
                            #& (tugboat_df['distance'] > 60)
                            #(tugboat_df['distance'] > 60)
                            ]
    temp_df = filtered_df[['ID', 'type', 'name', 'enter_datetime', 'exit_datetime', 
                           'tugboat_id','distance', 'time', 'speed','order_trip',
                      # 'distance', 'time', 'speed', 'order_trip', 'total_load', 'barge_ids'
                      'total_load', 'barge_ids',
       #'order_distance', 'order_time', 'barge_speed', 'order_arrival_time',
       #'tugboat_id', 'order_id', 'water_type'
       ]]
    if not testing:
        print(temp_df)

    
#     filtered_df = tugboat_df[
#                             ((tugboat_df['tugboat_id'] == 'tbr1') | (tugboat_df['tugboat_id'] == 'tbr1')) 
#                             #((tugboat_df['order_id'] == 'o1') | (tugboat_df['order_id'] == 'o2'))
#                             #& (tugboat_df['order_trip'] == 1) 
#                             #& ((tugboat_df['type'] == 'Loader-Customer') | (tugboat_df['type'] == 'Crane-Carrier') | 
#                             #   (tugboat_df['type'] == 'Customer Station')| (tugboat_df['type'] == 'Start Order Carrier'))
#                             #& (tugboat_df['distance'] > 60)
#                             #(tugboat_df['distance'] > 60)
#                             #(tugboat_df['name'].str.contains('ld1', case=False, na=False))
#     ]
    
    
    
#     temp_df = filtered_df[['ID', 'type', 'name', 'enter_datetime', 'exit_datetime',
#                             'tugboat_id','distance', 'speed','order_trip'
#                       # 'distance', 'time', 'speed', 'order_trip', 'total_load', 'barge_ids'
#        #'order_distance', 'order_time', 'barge_speed', 'order_arrival_time',
#        #'tugboat_id', 'order_id', 'water_type'
#        ]]
#     # print(temp_df)
    
    

#     filtered_df = tugboat_df[
#                             (
#                             #& (tugboat_df['order_trip'] == 1) 
#                             (tugboat_df['type'] == 'Customer Station'))
#                             #(tugboat_df['type'] == 'Appointment'))
#                             #& (tugboat_df['distance'] > 60)
#                             #(tugboat_df['distance'] > 60)
#     ]
#     temp_df = filtered_df[['ID', 'type', 'name', 'enter_datetime',  'total_load', 'order_id',
#                            'exit_datetime', 'tugboat_id','distance', 'time', 'speed','order_trip'
#                       # 'distance', 'time', 'speed', 'order_trip', 'total_load', 'barge_ids'
#        #'order_distance', 'order_time', 'barge_speed', 'order_arrival_time',
#        #'tugboat_id', 'order_id', 'water_type'
#        ]]
#     #print(temp_df)
#     #demand_load = sum(order_df['DEMAND'])
#     #print("Total Load",  sum(temp_df['total_load']), demand_load)
    
#     grouped_df = temp_df.groupby('order_id')['total_load'].sum().reset_index()
# # Now you can print the grouped data
#     #print(grouped_df)
#     grouped_df = order_df.groupby('ID')['DEMAND'].sum().reset_index()
# # Now you can print the grouped data
#     #print(grouped_df)

#     #print("customer_river_time_lates", customer_river_time_lates, list_lates)


#     # for order_id, order_barge_info in lookup_order_barges.items():
#     #     print(order_barge_info)
        
        
#     # #print('-------------------------- Tugboat')
#     # for tugboat_id, results in lookup_river_tugboat_results.items( ):
#     #     print(tugboat_id, results['data_points'][1]['exit_datetime'])

    if not testing:
        solution.save_schedule_to_csv(tugboat_df, barge_df,
                                    tugboat_path='CodeVS/data/output/tugboat_schedule.xlsx',
                                    barge_path='CodeVS/data/output/barge_schedule.xlsx')
        print("Schedule Created")
    return tugboat_df
    
def main(testing=False):
    # Initialize data structures
    
    data = initialize_data(carrier_df, station_df, order_df, tugboat_df, barge_df)
    TravelHelper()
    TravelHelper._set_data(TravelHelper._instance,  data)
    
    # Print all objects (optional)
    #print_all_objects(data)
    
    # Run tests
    #test_assign_barge_to_order(data)
    result_df = test_transport_order(data, testing)
    # print(Travel_Helper.get_next_station(TransportType.IMPORT, 11))
    # print(Travel_Helper.get_next_station(TransportType.IMPORT, 15))
    # print(Travel_Helper.get_next_station(TransportType.EXPORT, 15))
    return result_df

if __name__ == "__main__":
    result_df = main()
