import sys
import os

from pandas._config import config

from CodeVS import config_problem

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


def travel_appointment_import(solution, order, lookup_schedule_results, lookup_tugboat_results, appointment_infos, order_trip):
    last_point_exit_lookup = {}
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
            #print("\t", 'BBBBBBBBBBBBBBBBBB',crane) if tugboat_id == 'tbs1' else None
            min_start_crane = min(min_start_crane, crane['start_time'])
        
        tugboat_result = lookup_tugboat_results[tugboat_schedule['tugboat_id']]
        #print('Appointment Tugboat Result: XXXXXXXXXXXXXXXX', tugboat_result) if tugboat_id == 'tbs1' and order.order_id == 'o1' else None 
      
        #last_point = tugboat_result['data_points'][-1]
        last_point = next((point for point in reversed(tugboat_result['data_points']) if point['type_point'] == "main_point"), None)
        #print("last_point", tugboat_id, last_point) if (tugboat_id == 'tbs1' or tugboat_id == 'tbs2') and order.order_id == 'o1' else None
        #order_arrival_time = last_point['order_arrival_time'] 
        last_point_exit_datetime = last_point['exit_datetime']
        
        travel_time = last_point['order_distance'] / last_point['barge_speed']
        arrival_datetime = last_point_exit_datetime + timedelta(hours=travel_time)
        print("Fixed Error Time Start ==========================")
        print ("SeaTB_01 Travel Time:", travel_time,  last_point_exit_datetime) if tugboat_id == 'SeaTB_01' else None
        print ("SeaTB_01 Travel Time:", arrival_datetime,  order.start_datetime) if tugboat_id == 'SeaTB_01' else None

        
        order_location ={
                "ID": order.start_object.order_id,
                'type': "Start Order Carrier",
                'name': order.start_object.name,
                'enter_datetime': arrival_datetime,
                'exit_datetime':tugboat_schedule['end_datetime'],
                'distance': last_point['order_distance'],
                'speed': last_point['barge_speed'],
                'time': travel_time,
                'type_point': 'main_point'
            }
        tugboat_result['data_points'].append(order_location) # add result data points
        for crane in crane_shedule:
            
            crane_start_time = order.start_datetime + timedelta(minutes=(crane['start_time'])*60)
            
            #print("Crane Info:", min_start_crane, arrival_datetime, crane_arrival, (crane['start_time'] - min_start_crane)*60) if tugboat_id == 'tbs1' and order.order_id == 'o1'   else None
            #print("Crane Info:", tugboat_id, crane_start_time, arrival_datetime) if (tugboat_id == 'tbs1' or tugboat_id == 'tbs2') and order.order_id == 'o1'  and crane['crane_id'] == 'cr1' else None
            
            if arrival_datetime > crane_start_time:
                crane_start_time = arrival_datetime
            
            crane_id = crane['crane_id']
            if order_trip > 1:
                #filter from tugboat_result['data_points'] of 'name' contain crane_id from all lookup_tugboat_results
                max_time_exit = order.start_datetime
                
                for tugboat_result_temp in lookup_tugboat_results.values():
                    crane_data_points = [point for point in tugboat_result_temp['data_points'] if crane_id in point['name']]
                    if len(crane_data_points) == 0:
                        continue
                    last_point_crane_finish = crane_data_points[-1]
                    #print("######################################### Finish Crane info points:", last_point_crane_finish, crane_start_time, max_time_exit)
                    max_time_exit = max(max_time_exit, last_point_crane_finish['exit_datetime'])
                
                
                if crane_start_time < max_time_exit:
                    #print("######################################### Crane start time is less than max time exit")
                    crane_start_time = max_time_exit
                
                
            
            crane_location = {
                "ID": order.start_object.order_id,
                'type': "Crane-Carrier",
                'name': crane['crane_id'] + ' - ' + crane['barge'].barge_id,
                'enter_datetime': crane_start_time,
                'exit_datetime':crane_start_time + timedelta(minutes=crane['time_consumed']*60),
                'distance': 0,
                'speed': crane['rate'],
                'time': crane['time_consumed'],
                'type_point': 'loading_point'
            }
            tugboat_result['data_points'].append(crane_location) # add result data points
            order_location['exit_datetime'] = max(order_location['exit_datetime'], crane_location['exit_datetime'])
        
        last_point_exit_lookup[tugboat_id] = order_location['exit_datetime']
        
        
    #print("----------------- Travel to Appointment -----------------")
    data = TravelHelper._instance.data
    for tugboat_id, appoint_info in appointment_infos.items():
        tugboat = appoint_info["sea_tugboat"]
        tugboat_id = tugboat.tugboat_id
        tugboat_result = lookup_tugboat_results[tugboat_id]
        schedule_result = lookup_schedule_results[tugboat_id]
        
        #print(appoint_info['appointment_station'])
        appointment_station = data['stations'][appoint_info['appointment_station']]
        
        travel_info = tugboat.calculate_travel_to_appointment(appoint_info)
       
        # print("Travel Info:", travel_info) if tugboat_id == 'tbs1' and order.order_id == 'o1' else None
        # for step in travel_info['steps']:
        #      print(step)  if tugboat_id == 'tbs1' and order.order_id == 'o1' else None
        #print(travel_info)
       #print()
        
        tugboat_schedule = schedule_result['tugboat_schedule']
        arrival_datetime = last_point_exit_lookup[tugboat_id] + timedelta(minutes=travel_info['travel_time']*60)
        arrival_datetime = get_previous_quarter_hour(arrival_datetime)
        

        appointment_location ={
                "ID": appointment_station.station_id,
                'name': f"From {travel_info['start_object'].name} To {appointment_station.name}",
                'type': "Appointment",
                'enter_datetime': arrival_datetime,
                'exit_datetime':None,
                'distance': travel_info['travel_distance'],
                'time': travel_info['travel_time'],
                'speed': travel_info['speed'],
                'type_point': 'main_point'
            }
        tugboat_result['data_points'].append(appointment_location) # add result data points
        
        
        trave_steps = generate_travel_steps(arrival_datetime, travel_info)
        #loop to find max exit_datetime
        max_exit_datetime = max(trave_steps, key=lambda x: x['exit_datetime'])['exit_datetime']
        appointment_location['exit_datetime'] = max_exit_datetime
        
        tugboat_result["data_points"].extend(trave_steps)
        
        time_release_barges = config_problem.BARGE_RELEASE_MINUTES*len(tugboat.assigned_barges)
        barge_ids = [barge.barge_id for barge in tugboat.assigned_barges]
        release_barges_location ={
                "ID": appointment_station.station_id,
                'type': "Barge Release",
                'name': "Release Barges (" + " - ".join(barge_ids) + ")",
                'enter_datetime': appointment_location['exit_datetime'],
                'exit_datetime':appointment_location['exit_datetime'] + timedelta(minutes=time_release_barges),
                'distance': 0,
                'speed': 0,
                'time': time_release_barges,
                'type_point': 'main_point'
            }
        tugboat_result['data_points'].append(release_barges_location)
        release_steps = generate_release_steps(release_barges_location['enter_datetime'], barge_ids)
        
        for i, release_step in enumerate(release_steps):
            solution.update_single_barge_scheule(order, barge_ids[i], release_step['enter_datetime'], release_step['exit_datetime'], appointment_station.km, 
                                             appointment_station.water_type, (appointment_station.lat, appointment_station.lng), appointment_station.station_id)
            #print("Update barge schedule ##################### ", appointment_station.station_id, solution.barge_scheule[barge_ids[i]][-1])
        
        tugboat_result['data_points'].extend(release_steps)

