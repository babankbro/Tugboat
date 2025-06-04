from CodeVS.operations.assigned_barge import *
from CodeVS.operations.transport_order import *
import config_problem 
from CodeVS.utility.helpers import *
import string
import pandas as pd
import numpy as np
import warnings
from itertools import cycle
import random
warnings.filterwarnings("ignore")


class Solution:
    def __init__(self, data):
        self.data = data
        self.tugboat_scheule = {}
        self.barge_scheule = {}
        self.tugboat_travel_results = {}
        
        for tugboat_id, tugboat in data['tugboats'].items():
            closeset_station = TravelHelper._instance.get_next_river_station(TransportType.EXPORT, tugboat._km)
            info = {
                'tugboat_id': tugboat.tugboat_id,
                'order_id': None,
                'start_datetime': tugboat._ready_time,
                'end_datetime': tugboat._ready_time,
                'river_km': tugboat._km,
                'water_status': tugboat._status , 
                'location': (tugboat._lat, tugboat._lng),
                'station_id':  closeset_station.station_id if closeset_station != None  else None,
                'barge_infos': [],
                 
            }
            self.tugboat_scheule[tugboat_id] = [info]
            
            self.tugboat_travel_results[tugboat.tugboat_id] = []
            
            
        for barge_id, barge in data['barges'].items():
            closeset_station, _ = TravelHelper._instance.get_closest_sea_station((barge._lat, barge._lng))
            
            
            info = {
                'barge_id': barge.barge_id,
                'order_id': None,
                'start_datetime': barge._ready_time,
                'end_datetime': barge._ready_time,
                'river_km': barge._river_km,
                'water_status': barge._water_status, 
                'location': (barge._lat, barge._lng),
                'station_id': closeset_station.station_id if barge._water_status == WaterBody.SEA else barge._station_id,
                    
            }
            self.barge_scheule[barge_id] = [info]
            
    def get_ready_barge(self, barge):
        return self.barge_scheule[barge.barge_id][-1]['end_datetime']
    
    def get_location_barge(self, barge):
        return self.barge_scheule[barge.barge_id][-1]['location']
    
    def get_river_km_barge(self, barge):
        return self.barge_scheule[barge.barge_id][-1]['river_km']
    
    def get_station_id_barge(self, barge):
        return self.barge_scheule[barge.barge_id][-1]['station_id']
    
    def get_water_status_barge(self, barge):
        return self.barge_scheule[barge.barge_id][-1]['water_status']
        
    def get_ready_time_tugboat(self, tugboat):
        return self.tugboat_scheule[tugboat.tugboat_id][-1]['end_datetime']
    
    def get_location_tugboat(self, tugboat):
        return self.tugboat_scheule[tugboat.tugboat_id][-1]['location']
    
    def get_river_km_tugboat(self, tugboat):
        return self.tugboat_scheule[tugboat.tugboat_id][-1]['river_km']
    
    def get_station_id_tugboat(self, tugboat):
        return self.tugboat_scheule[tugboat.tugboat_id][-1]['station_id']
    
    def get_water_status_tugboat(self, tugboat):
        return self.tugboat_scheule[tugboat.tugboat_id][-1]['water_status']
    
    def get_barge_infos_tugboat(self, tugboat):
       #print(self.tugboat_scheule[tugboat.tugboat_id])
        return self.tugboat_scheule[tugboat.tugboat_id][-1]['barge_infos']
    
    def assign_barges_to_single_order(self, order, barges):
        assigned_barges = []
        remaining_demand = order.demand
        
        # Get order time window
        order_start = order.start_datetime
        order_end = order.due_datetime
        
    
        
        # Filter available barges that are free during order time window and ready
        available_barges = [
            b for b in barges.values() 
            #if (self.get_ready_barge(b)is None or self.get_ready_barge(b) < order_end - timedelta(days=4) ) 
            if (self.get_ready_barge(b)is None or self.get_ready_barge(b) < order_start + timedelta(days=2)) 
        ]
        
        # sum the capacity of available barges
        total_capacity = sum(b.capacity for b in available_barges)
        #print(f"AS  Total capacity: {total_capacity}")
        
        stations = TravelHelper._instance.data['stations']
        station_s0 = stations['s0']
        
        # For import orders, sort by distance to carrier
        if order.order_type == TransportType.IMPORT:
            carrier_location = (order.start_object.lat, order.start_object.lng)
            available_barges.sort(key=lambda b:
                 (self.get_river_km_barge(b)  if self.get_water_status_barge(b) == WaterBody.RIVER 
                 else TravelHelper._instance.get_distance_location(carrier_location, self.get_location_barge(b)))
            )
        
        #print(f"Remaining: {remaining_demand} | Available: {len(available_barges)}")
        #barges_ids = [b.barge_id for b in available_barges]
        #print("Barges ids", barges_ids)    

        
        
        # Assign barges until demand is met
        for barge in available_barges:
            if remaining_demand <= 0:
                break
                
            blocation = self.get_location_barge(barge)
            distance = haversine(blocation[0], blocation[1], order.start_object.lat, order.start_object.lng)
            assign_amount = min(barge.capacity, remaining_demand)
            
            # Update barge status and time usage
            #barge.assinged_status = 'assigned'
            barge.current_order = order
            barge.set_load(assign_amount)
            barge.used_start = order_start
            barge.used_end = order_end
            
            assigned_barges.append({
                'barge': barge, 
                'load': assign_amount, 
                'distance': distance,
                'time_window': (order_start, order_end)
            })
            remaining_demand -= assign_amount
                
        return assigned_barges
 
    def assign_barges_to_tugboats(self, order, tugboats, order_assigned_barges):
        assigned_tugboats = []  
        
        for tugboat_id in tugboats:
            tugboat = tugboats[tugboat_id]
            tugboat_ready_time = self.get_ready_time_tugboat(tugboat)
            if order.due_datetime < tugboat_ready_time:
                print("Tugboat is not ready",tugboat_id, order.order_id, order.due_datetime, tugboat_ready_time)  
                continue
            assign_barges_to_tugboat(tugboat, order_assigned_barges)
            if len(tugboat.assigned_barges) != 0:
                assigned_tugboats.append(tugboat)
            if len(tugboat.assigned_barges) == 0:
                #print("Commpleted all barges assignment")
                break
        return assigned_tugboats
    
    
    def update_barge_infos(self, lookup_order_barges, lookup_river_tugboat_results):
        data = self.data
        #for order_id, order_barge_info in lookup_order_barges.items():
            #print(order_barge_info)
            
            
        #print('-------------------------- Tugboat')
        for tugboat_id, results in lookup_river_tugboat_results.items( ):
            exit_datetime = results['data_points'][1]['exit_datetime']
            tugboat = data['tugboats'][tugboat_id]
            max_datetime = self.get_ready_time_tugboat(tugboat)
            for barge in tugboat.assigned_barges:
                barge_info = lookup_order_barges[barge.barge_id]
                barge_info['exit_datetime'] = exit_datetime
                if max_datetime > exit_datetime:
                    max_datetime = exit_datetime
    
    def arrival_step_transport_order(self, order, assigned_tugboats, order_trip = 1):
        time_boat_lates = []
        tugboat_results = []
        arrival_times = []
        for tugboat in assigned_tugboats:
            tugboat_info = self.tugboat_scheule[tugboat.tugboat_id][-1]
            
            collection_time_info = tugboat.calculate_collection_barge_time(tugboat_info, self.barge_scheule)
            travel_info = tugboat.calculate_travel_to_start_object(self.barge_scheule)
            
            station_tugboat_id = self.get_station_id_tugboat(tugboat) 
                                 
            
            station_barge_ids = [ self.get_station_id_barge(b) 
                                 if self.get_station_id_barge(b) is not None else b.barge_id 
                                 for b in tugboat.assigned_barges]
            
            
            # print("DEBUG BAGE COLLECTION INFO", ['travel_steps'])
            # for barge_collect_info in collection_time_info['barge_collect_infos']:
            #     (print( barge_collect_info['barge_id'], barge_collect_info ) 
            #      if len(barge_collect_info['travel_steps']) == 1 else None)

            first_barge_location = collection_time_info['barge_collect_infos'][0]
            tugboat_ready_time = self.get_ready_time_tugboat(tugboat)
            
            
            
            
            start_pos = tugboat_info['station_id'] 
            start_pos = tugboat_info['location'] if start_pos == None else start_pos  
            
            start_location = {
                "ID": "Start",
                'type': "Start",
                'name': "Start at " + start_pos,
                'enter_datetime': tugboat_ready_time,
                'exit_datetime': tugboat_ready_time,
                'distance': 0,
                'time': 0,
                'speed': 0,
                'type_point': 'main_point',
            }
            
            barge_ready_time = tugboat_ready_time + timedelta(minutes=first_barge_location['travel_time']*60)
            barge_ready_time = get_next_quarter_hour(barge_ready_time)
            if barge_ready_time < tugboat_ready_time:
                barge_ready_time = tugboat_ready_time
            barge_location ={
                "ID": "Barge",
                'type': "Barge Collection",
                'name': "Barge Location",
                'enter_datetime': barge_ready_time,
                'exit_datetime': barge_ready_time + timedelta(minutes=collection_time_info['total_time']*60),
                'distance': first_barge_location['travel_distance'],
                'speed': tugboat.max_speed,
                'time': first_barge_location['travel_time'],
                'type_point': 'main_point',
            }
            
            
            
            #if travel_info['travel_distance'] > 50:
                #raise Exception('Not on the sea')
            
            tugboat_order_results = {'tugboat_id': tugboat.tugboat_id, 
                                    "data_points" : [start_location, barge_location]}
            #tugboat_order_results["data_points"].extend(barge_steps)
            
            tugboat_results.append(tugboat_order_results)
            
            travel_total_time = collection_time_info['total_time'] + travel_info['travel_time'] + first_barge_location['travel_time']
        # print(total_time, travel_info)
     
            tugboat_ready_time = self.get_ready_time_tugboat(tugboat)
            arrival_time = tugboat_ready_time + timedelta(minutes=travel_total_time*60)
            arrival_time = get_next_quarter_hour(arrival_time)
            time_lated_start = 0
            
            
            
            if order_trip == 1:
                if arrival_time < order.start_datetime:
                    arrival_time = order.start_datetime
                
                else:
                    time_lated_start = (arrival_time - order.start_datetime).total_seconds() / 3600
            
            
           
          
            
            if order_trip == 1:
                new_barge_location_exit_time = arrival_time - timedelta(minutes=travel_info['travel_time']*60)
                new_barge_location_exit_time = get_previous_quarter_hour(new_barge_location_exit_time)
                new_barge_location_enter_time = arrival_time - timedelta(minutes=(collection_time_info['total_time'] + travel_info['travel_time'])*60)
                new_barge_location_enter_time = get_previous_quarter_hour(new_barge_location_enter_time)
                new_start_location_exit_time = arrival_time - timedelta(minutes=travel_total_time*60)
                new_start_location_exit_time = get_previous_quarter_hour(new_start_location_exit_time)
                
            else:
                tugboat_ready_time = self.get_ready_time_tugboat(tugboat)
                new_start_location_exit_time = get_next_quarter_hour(tugboat_ready_time)
                new_barge_location_enter_time = new_start_location_exit_time
                new_barge_location_exit_time = new_barge_location_enter_time + timedelta(minutes=(collection_time_info['total_time'])*60)
                new_barge_location_exit_time = get_next_quarter_hour(new_barge_location_exit_time)
            
            
            time_boat_lates.append(time_lated_start)
            arrival_times.append(arrival_time)
            
            #print("Check ready time CCCCCC", tugboat.tugboat_id, tugboat_ready_time, arrival_time, new_start_location_exit_time) if tugboat.tugboat_id == 'tbs1' else None
            
            barge_location['enter_datetime'] = new_barge_location_enter_time
            barge_location['exit_datetime'] = new_barge_location_exit_time
            
            # print("arrival_time CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC", tugboat.tugboat_id, 
            #       tugboat_ready_time, arrival_time, start_location['enter_datetime'], 
            #       new_start_location_exit_time, travel_total_time)
            start_location['enter_datetime'] = new_start_location_exit_time
            start_location['exit_datetime'] = new_start_location_exit_time
            barge_location['order_distance'] = travel_info['travel_distance']
            barge_location['order_time'] = travel_info['travel_time']
            barge_location['barge_speed'] = travel_info['speed']
            barge_location['order_arrival_time'] = arrival_time
            
            #print("Barge collection infomations vvvvvvvvvvvvv")
            barge_steps = []
            start_travel_barge = barge_location['enter_datetime']
            start_station_id = station_tugboat_id
            
            for i, collection_info in enumerate(collection_time_info['barge_collect_infos']):# collection_time_info['barge_collect_infos'][:]:
                
                barge_id = collection_info['barge_id']
                barge = TravelHelper._instance.data['barges'][barge_id]
                barge_ready_time = self.get_ready_barge(barge)
                if barge_ready_time > start_travel_barge:
                    start_travel_barge = barge_ready_time
                
                
                finish_barge_time = start_travel_barge + timedelta(minutes=(collection_info['travel_time'] + collection_info['setup_time'])*60)
                #print(collection_info)
                #finish_barge_time = get_next_quarter_hour(finish_barge_time)
                #if start_station_id == station_barge_ids[i]:
                #print(collection_info)
                start_barge_station_id = collection_info['travel_steps'][0]['start_id']
                end_barge_station_id = collection_info['travel_steps'][-1]['end_id']
                
                name = "Collecting Barge - " + collection_info['barge_id'] + " - " 
                name += f"({start_barge_station_id} to {str(end_barge_station_id)})"
                # if 'nan' in name and tugboat.tugboat_id == 'tbs4' and order.order_id == 'o3' and i == 1:
                #     print("##################################################### ", tugboat.tugboat_id, start_barge_station_id, end_barge_station_id)
                #     for j, collection_infov in enumerate(collection_time_info['barge_collect_infos']):
                #         print(j, collection_infov)
                
                #name += " - " + station_barge_ids[i]
                barge_step ={
                    "ID": "Barge",
                    'type': "Barge Step Collection",
                    'name': name,
                    'enter_datetime': start_travel_barge,
                    'exit_datetime': finish_barge_time,
                    'distance': collection_info['travel_distance'],
                    'speed': 0 if collection_info['travel_time'] == 0 else collection_info['travel_distance']/collection_info['travel_time'],
                    'time': collection_info['travel_time'],
                    'type_point': 'travel_point',
                }
                start_station_id = station_barge_ids[i]
                start_travel_barge = finish_barge_time
                barge_location['exit_datetime'] = max(barge_location['exit_datetime'], finish_barge_time)
                #print(barge_step)
                barge_steps.append(barge_step)
            
            tugboat_order_results["data_points"].extend(barge_steps)
        #print("Time late start:", time_boat_lates)
        #print("Arrival times:", arrival_times)
        
        return tugboat_results, time_boat_lates

    def arrival_step_river_transport(self, order, river_tugboats, lookup_barge_infos, sea_tugboat_results, round_order_trip):
        """
        Calculate timing for river tugboats collecting barges from sea tugboats
        Args:
            river_tugboats: List of river tugboats with assigned barges
            appointment_location: Location object for barge handoff
        Returns:
            tugboat_results: List of timeline data for each river tugboat
            time_boat_lates: List of scheduling delays
        """
        time_boat_lates = []
        tugboat_results = []
        arrival_times = []
        
        for tugboat in river_tugboats:
            tugboat_info = self.tugboat_scheule[tugboat.tugboat_id][-1]
            #if order.order_id == 'o1':
            print("Tugboat Riverrrrrrr ##########################################################")
            #print(tugboat_info)
            
            
            lookup_steps = {}
            for barge in tugboat.assigned_barges:
                #print("barge", barge.barge_id, order.order_id)
                barge_release_step = self._find_barge_release_step(sea_tugboat_results, barge.barge_id)
                lookup_steps[barge.barge_id] = barge_release_step
                #print(self.barge_scheule[barge.barge_id][-1])
                
            
                
            # for barge in tugboat.assigned_barges:
            #     barge_info = self.barge_scheule[barge.barge_id][-1]
            #     info = {
            #         'barge_id': barge.barge_id,
            #         'order_id': None,
            #         'start_datetime': barge_info['end_datetime'],
            #         'end_datetime': barge_info['end_datetime'],
            #         'river_km': barge_info['river_km'],
            #         'water_status': barge_info['water_status'], 
            #         'location': barge_info['location'],
            #         'station_id': barge_info['station_id'],
                        
            #     }
                
                
            #     self.barge_scheule[barge.barge_id].append(info)
                
            collection_time_info = tugboat.calculate_collection_barge_time(tugboat_info, self.barge_scheule)
            tugboat_info = self.tugboat_scheule[tugboat.tugboat_id][-1]
            
            tugboat_ready_time = self.get_ready_time_tugboat(tugboat)
            
            start_station = tugboat_info['station_id']
            
            # Create start location data point
            start_location = {
                "ID": "Start",
                'type': "Start",
                'name': "River Start at " + start_station,
                'enter_datetime': tugboat_ready_time,
                'exit_datetime': tugboat_ready_time,
                'distance': 0,
                'time': 0,
                'speed': 0,
                'type_point': 'main_point',
            }
            #print(collection_time_info)
            #print(  collection_time_info['barge_collect_infos'])
            first_barge_location = collection_time_info['barge_collect_infos'][0]
            
            # for collect_info in collection_time_info['barge_collect_infos']:
            #     #barge_id = collect_info['barge_id']
            #     print(collect_info)
            #     print(collect_info['travel_time'], collect_info['travel_distance'], collect_info['start_status'], collect_info['end_status'])
            
        #     # Calculate barge location timing
            barge_ready_time = tugboat_ready_time + timedelta(minutes=first_barge_location['travel_time']*60)
            barge_id = first_barge_location['barge_id']
            barge_info = lookup_barge_infos[barge_id]
            appointment_station =TravelHelper._instance.data['stations'][  barge_info['appointment_station']]
            barge_location = {
                "ID": appointment_station.station_id,
                'type': "Barge Change",
                'name': "Change at " + appointment_station.name,
                'enter_datetime': barge_ready_time,
                'exit_datetime': (barge_ready_time +
                 timedelta(minutes=collection_time_info['total_time']*60)),
                'distance': first_barge_location['travel_distance'],
                'speed': tugboat.max_speed,
                'time': first_barge_location['travel_time'],
                'type_point': 'main_point',
            }

            
            # Create result structure
            tugboat_result = {
                'tugboat_id': tugboat.tugboat_id,
                'data_points': [start_location, barge_location]
            }
            
        
            max_ready_datetime = self.get_max_datetime(tugboat, lookup_barge_infos)    
            #print("############# max_ready_datetime", max_ready_datetime)
            
        #     # Calculate total time and potential delays
        #     total_time = collection_time_info['total_time'] + travel_info['travel_time']
        #     arrival_time = tugboat.ready_time + timedelta(minutes=total_time*60)
            
        #     # Adjust for quarter-hour intervals
        #     arrival_time = get_previous_quarter_hour(arrival_time)
            
        #     # Calculate time late if any
        #     time_lated = max(0, (arrival_time - appointment_location.expected_arrival).total_seconds() / 3600)
            
        #     # Store results
            tugboat_results.append(tugboat_result)
            
            travel_total_time = first_barge_location['travel_time']
            
            start_time_needed = max_ready_datetime - timedelta(minutes=travel_total_time*60)
            start_time_needed = get_previous_quarter_hour(start_time_needed)
            arrival_time_needed = max_ready_datetime
            time_lated_start = 0
            
            if tugboat_ready_time > start_time_needed:
                arrival_time = tugboat_ready_time + timedelta(minutes=travel_total_time*60)
                time_lated_start = (tugboat_ready_time - start_time_needed).total_seconds() / 3600
                start_time_needed = tugboat_ready_time
            else:
                arrival_time = arrival_time_needed
            
            
            
            time_boat_lates.append(time_lated_start)
            arrival_times.append(arrival_time)
            
            
            collection_barge_time = collection_time_info['total_time'] - first_barge_location['travel_time']
        
            
            new_barge_location_enter_time = get_previous_quarter_hour(arrival_time)
            new_barge_location_exit_time = new_barge_location_enter_time + timedelta(minutes=collection_barge_time*60)
            #print(new_barge_location_exit_time, collection_barge_time*60)
            new_barge_location_exit_time = get_next_quarter_hour(new_barge_location_exit_time)
            
            new_start_location_exit_time = new_barge_location_enter_time - timedelta(minutes=collection_barge_time*60)
            new_start_location_exit_time = get_previous_quarter_hour(new_start_location_exit_time)
            
            print("Debug Tugboat Ready time 000000000000000000000000000", tugboat_ready_time) if tugboat.tugboat_id == 'tbr2' and order.order_id == 'o3'    else None
            
            
        #     # Update data points with calculated times
            barge_location['enter_datetime'] = new_barge_location_enter_time
            barge_location['exit_datetime'] = new_barge_location_exit_time
            start_location['enter_datetime'] = new_start_location_exit_time
            start_location['exit_datetime'] = new_start_location_exit_time
            
            if tugboat_ready_time > new_start_location_exit_time:
                start_location['enter_datetime'] = get_next_quarter_hour(tugboat_ready_time)
                start_location['exit_datetime'] = get_next_quarter_hour(tugboat_ready_time)
                barge_location['enter_datetime'] = tugboat_ready_time + timedelta(minutes=first_barge_location['travel_time']*60)
                barge_location['enter_datetime']  = get_next_quarter_hour(barge_location['enter_datetime'])
                
                
                
            
            
            # Add additional metrics
            #barge_location['order_distance'] = travel_info['travel_distance']
            #barge_location['order_time'] = travel_info['travel_time']
            #barge_location['barge_speed'] = travel_info['speed']
            #barge_location['order_arrival_time'] = arrival_time
        
        #print("River Tugboat Time Lates:", time_boat_lates)
        #print("River Tugboat Arrival Times:", arrival_times)
            barge_steps = []
            start_travel_barge = barge_location['enter_datetime']
            for collection_info in collection_time_info['barge_collect_infos'][:]:
                if start_travel_barge < lookup_steps[collection_info['barge_id']]['exit_datetime']:
                    start_travel_barge = lookup_steps[collection_info['barge_id']]['exit_datetime']    
                
                finish_barge_time = start_travel_barge + timedelta(minutes=(collection_info['setup_time'])*60)
                
                start_barge_station_id = collection_info['travel_steps'][0]['start_id']
                end_barge_station_id = collection_info['travel_steps'][-1]['end_id']
                
                name = "Change Barge - " + collection_info['barge_id'] + " - " 
                name += f"({start_barge_station_id} to {str(end_barge_station_id)})"
                
                
                
                #print(collection_info)
                barge_step ={
                    "ID": "Barge",
                    'type': "Barge Change Collection",
                    'name': name,
                    'enter_datetime': start_travel_barge,
                    'exit_datetime': finish_barge_time,
                    'distance': collection_info['travel_distance'],
                    'speed': 0 if collection_info['travel_time'] == 0 else collection_info['travel_distance']/collection_info['travel_time'],
                    'time': collection_info['travel_time'],
                    'type_point': 'travel_point',
                }
                start_travel_barge = finish_barge_time
                #print(barge_step)
                barge_steps.append(barge_step)
            barge_location['exit_datetime'] = finish_barge_time
            tugboat_result["data_points"].extend(barge_steps)
            
        
        return tugboat_results, time_boat_lates
    
    def arrival_step_travel_empty_barges(self, order, river_tugboats, appointment_infos):
        time_boat_lates = []
        tugboat_results = []
        arrival_times = []
        data = self.data
        for tugboat in river_tugboats:
            tugboat_info = self.tugboat_scheule[tugboat.tugboat_id][-1]
            
            collection_time_info = tugboat.calculate_collection_barge_time(tugboat_info, self.barge_scheule)
            
            #location = self.get_location_tugboat(tugboat)
            appointment_info = appointment_infos[tugboat.tugboat_id]
            
            river_station = TravelHelper.get_next_river_station(self, TransportType.EXPORT, tugboat_info['river_km'])
            end_station = data['stations'][appointment_info['appointment_station']]
            
            
            
            
            first_barge_location = collection_time_info['barge_collect_infos'][0]
            tugboat_ready_time = self.get_ready_time_tugboat(tugboat)
            #print("Check ready time CC", tugboat.tugboat_id, tugboat_ready_time)
            start_location = {
                "ID": "Start",
                'type': "Start",
                'name': f"Start Collect Barge River Down From {river_station.name} To {end_station.name}",
                'enter_datetime': tugboat_ready_time,
                'exit_datetime': tugboat_ready_time,
                'distance': 0,
                'time': 0,
                'speed': 0,
                'type_point': 'main_point',
            }
            
            barge_ready_time = get_next_quarter_hour( tugboat_ready_time +
                                                     timedelta(minutes=first_barge_location['travel_time']*60))
            exit_barge_time = get_next_quarter_hour(barge_ready_time + timedelta(minutes=collection_time_info['total_time']*60))
            barge_location ={
                "ID": "Barge",
                'type': "Barge Collection",
                'name': "Barge Location",
                'enter_datetime': barge_ready_time,
                'exit_datetime': exit_barge_time,
                'distance': first_barge_location['travel_distance'],
                'speed': tugboat.max_speed,
                'time': first_barge_location['travel_time'],
                'type_point': 'main_point',
            }
            
            
   
            tugboat_order_results = {'tugboat_id': tugboat.tugboat_id, 
                                    "data_points" : [start_location, barge_location]}
     
            
            tugboat_results.append(tugboat_order_results)
            
            
            #print("Barge collection infomations vvvvvvvvvvvvv")
            barge_steps = []
            start_travel_barge = barge_location['enter_datetime']
            for collection_info in collection_time_info['barge_collect_infos'][:]:
                #print(collection_info)
                barge = self.data['barges'][collection_info['barge_id']]
                barge_ready_time = self.get_ready_barge(barge)
                if barge_ready_time > start_travel_barge:
                    start_travel_barge = barge_ready_time
                finish_barge_time = start_travel_barge + timedelta(minutes=(collection_info['travel_time'] + collection_info['setup_time'])*60)
                
                
                barge_step ={
                    "ID": "Barge",
                    'type': "Barge Step Collection",
                    'name': "Collecting Barge - " + collection_info['barge_id'],
                    'enter_datetime': start_travel_barge,
                    'exit_datetime': finish_barge_time,
                    'distance': collection_info['travel_distance'],
                    'speed': 0 if collection_info['travel_time'] == 0 else collection_info['travel_distance']/collection_info['travel_time'],
                    'time': collection_info['travel_time'],
                    'type_point': 'travel_point',
                }
                start_travel_barge = finish_barge_time
                #print(collection_info)
                barge_steps.append(barge_step)
            
            tugboat_order_results["data_points"].extend(barge_steps)
            
            start_info = {'station':river_station, 'location': (river_station.lat, river_station.lng)}
            end_info = {'station':data['stations'][appointment_info['appointment_station']], 'location': (end_station.lat, end_station.lng)}
            
            
            travel_river_info =  tugboat.calculate_travel_start_to_end_river_location(start_info, end_info, start_status=WaterBody.RIVER, end_status= WaterBody.RIVER)
            #print("River info", river_station.km, travel_river_info)
            
    
            arrival_datetime = get_next_quarter_hour( exit_barge_time + timedelta(minutes=travel_river_info['travel_time']*60))
            exit_appointment_time = get_next_quarter_hour(arrival_datetime + 
                                                          timedelta(minutes=len(tugboat.assigned_barges)*config_problem.BARGE_SETUP_MINUTES))
            
            # print(river_station.name)
            # print(appointment_info['appointment_station'])
            appoinment_location ={
                "ID": order.start_object.order_id,
                'type': "Destination Barge",
                'name': f"Appointment From {river_station.name} To {appointment_info['appointment_station']}" ,
                'enter_datetime': arrival_datetime,
                'exit_datetime':arrival_datetime,
                'distance': travel_river_info['travel_distance'],
                'time': travel_river_info['travel_time'],
                'speed': travel_river_info['speed'],
                'type_point': 'main_point'
            }
            tugboat_order_results['data_points'].append(appoinment_location) # add result data points
            trave_steps = generate_travel_steps(arrival_datetime, travel_river_info)
            tugboat_order_results['data_points'].extend(trave_steps)
            
            max_exit_datetime = max(trave_steps, key=lambda x: x['exit_datetime'])['exit_datetime']
            appoinment_location['exit_datetime'] = max_exit_datetime
            
            barge_ids = [barge.barge_id for barge in tugboat.assigned_barges]
            time_release_barges = config_problem.BARGE_RELEASE_MINUTES*len(tugboat.assigned_barges)
            release_barges_location ={
                "ID": appointment_info['appointment_station'],
                'type': "Barge Release",
                'name': "Release Barges (" + " - ".join(barge_ids) + ")",
                'enter_datetime': appoinment_location['exit_datetime'],
                'exit_datetime':appoinment_location['exit_datetime'] + timedelta(minutes=time_release_barges),
                'distance': 0,
                'speed': 0,
                'time': time_release_barges,
                'type_point': 'main_point'
            }
            tugboat_order_results['data_points'].append(release_barges_location)
            release_steps = generate_release_steps(release_barges_location['enter_datetime'], barge_ids)
            tugboat_order_results['data_points'].extend(release_steps)
            
            
            appointment_station = self.data['stations'][appointment_info['appointment_station']]
            
            for i, release_step in enumerate(release_steps):
                self.update_single_barge_scheule(order, barge_ids[i], release_step['enter_datetime'], release_step['exit_datetime'], appointment_station.km, 
                                             appointment_station.water_type, (appointment_station.lat, appointment_station.lng), appointment_station.station_id)
                #print("Update barge schedule ##################### ", appointment_station.station_id, self.barge_scheule[barge_ids[i]][-1])
            
        #print("Time late start:", time_boat_lates)
        print("Arrival times:", arrival_times)
        
        return tugboat_results, time_boat_lates
    
    def get_max_datetime(self, tugboat, lookup_barge_infos):
        max_ready_barge_datetime = self.get_ready_time_tugboat(tugboat)
        for barge in tugboat.assigned_barges:
            barge_id = barge.barge_id
            barge_info = lookup_barge_infos[barge_id]
            enter_datetime = barge_info["arrival_appointment_datetime"]
            if enter_datetime > max_ready_barge_datetime:
                max_ready_barge_datetime = enter_datetime
        return max_ready_barge_datetime
    
    def _find_barge_release_step(self, tugboat_results, barge_id):
        for tugboat_id, tugboat_result in tugboat_results.items():
            for j in range(10):
                step = tugboat_result['data_points'][-1-j]
        #        print(step)
                if barge_id in step['name']:
                    return step
                if "Releasing" not in step['name']:
                    break
        raise Exception("Barge release step not found")
    
    def _find_tugboat_result(self, barge_id, tugboat_results):
        tugboat = None
        for tugboat_id, results in tugboat_results.items():
            tugboat = self.data['tugboats'][tugboat_id]
            isFound = False
            for barge in tugboat.assigned_barges:
                if barge.barge_id == barge_id:
                    isFound = True
                    break
            if isFound:
                break
        if tugboat == None: raise Exception("Tugboat not found")
        return tugboat_results[tugboat.tugboat_id]
    
    def __update_tugboat_scheule(self, order, lookup_tugboat_results):
        data = self.data
        for tugboat_id, tugboat_result in lookup_tugboat_results.items():
            tugboat = data['tugboats'][tugboat_id]
            #end_point = tugboat_result['data_points'][-1]
            end_point = next((point for point in reversed(tugboat_result['data_points']) if point['type_point'] == "main_point"), None)
            
            station_last = data['stations'][end_point['ID']]
            # Ensure schedule continuity by using previous end time as new start
            prev_end = self.tugboat_scheule[tugboat_id][-1]['end_datetime']
            #print("DEGUGGGGGGGGGGGGGGGGGGGG")
           
            #for point in tugboat_result['data_points']:
                #print(point)
            #print(tugboat_id, prev_end, end_point['enter_datetime'], end_point['exit_datetime'])
            new_start = max(end_point['enter_datetime'], prev_end)
            
            info = {
                'tugboat_id': tugboat.tugboat_id,
                'order_id': order.order_id,
                'start_datetime': new_start,
                'end_datetime': max(end_point['exit_datetime'], new_start),
                'barge_infos': [],
                'river_km': station_last.km,
                'water_status': station_last.water_type , 
                'location': (station_last.lat, station_last.lng),
                'station_id': station_last.station_id,
            }
            
            tugboat._lat = station_last.lat 
            tugboat._lng = station_last.lng
            tugboat._km = station_last.km
            
            
            for barge in tugboat.assigned_barges:
                info['barge_infos'].append({
                    'barge_id': barge.barge_id,
                    'load' : barge.get_load(True),
                })
            
            self.tugboat_scheule[tugboat_id].append(info)
            #if tugboat_id== 'tbs1' :
                #print(order.order_id, info['barge_infos'])
            #print("tugboat_scheule result",tugboat_id,  len( self.tugboat_scheule[tugboat_id]))
    
    def update_shedule(self, order, lookup_order_barges, 
                       lookup_sea_tugboat_results, lookup_river_tugboat_results):
        data = self.data
    
        for order_id, order_barge_info in lookup_order_barges.items():
            barge_id = order_barge_info['barge_id']
            
            start_tugboat_result = self._find_tugboat_result(barge_id, lookup_sea_tugboat_results)
            end_tugboat_result = self._find_tugboat_result(barge_id, lookup_river_tugboat_results)
            
            data_point_start = start_tugboat_result['data_points'][1]
            data_point_end = next((point for point in reversed(end_tugboat_result['data_points']) if point['type_point'] == "main_point" ), None)
            barge_end_loader = next((point for point in reversed(end_tugboat_result['data_points']) if barge_id in point['name'] and point['type_point'] == "Loader-Customer" ), None)
                
            #data_point_end = end_tugboat_result['data_points'][-1]
            station_last = data['stations'][data_point_end['ID']]
            
            # Ensure barge schedule continuity by using max of previous end time and new start
            prev_barge_end = self.barge_scheule[barge_id][-1]['end_datetime']
            new_barge_start = max(prev_barge_end, data_point_start['enter_datetime'])
            
            info = {
                'barge_id': barge_id,
                'order_id': order.order_id,
                'start_datetime': new_barge_start,
                'end_datetime': max(data_point_end['exit_datetime'], new_barge_start),
                'river_km': station_last.km,
                'water_status': station_last.water_type, 
                'location': (station_last.lat, station_last.lng),
                'station_id':data_point_end['ID'],
            }
            
            
            self.barge_scheule[barge_id].append(info)
       
        self.__update_tugboat_scheule(order, lookup_sea_tugboat_results)
        self.__update_tugboat_scheule(order, lookup_river_tugboat_results)
        
        
        #for tugboat_id, tugboat_scedule in self.tugboat_scheule.items():
            #print(tugboat_id, tugboat_scedule[-1])
    
    def update_single_barge_scheule(self, order, barge_id, start_datetime, end_datetime, river_km, water_status, location, station_id):
        info = {
                'barge_id': barge_id,
                'order_id': order.order_id,
                'start_datetime': start_datetime,
                'end_datetime': end_datetime,
                'river_km': river_km,
                'water_status': water_status, 
                'location': location,
                'station_id':station_id,
            }
        self.barge_scheule[barge_id].append(info)
            
    
    
    def update_shedule_bring_down_barges(self, order, lookup_order_barges, lookup_tugboat_results):
        data = self.data
    
        for order_id, order_barge_info in lookup_order_barges.items():
            barge_id = order_barge_info['barge_id']
            
            tugboat_result = self._find_tugboat_result(barge_id, lookup_tugboat_results)
            
            data_point_start = tugboat_result['data_points'][1]
            data_point_end = next((point for point in reversed(tugboat_result['data_points']) if point['type_point'] == "main_point" ), None)
            barge_end_loader = next((point for point in reversed(tugboat_result['data_points']) if barge_id in point['name'] and point['type_point'] == "Loader-Customer" ), None)
                
            station_last = data['stations'][data_point_end['ID']]
            
            # Ensure barge schedule continuity by using max of previous end time and new start
            prev_barge_end = self.barge_scheule[barge_id][-1]['end_datetime']
            new_barge_start = max(prev_barge_end, data_point_start['enter_datetime'])
            
            self.update_single_barge_scheule(order, barge_id, new_barge_start, max(data_point_end['exit_datetime'], new_barge_start), station_last.km, 
                                             station_last.water_type, (station_last.lat, station_last.lng), data_point_end['ID'])
       
        self.__update_tugboat_scheule(order, lookup_tugboat_results)
    
    def _reset_all_tugboats(self):
        tugboats = self.data['tugboats']
        for tugboat in tugboats.values():
            tugboat.reset()
              
    def _extend_update_tugboat_results(self, tugboat_results, order_trip):
        for tugboat_result in tugboat_results:
            for data_point in tugboat_result['data_points']:
                tugboat_id = tugboat_result['tugboat_id']
                data_point['order_trip'] = order_trip
                
                data_point['total_load'] = sum([barge.get_load(True) for barge in self.data['tugboats'][tugboat_id].assigned_barges])
                data_point['barge_ids'] = [barge.barge_id for barge in self.data['tugboats'][tugboat_id].assigned_barges]
                data_point['barge_ids'] = ','.join([str(barge_id) for barge_id in data_point['barge_ids']])
                
                if 'type_point' in data_point:
                    if data_point['type_point'] == 'loading_point':
                        barge_id = data_point['name'].split(' - ')[1]
                        search_barge = next((barge for barge in self.data['tugboats'][tugboat_id].assigned_barges if barge.barge_id == barge_id), None)
                 
                        data_point['barge_ids'] = barge_id
                        data_point['total_load'] = search_barge.get_load(True)
                        
                        
                    continue
                else:
                    raise Exception("DONOT Have type point")
                
                
                
                
                
        # if len(temp_tugboat_results) == 0:
        #     temp_tugboat_results.extend(tugboat_results)
        # else:
        #     for tugboat_result in tugboat_results:
        #         isFound = False
        #         tugboat_result['order_trip'] = order_trip
        #         for temp_tugboat_result in temp_tugboat_results:
        #             if temp_tugboat_result['tugboat_id'] == tugboat_result['tugboat_id']:
        #                 isFound = True
        #                 temp_tugboat_result['data_points'].extend(tugboat_result['data_points']) # add result data points
        #                 break
        #         if not isFound:
        #             temp_tugboat_results.append(tugboat_result)
                    
    def _bring_barge_travel_import(self, order, bring_down_river_barges):
        river_tugboats =  self.data['river_tugboats'] 
        print("BRING_DOWN -------------------------------")
        tugboat_results = []
        while len(bring_down_river_barges) > 0:
            print("Bring down barge remain:", len(bring_down_river_barges))
            assigned_tugboats = self.assign_barges_to_tugboats(order, river_tugboats, bring_down_river_barges)
            print("Assigned tugboats:", len(assigned_tugboats))
            for tugboat in assigned_tugboats:
                print(tugboat.tugboat_id, [barge.barge_id for barge in tugboat.assigned_barges])
            appointment_info = {}
            for i in range(len(assigned_tugboats)):
                tugboat = assigned_tugboats[i]
                tugboat_id = tugboat.tugboat_id
                appointment_info[tugboat_id] = {
                    'river_tugboat': assigned_tugboats[i],
                    'tugboat_id': tugboat_id,
                    'appointment_station': 's2',
                    'meeting_time': None
                }
            
            #[print(tugboat.tugboat_id, [barge.barge_id for barge in tugboat.assigned_barges]) for tugboat in assigned_tugboats]
            river_down_barge_tugboat_results, late_time = self.arrival_step_travel_empty_barges(order, assigned_tugboats, appointment_info)
            print("Tugboat river results:", late_time)
            tugboat_results.extend(river_down_barge_tugboat_results)
            for tugboat_result in river_down_barge_tugboat_results:
                print(tugboat_result['tugboat_id'])
                df = pd.DataFrame(tugboat_result['data_points'])
                print(df)
            
        print("END_DOWN -------------------------------")
        return tugboat_results

    def __create_active_cranes(self, order, schedule_results):
        active_cranes = []
        crane_last_time_lookup = {}
        for schedule_result in schedule_results:
            for crane_schedule in schedule_result['crane_schedule']:
                #print(crane_schedule)  if order.order_id == 'o1' else None
                crane_last_time_lookup[crane_schedule['crane_id']] = crane_schedule['crane_schedule']
            #print()
        #print("Total load: ", total_load, order.demand
        for i in range(7):
            rate = order.get_crane_rate(f'cr{i+1}')
            key = f'cr{i+1}'
            if rate > 0:
                active_cranes.append({
                    'crane_id': f'cr{i+1}',
                    'rate': rate,
                    'time_ready':  crane_last_time_lookup[key] + 0.25 if key   in crane_last_time_lookup else order.get_crane_ready_time(f'cr{i+1}'),
                    'assigned_product': 0
                })
        return active_cranes
    
    def __create_active_loadings(self, order, schedule_results):
        active_loadings = []
        loader_last_time_lookup = {}
        for schedule_result in schedule_results:
            for loader_schedule in schedule_result['loader_schedule']:
                loader_last_time_lookup[loader_schedule['loader_id']] = loader_schedule['loader_schedule']
        #print(loader_last_time_lookup, schedule_results)
        for i in range(1):
            rate = order.loading_rate
            key = f'ld{i+1}'
            if rate > 0:
                active_loadings.append({
                    'loader_id': f'ld{i+1}',
                    'rate': rate,
                    'time_ready':  loader_last_time_lookup[key] + 0.25 if key   in loader_last_time_lookup else loader_last_time_lookup[key],
                    'assigned_product': 0
                })
        return active_loadings
    
    def __init_active_cranes(self, order):
        """
        Initialize active cranes for the order.
        
        Args:
            order: The order object containing crane information.
        
        Returns:
            active_cranes: List of active cranes initialized for the order.
        """
        active_cranes_infos = []
        active_cranes = []
        for i in range(7):
            rate = order.get_crane_rate(f'cr{i+1}')
            if rate > 0:
                active_cranes.append({
                    'crane_id': f'cr{i+1}',
                    'rate': rate,
                    'time_ready':  order.get_crane_ready_time(f'cr{i+1}'),
                    'assigned_product': 0
                })
        active_cranes_infos.append(active_cranes)
        
        active_loadings_infos = []
        active_loadings = []
        for i in range(1):
            rate = order.loading_rate
            if rate > 0:
                active_loadings.append({
                    'loader_id': f'ld{i+1}',
                    'rate': rate,
                    'time_ready':  0,
                    'assigned_product': 0
                })
        active_loadings_infos.append(active_loadings)
        return active_cranes_infos, active_loadings_infos

    def travel_import(self, order):
        data = self.data
        orders = data['orders']
        barges = data['barges']
        stations = data['stations']
        
        assigned_barge_infos = self.assign_barges_to_single_order( order, barges)
        based_brage_ids = [barge_info['barge'].barge_id for barge_info in assigned_barge_infos]
        assigned_barges_print = [(barge_info['barge'].barge_id, barge_info['barge'].get_load(is_only_load=True)) for barge_info in assigned_barge_infos]
        total_load = sum(barge_info['barge'].get_load(is_only_load=True) for barge_info in assigned_barge_infos)
        #print(assigned_barges_print)
        #print("Assignment assigned_barge_infos GGGGGGGGGGGGGGGG:", len(assigned_barge_infos))
        #print('Total load: ', total_load, order.demand)
        
        sea_tugboats =  data['sea_tugboats'] 
        all_assigned_barges = [barge_info['barge'] for barge_info in assigned_barge_infos]
        temp_river_assigned_tugboats = []
        temp_sea_assigned_tugboats = []
        temp_river_tugboat_results = []
        temp_sea_tugboat_results = []
        round_trip_order = 1
        
        
        debug_barges = {}
        for barge in all_assigned_barges:
            km = self.get_river_km_barge(barge)
            debug_barges[barge.barge_id] = {'barge_id': barge.barge_id, 'before_km': km}
            if km > config_problem.RIVER_KM:
                print(barge.barge_id, km)
            
        # travel barge from top river to bottom river
        # filter barges to bring down river
        bring_down_river_barges = []
        save_load = {}
        for barge in all_assigned_barges:
            if self.get_river_km_barge(barge) > config_problem.RIVER_KM:
                save_load[barge.barge_id] = barge.get_load(is_only_load=True)
                barge.set_load(500)
                bring_down_river_barges.append(barge)
                continue
            
        #print("DEBUG_BARGE", order.order_id, len(all_assigned_barges), len(bring_down_river_barges))
        
        tugboat_results = self._bring_barge_travel_import(order, bring_down_river_barges)
        lookup_tugboat_results = {tugboat_result['tugboat_id']: tugboat_result for tugboat_result in tugboat_results}
        
        order_barges, lookup_order_barges = order_barges_from_arrival_tugboats(data, lookup_tugboat_results)
        self.update_shedule_bring_down_barges(order, lookup_order_barges, lookup_tugboat_results)  
        self._extend_update_tugboat_results(tugboat_results, 0)
        temp_river_tugboat_results.extend(tugboat_results)
        self._reset_all_tugboats()
        
        for barge in all_assigned_barges:
            if barge.barge_id in save_load.keys():
                barge.set_load(save_load[barge.barge_id])
        
        
        
        active_cranes_infos, active_loadings_infos = self.__init_active_cranes(order)
        first_arrival_customer_datetime = None
        
        while len(all_assigned_barges) > 0:
            print("Rotation barge remain:", len(all_assigned_barges))
            # for tugboat_id, tugboat in sea_tugboats.items():
            #     print(tugboat_id, self.get_ready_time_tugboat(tugboat))
            assigned_tugboats = self.assign_barges_to_tugboats(order, sea_tugboats, all_assigned_barges)
            
            
            if len(assigned_tugboats) == 0:
                raise Exception("No tugboat found for order: " + str(order.order_id), len(all_assigned_barges), len(temp_sea_tugboat_results))
                #print("Order: {} No tugboat found".format(order.order_id))
                break
            
            Total_load_barges = 0
            boat_brage_ids= []
            boat_load_weights = []
            #total_load = sum(barge_info['barge'].get_load(is_only_load=True) for barge_info in assigned_barge_infos)
            for tugboat in assigned_tugboats:
                load_barges = [b.get_load(is_only_load=True) for b in tugboat.assigned_barges]
                boat_load_weights.extend(load_barges)
                boat_brage_ids.extend([b.barge_id for b in tugboat.assigned_barges])
                #print(f"Assigning barges to Tugboat XX {tugboat.tugboat_id}... {load_barges} barges: {sum(load_barges)}")
                Total_load_barges += sum(load_barges)
            
            #print("Before", based_brage_ids)
            #print("After", boat_brage_ids)
           #print("After", boat_load_weights)
            tugboat_results, late_time = self.arrival_step_transport_order(order, assigned_tugboats, order_trip=round_trip_order)
            #print('XXXXXXXXXXXXXXX Len sea Tugbaots' , round_trip_order, len(assigned_tugboats), len(all_assigned_barges), Total_load_barges)
            total_load = 0
            barge_ids = []
            for tugboat in assigned_tugboats:
                load_barges = [b.get_load(is_only_load=True) for b in tugboat.assigned_barges]
                barge_ids.extend([b.barge_id for b in tugboat.assigned_barges])
                #print(f"Assigning barges to Tugboat XX {tugboat.tugboat_id}... {load_barges} barges: {sum(load_barges)}")
                total_load += sum(load_barges) 
                
            
            #print('MM Total load: ', total_load, order.demand)
            #print("barge_ids", barge_ids)
            active_cranes = active_cranes_infos[-1]
            schedule_results = schedule_carrier_order_tugboats(order, assigned_tugboats, active_cranes, late_time)
            #print(schedule_results) if order.order_id == 'o1' else None
            
            active_cranes = self.__create_active_cranes(order, schedule_results)
            active_cranes_infos.append(active_cranes)

            lookup_sea_tugboat_results = {result['tugboat_id']: result for result in tugboat_results}
            lookup_sea_schedule_results = {result['tugboat_schedule']['tugboat_id']: result for result in schedule_results}
            
            
            appointment_info = {}
            for i in range(len(tugboat_results)):
                tugboat = tugboat_results[i]
                tugboat_id = tugboat['tugboat_id']
                appointment_info[tugboat_id] = {
                    'sea_tugboat': assigned_tugboats[i],
                    'tugboat_id': tugboat_id,
                    'appointment_station': 's2',
                    'meeting_time': None
                }
            travel_appointment_import(self, order, lookup_sea_schedule_results, 
                                    lookup_sea_tugboat_results, appointment_info, round_trip_order    )
            
            
            
            
            
            order_barges, lookup_order_barges = order_barges_from_arrival_tugboats(data, lookup_sea_tugboat_results)
            #print("----------------------------------------------------")
            #for tugboat in assigned_tugboats:
                #print(tugboat)
                
            
            for tugboat in  assigned_tugboats:
                appoint_info = appointment_info[tugboat.tugboat_id]
                tugboat_id = appoint_info['tugboat_id']
                for barge in tugboat.assigned_barges:
                    barge_info = lookup_order_barges[barge.barge_id] 
                    barge_info['appointment_station'] = appoint_info['appointment_station']
                    
            
            river_tugboats =  data['river_tugboats'] 
            appointment_location= (stations['s2'].lat, stations['s2'].lng)
            river_assigned_tugboats = assign_barges_to_river_tugboats(self, appointment_location, order,
                                                                    data, river_tugboats, order_barges)
            
        
            
            #for 
            
            river_tugboat_results, river_time_lates = self.arrival_step_river_transport(order, river_assigned_tugboats, 
                                                                                        lookup_order_barges, 
                                                                                        lookup_sea_tugboat_results, 
                                                                                        round_trip_order)
     
            
            
            
            
            
            lookup_river_tugboat_results = {result['tugboat_id']: result for result in river_tugboat_results}
            self.update_barge_infos( lookup_order_barges, lookup_river_tugboat_results)
            customer_river_time_lates = travel_trought_river_import_to_customer(order, lookup_river_tugboat_results)
            
            list_lates = []
            for river_tugboat in river_assigned_tugboats:
                list_lates.append(customer_river_time_lates[river_tugboat.tugboat_id])
            
            active_loadings = active_loadings_infos[-1]
            river_schedule_results = shecdule_customer_order_tugboats(order, river_assigned_tugboats, active_loadings, list_lates)
            #print("River Schedule Results:", len(river_schedule_results), river_schedule_results) if order.order_id == 'o3' else None
            # print("River Schedule Results:", river_schedule_results, 
            #       len(river_assigned_tugboats), len(lookup_sea_schedule_results), 
            #       len(lookup_sea_tugboat_results))
            active_loadings = self.__create_active_loadings(order, river_schedule_results)
            active_loadings_infos.append(active_loadings)   
            
            #rint("Load Schedule Results:", len(active_loadings_infos) ,active_loadings_infos) if order.order_id == 'o3' else None
            
            
            lookup_river_schedule_results = {result['tugboat_schedule']['tugboat_id']: result for result in river_schedule_results}
            
            
            
            update_sea_travel_tugboats(self,  order, lookup_sea_tugboat_results, lookup_river_tugboat_results)
            
            if round_trip_order == 1:
                for tugboat_id, tugboat_result in lookup_river_tugboat_results.items():
                    if ((first_arrival_customer_datetime is None) or 
                        (first_arrival_customer_datetime > tugboat_result['data_points'][-1]['enter_datetime'])):
                        first_arrival_customer_datetime = tugboat_result['data_points'][-1]['enter_datetime']
            
        
                    
                    #print("River Tugboat Result:", tugboat_id, first_arrival_customer_datetime, tugboat_result['data_points'][-1])
            
            update_river_travel_tugboats(order, first_arrival_customer_datetime, lookup_river_schedule_results, 
                                         lookup_river_tugboat_results, temp_river_tugboat_results, round_trip_order)
            
            
            self.update_shedule(order, lookup_order_barges, lookup_sea_tugboat_results, lookup_river_tugboat_results)
          
            temp_river_assigned_tugboats.extend(river_assigned_tugboats)
            temp_sea_tugboat_results.extend(tugboat_results)
            temp_river_tugboat_results.extend(river_tugboat_results)
            
            
            self._extend_update_tugboat_results(tugboat_results, round_trip_order)
            self._extend_update_tugboat_results(river_tugboat_results,  round_trip_order)
            round_trip_order += 1            
                        
            # Keep tugboat state between trips to maintain schedule continuity
            self._reset_all_tugboats()  
            
        # print("Check before round trip EE")
        # for tugboat_result in temp_sea_tugboat_results:
        #     #print(tugboat_id)
        #     tugboat_id = tugboat_result['tugboat_id']
        #     tugboat = data['tugboats'][tugboat_id]
            
        #     end_datetimes = [item['end_datetime'] for item in self.tugboat_scheule[tugboat_id]]
            
        #     print(tugboat_id, end_datetimes, self.get_ready_time_tugboat(tugboat))
        
        #DEBUG
        # for barge_id in debug_barges:
        #     barge = self.data['barges'][barge_id]
        #     debug_barges[barge.barge_id]['after_km'] = self.get_river_km_barge(barge)

        #df = pd.DataFrame(debug_barges.values())
        #print(df)
        
        
           
                
        return {
            'assign_barge_infos': assigned_barge_infos,
            'assign_river_barges':temp_river_assigned_tugboats,
            "sea_tugboat_results": temp_sea_tugboat_results,
            'schedule_results': schedule_results,
            "river_tugboat_results": temp_river_tugboat_results
        }
        
    def generate_schedule(self):
        data = self.data
        orders = data['orders']
        barges = data['barges']
        tugboats = data['tugboats']
   
        all_dfs = []
        barge_dfs = []
        
        total_tugboat_weight = 0
        
        for order_id, order in orders.items():
            if order.order_type != TransportType.IMPORT:
                continue
            
        
            #print(order)
            print("Tugboat available time for order {}".format(order.order_id), " ###################################################")
            #for tugboat_id, single_tugboat_schedule in self.tugboat_scheule.items():
                 #print(tugboat_id, single_tugboat_schedule[-1]['end_datetime'])
            
            # print("Barge available time for order {}".format(order.order_id))
            # for barge_id, single_barge_schedule in barges.items():
            #     barge_ready_time = self.get_ready_barge(single_barge_schedule)
            #     if barge_ready_time < order.start_datetime:
            #         print(barge_id, barge_ready_time)
            
            total_weight = sum(barge.capacity for barge_id, barge in barges.items() 
                               if self.get_ready_barge(barge) < order.due_datetime - timedelta(days=4))
            #print(order.order_id, "order start time: {}".format(order.start_datetime))
            #print("########### Total weight for available barges: {}".format(total_weight))
            total_load_tugboat_order = 0
            
            
            
            
            result_order1 = self.travel_import(order)
            assigned_barge_infos = result_order1['assign_barge_infos']
            sea_tugboat_results = result_order1['sea_tugboat_results']
            river_tugboat_results = result_order1['river_tugboat_results']
            schedule_results = result_order1['schedule_results']
            #assigned_river_barge_infos = result_order1['assign_river_barges']
            
            
            
            
            
            #break
            
            # Assume sea_tugboat_results is a list of tugboat dictionaries

            for tugboat in sea_tugboat_results:
                df = pd.DataFrame(tugboat['data_points'])
                df['tugboat_id'] = tugboat['tugboat_id']  # Add tugboat ID to each row
                df['order_id'] = order.order_id
                df['water_type']= 'Sea'
                all_dfs.append(df)
                total_load_tugboat_order += tugboat['data_points'][0]['total_load']
                #print("      single tugboat", tugboat['tugboat_id'],tugboat.keys(), len(sea_tugboat_results))
        
                
            for tugboat in river_tugboat_results:
                df = pd.DataFrame(tugboat['data_points'])
                df['tugboat_id'] = tugboat['tugboat_id']  # Add tugboat ID to each row
                df['order_id'] = order.order_id
                df['water_type']= 'River'
                all_dfs.append(df)
                
            for entry in assigned_barge_infos:
                entry['start_time'] = entry['time_window'][0]
                entry['end_time'] = entry['time_window'][1]
                del entry['time_window']  # optional: remove if not needed
                entry['barge_id'] = entry['barge'].barge_id
                entry['order_id'] = order.order_id
                entry['capacity'] = entry['barge'].capacity
                del entry['barge']
                for tugboat in river_tugboat_results:
                    tugboat_id = tugboat['tugboat_id']
                    tugboat_object = tugboats[tugboat_id]
                    barge_infos =  self.get_barge_infos_tugboat(tugboat_object)
                    
                    barge_ids = [barge["barge_id"] for barge in barge_infos]
                    #print(entry['barge_id'], barge_ids)
                    #print(order.order_id, tugboat_id, barge_ids)
                    if entry['barge_id'] in barge_ids:
                        entry['tugboat_river_id'] = tugboat['tugboat_id']
                for tugboat in sea_tugboat_results:
                    tugboat_id = tugboat['tugboat_id']
                    tugboat_object = tugboats[tugboat_id]
                    barge_infos =  self.get_barge_infos_tugboat(tugboat_object)
                    #for barge_info in barge_infos:
                        #print("BBB", barge_info)
                    barge_ids = [barge["barge_id"] for barge in barge_infos]
                   #print(order.order_id, barge_ids)
                    if entry['barge_id'] in barge_ids:
                        entry['tugboat_sea_id'] = tugboat['tugboat_id']
            
            print("############## Order: {}, Total Load: {}".format(order.order_id, total_load_tugboat_order))
                
            df = pd.DataFrame(assigned_barge_infos)
            barge_dfs.append(df)
            #print("order_id", order_id)
            #print(df)
            #print(assigned_barge_infos)

            # Merge all into one DataFrame
        # combined_df = pd.concat(all_dfs, ignore_index=True)
            # Show the final merged DataFrame
        #print(combined_df)
        return pd.concat(all_dfs, ignore_index=True), pd.concat(barge_dfs, ignore_index=True)

    def save_schedule_to_csv(self, tugboat_df, barge_df, 
                           tugboat_path='data/output/tugboat_schedule_v4.xlsx',
                           barge_path='data/output/barges.xlsx'):
        """Saves schedule DataFrames to CSV files"""
        tugboat_df["enter_datetime"] = pd.to_datetime(tugboat_df["enter_datetime"])
        tugboat_df["exit_datetime"] = pd.to_datetime(tugboat_df["exit_datetime"])
        early_start_time = min(tugboat_df["enter_datetime"])
        late_finish_time = max(tugboat_df["exit_datetime"])
        start_date = early_start_time.date()
        end_date = late_finish_time.date()
        start_datetime = pd.to_datetime(start_date)
        end_datetime = pd.to_datetime(end_date)
        hourly_range = pd.date_range(start=start_datetime, end=end_datetime, freq='H')

        # Insert an empty row at the beginning
        df = tugboat_df.copy()
        df.loc[-1] = np.nan  # Add a row of NaNs at the top
        df.index = df.index + 1  # Shift index to make room for the new row
        df = df.sort_index()     # Sort by index to put the new row at the top

        # Create a row with dates
        date_row = pd.Series(index=df.columns)
        for i, col in enumerate(df.columns):
            if pd.api.types.is_datetime64_any_dtype(df[col]) and i > 2: # Assuming the first few columns are not dates
                date_row[col] = df[col].iloc[1].date() # Get date from the first actual row
            else:
                date_row[col] = ''

        # Assign the date_row to the first row of the DataFrame
        df.iloc[0] = date_row

        # Now, the data processing logic needs to be adjusted to handle the header row.
        # You would likely skip the first row when iterating through the data rows for processing.

        # For example, when creating the 'data' list, you would iterate from the second row:
        data = []
        machine_list = []

        for index, row in df.iloc[1:].iterrows(): # Start from the second row
            # row_data['ID'] = index
            # Filter out unwanted row
            if row['type'] in ['Barge Collection', 'Start Order Carrier', 'Appointment', 'Barge Change', 'Customer Station','Barge Release']:
                continue

            order_id_val = row['order_id']
            activity_val = row['name']
            if 'cr' in row['name']:
                machine_val = row['name'].split(' - ')[0]
            else:
                machine_val = row['tugboat_id']
            if row['type'] in ['Barge Step Collection', 'Barge Change Collection']:
                barge_val = row['name'].split(' - ')[1]
            else:
                barge_val = row['barge_ids']
            row_data = {'row_id': index+1,
                        "order_id": order_id_val,
                        "activity": activity_val,
                        "machine": machine_val,
                        "barge": barge_val}

            enter_time = row['enter_datetime']
            exit_time = row['exit_datetime']

            if machine_val in machine_list:
                pass
            else:
                machine_list.append(machine_val)

            for hour in hourly_range:

                # Check if the activity time range overlaps with the current hour\

                if (enter_time <= hour) and (exit_time + pd.Timedelta(1,'hour') > hour):
                    row_data[hour] = machine_val
                else:
                    row_data[hour] = '' # Or leave as NaN if preferred

            data.append(row_data)

        # When creating the output DataFrame, you will need to manually create the header
        # including the date row and the original column names.
        # A simpler approach for merging the date would be to create a MultiIndex header
        # on the output_df after it's created.

        output_df_data = pd.DataFrame(data)

        # Create a list for the date header
        date_header = [''] * 5 # Placeholders for the first 3 columns

        for hour in hourly_range:
            date_header.append(hour.date())

        # Create a list for the column name header
        column_name_header = []
        # print(output_df_data.columns)
        # dde
        for col in output_df_data.columns:
            if col == 'row_id':
                column_name_header.append('Row ID')
            elif col == 'order_id':
                column_name_header.append('Order ID')
            elif col == 'activity':
                column_name_header.append('Activity')
            elif col == 'machine':
                column_name_header.append('Machine')
            elif col == 'barge':
                column_name_header.append('Barge')
            else:
                column_name_header.append(col.hour)

        # Create a MultiIndex from the two header rows
        multiindex = pd.MultiIndex.from_arrays([date_header, column_name_header])

        # Assign the MultiIndex to the output DataFrame
        output_df_data.columns = multiindex

        # output_df_data

        # Create a Pandas Excel writer using XlsxWriter as the engine.
        writer = pd.ExcelWriter(tugboat_path, engine='xlsxwriter')

        # Convert the dataframe to an XlsxWriter Excel object.
        tugboat_df.to_excel(writer, sheet_name='Summary', index=False)
        tugboat_df_rows, tugboat_df_cols = tugboat_df.shape
        # Get the xlsxwriter objects from the dataframe writer object.
        workbook  = writer.book
        worksheet_summary = writer.sheets['Summary']
        max_char_tugboat = string.ascii_uppercase[(tugboat_df_cols%26) - 1]
        cell_range = f"A1:{max_char_tugboat}1"
        worksheet_summary.autofilter(cell_range)
        worksheet_summary.freeze_panes(1, 0)
        worksheet_summary.autofit()

        output_df_data.to_excel(writer, sheet_name='Timeline Detail')
        worksheet_timeline = writer.sheets['Timeline Detail']

        (max_row, max_col) = output_df_data.shape
        main_char = string.ascii_uppercase[(max_col // 26)-1] if max_col // 26 > 0 else ""
        max_char = main_char + string.ascii_uppercase[max_col%26]
        cell_range = f"G4:{max_char}{max_row+4}"

        def generate_random_colors(n):
            """Generate a list of n random hex color codes."""
            colors = []
            for _ in range(n):
                color = "#{:06x}".format(random.randint(0, 0xFFFFFF))
                colors.append(color)
            return colors

        # Example usage:
        random_colors = generate_random_colors(len(machine_list))

        colors = cycle(random_colors)

        for i in range(len(machine_list)):
            color = next(colors)

            worksheet_timeline.conditional_format(cell_range,
            {
                'type': 'text',
                'criteria': 'containing',
                'value': machine_list[i],
                'format': workbook.add_format({'bg_color': color,
                                            'font_color': color})
            }
                                        )
        worksheet_timeline.autofit()
        worksheet_timeline.autofilter(f'A3:F3')
        worksheet_timeline.freeze_panes(3, 5)
        writer.close()
        # output_df_data.to_excel('tugboat_timeline_analysis.xlsx')
        barge_df.to_excel(barge_path, index=False)

    def calculate_cost(self):
        tugboat_df_o, barge_df = self.generate_schedule()
        
        # filter only main_type = 'TUGBOAT'
        tugboat_df = tugboat_df_o[(tugboat_df_o['type'] == 'Customer Station') | (tugboat_df_o['type'] == 'Appointment') | 
                                  (tugboat_df_o['type'] == 'Barge Collection')]
        
        
        cost_results = {}
        data = self.data
        tugboats = data['tugboats']
        orders = data['orders']
        print("Result ====================================================")
        tugboat_df_grouped = tugboat_df.groupby(['tugboat_id', 'order_id'], as_index=False).agg({'time': 'sum', 'distance': 'sum'})
        
        #tugboat_df_grouped['cost'] = tugboat_df_grouped['time'] * tugboats[tugboat_df_grouped['tugboat_id']]['max_fuel_con'] + tugboat_df_grouped['distance'] * tugboats[tugboat_df_grouped['tugboat_id']]['fuel_con']
        
        tugboat_df_grouped['consumption_rate'] = np.zeros(len(tugboat_df_grouped))
        tugboat_df_grouped['cost'] = np.zeros(len(tugboat_df_grouped))
        
        #tugboat_df_grouped['load'] = np.zeros(len(tugboat_df_grouped))
        
        for tugboat_id, tugboat in tugboats.items():
            for order_id, order in orders.items():
                tugboat_df_grouped.loc[(tugboat_df_grouped['tugboat_id'] == tugboat_id) & (tugboat_df_grouped['order_id'] == order_id), 
                                       'consumption_rate'] = tugboat.max_fuel_con
                
        tugboat_df_grouped['cost'] = tugboat_df_grouped['time'] * tugboat_df_grouped['consumption_rate']     
        
        
        # print("Total Cost", tugboat_df_grouped['cost'].sum())
        # print("Total Time", tugboat_df_grouped['time'].sum())
        # print("Total Distance", tugboat_df_grouped['distance'].sum())
        # print("End Result ====================================================")
        
        tugboat_dfv2 = tugboat_df[(tugboat_df['type'] == 'Customer Station') | (tugboat_df['type'] == 'Appointment')]
        tugboat_df_groupedv2 = tugboat_dfv2.groupby(['tugboat_id', 'order_id'], as_index=False)
        
        # print(tugboat_df_groupedv2)
        # # display tugboat_df_groupedv2 in each group
        for name, group in tugboat_df_groupedv2:
            tugboat_df_grouped.loc[(tugboat_df_grouped['tugboat_id'] == name[0]) & (tugboat_df_grouped['order_id'] == name[1]), 
                                       'total_load'] = (group['total_load'].sum())
        
       
        print(tugboat_df_grouped)
        print("Total Cost", tugboat_df_grouped['cost'].sum())
        print("Total Time", tugboat_df_grouped['time'].sum())
        print("Total Distance", tugboat_df_grouped['distance'].sum())
        print("Total Load", tugboat_df_grouped['total_load'].sum()/2)
        print("End Result ====================================================")
      

        
        return cost_results, tugboat_df_o, barge_df
        