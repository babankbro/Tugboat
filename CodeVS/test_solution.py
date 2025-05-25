import sys
import os



sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from datetime import timedelta, datetime
import pandas as pd
from CodeVS.main import main
from CodeVS.read_data import *
from CodeVS.initialize_data import initialize_data, print_all_objects
from CodeVS.operations.assigned_barge import *
from CodeVS.operations.scheduling import *
from CodeVS.operations.transport_order import *
from CodeVS.operations.travel_helper import *
from CodeVS.compoents.solution import Solution
import unittest
import numpy as np


# @pytest.fixture 
# def test_data():
#     data = initialize_data(carrier_df, station_df, order_df, tugboat_df, barge_df)
#     TravelHelper()
#     TravelHelper._set_data(TravelHelper._instance,  data)
#     return {'data': data,
#             'TravelHelper': TravelHelper._instance}

                   
# def test_distance_sea_sea(test_data):
#     data = test_data['data']
#     start_station = data['stations']['c1']
#     end_station = data['stations']['s0']
#     start_location = (start_station.lat, start_station.lng)
#     end_location = (end_station.lat, end_station.lng)
#     start_station = (13.18310799,	100.8126384)
#     end_station = (13.4717077924905, 100.595846778158)
#     distance = TravelHelper._instance.get_distance_location(start_location, end_location)
#     assert int(distance) == 39
                                                                                
# def test_solution_schedule(test_data):
#     solution = Solution(test_data['data'])
#     tugboat_df, barge_df =  solution.generate_schedule()
    
#     filtered_df = tugboat_df[
#                             ((tugboat_df['tugboat_id'] == 'tbs1') & (tugboat_df['type'] == 'Appointment')) 
#                             &  ((tugboat_df['order_id'] == 'o1') | (tugboat_df['order_id'] == 'o1'))
#                             & (tugboat_df['order_trip'] == 1)
#                             #& (tugboat_df['distance'] > 60)
#                             #(tugboat_df['distance'] > 60)
#                             ]
#     print(filtered_df)
#     filtered_df2 = tugboat_df[
#                             ((tugboat_df['tugboat_id'] == 'tbs1') & (tugboat_df['type'] == 'Barge Collection')) 
#                             &  ((tugboat_df['order_id'] == 'o1') | (tugboat_df['order_id'] == 'o1'))
#                             & (tugboat_df['order_trip'] == 2)
#                             #& (tugboat_df['distance'] > 60)
#                             #(tugboat_df['distance'] > 60)
#                             ]
    
    
#     assert int(filtered_df.iloc[0]['distance']) == int(filtered_df2.iloc[0]['distance'])
    
