import sys
import os

# Add the project root directory to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Add CodeVS directory to path
codevs_path = os.path.join(project_root, 'CodeVS')
sys.path.insert(0, codevs_path)

from datetime import timedelta, datetime
import pandas as pd
import unittest
import numpy as np
import warnings
warnings.filterwarnings(action='ignore')

# Import from the CodeVS modules - use relative imports from the CodeVS directory
try:
    from main import main, test_transport_order
    from read_data import *
    from initialize_data import initialize_data, print_all_objects
    from operations.assigned_barge import *
    from operations.scheduling import *
    from operations.transport_order import *
    from operations.travel_helper import *
    from components.solution import Solution
except ImportError as e:
    print(f"Import error: {e}")
    print("Current working directory:", os.getcwd())
    print("Python path:", sys.path[:3])
    raise
        
        
def get_tugboat_df():
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
    
    Number_Code_Tugboat = 4*int(2*total_demand//(average_tugboat_capacity)) #for barge and tugboat
    print("Number Code Tugboat", Number_Code_Tugboat)
    
    
    solution = Solution(data)
    
    np.random.seed(1)
    xs = np.random.rand(Number_Code_Tugboat)
    
    tugboat_df, barge_df = solution.generate_schedule(order_ids, xs=xs)
    return tugboat_df
        
class TestSingleOrder(unittest.TestCase):
    # def test_file_type(self):
    #     result_df = main()
    #     self.assertIsInstance(result_df, pd.DataFrame)

    # uncomment below to skip this method for testing
    #@unittest.skip("Skipping crane loading test for now")
    def test_crane_load(self):
    
        tugboat_df = get_tugboat_df()
        
        result_df = tugboat_df
        name = list(result_df['name'].unique())
        # print(name)
        unique_crane_names = set([cr.split(" - ")[0] for cr in name if "cr" in cr])

        data = TravelHelper._instance.data
        orders = data['orders']
        for crane_name in unique_crane_names:
            # get the crane load from the result_df
            isBreak = False
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
                
                #print(crane_activity)
                # get enter_datetime and exit_datetime
                enter_datetime = crane_activity['enter_datetime'].values
                exit_datetime = crane_activity['exit_datetime'].values
                order_ids = crane_activity['order_id'].values
                tugboat_ids = crane_activity['tugboat_id'].values
                # print(len(enter_datetime))
                # iterate through the crane_activity and find the difference of exit_datetime and enter_datetime
                is_passed = True
                for i in range(len(crane_activity)):
                    if i == 0:
                        continue
                    # get the difference of exit_datetime and enter_datetime
                    time_difference = (enter_datetime[i] - exit_datetime[i-1] )
                    time_difference = (enter_datetime[i] - exit_datetime[i-1] )
                
                    seconds = time_difference / np.timedelta64(1, 's')
                    # print("Time difference: ", time_difference)
                    if seconds >= -1 * 60:
                        is_passed = True
                    else:
                        is_passed = False
                        print(i, seconds, order_ids[i], order_ids[i-1], enter_datetime[i], exit_datetime[i-1], tugboat_ids[i], tugboat_ids[i-1])
                        print(crane_activity)
                        break
                
                self.assertTrue(is_passed, f"Load Crane {crane_name} has a time difference issue.")
                if not is_passed:
                    isBreak = True
                    break
            if isBreak:
                break

    
    
    def test_crane_unload(self):
        tugboat_df = get_tugboat_df()
        result_df = tugboat_df
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
                # print(len(enter_datetime))
                # iterate through the crane_activity and find the difference of exit_datetime and enter_datetime
                is_passed = True
                for i in range(len(crane_activity)):
                    if i == 0:
                        continue
                    # get the difference of exit_datetime and enter_datetime
                    time_difference = (enter_datetime[i] - exit_datetime[i-1] )
                    time_difference = (enter_datetime[i] - exit_datetime[i-1] )
                
                    seconds = time_difference / np.timedelta64(1, 's')
                    # print("Time difference: ", time_difference)
                    if seconds >= -1 * 60:
                        is_passed = True
                    else:
                        is_passed = False
                        print(i, seconds, order_ids[i], order_ids[i-1], enter_datetime[i], exit_datetime[i-1], tugboat_ids[i], tugboat_ids[i-1])
                        break
                self.assertTrue(is_passed, f"Unload Crane {crane_name} has a time difference issue.")
    
    def test_tugboat_timeline_overlap(self):
        tugboat_df = get_tugboat_df()
        result_df = tugboat_df
        filter_out_type = ['Barge Collection', 'Barge Release', 'Start Order Carrier', 'Destination Barge', 
                           'Crane-Carrier', 'Appointment', 'Barge Change', 'Customer Station']
        filter_df = result_df[~result_df['type'].isin(filter_out_type)]

        # get order id
        order_ids = filter_df["order_id"].unique()

        # get tugboat id
        tugboat_ids = filter_df["tugboat_id"].unique()

        # iterate through each order and tugboat
        is_passed = True
        for order_id in order_ids:
            for tugboat_id in tugboat_ids:
                test_df = filter_df[(filter_df["order_id"] == order_id) & (filter_df["tugboat_id"] == tugboat_id)]
                test_df['enter_datetime'] = pd.to_datetime(test_df['enter_datetime'])
                activity = test_df.copy() # The time must not be sorted. It should be in the generated sequences.
                print("UNITTEST TUGBOAT OVERLAB ")
                print(activity)
                # get enter_datetime and exit_datetime
                enter_datetime = activity['enter_datetime'].values
                exit_datetime = activity['exit_datetime'].values

                for i in range(len(activity)):
                    if i == 0:
                        continue
                    # get the difference of exit_datetime and enter_datetime
                    time_difference = (enter_datetime[i] - exit_datetime[i-1] )
                    time_difference = (enter_datetime[i] - exit_datetime[i-1] )
                
                    seconds = time_difference / np.timedelta64(1, 's')
                    # print("Time difference: ", time_difference)
                    if seconds >= -1 * 60:
                        is_passed = True
                    else:
                        is_passed = False
                        print(i, seconds, order_id, enter_datetime[i], exit_datetime[i-1], tugboat_id)
                        break
                self.assertTrue(is_passed, f"Tugboat {tugboat_id} in Order {order_id}: Time overlapping")
                if not is_passed:
                    break
            if not is_passed:
                break
    
    def test_nan_ensuring(self):
        tugboat_df = get_tugboat_df()
        result_df = tugboat_df
        
        names = result_df["name"].values
        name_with_nan = ""
        is_passed = True
        for name in names:
            if "nan" in name:
                name_with_nan = name
                is_passed = False
                break

        self.assertTrue(is_passed, f"There is nan in {name_with_nan}")

    def test_barge_timeline_overlap(self):
        tugboat_df = get_tugboat_df()
        result_df = tugboat_df
        filter_out_type = ['main_point']
    
        barge_df = result_df[~result_df['type_point'].isin(filter_out_type)]
        unique_barge_ids = barge_df["barge_ids"].unique()
        is_passed_overall = True
        error_messages = []

        for barge_id in unique_barge_ids:
            if ',' in barge_id:
                continue
     
            barge_activities = barge_df[barge_df['name'].str.contains(rf"\b{barge_id}\b", regex=True)].copy()
            
            barge_activities['enter_datetime'] = pd.to_datetime(barge_df['enter_datetime'])
            barge_activities = barge_activities.sort_values(by='enter_datetime')
            
            print(barge_activities)
            # get enter_datetime and exit_datetime
            enter_datetimes = barge_activities['enter_datetime'].values
            exit_datetimes = barge_activities['exit_datetime'].values
            order_ids = barge_activities['order_id'].values
            tugboat_ids = barge_activities['tugboat_id'].values

            for i in range(1, len(barge_activities)):
                # Check for NaT values which can occur if data is incomplete
                                

                time_difference = (enter_datetimes[i] - exit_datetimes[i-1])
                seconds = time_difference / np.timedelta64(1, 's')

                # Allow a small tolerance (e.g., -60 seconds for 1 minute overlap)
                if seconds < -60:
                    activity_prev_name = barge_activities['name'].iloc[i-1] if 'name' in barge_activities.columns else 'N/A'
                    activity_curr_name = barge_activities['name'].iloc[i] if 'name' in barge_activities.columns else 'N/A'
                    msg = (
                        f"Barge ID: {i} - {barge_activities.iloc[i]['name']}\n"
                        f"Barge Timeline Overlap: Barge ID: {barge_id}\n"
                        f"  Previous Activity End: {exit_datetimes[i-1]} (Name: {activity_prev_name})\n"
                        f"  Current Activity Start: {enter_datetimes[i]} (Name: {activity_curr_name})\n"
                        f"  Overlap (seconds): {seconds:.2f}"
                    )
                    error_messages.append(msg)
                    is_passed_overall = False
                    break # Optional: Stop checking this barge on first error, or collect all errors
        
                self.assertTrue(is_passed_overall, "\n".join(["One or more barges have timeline overlapping issues:"] + error_messages))
                if not is_passed_overall:
                    break


if __name__ == "__main__":
    unittest.main()
    


#  5  ใช้ทุกบาร์จ / passed
#  6  เรือเเม่น้ำขน บาร์จ test sea tugboat ไปเกิน กม. 40 
#  7  น้ำขึ้นนำลง 
#  8  calculate cost 
    