def generate_travel_steps(arrival_datetime, travel_info):
    trave_steps = []
    start_travel_time = arrival_datetime
    # print(travel_info['steps'][0]['start_id'])
    # print(travel_info['steps'][-1]['end_id'])
    start_station = TravelHelper._instance.data['stations'][travel_info['steps'][0]['start_id']]
    end_station = TravelHelper._instance.data['stations'][travel_info['steps'][-1]['end_id']]
    if (start_station.water_type == WaterBody.SEA) and (end_station.water_type == WaterBody.SEA):
        travel_type = 'Sea-Sea'
    elif(start_station.water_type == WaterBody.RIVER) and (end_station.water_type == WaterBody.SEA):
        travel_type = 'River-Sea'

    elif(start_station.water_type == WaterBody.SEA) and (end_station.water_type == WaterBody.RIVER):
        travel_type = 'Sea-River'
    elif(start_station.water_type == WaterBody.RIVER) and (end_station.water_type == WaterBody.RIVER):
        travel_type = 'River-River'

    data = TravelHelper._instance.data
    # print("\n")

    # print(data['stations']['c1'])
    # print("\n")
    # eeeeee
    for step in travel_info['steps']:
        finish_travel_time = start_travel_time + timedelta(minutes=(step['travel_time'])*60)
        start_station_step = data['stations'][step['start_id']]
        end_station_step = data['stations'][step['end_id']]
        travel_step ={
                "ID": "Travel",
                'type': travel_type,
                'name': start_station_step.station_id + ' to ' + end_station_step.station_id ,
                'enter_datetime': start_travel_time,
                'exit_datetime': finish_travel_time,
                'distance': step['distance'],
                'speed': step['speed'],
                'time': step['travel_time'],
                'type_point': 'travel_point',
            }
        start_travel_time = finish_travel_time
            #print(collection_info)
        trave_steps.append(travel_step)
    return trave_steps

