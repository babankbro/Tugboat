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
    for result in lookup_schedule_results.values():
        #print("\nSchedule for Tugboat TT", result['tugboat_schedule']['tugboat_id'])
        tugboat_schedule = result['tugboat_schedule']
        # if 'tbs1' != result['tugboat_schedule']['tugboat_id']:
        #      continue
        #print(tugboat_schedule)
        
        tugboat_result = lookup_tugboat_results[tugboat_schedule['tugboat_id']]
        #print(tugboat_result)
        last_point = tugboat_result['data_points'][-1]
        arrival_datetime = last_point['order_arrival_time'] 
        order_location ={
                "ID": order.start_object.order_id,
                'type': "Start Order",
                'name': order.start_object.name,
                'enter_datetime': arrival_datetime,
                'exit_datetime':tugboat_schedule['end_datetime'],
                'distance': last_point['order_distance'],
                'speed': last_point['barge_speed'] 
            }
        tugboat_result['data_points'].append(order_location)
        
    #print("----------------- Travel to Appointment -----------------")
    data = Travel_Helper.data
    for tugboat_id, appoint_info in appointment_infos.items():
        tugboat = appoint_info["sea_tugboat"]
        tugboat_id = tugboat.tugboat_id
        tugboat_result = lookup_tugboat_results[tugboat_id]
        schedule_result = lookup_schedule_results[tugboat_id]
        
        appointment_station = data['stations'][appoint_info['appointment_station']]
        
        travel_info = tugboat.calculate_travel_to_appointment(appoint_info)
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
                'speed': travel_info['speed'] 
            }
        tugboat_result['data_points'].append(appointment_location)


def travel_trought_river_import_to_customer(order, lookup_river_tugboat_results):
    late_times = {}
    for tugboat_id, tugboat_result in lookup_river_tugboat_results.items():
        tugboat = Travel_Helper.data['tugboats'][tugboat_id]
        tugboat_result = lookup_river_tugboat_results[tugboat_id]
        
        
        previous_location = tugboat_result['data_points'][-1]
        appointment_station_id = previous_location['ID']
        appointment_station = Travel_Helper.data['stations'][appointment_station_id]
        input_travel_info = {
            'order':order,
            'appointment_station_id':appointment_station_id,
        }
        travel_info =tugboat.calculate_river_to_customer(input_travel_info)
        arrival_datetime = previous_location['exit_datetime'] + timedelta(minutes=travel_info['travel_time']*60)
        #print(travel_info)
        customer_station = Travel_Helper.data['stations'][order.des_object.station_id]
        customer_location = {
            "ID": order.des_object.station_id,
            'name': customer_station.name,
            'type': "Customer Station",
            'enter_datetime': arrival_datetime,
            'exit_datetime':None,
            'distance': travel_info['travel_distance'],
            'speed': travel_info['speed']
        }
        tugboat_result['data_points'].append(customer_location)
        
        if order.due_datetime > arrival_datetime:
            late_times[tugboat_id] = 0
        else:
            late_times[tugboat_id] = (order.due_datetime - arrival_datetime).total_seconds()/60
    return late_times
        
def update_river_travel_tugboats(order, river_schedule_results, lookup_river_tugboat_results):
    
    for tugboat_id, tugboat_result in lookup_river_tugboat_results.items():
        tugboat_result = lookup_river_tugboat_results[tugboat_id]
        
        tugboat_shedule = river_schedule_results[tugboat_id]['tugboat_schedule']    
        customer_location = tugboat_result['data_points'][-1]
        if customer_location['type'] != "Customer Station":
            raise Exception("Customer Station not found")
        customer_location['exit_datetime'] = tugboat_shedule['end_datetime']
        
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
            date_time = pair_tugboat_result['data_points'][1]['enter_datetime']
            #print(date_time)
            if date_time > max_datetime:
                max_datetime = date_time
        
        tugboat_result['data_points'][-1]['exit_datetime']  = max_datetime
        #print(tugboat_result['data_points'][-1]['exit_datetime'] )
        
        
    #print("-----------------------------------------------------------")
    
    
        