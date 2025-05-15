import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from datetime import timedelta, datetime
import pandas as pd
from CodeVS.operations.travel_helper import *
from read_data import *
from CodeVS.operations.assigned_barge import *
from CodeVS.operations.scheduling import *
from CodeVS.utility.helpers import *


class TugboatTravelStatus:
    def __init__(self, tugboat, is_river_status):
        self.tugboat = tugboat
        self.is_river_status = is_river_status
        self.is_move_down = True


def travel_appointment_import(order, lookup_schedule_results, lookup_tugboat_results, appointment_infos):
    for tugboat_id, result in lookup_schedule_results.items():
        #print("\nSchedule for Tugboat TT", result['tugboat_schedule']['tugboat_id'])
        tugboat_schedule = result['tugboat_schedule']
        # if 'tbs1' != result['tugboat_schedule']['tugboat_id']:
        #      continue
        #print(tugboat_schedule)
        
        schedule_result = result
        #print("Example Schedule VVVV Result:", tugboat_id)
        #print("\tTugboat Schedule:", tugboat_schedule)
        crane_shedule = schedule_result['crane_schedule'] 
        min_start_crane = 10000000000000000000000000000000
        for crane in crane_shedule:
            print("\t", crane) if tugboat_id == 'tsb1' else None
            min_start_crane = min(min_start_crane, crane['start_time'])
        
        tugboat_result = lookup_tugboat_results[tugboat_schedule['tugboat_id']]
        #print('Appointment Tugboat Result: XXXXXXXXXXXXXXXX', tugboat_result) if tugboat_id == 'tbs1' and order.order_id == 'o1' else None 
      
        #last_point = tugboat_result['data_points'][-1]
        last_point = next((point for point in reversed(tugboat_result['data_points']) if point['type_point'] == "main_point"), None)
        #print("last_point", tugboat_id, last_point) if tugboat_id == 'tbs1' and order.order_id == 'o1' else None
        arrival_datetime = last_point['order_arrival_time'] 
        order_location ={
                "ID": order.start_object.order_id,
                'type': "Start Order Carrier",
                'name': order.start_object.name,
                'enter_datetime': arrival_datetime,
                'exit_datetime':tugboat_schedule['end_datetime'],
                'distance': last_point['order_distance'],
                'speed': last_point['barge_speed'],
                'type_point': 'main_point'
            }
        tugboat_result['data_points'].append(order_location) # add result data points
        for crane in crane_shedule:
            crane_arrival = arrival_datetime + timedelta(minutes=(crane['start_time'] - min_start_crane)*60)
            #print("Crane Info:", min_start_crane, arrival_datetime, crane_arrival, (crane['start_time'] - min_start_crane)*60) if tugboat_id == 'tbs1' and order.order_id == 'o1'   else None
            crane_location = {
                "ID": order.start_object.order_id,
                'type': "Crane-Carrier",
                'name': crane['crane_id'] + ' - ' + crane['barge'].barge_id,
                'enter_datetime': crane_arrival,
                'exit_datetime':crane_arrival + timedelta(minutes=crane['time_consumed']*60),
                'distance': 0,
                'speed': crane['rate'],
                'type_point': 'loading_point'
            }
            tugboat_result['data_points'].append(crane_location) # add result data points
        
        
        
        
    #print("----------------- Travel to Appointment -----------------")
    data = TravelHelper._instance.data
    for tugboat_id, appoint_info in appointment_infos.items():
        tugboat = appoint_info["sea_tugboat"]
        tugboat_id = tugboat.tugboat_id
        tugboat_result = lookup_tugboat_results[tugboat_id]
        schedule_result = lookup_schedule_results[tugboat_id]
        
        appointment_station = data['stations'][appoint_info['appointment_station']]
        
        travel_info = tugboat.calculate_travel_to_appointment(appoint_info)
       
            #for step in travel_info['steps']:
                #print(step)
        #print(travel_info)
       #print()
        
        tugboat_schedule = schedule_result['tugboat_schedule']
        arrival_datetime = tugboat_schedule['end_datetime'] + timedelta(minutes=travel_info['travel_time']*60)
        arrival_datetime = get_previous_quarter_hour(arrival_datetime)
        
        appointment_location ={
                "ID": appointment_station.station_id,
                'name': appointment_station.name,
                'type': "Appointment",
                'enter_datetime': arrival_datetime,
                'exit_datetime':None,
                'distance': travel_info['travel_distance'],
                'speed': travel_info['speed'],
                'type_point': 'main_point'
            }
        tugboat_result['data_points'].append(appointment_location) # add result data points


def travel_trought_river_import_to_customer(order, lookup_river_tugboat_results):
    late_times = {}
    for tugboat_id, tugboat_result in lookup_river_tugboat_results.items():
        tugboat = TravelHelper._instance.data['tugboats'][tugboat_id]
        tugboat_result = lookup_river_tugboat_results[tugboat_id]
        
        
        #previous_location = tugboat_result['data_points'][-1]
        #print(tugboat_result['data_points'])
        previous_location = [point for point in tugboat_result['data_points'] if point['type_point'] == "main_point"][-1]
        
        
        
        appointment_station_id = previous_location['ID']
        input_travel_info = {
            'order':order,
            'appointment_station_id':appointment_station_id,
        }
        travel_info =tugboat.calculate_river_to_customer(input_travel_info)
        arrival_datetime = previous_location['exit_datetime'] + timedelta(minutes=travel_info['travel_time']*60)
        #print(travel_info)
        customer_station = TravelHelper._instance.data['stations'][order.des_object.station_id]
        customer_location = {
            "ID": order.des_object.station_id,
            'name': customer_station.name,
            'type': "Customer Station",
            'enter_datetime': arrival_datetime,
            'exit_datetime':None,
            'distance': travel_info['travel_distance'],
            'speed': travel_info['speed'],
            'type_point': 'main_point'
        }
        tugboat_result['data_points'].append(customer_location) # add result data points
        
        if order.due_datetime > arrival_datetime:
            late_times[tugboat_id] = 0
        else:
            late_times[tugboat_id] = (order.due_datetime - arrival_datetime).total_seconds()/60
    return late_times
        