def generate_release_steps(arrival_datetime, barge_ids):
    trave_steps = []
    start_travel_time = arrival_datetime
    for barge_id in barge_ids:
        finish_travel_time = start_travel_time + timedelta(minutes=(config_problem.BARGE_RELEASE_MINUTES))
        
        travel_step ={
                "ID": "Travel",
                'type': "Barge Step Release",
                'name': "Barge Releasing (" + barge_id + ")",
                'enter_datetime': start_travel_time,
                'exit_datetime': finish_travel_time,
                'distance': 0,
                'speed': 0,
                'time': config_problem.BARGE_RELEASE_MINUTES/60,
                'type_point': 'release_point',
            }
        start_travel_time = finish_travel_time
        trave_steps.append(travel_step)
    return trave_steps


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
        #arrival_datetime = previous_location['exit_datetime'] + timedelta(minutes=travel_info['travel_time']*60)
        arrival_datetime = previous_location['exit_datetime']

        customer_station = TravelHelper._instance.data['stations'][order.des_object.station_id]
        customer_location = {
            "ID": order.des_object.station_id,
            'name': f'From {travel_info["start_object"].name} To {customer_station.name}',
            'type': "Customer Station",
            'enter_datetime': arrival_datetime,
            'exit_datetime':None,
            'distance': travel_info['travel_distance'],
            'speed': travel_info['speed'],
            'time': travel_info['travel_time'],
            'type_point': 'main_point'
        }
        tugboat_result['data_points'].append(customer_location) # add result data points
        
        travel_steps = generate_travel_steps(arrival_datetime, travel_info)
        tugboat_result['data_points'].extend(travel_steps)
        
        
        if order.due_datetime > arrival_datetime:
            late_times[tugboat_id] = 0
        else:
            late_times[tugboat_id] = (order.due_datetime - arrival_datetime).total_seconds()/60
    return late_times
        