# def test_travel_process(test_data):
#     data = test_data['data']
#     tugboats  = data['tugboats']
#     tugboat = tugboats['tbs1']
#     station_barge = data['stations']['c1']
#     end_station = data['stations']['s2']
#     travel_infos = {
#                 'start_location': (tugboat._lat, tugboat._lng),
#                 'end_location': (end_station.lat, end_station.lng),
#                 'speed': 10,
#                 'start_km': 0,
#                 'end_km': 20
#             }
#     distance, travel_time, travel_steps = TravelHelper._instance.process_travel_steps(WaterBody.SEA, 
#                                                                                       WaterBody.RIVER, travel_infos)
#     print("Distance #######################################", distance)
#     assert int(distance) == 59
      
        
class TestSchedulingSolution(unittest.TestCase):
    # def test_file_type(self):
    #     result_df = main()
    #     self.assertIsInstance(result_df, pd.DataFrame)
    def test_crane_load(self):
        # get unique crane name from name column in the self.result_df
        result_df = main()
        name = list(result_df['name'].unique())
        # print(name)
        unique_crane_names = set([cr.split(" - ")[0] for cr in name if "cr" in cr])
        
        for crane_name in unique_crane_names:
            # get the crane load from the result_df
            crane_activity = result_df[result_df['name'].str.contains(crane_name)]
            crane_activity['enter_datetime'] = pd.to_datetime(crane_activity['enter_datetime'])
            crane_activity = crane_activity.sort_values(by='enter_datetime')
            
            crane_activity['exit_datetime'] = pd.to_datetime(crane_activity['exit_datetime'])
            crane_activity = crane_activity.sort_values(by='exit_datetime')
            # print(crane_activity)
            # get enter_datetime and exit_datetime
            enter_datetime = crane_activity['enter_datetime'].values
            exit_datetime = crane_activity['exit_datetime'].values
            
         
            order_ids = crane_activity['order_id'].values
            tugboat_ids = crane_activity['tugboat_id'].values
            print(len(enter_datetime))
            
            # print(enter_datetime)
            # iterate through the crane_activity and find the difference of exit_datetime and enter_datetime
            is_passed = False
            for i in range(len(crane_activity)):
                if i == 0:
                    continue
                # get the difference of exit_datetime and enter_datetime
                time_difference = (exit_datetime[i] - enter_datetime[i-1])
                time_difference = (enter_datetime[i] - exit_datetime[i-1] )
            
                seconds = time_difference / np.timedelta64(1, 's')
                # print("Time difference: ", time_difference)
                if seconds >= -1*60:
                    is_passed = True
                else:
                    is_passed = False
                    print(i, seconds, order_ids[i], order_ids[i-1], enter_datetime[i], exit_datetime[i-1], tugboat_ids[i], tugboat_ids[i-1])
                    break
            self.assertTrue(is_passed, f"Crane {crane_name} has a time difference issue.")

    # skip this method for testing
    #@unittest.skip("Skipping crane unload test for now")
    def test_crane_unload(self):
        result_df = main()
        name = list(result_df['name'].unique())
        # print(name)
        unique_crane_names = set([ld.split(" - ")[0] for ld in name if "ld" in ld])
        data = TravelHelper._instance.data
        orders = data['orders']
        for crane_name in unique_crane_names:
            # get the crane load from the result_df
            
            for order in orders.values():
                crane_activity = result_df[(result_df['name'].str.contains(crane_name))&
                                           #((result_df['order_id'] == 'o2' ) | (result_df['order_id'] == 'o1') )
                                                  (result_df['order_id'] == order.order_id )                          
                                           
                                           # |(order.order_id == result_df['order_id']) ) 
                                           ]
                                            #| result_df['type'].str.contains('Customer'))]
                #crane_activity = crane_activity[crane_activity['order_id'] == order.order_id]
                crane_activity['enter_datetime'] = pd.to_datetime(crane_activity['enter_datetime'])
                crane_activity = crane_activity.sort_values(by='enter_datetime')
                
                print(crane_activity)
                # get enter_datetime and exit_datetime
                enter_datetime = crane_activity['enter_datetime'].values
                exit_datetime = crane_activity['exit_datetime'].values
                order_ids = crane_activity['order_id'].values
                tugboat_ids = crane_activity['tugboat_id'].values
                print(len(enter_datetime))
                # iterate through the crane_activity and find the difference of exit_datetime and enter_datetime
                is_passed = False
                for i in range(len(crane_activity)):
                    if i == 0:
                        continue
                    # get the difference of exit_datetime and enter_datetime
                    time_difference = (enter_datetime[i] - exit_datetime[i-1] )
                    time_difference = (enter_datetime[i] - exit_datetime[i-1] )
                
                    seconds = time_difference / np.timedelta64(1, 's')
                    # print("Time difference: ", time_difference)
                    if seconds >= -1*60:
                        is_passed = True
                    else:
                        is_passed = False
                        print(i, seconds, order_ids[i], order_ids[i-1], enter_datetime[i], exit_datetime[i-1], tugboat_ids[i], tugboat_ids[i-1])
                        break
                self.assertTrue(is_passed, f"Unload Crane {crane_name} has a time difference issue.")


if __name__ == "__main__":
    unittest.main()