def update_river_travel_tugboats(order, river_schedule_results, lookup_river_tugboat_results):
    
    for tugboat_id, tugboat_result in lookup_river_tugboat_results.items():
        tugboat_result = lookup_river_tugboat_results[tugboat_id]
        
        tugboat_shedule = river_schedule_results[tugboat_id]['tugboat_schedule']  
        #print("Tugboat Schedule GGGGGGGGGGGGGGGGGGGGG:\n", ) if tugboat_id == 'tbr1' else None
        #[print(schedule) for schedule in river_schedule_results[tugboat_id]['loader_schedule']  if (tugboat_id == 'tbr1' )]
        loading_schedule =  river_schedule_results[tugboat_id]['loader_schedule']
        #print(tugboat_shedule)
        
        customer_location = tugboat_result['data_points'][-1]
        arrival_customer_time = (customer_location['enter_datetime'])
        #if arrival_customer_time < order.due_datetime:
            
        # print("Update River Tugboat", tugboat_id)
        # for point in tugboat_result['data_points']:
        #     print(point)
        
        
        if customer_location['type'] != "Customer Station":
            raise Exception("Customer Station not found")
        
        end_date_last = arrival_customer_time
        for loader in loading_schedule:

            loader_start = arrival_customer_time + timedelta(minutes=(int(loader['start_time']*60)))
            #loader_start = get_next_quarter_hour(loader_start)
            loader_end = arrival_customer_time + timedelta(minutes=int(loader['loader_schedule']*60))
            #loader_end = get_next_quarter_hour(loader_end)
            print("Loader Info:", loader) if tugboat_id == 'tbr1' and order.order_id == 'o1'   else None
            crane_location = {
                "ID": order.start_object.order_id,
                'type': "Loader-Customer",
                'name': loader["loader_id"] + " - " + loader['barge'].barge_id,
                'enter_datetime':loader_start,
                'exit_datetime': loader_end,
                'distance': 0,
                'speed': loader['rate'],
                'time': loader['time_consumed'],
                'type_point': 'loading_point'
            }
            tugboat_result['data_points'].append(crane_location) # add result data points
            
            if end_date_last < crane_location['exit_datetime']:
                end_date_last = crane_location['exit_datetime']
        #print("Set Customer End Time:", end_date_last) if tugboat_id == 'tbr1' else None
        customer_location['exit_datetime'] = end_date_last
        

        
def update_sea_travel_tugboats(solution, order, lookup_sea_tugboat_results, lookup_river_tugboat_results):
    data = solution.data
    sea_pair_river_tugboat_lookup = {}
    #print("-----------------------------------------------------------")
    for tugboat_id, tugboat_result in lookup_sea_tugboat_results.items():
        #print(tugboat_result)
        tugboat_result = lookup_sea_tugboat_results[tugboat_id]
        tugboat = data['tugboats'][tugboat_id]
        barge_ids = [barge.barge_id for barge in tugboat.assigned_barges]
        tugboat_pairs = []
        for river_tugboat_id, river_tugboat_result in lookup_river_tugboat_results.items():
            river_tugboat = data['tugboats'][river_tugboat_id]
            for barge in river_tugboat.assigned_barges:
                if barge.barge_id in barge_ids:
                    tugboat_pairs.append(river_tugboat_id)
                    break
         
        sea_pair_river_tugboat_lookup[tugboat_id] = tugboat_pairs
        #print(barge_ids)
    
    for tugboat_id, pair_tugboat in sea_pair_river_tugboat_lookup.items():
        #print(f"Tugboat {tugboat_id} has pair tugboats: {pair_tugboat}")
        tugboat_result = lookup_sea_tugboat_results[tugboat_id]
        max_datetime = lookup_river_tugboat_results[pair_tugboat[0]]['data_points'][1]['enter_datetime']
        for pair_tugboat_id in pair_tugboat:
            pair_tugboat_result = lookup_river_tugboat_results[pair_tugboat_id]
            date_time = pair_tugboat_result['data_points'][1]['exit_datetime']
            #print(date_time)
            if date_time > max_datetime:
                max_datetime = date_time
        # if order.order_id == 'o1':
        #      print("Tugboat XXX", tugboat_id, tugboat_result['data_points'][-1]['type'],
        #            tugboat_result['data_points'][-1]['exit_datetime'], max_datetime)
        #if tugboat_id == "tsb1" or tugboat_id == "tsr1":
       
        tugboat_result['data_points'][-1]['exit_datetime']  = max_datetime
        #print(tugboat_result['data_points'][-1]['exit_datetime'] )
        
        
    #print("-----------------------------------------------------------")
    
    
        