def update_river_travel_tugboats(order, first_arrival_customer_datetime, river_schedule_results, 
                                 lookup_river_tugboat_results, temp_river_tugboat_results,round_order_trip):
    
    for tugboat_id, tugboat_result in lookup_river_tugboat_results.items():
        tugboat_result = lookup_river_tugboat_results[tugboat_id]
        
        tugboat_shedule = river_schedule_results[tugboat_id]['tugboat_schedule']  
        #print("Tugboat Schedule GGGGGGGGGGGGGGGGGGGGG:\n", ) if tugboat_id == 'tbr1' else None
        #[print(schedule) for schedule in river_schedule_results[tugboat_id]['loader_schedule']  if (tugboat_id == 'tbr1' )]
        loading_schedule =  river_schedule_results[tugboat_id]['loader_schedule']
        #print(tugboat_shedule)
        customer_location = [point for point in tugboat_result['data_points'] if point['type_point'] == "main_point"][-1]
        arrival_customer_time = (tugboat_result['data_points'] [-1]['exit_datetime'])
        #if arrival_customer_time < order.due_datetime:
            
        # print("Update River Tugboat", tugboat_id)
        # for point in tugboat_result['data_points']:
        #     print(point)
        
        
        if customer_location['type'] != "Customer Station":
            raise Exception("Customer Station not found")
        
        
        
        
        end_date_last = arrival_customer_time
        loader_start = first_arrival_customer_datetime
        
        
        all_tugboat_results = []
        for tugboat_result_temp in temp_river_tugboat_results:
            all_tugboat_results.append(tugboat_result_temp)
        for tugboat_result_temp in lookup_river_tugboat_results.values():
            all_tugboat_results.append(tugboat_result_temp)
            
        
        
        for loader in loading_schedule:
            
            
            temp_loader_start = first_arrival_customer_datetime + timedelta(minutes=(int(loader['start_time']*60)))
            if temp_loader_start > loader_start:
                loader_start = temp_loader_start
            
            
            if arrival_customer_time > loader_start:
                loader_start = arrival_customer_time
           
            #loader_start = get_next_quarter_hour(loader_start)
            
            #loader_end = get_next_quarter_hour(loader_end)
            #print("Loader Info:", loader) if tugboat_id == 'tbr1' and order.order_id == 'o1'   else None
            #if arrival_customer_time > loader_start:
            #    loader_start = arrival_customer_time
            #if loader_start < old_loader_start:
                #loader_start = first_arrival_customer_datetime
            
            
            
            #print("Loader Start:", first_arrival_customer_datetime, loader_start, old_loader_start, loader_end) if order.order_id == 'o1' else None
            #if round_order_trip > 1:
            max_time_exit = loader_start
            loader_id = loader["loader_id"]
            for tugboat_result_temp in all_tugboat_results:
                loader_data_points = [point for point in tugboat_result_temp['data_points'] if loader_id in point['name']]
                if len(loader_data_points) == 0:
                    continue
                last_point_crane_finish = loader_data_points[-1]
                #print("######################################### Finish Crane info points:", last_point_crane_finish, crane_start_time, max_time_exit)
                max_time_exit = max(max_time_exit, last_point_crane_finish['exit_datetime'])
            
            if max_time_exit > loader_start:
                loader_start = max_time_exit

            
            
            loader_end = loader_start + timedelta(minutes=int((loader['loader_schedule'] - loader['start_time'])*60))
            
            
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
            loader_start = loader_end
            if end_date_last < crane_location['exit_datetime']:
                end_date_last = crane_location['exit_datetime']
        #print("Set Customer End Time:", end_date_last) if tugboat_id == 'tbr1' else None
        customer_location['exit_datetime'] = end_date_last
        

def update_sea_travel_tugboats(solution, order, lookup_sea_tugboat_results, lookup_river_tugboat_results):
    data = solution.data
    sea_pair_river_tugboat_lookup = {}
    #print("DEBUG UPDATE SEA TRAVEL TUGBOAT -----------------------------------------------------------")
    for tugboat_id, tugboat_result in lookup_sea_tugboat_results.items():
        #print(tugboat_result)
        tugboat_result = lookup_sea_tugboat_results[tugboat_id]
        data_points = tugboat_result['data_points']
        #filter type 'Sea-River'
        data_points = [point for point in data_points if point['type'] == 'Sea-River']
        max_datetime = max(data_points, key=lambda x: x['exit_datetime'])['exit_datetime']
        end_point = next((point for point in reversed(tugboat_result['data_points']) if point['type_point'] == "main_point"), None)
        #end_point['exit_datetime']  = max_datetime
        #print(tugboat_result)
        #print()
    
        
def old_step_update_sea_travel_tugboats(solution, order, lookup_sea_tugboat_results, lookup_river_tugboat_results):
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
        
        
        #Replace last exit datetime with max datetime
        end_point = next((point for point in reversed(tugboat_result['data_points']) if point['type_point'] == "main_point"), None)
        end_point['exit_datetime']  = max_datetime
        #print(tugboat_result['data_points'][-1]['exit_datetime'] )
        
        
    #print("-----------------------------------------------------------")
    
    
        