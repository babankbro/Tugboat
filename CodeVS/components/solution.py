from sys import path
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
from CodeVS.problems.code_info import CodeInfo
from CodeVS.components.datapoint import DataPoint
from datetime import timedelta


class Solution:
    def __init__(self, data):
        self.data = data
        self.crane_order_scheule = {}
        self.tugboat_scheule = {}
        self.barge_scheule = {}
        self.tugboat_travel_results = {}
    
        # print("========================================")
        # print(f"Type {type(TravelHelper._instance)}")
        # print("========================================")
        if TravelHelper._instance is None:
            TravelHelper(data=data)
        else:
            TravelHelper._set_data(TravelHelper._instance,  data)
        
        
        for order_id, order in data['orders'].items():
            self.crane_order_scheule[order_id] = {}
            for i in range(len(order.crane_rates)):
                info = {
                    'crane_id': f'cr{i+1}',
                    'order_id': order_id,
                    'start_datetime': order.start_datetime + timedelta(hours=order.crane_ready_times[i]),
                    'end_datetime': order.start_datetime + timedelta(hours=order.crane_ready_times[i]),
                     
                }
                self.crane_order_scheule[order_id][info['crane_id']]= [info]
            
        
        
        for tugboat_id, tugboat in data['tugboats'].items():
            if tugboat.start_station.water_type == WaterBody.RIVER:
                closeset_station = TravelHelper._instance.get_next_river_station(transport_type=TransportType.EXPORT, km=tugboat._km)
            else:
                closeset_station =tugboat.start_station
            if closeset_station.station_id == "ST_047":
                raise Exception("Closest station is ST_047", tugboat._km)
            info = {
                'tugboat_id': tugboat.tugboat_id,
                'order_id': None,
                'start_datetime': tugboat._ready_time,
                'end_datetime': tugboat._ready_time,
                'river_km': closeset_station.km,
                'water_status': tugboat.start_station.water_type , 
                'location': (closeset_station.lat, closeset_station.lng),
                'station_id':  closeset_station.station_id if closeset_station != None  else None,
                'barge_infos': [],
                 
            }
            # print("You're Doing Great!")
            self.tugboat_scheule[tugboat_id] = [info]
            
            self.tugboat_travel_results[tugboat.tugboat_id] = []
            
            
        for barge_id, barge in data['barges'].items():
           
            
            closeset_station =barge.start_station
            station_id = closeset_station.station_id
            
            if station_id == "ST_002": raise Exception("Closest station is ST_002", barge._km)
            
            info = {
                'barge_id': barge.barge_id,
                'order_id': None,
                'start_datetime': barge._ready_time,
                'end_datetime': barge._ready_time,
                'river_km': closeset_station.km,
                'water_status': closeset_station.water_type, 
                'location': (closeset_station.lat, closeset_station.lng),
                'station_id': station_id,
                    
            }
            self.barge_scheule[barge_id] = [info]
        
        self.code_info = CodeInfo(data=data, solution=self)
        
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
    
    def __iterate_assign_barges(self, order, barges, days):
        # Filter available barges that are free during order time window and ready
        assigned_barges = []
        remaining_demand = order.demand
        order_start = order.start_datetime
        order_end = order.due_datetime
        # available_barges = [
        #     b for b in barges.values() 
        #     #if (self.get_ready_barge(b)is None or self.get_ready_barge(b) < order_end - timedelta(days=4) ) 
        #     if (self.get_ready_barge(b)is None or self.get_ready_barge(b) < order_start + timedelta(days=days)) 
        # ]
        
        
        # # sum the capacity of available barges
        # total_capacity = sum(b.capacity for b in available_barges)
        # #print(f"AS  Total capacity: {total_capacity}")
        
        
        
        # # For import orders, sort by distance to carrier
        # if order.order_type == TransportType.IMPORT:
        #     carrier_location = (order.start_object.lat, order.start_object.lng)
        #     available_barges.sort(key=lambda b:
        #          (self.get_river_km_barge(b) + 20  if self.get_water_status_barge(b) == WaterBody.RIVER 
        #          else TravelHelper._instance.get_distance_location(carrier_location, self.get_location_barge(b)))
        #     )
        # else:
        #     customer_location = (order.start_object.lat, order.start_object.lng)
        #     customer_station = self.data['stations'][order.start_object.station_id]
        #     bar_station = self.data['stations'][config_problem.BAR_STATION_BASE_REFERENCE_ID]
        #     available_barges.sort(key=lambda b:
        #          (self.get_river_km_barge(b) + 20  if self.get_water_status_barge(b) == WaterBody.RIVER 
        #          else TravelHelper._instance.get_distance_location(customer_location, (bar_station.lat, bar_station.lng)) + customer_station.km)) 
        
        # print("Available barges", [b.barge_id for b in available_barges])
        
        sorted_barges = self.code_info.get_code_next_barge(order, barges, days)
        #print("Count Sorted barges", self.code_info.index_code_barge)
        
        # Assign barges until demand is met
        for barge in sorted_barges:
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
            
    
    def assign_barges_to_single_order(self, order, barges):
        assigned_barges = []
 
        assigned_barges = self.__iterate_assign_barges(order, barges, config_problem.RELAX_DAYS)
        
        total_capacity = sum(barge['barge'].capacity for barge in assigned_barges)
        
        days = config_problem.RELAX_DAYS
        
        while total_capacity < order.demand:
            assigned_barges = self.__iterate_assign_barges(order, barges, days)
            days = days + 2
            total_capacity = sum(barge['barge'].capacity for barge in assigned_barges)
            
        if total_capacity < order.demand:
            raise Exception(f"Not enough capacity for order {order.order_id}")
        
        return assigned_barges
 
    def assign_barges_to_tugboats(self, order, tugboats, order_assigned_barges):
        assigned_tugboats = []
        sorted_tugboats = self.code_info.get_code_next_tugboat(order, tugboats, config_problem.RELAX_DAYS)
        #print("sorted_tugboats", [t.tugboat_id for t in sorted_tugboats])
        copy_order_assigned_barges = order_assigned_barges.copy()
        for tugboat in sorted_tugboats:
            tugboat_ready_time = self.get_ready_time_tugboat(tugboat)
            tugboat_id = tugboat.tugboat_id
            if order.due_datetime < tugboat_ready_time:
                print("Tugboat is not ready",tugboat_id, order.order_id, order.due_datetime, tugboat_ready_time)  
                continue
            assign_barges_to_tugboat(tugboat, order_assigned_barges)
            if len(tugboat.assigned_barges) != 0:
                assigned_tugboats.append(tugboat)
            if len(tugboat.assigned_barges) == 0:
                #print("Commpleted all barges assignment")
                break
        
        if len(assigned_tugboats) != 0 and len(order_assigned_barges) != len(copy_order_assigned_barges):
            #order_assigned_barges = copy_order_assigned_barges
            #raise Exception("No tugboat found for order: " + str(order.order_id))
            #print("Len assigned_tugboats", len(copy_order_assigned_barges), len(order_assigned_barges))
            return True, assigned_tugboats
        
        #print("Not Enough Tugboats-------------------------------------------------------", len(assigned_tugboats))
        for tugboat in assigned_tugboats:
            tugboat.reset()
        assigned_tugboats = []
        sorted_tugboats = self.code_info.get_code_next_tugboat(order, tugboats, config_problem.MAX_RELAX_DAYS)
        order_assigned_barges.clear()
        for barge in copy_order_assigned_barges:
            order_assigned_barges.append(barge)
            
        #print("Sorted Tugboats", [t.tugboat_id for t in sorted_tugboats])
        for tugboat in sorted_tugboats:
            tugboat_ready_time = self.get_ready_time_tugboat(tugboat)
            tugboat_id = tugboat.tugboat_id
            assign_barges_to_tugboat(tugboat, order_assigned_barges)
            if len(tugboat.assigned_barges) != 0:
                assigned_tugboats.append(tugboat)
            if len(tugboat.assigned_barges) == 0:
                #print("Commpleted all barges assignment")
                break
        
        if len(assigned_tugboats) != 0:
            #raise Exception("No tugboat found for order: " + str(order.order_id))
            return True, assigned_tugboats
        
        return False, None
        
        #raise Exception("No tugboat found for order 30 days: " + str(order.order_id))
    
    def update_barge_infos(self, lookup_order_barges, lookup_tugboat_results):
        data = self.data
        #for order_id, order_barge_info in lookup_order_barges.items():
            #print(order_barge_info)
            
            
        #print('-------------------------- Tugboat')
        for tugboat_id, results in lookup_tugboat_results.items( ):
            exit_datetime = results['data_points'][1].exit_datetime
            tugboat = data['tugboats'][tugboat_id]
            max_datetime = self.get_ready_time_tugboat(tugboat)
            for barge in tugboat.assigned_barges:
                barge_info = lookup_order_barges[barge.barge_id]
                barge_info['exit_datetime'] = exit_datetime
                if max_datetime > exit_datetime:
                    max_datetime = exit_datetime
    
    def update_collection_barge_time(self, order, tugboat, collection_time_info):
        if order.order_type == TransportType.IMPORT or order.order_type == TransportType.EXPORT:
            #print("-------------------------------------------------------------")
            #print("Order Type: ", order.order_type)
            #print("Collection Barge Infos:", collection_time_info)
            #print("-------------------------------------------------------------")
            ORDER_DATETIME = order.start_datetime
            #convert ORDER_DATETIME to string format %Y-%m-%d %H:%M:%S
            ORDER_DATETIME = ORDER_DATETIME.strftime("%Y-%m-%d %H:%M:%S")
            #print("Total Distance:", collection_time_info['total_distance'], ORDER_DATETIME, type(ORDER_DATETIME))
            #lookup = self.data['water_level_down']

            total_distance = 0
            total_time = 0
            for barge_collect_info in collection_time_info['barge_collect_infos']:
                #print("---------------------------")
                for travel_step in barge_collect_info['travel_steps']:
                    travel_step.update_travel_prev_step_move(ORDER_DATETIME)
                    total_distance += travel_step.distance
                    total_time += travel_step.travel_time
                    #print(travel_step)
                #print(barge_collect_info)
                #print("---------------------------")
            #print("Total Distance:", total_distance)
            #sea to river
            
        else:
            #river to sea
            raise Exception("Update Collection Barge Time")
        
        
        collection_time_info['total_time'] = total_time + collection_time_info['total_setup_time']
        collection_time_info['total_distance'] = total_distance
    
    def update_travel_info(self, order, tugboat, travel_time_info):  
        if ("travel_time" not in travel_time_info or "travel_distance" not in travel_time_info or 
            "speed" not in travel_time_info or "travel_steps" not in travel_time_info):
            raise Exception("Update Travel Info")
        
        
        if order.order_type == TransportType.IMPORT or order.order_type == TransportType.EXPORT:
             ORDER_DATETIME = order.start_datetime
             ORDER_DATETIME = ORDER_DATETIME.strftime("%Y-%m-%d %H:%M:%S")
             total_distance = 0
             total_travel_time = 0
             for travel_step in travel_time_info['travel_steps']:
                 travel_step.update_travel_prev_step_move(ORDER_DATETIME)
                 total_distance += travel_step.distance
                 total_travel_time += travel_step.travel_time
             
        else:
            raise Exception("Update Travel To Start Object")
          
        
        travel_time_info['travel_time'] = total_travel_time 
        travel_time_info['travel_distance'] = total_distance
        if total_travel_time == 0:
            travel_time_info['speed'] = 0
        else:
            travel_time_info['speed'] = total_distance / total_travel_time
        
    
    def arrival_step_transport_order(self, order, assigned_tugboats, order_trip = 1):
        time_boat_lates = []
        tugboat_results = []
        arrival_times = []
        for tugboat in assigned_tugboats:
            tugboat_info = self.tugboat_scheule[tugboat.tugboat_id][-1]
            
            #print("Calculate collection barge:", tugboat.tugboat_id, len(self.tugboat_scheule[tugboat.tugboat_id]), tugboat_info) if tugboat.tugboat_id == 'SeaTB_05' else None
            #print("$$$$$$$$$$$$$$$$$$$$$$$$", tugboat_info) if tugboat.tugboat_id == 'SeaTB_02' else None
            
            
            collection_time_info = tugboat.calculate_collection_barge_time(tugboat_info, self.barge_scheule)
            self.update_collection_barge_time(order, tugboat, collection_time_info)
            
            
            travel_info = tugboat.calculate_travel_to_start_object(tugboat_info, self.barge_scheule)
            
            #print("arrival_step_transport_order ########################")
            #print(tugboat_info)
            #for travel_step in travel_info['travel_steps']:
            #    print(travel_step)
            
            #print("Travel info", travel_info)
            self.update_travel_info(order, tugboat, travel_info)
            #print("Travel info updated", travel_info)
            #raise Exception("Travel info updated")
            
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
            
            start_location = DataPoint(
                ID = "Start",
                type = "Start",
                name = "Start at " + start_pos,
                enter_datetime = tugboat_ready_time,
                #exit_datetime = tugboat_ready_time,
                distance = 0,
                time = 0,
                speed = 0,
                type_point = 'main_point',
                rest_time= 0,
                order_trip = order_trip,
                barge_ids = None,
                station_id = station_tugboat_id,
            )
            
            #print("Tugboat ready time:", tugboat.tugboat_id, tugboat_ready_time)
            
            
            barge_ready_time = tugboat_ready_time + timedelta(minutes=first_barge_location['travel_time']*60)
            barge_ready_time = get_next_quarter_hour(barge_ready_time)
            start_barge_station_id = first_barge_location['travel_steps'][0].start_id
            
            
            if barge_ready_time < tugboat_ready_time:
                barge_ready_time = tugboat_ready_time
            barge_location = DataPoint(
                ID = "Barge",
                type = "Barge Collection",
                name = "Barge Location",
                enter_datetime = barge_ready_time,
                #exit_datetime = barge_ready_time + timedelta(minutes=collection_time_info['total_time']*60),
                distance = first_barge_location['travel_distance'],
                speed = tugboat.max_speed,
                time = first_barge_location['travel_time'],
                type_point = 'main_point',
                rest_time = 0,
                order_trip = order_trip,
                barge_ids = None,
                station_id = start_barge_station_id,
            )
            
            
            
            
            #if travel_info['travel_distance'] > 50:
                #raise Exception('Not on the sea'
            
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
                new_start_location_exit_time_pre = arrival_time - timedelta(minutes=travel_total_time*60)
                new_start_location_exit_time = get_previous_quarter_hour(new_start_location_exit_time_pre)
                #(print("Fixed Error Time Start ========================== v1", arrival_time, travel_total_time, new_start_location_exit_time) 
                #if tugboat.tugboat_id == 'SeaTB_01' else None)
                barge_location.enter_datetime = new_start_location_exit_time
                barge_location.exit_datetime = new_barge_location_exit_time
                barge_location.start_arrival_datetime = barge_location.enter_datetime
                
                
                
            else:
                tugboat_ready_time = self.get_ready_time_tugboat(tugboat)
                new_start_location_exit_time = get_next_quarter_hour(tugboat_ready_time)
                new_barge_location_enter_time = new_start_location_exit_time
                new_barge_location_exit_time = new_barge_location_enter_time + timedelta(minutes=(collection_time_info['total_time'])*60)
                new_barge_location_exit_time = get_next_quarter_hour(new_barge_location_exit_time)
                barge_location.enter_datetime = new_barge_location_enter_time
                barge_location.exit_datetime = new_barge_location_exit_time
                barge_location.start_arrival_datetime = barge_location.enter_datetime
            
            time_boat_lates.append(time_lated_start)
            arrival_times.append(arrival_time)
            
            #print("Check ready time CCCCCC", tugboat.tugboat_id, tugboat_ready_time, arrival_time, new_start_location_exit_time) if tugboat.tugboat_id == 'tbs1' else None
            
           
            
            
            
            
            # print("arrival_time CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC", tugboat.tugboat_id, 
            #       tugboat_ready_time, arrival_time, start_location['enter_datetime'], 
            #       new_start_location_exit_time, travel_total_time)
            start_location.enter_datetime = new_start_location_exit_time
            start_location.exit_datetime = new_start_location_exit_time
            barge_location.order_distance = travel_info['travel_distance']
            barge_location.time = travel_info['travel_time']
            barge_location.barge_speed = travel_info['speed']
            barge_location.order_arrival_time = arrival_time
            barge_location.travel_info = travel_info
            
            #print("Barge collection infomations vvvvvvvvvvvvv")
            barge_steps = []
            start_travel_barge = barge_location.enter_datetime
            isDeBug = False
            barge_ids = []
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
                start_barge_station_id = collection_info['travel_steps'][0].start_id
                end_barge_station_id = collection_info['travel_steps'][-1].end_id
                
              
                
                barge_ids.append(barge_id)
        
        
                
                
                
                name = "Collecting Barge - " + collection_info['barge_id'] + " - " 
                name += f"({start_barge_station_id} to {str(end_barge_station_id)})"
                # if 'nan' in name and tugboat.tugboat_id == 'tbs4' and order.order_id == 'o3' and i == 1:
                #     print("##################################################### ", tugboat.tugboat_id, start_barge_station_id, end_barge_station_id)
                #     for j, collection_infov in enumerate(collection_time_info['barge_collect_infos']):
                #         print(j, collection_infov)
                
                #name += " - " + station_barge_ids[i]
                if '- to ST' in name:
                    print(tugboat_info)
                    raise Exception("- to ST", str(collection_info['travel_steps'][0]))
                
                
                #if barge_id == 'B_084' and tugboat.tugboat_id == 'SeaTB_02':
                    # print("Collecting B_084", start_barge_station_id, end_barge_station_id)
                    # for travel_step in collection_info['travel_steps']:
                    #     print(travel_step)
                    #print("name B_084", name)
                    #isDeBug = True
                
                
                barge_step = DataPoint(
                    ID= "Barge",
                    type= "Barge Step Collection",
                    name= name,
                    enter_datetime= start_travel_barge,
                    #exit_datetime= finish_barge_time,
                    distance= collection_info['travel_distance'],
                    speed= 0 if collection_info['travel_time'] == 0 else collection_info['travel_distance']/collection_info['travel_time'],
                    time= collection_info['travel_time'],
                    type_point= 'travel_point',
                    rest_time= collection_info['setup_time'],
                    barge_ids= collection_info['barge_ids'],
                    order_trip = order_trip,
                    station_id = end_barge_station_id,
                )
                start_station_id = station_barge_ids[i]
                start_travel_barge = finish_barge_time
                barge_location.exit_datetime = max(barge_location.exit_datetime, finish_barge_time)
                barge_location.barge_ids = collection_info['barge_ids'].copy()
                #print(barge_step)
                barge_steps.append(barge_step)
                
            
            
            if isDeBug:
                print("ORDER", order.order_id, tugboat.tugboat_id)
                for barge_step in barge_steps:
                    print(barge_step)
            tugboat_order_results["data_points"].extend(barge_steps)
            
            barge_location.travel_info['exit_datetime'] = barge_location.exit_datetime
            
        #print("Time late start:", time_boat_lates)
        #print("Arrival times:", arrival_times)
        #if order_trip == 1:
            
            start_location.start_arrival_datetime = start_location.enter_datetime
        
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
            
            lookup_steps = {}
            for barge in tugboat.assigned_barges:
                #print("barge", barge.barge_id, order.order_id)
                barge_release_step = self._find_barge_release_step(sea_tugboat_results, barge.barge_id)
                lookup_steps[barge.barge_id] = barge_release_step
                #print(self.barge_scheule[barge.barge_id][-1])
            
            collection_time_info = tugboat.calculate_collection_barge_time(tugboat_info, self.barge_scheule)
            self.update_collection_barge_time(order, tugboat, collection_time_info)
            tugboat_info = self.tugboat_scheule[tugboat.tugboat_id][-1]
            tugboat_ready_time = self.get_ready_time_tugboat(tugboat)
            start_station = tugboat_info['station_id']
        
            start_location = DataPoint(
                ID= "Start",
                type= "Start",
                name= "River Start at " + start_station,
                enter_datetime= tugboat_ready_time,
                #exit_datetime= tugboat_ready_time,
                distance= 0,
                time= 0,
                speed= 0,
                type_point= 'main_point',
                rest_time= 0,
                order_trip = round_order_trip,
                barge_ids = None,
                station_id = start_station,
            )
            
            first_barge_location = collection_time_info['barge_collect_infos'][0]

            barge_ready_time = tugboat_ready_time + timedelta(minutes=first_barge_location['travel_time']*60)
            barge_id = first_barge_location['barge_id']
            barge_info = lookup_barge_infos[barge_id]
            appointment_station =TravelHelper._instance.data['stations'][  barge_info['appointment_station']]
            barge_location = DataPoint(
                ID= appointment_station.station_id,
                type= "Barge Change",
                name= "Change at " + appointment_station.name,
                enter_datetime= barge_ready_time,
                #exit_datetime= (barge_ready_time +
                 #timedelta(minutes=collection_time_info['total_time']*60)),
                distance= first_barge_location['travel_distance'],
                speed= tugboat.max_speed,
                time= first_barge_location['travel_time'],
                type_point= 'main_point',
                rest_time= 0,
                order_trip = round_order_trip,
                barge_ids = None,
                station_id = appointment_station.station_id,
            )
            barge_location.exit_datetime = barge_location.enter_datetime + timedelta(minutes=first_barge_location['travel_time']*60)

            
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
            
            # print("Debug Tugboat Ready time 000000000000000000000000000", tugboat_ready_time) if tugboat.tugboat_id == 'tbr2' and order.order_id == 'o3'    else None
            
            
        #     # Update data points with calculated times
            barge_location.enter_datetime = new_barge_location_enter_time
            barge_location.exit_datetime = new_barge_location_exit_time
            start_location.enter_datetime = new_start_location_exit_time
            start_location.exit_datetime = new_start_location_exit_time
            
            if tugboat_ready_time > new_start_location_exit_time:
                start_location.enter_datetime = get_next_quarter_hour(tugboat_ready_time)
                start_location.exit_datetime = get_next_quarter_hour(tugboat_ready_time)
                barge_location.enter_datetime = tugboat_ready_time + timedelta(minutes=first_barge_location['travel_time']*60)
                barge_location.enter_datetime  = get_next_quarter_hour(barge_location.enter_datetime)
                
            barge_location.start_arrival_datetime = barge_location.enter_datetime
            barge_steps = []
            start_travel_barge = barge_location.enter_datetime
            for collection_info in collection_time_info['barge_collect_infos'][:]:
                if start_travel_barge < lookup_steps[collection_info['barge_id']].exit_datetime:
                    start_travel_barge = lookup_steps[collection_info['barge_id']].exit_datetime    
                
                finish_barge_time = start_travel_barge + timedelta(minutes=(collection_info['setup_time'])*60)
                
                start_barge_station_id = collection_info['travel_steps'][0].start_id
                end_barge_station_id = collection_info['travel_steps'][-1].end_id
                
                name = "Change Barge - " + collection_info['barge_id'] + " - " 
                name += f"({start_barge_station_id} to {str(end_barge_station_id)})"
                
                
                
                #print(collection_info)
                barge_step = DataPoint(
                    ID= "Barge",
                    type= "Barge Change Collection",
                    name= name,
                    enter_datetime= start_travel_barge,
                   # exit_datetime= finish_barge_time,
                    distance= collection_info['travel_distance'],
                    speed= 0 if collection_info['travel_time'] == 0 else collection_info['travel_distance']/collection_info['travel_time'],
                    time= collection_info['travel_time'],
                    type_point= 'travel_point',
                    rest_time= 0,
                    barge_ids= collection_info['barge_ids'].copy(),
                    order_trip = round_order_trip,
                    station_id = end_barge_station_id,
                )
                barge_step.exit_datetime = finish_barge_time
                start_travel_barge = finish_barge_time
                #print(barge_step)
                barge_steps.append(barge_step)
            barge_location.exit_datetime = finish_barge_time
            barge_location.barge_ids = collection_info['barge_ids'].copy()
            tugboat_result["data_points"].extend(barge_steps)
            
            start_location.start_arrival_datetime = start_location.enter_datetime
    
        
        return tugboat_results, time_boat_lates
    
    def arival_step_to_sea_transport(self, order, sea_tugboats, lookup_barge_infos, river_tugboat_results, round_order_trip):
        time_boat_lates = []
        tugboat_results = []
        arrival_times = []
        data = self.data
        for tugboat in sea_tugboats:
            tugboat_info = self.tugboat_scheule[tugboat.tugboat_id][-1]
            
            lookup_steps = {}
            for barge in tugboat.assigned_barges:
                #print("barge", barge.barge_id, order.order_id)
                barge_release_step = self._find_barge_release_step(river_tugboat_results, barge.barge_id)
                lookup_steps[barge.barge_id] = barge_release_step
                #print(self.barge_scheule[barge.barge_id][-1])
            
            collection_time_info = tugboat.calculate_collection_barge_time(tugboat_info, self.barge_scheule)
            self.update_collection_barge_time(order, tugboat, collection_time_info)
            tugboat_info = self.tugboat_scheule[tugboat.tugboat_id][-1]
            tugboat_ready_time = self.get_ready_time_tugboat(tugboat)
            start_station = tugboat_info['station_id']
        
            start_location = DataPoint(
                ID= "Start",
                type= "Start",
                name= "River Start at " + start_station,
                enter_datetime= tugboat_ready_time,
                #exit_datetime= tugboat_ready_time,
                distance= 0,
                time= 0,
                speed= 0,
                type_point= 'main_point',
                rest_time= 0,
                order_trip = round_order_trip,
                barge_ids = None,
                station_id = start_station,
            )
            
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
            barge_location = DataPoint(
                ID= appointment_station.station_id,
                type= "Barge Change",
                name= "Change at " + appointment_station.name,
                enter_datetime= barge_ready_time,
                #exit_datetime= (barge_ready_time +
                 #timedelta(minutes=collection_time_info['total_time']*60)),
                distance= first_barge_location['travel_distance'],
                speed= tugboat.max_speed,
                time= first_barge_location['travel_time'],
                type_point= 'main_point',
                rest_time= 0,
                order_trip = round_order_trip,
                barge_ids = None,
                station_id = appointment_station.station_id,
            )
            barge_location.exit_datetime = barge_location.enter_datetime +timedelta(minutes=collection_time_info['total_time']*60)

            
            # Create result structure
            tugboat_result = {
                'tugboat_id': tugboat.tugboat_id,
                'data_points': [start_location, barge_location]
            }
            
        
            max_ready_datetime = self.get_max_datetime(tugboat, lookup_barge_infos)    
            
            
            
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
            
            # print("Debug Tugboat Ready time 000000000000000000000000000", tugboat_ready_time) if tugboat.tugboat_id == 'tbr2' and order.order_id == 'o3'    else None
            
            
        #     # Update data points with calculated times
            barge_location.enter_datetime = new_barge_location_enter_time
            barge_location.exit_datetime = new_barge_location_exit_time
            start_location.enter_datetime = new_start_location_exit_time
            start_location.exit_datetime = new_start_location_exit_time
            
            if tugboat_ready_time > new_start_location_exit_time:
                start_location.enter_datetime = get_next_quarter_hour(tugboat_ready_time)
                start_location.exit_datetime = get_next_quarter_hour(tugboat_ready_time)
                barge_location.enter_datetime = tugboat_ready_time + timedelta(minutes=first_barge_location['travel_time']*60)
                barge_location.enter_datetime  = get_next_quarter_hour(barge_location.enter_datetime)
        
            barge_location.start_arrival_datetime = barge_location.enter_datetime
                
            barge_steps = []
            barge_ids = []
            start_travel_barge = barge_location.enter_datetime
            for collection_info in collection_time_info['barge_collect_infos'][:]:
                if start_travel_barge < lookup_steps[collection_info['barge_id']].exit_datetime:
                    start_travel_barge = lookup_steps[collection_info['barge_id']].exit_datetime    
                
                finish_barge_time = start_travel_barge + timedelta(minutes=(collection_info['setup_time'])*60)
                
                start_barge_station_id = collection_info['travel_steps'][0].start_id
                end_barge_station_id = collection_info['travel_steps'][-1].end_id
                
                name = "Change Barge - " + collection_info['barge_id'] + " - " 
                name += f"({start_barge_station_id} to {str(end_barge_station_id)})"
                
                barge_ids.append(collection_info['barge_id'])
                
                #print(collection_info)
                barge_step = DataPoint(
                    ID= "Barge",
                    type= "Barge Change Collection",
                    name= name,
                    enter_datetime= start_travel_barge,
                    #exit_datetime= finish_barge_time,
                    distance= collection_info['travel_distance'],
                    speed= 0 if collection_info['travel_time'] == 0 else collection_info['travel_distance']/collection_info['travel_time'],
                    time= collection_info['travel_time'],
                    type_point= 'travel_point',
                    rest_time= 0,
                    barge_ids= barge_ids,
                    order_trip = round_order_trip,
                    station_id = end_barge_station_id,
                )
                barge_step.exit_datetime = finish_barge_time
                start_travel_barge = finish_barge_time
                #print(barge_step)
                barge_steps.append(barge_step)
            barge_location.exit_datetime = finish_barge_time
            tugboat_result["data_points"].extend(barge_steps)
            start_location.start_arrival_datetime = start_location.enter_datetime
        
        return tugboat_results, time_boat_lates
                
    def arrival_step_travel_empty_barges(self, order, tugboats, appointment_infos, order_trip):
        
        time_boat_lates = []
        tugboat_results = []
        arrival_times = []
        data = self.data
        for tugboat in tugboats:
            tugboat_info = self.tugboat_scheule[tugboat.tugboat_id][-1]
            
            collection_time_info = tugboat.calculate_collection_barge_time(tugboat_info, self.barge_scheule)
            self.update_collection_barge_time(order, tugboat, collection_time_info)
            
            #location = self.get_location_tugboat(tugboat)
            appointment_info = appointment_infos[tugboat.tugboat_id]
            
            
            if order.order_type == TransportType.IMPORT:
                start_station = TravelHelper.get_next_river_station(self, TransportType.IMPORT, tugboat_info['river_km'])
            else:
                #print("EMPTY TRAVEL==============", len(self.tugboat_scheule[tugboat.tugboat_id]), tugboat_info)
                start_station = self.data['stations'][tugboat_info['station_id']]
                #raise Exception("Order type not supported")
                # river_station = TravelHelper.get_next_river_station(self, TransportType.EXPORT, tugboat_info['river_km'])
            end_station = data['stations'][appointment_info['appointment_station']]
            
            
            
            
            first_barge_location = collection_time_info['barge_collect_infos'][0]
            tugboat_ready_time = self.get_ready_time_tugboat(tugboat)
            
            start_location = DataPoint(
                ID="Start",
                type="Start",
                name=f"Start Collect Barge River Down From {start_station.name} To {end_station.name}",
                enter_datetime=tugboat_ready_time,
                #exit_datetime=tugboat_ready_time,
                distance=0,
                time=0,
                speed=0,
                type_point='main_point',
                rest_time=0,
                order_trip = order_trip,
                barge_ids = None,
                station_id = start_station.station_id,
            )
            
            barge_ready_time = get_next_quarter_hour( tugboat_ready_time +
                                                     timedelta(minutes=first_barge_location['travel_time']*60))
            exit_barge_time = get_next_quarter_hour(barge_ready_time + timedelta(minutes=collection_time_info['total_time']*60))
            barge_location = DataPoint(
                ID="Barge",
                type="Barge Collection",
                name="Barge Location",
                enter_datetime=barge_ready_time,
                #exit_datetime=exit_barge_time,
                distance=first_barge_location['travel_distance'],
                speed=tugboat.max_speed,
                time=first_barge_location['travel_time'],
                type_point='main_point',
                rest_time=0,
                order_trip = order_trip,
                barge_ids = None,
                station_id = end_station.station_id,
            )
            barge_location.exit_datetime = exit_barge_time
            
            tugboat_order_results = {'tugboat_id': tugboat.tugboat_id, 
                                    "data_points" : [start_location, barge_location]}
     
            
            tugboat_results.append(tugboat_order_results)
            
            
            #print("Barge collection infomations vvvvvvvvvvvvv")
            barge_steps = []
            barge_ids = []
            start_travel_barge = barge_location.enter_datetime
            for collection_info in collection_time_info['barge_collect_infos'][:]:
                #print(collection_info)
                barge = self.data['barges'][collection_info['barge_id']]
                barge_ready_time = self.get_ready_barge(barge)
                if barge_ready_time > start_travel_barge:
                    start_travel_barge = barge_ready_time
                
                
                
                start_barge_station_id = collection_info['travel_steps'][0].start_id
                end_barge_station_id = collection_info['travel_steps'][-1].end_id
                
              
                barge_id = collection_info['barge_id']
                
                
                if start_barge_station_id != end_barge_station_id:
                    travel_steps = generate_travel_steps_for_barge_collection(start_travel_barge, collection_info, order_trip, barge_ids)
                    barge_steps.extend(travel_steps)
                    start_travel_barge = travel_steps[-1].exit_datetime
                finish_barge_time = start_travel_barge + timedelta(minutes=collection_info['setup_time']*60)
                
                name = "Collecting Barge - " + collection_info['barge_id'] + " - " 
                name += f"({end_barge_station_id} to {str(end_barge_station_id)})"
                
                barge_step = DataPoint(
                    ID="Barge",
                    type="Barge Step Collection",
                    name=name,
                    enter_datetime=start_travel_barge,
                    #exit_datetime=finish_barge_time,
                    distance=0,
                    speed=0,
                    time=0,
                    type_point='travel_point',
                    rest_time=0,
                    barge_ids= barge_ids,
                    order_trip = order_trip,
                    station_id = end_barge_station_id,
                )
                barge_ids.append(barge_id)
                barge_step.exit_datetime = finish_barge_time
                start_travel_barge = finish_barge_time
                #print(collection_info)
                barge_steps.append(barge_step)
                start_station = data['stations'][end_barge_station_id]
            
            tugboat_order_results["data_points"].extend(barge_steps)
            start_info = {'station':start_station, 'location': (start_station.lat, start_station.lng)}
            end_station = data['stations'][appointment_info['appointment_station']]
            end_info = {'station':end_station, 'location': (end_station.lat, end_station.lng)}
            
            #print("River info ##########", tugboat.tugboat_id, start_station.water_type, end_station.water_type)
            if start_station.water_type == WaterBody.RIVER and end_station.water_type == WaterBody.RIVER:
                travel_river_info =  tugboat.calculate_travel_start_to_end_river_location(start_info, end_info, 
                                                                                        start_status=WaterBody.RIVER,
                                                                                        end_status= WaterBody.RIVER)
            elif start_station.water_type == WaterBody.SEA and end_station.water_type == WaterBody.RIVER:
                #raise Exception("Order type not supported", start_info,end_info)
                travel_river_info = tugboat.calculate_travel_start_to_end_river_location(start_info, end_info, 
                                                                                        start_status=WaterBody.SEA,
                                                                                        end_status= WaterBody.RIVER)
            else:
                raise Exception("Order type not supported", start_info,end_info)
            
            
            # for barge_step in barge_steps:
            #     print(barge_step)
            # print(start_barge_station_id, end_barge_station_id, travel_river_info['travel_steps'][0])
                
            self.update_travel_info(order, tugboat, travel_river_info)
            #print("River info", river_station.km, travel_river_info)
            
    
            arrival_datetime = get_next_quarter_hour( exit_barge_time + timedelta(minutes=travel_river_info['travel_time']*60))
            exit_appointment_time = get_next_quarter_hour(arrival_datetime + 
                                                          timedelta(minutes=len(tugboat.assigned_barges)*config_problem.BARGE_SETUP_MINUTES))
            
            travel_steps = generate_travel_steps(arrival_datetime, travel_river_info, barge_ids, extra=" Empty Barges")
            
            rest_time = sum([point.rest_time for point in travel_steps])
            
            # travel_to_customer = DataPoint(
            #     ID=order.start_object.order_id,
            #     type="Travel To Customer",
            #     name=order.start_object.name,
            #     enter_datetime=arrival_datetime,
            #     #exit_datetime=tugboat_schedule['end_datetime'],
            #     distance=travel_river_info['travel_distance'],
            #     time=travel_river_info['travel_time'],
            #     speed=travel_river_info['speed'],
            #     type_point='main_point',
            #     rest_time=rest_time,
            #     barge_ids= barge_ids,
            #     order_trip = order_trip,
            # )
            
            # tugboat_result['data_points'].append(travel_to_customer)
            # tugboat_result['data_points'].extend(travel_steps)
            # travel_to_customer.exit_datetime = last_point_exit_datetime
            
            
            
            
            
            # print(river_station.name)
            # print(appointment_info['appointment_station'])
            # appoinment_location ={
            #     "ID": order.start_object.order_id,
            #     'type': "Destination Barge",
            #     'name': f"Appointment From {start_station.name} To {appointment_info['appointment_station']}" ,
            #     'enter_datetime': arrival_datetime,
            #     'exit_datetime':arrival_datetime,
            #     'distance': travel_river_info['travel_distance'],
            #     'time': travel_river_info['travel_time'],
            #     'speed': travel_river_info['speed'],
            #     'type_point': 'main_point'
            # }
            barge_ids = [barge.barge_id for barge in tugboat.assigned_barges]
            appoinment_location = DataPoint(
                ID=order.start_object.order_id,
                type="Destination Barge",
                name=f"Appointment From {start_station.name} To {appointment_info['appointment_station']}",
                enter_datetime=arrival_datetime,
                #exit_datetime=arrival_datetime,
                distance=travel_river_info['travel_distance'],
                time=travel_river_info['travel_time'],
                speed=travel_river_info['speed'],
                type_point='main_point',
                rest_time=0,
                barge_ids=barge_ids,
                order_trip = order_trip,
                station_id = start_station.station_id,
                
            )
            barge_ids = [barge.barge_id for barge in tugboat.assigned_barges]
            tugboat_order_results['data_points'].append(appoinment_location) # add result data points
            trave_steps = generate_travel_steps(arrival_datetime, travel_river_info, order_trip=order_trip, 
                                                barge_ids=barge_ids, extra=" Empty Barges")
            tugboat_order_results['data_points'].extend(trave_steps)
         
            max_exit_datetime = max(trave_steps, key=lambda x: x.exit_datetime).exit_datetime
            appoinment_location.exit_datetime = max_exit_datetime
            
            
            time_release_barges = config_problem.BARGE_RELEASE_MINUTES*len(tugboat.assigned_barges)
            # release_barges_location ={
            #     "ID": appointment_info['appointment_station'],
            #     'type': "Barge Release",
            #     'name': "Release Barges (" + " - ".join(barge_ids) + ")",
            #     'enter_datetime': appoinment_location['exit_datetime'],
            #     'exit_datetime':appoinment_location['exit_datetime'] + timedelta(minutes=time_release_barges),
            #     'distance': 0,
            #     'speed': 0,
            #     'time': time_release_barges,
            #     'type_point': 'main_point'
            # }
            release_barges_location = DataPoint(
                ID=appointment_info['appointment_station'],
                type="Barge Release",
                name="Release Barges (" + " - ".join(barge_ids) + ")",
                enter_datetime=appoinment_location.exit_datetime,
                #exit_datetime=appoinment_location.exit_datetime + timedelta(minutes=time_release_barges),
                distance=0,
                time=time_release_barges,
                speed=0,
                type_point='main_point',
                rest_time=0,
                barge_ids=barge_ids,
                order_trip = order_trip,
                station_id = appoinment_location.station_id,
            )
            release_barges_location.exit_datetime = release_barges_location.enter_datetime + timedelta(minutes=time_release_barges)
            tugboat_order_results['data_points'].append(release_barges_location)
            release_steps = generate_release_steps(release_barges_location.enter_datetime, order_trip, barge_ids,
                                                   appoinment_location.station_id)
            tugboat_order_results['data_points'].extend(release_steps)
            
            
            appointment_station = self.data['stations'][appointment_info['appointment_station']]
            
            for i, release_step in enumerate(release_steps):
                self.update_single_barge_scheule(order, barge_ids[i], release_step.enter_datetime, release_step.exit_datetime, appointment_station.km, 
                                             appointment_station.water_type, (appointment_station.lat, appointment_station.lng), appointment_station.station_id)
                #print("Update barge schedule ##################### ", appointment_station.station_id, self.barge_scheule[barge_ids[i]][-1])
            
        #print("Time late start:", time_boat_lates)
        #print("Arrival times:", arrival_times)
        
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
                if barge_id in step.name:
                    return step
                if "Releasing" not in step.name:
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
            end_point = next((point for point in reversed(tugboat_result['data_points']) if point.type_point == "main_point"), None)
            
            station_last = data['stations'][end_point.ID]
            # Ensure schedule continuity by using previous end time as new start
            prev_end = self.tugboat_scheule[tugboat_id][-1]['end_datetime']
            #print("DEGUGGGGGGGGGGGGGGGGGGGG")
           
            #for point in tugboat_result['data_points']:
                #print(point)
            #print(tugboat_id, prev_end, end_point['enter_datetime'], end_point['exit_datetime'])
            new_start = max(end_point.enter_datetime, prev_end)
            
            info = {
                'tugboat_id': tugboat.tugboat_id,
                'order_id': order.order_id,
                'start_datetime': new_start,
                'end_datetime': max(end_point.exit_datetime, new_start),
                'barge_infos': [],
                'river_km': station_last.km,
                'water_status': station_last.water_type , 
                'location': (station_last.lat, station_last.lng),
                'station_id': station_last.station_id,
            }
            
            #tugboat._lat = station_last.lat 
            #tugboat._lng = station_last.lng
            #tugboat._km = station_last.km
            
            
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
            data_point_end = next((point for point in reversed(end_tugboat_result['data_points']) if point.type_point == "main_point" ), None)
            barge_end_loader = next((point for point in reversed(end_tugboat_result['data_points']) if barge_id in point.name and point.type_point == "Loader-Customer" ), None)
                
            station_last = data['stations'][data_point_end.ID]
            
            # Ensure barge schedule continuity by using max of previous end time and new start
            prev_barge_end = self.barge_scheule[barge_id][-1]['end_datetime']
            new_barge_start = max(prev_barge_end, data_point_start.enter_datetime)
            
            info = {
                'barge_id': barge_id,
                'order_id': order.order_id,
                'start_datetime': new_barge_start,
                'end_datetime': max(data_point_end.exit_datetime, new_barge_start),
                'river_km': station_last.km,
                'water_status': station_last.water_type, 
                'location': (station_last.lat, station_last.lng),
                'station_id':data_point_end.ID,
            }
            
            #print("Barge info main", info) if barge_id == "B_084" else None
            
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
        #print("Barge info:update_single_barge_scheule", info) if barge_id == "B_084" else None
            
    def update_shedule_bring_down_barges(self, order, lookup_order_barges, lookup_tugboat_results):
        data = self.data
    
        for order_id, order_barge_info in lookup_order_barges.items():
            barge_id = order_barge_info['barge_id']
            
            tugboat_result = self._find_tugboat_result(barge_id, lookup_tugboat_results)
            
            data_point_start = tugboat_result['data_points'][1]
            data_point_end = next((point for point in reversed(tugboat_result['data_points']) if point.type_point == "main_point" ), None)
            barge_end_loader = next((point for point in reversed(tugboat_result['data_points']) if barge_id in point.name and point.type_point == "Loader-Customer" ), None)
                
            station_last = data['stations'][data_point_end.ID]
            
            # Ensure barge schedule continuity by using max of previous end time and new start
            prev_barge_end = self.barge_scheule[barge_id][-1]['end_datetime']
            new_barge_start = max(prev_barge_end, data_point_start.enter_datetime)
            
            #print("Bring down barge", barge_id) if barge_id == "B_084" else None
            self.update_single_barge_scheule(order, barge_id, new_barge_start, max(data_point_end.exit_datetime, new_barge_start), station_last.km, 
                                             station_last.water_type, (station_last.lat, station_last.lng), data_point_end.ID)
       
        self.__update_tugboat_scheule(order, lookup_tugboat_results)
    
    def _reset_all_tugboats(self):
        tugboats = self.data['tugboats']
        for tugboat in tugboats.values():
            tugboat.reset()
              
    def _extend_update_tugboat_results(self, order, tugboat_results, order_trip):
        for tugboat_result in tugboat_results:
            for data_point in tugboat_result['data_points']:
                tugboat_id = tugboat_result['tugboat_id']
                data_point.order_trip = order_trip
                
                barges = [self.data['barges'][barge_id] for barge_id in data_point.barge_ids]
                if data_point.type == 'Barge Collection' or data_point.type == 'Barge Step Collection':
                    data_point.total_load = sum([barge.weight_barge for barge in barges])
                elif data_point.type == 'Start Order Carrier' or data_point.type == 'Crane-Carrier':
                    data_point.total_load = sum([barge.get_load(True) for barge in barges])
                elif data_point.type == 'Appointment' or  'Sea-River' in data_point.type:
                    data_point.total_load = sum([barge.get_load(True) for barge in barges])
                elif data_point.type == 'Barge Release':
                    data_point.total_load = sum([barge.get_load(True) for barge in barges])
                elif data_point.type == 'Barge Step Release':
                    data_point.total_load = sum([barge.get_load(True) for barge in barges])
                elif data_point.type == 'Barge Step Release':
                    data_point.total_load = sum([barge.get_load(True) for barge in barges])
                elif data_point.type == 'Barge Change' or data_point.type == 'Barge Change Collection':
                    data_point.total_load = sum([barge.get_load(True) for barge in barges])
                elif data_point.type == 'Customer Station' or  'River-River' in data_point.type:
                    if 'Empty' in data_point.type:
                        data_point.total_load = sum([barge.weight_barge for barge in barges])
                    else:
                        data_point.total_load = sum([barge.get_load(True) for barge in barges])
                elif data_point.type == 'Carrier Station':
                    data_point.total_load = sum([barge.get_load(True) for barge in barges])
                    
                
                
                #data_point.barge_ids = [barge.barge_id for barge in self.data['tugboats'][tugboat_id].assigned_barges]
                #if len(data_point.barge_ids) == 0:
                #    raise Exception("More than one barge in tugboat", data_point)
                data_point.barge_ids = ','.join([str(barge_id) for barge_id in data_point.barge_ids])
                
                
               
                if data_point.type_point == 'loading_point':
                    barge_id = data_point.name.split(' - ')[1]
                    search_barge = next((barge for barge in self.data['tugboats'][tugboat_id].assigned_barges if barge.barge_id == barge_id), None)
                
                    data_point.barge_ids = barge_id
                    data_point.total_load = search_barge.get_load(True)
                        
                    
                    
                
                
                
                
                
                
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
                    
    def _bring_barge_travel(self, order, barges, order_trip, is_import=True):
        """
        Unified method to handle both import and export barge travel.
        
        Args:
            order: The order being processed
            barges: List of barges to be assigned
            is_import: Boolean flag to determine if this is an import operation (default) or export
        
        Returns:
            Tuple of (isCompleted, tugboat_results)
        """
        # Select the appropriate tugboats based on operation type
        if is_import:
            tugboats = self.data['river_tugboats']
            tugboat_key = 'river_tugboat'
            # print("BRING_DOWN -------------------------------")
        else:
            tugboats = self.data['sea_tugboats']
            tugboat_key = 'sea_tugboat'
            
        tugboat_results = []
        iteration = 0
        while len(barges) > 0:
            #print("Barges remain:", len(barges))
            is_completed, assigned_tugboats = self.assign_barges_to_tugboats(order, tugboats, barges)
            #print("Assigned Barges:", len(barges))
            ##`if len(barges) > 0:
            #print("Not completed here bring barge travel",  len(assigned_tugboats), order.order_id, [tugboat.tugboat_id for tugboat in assigned_tugboats])
            #return False, tugboat_results
            iteration += 1
            if iteration > 100:
                print("Not completed here bring barge travel", order.order_id, len(barges))
                return False, tugboat_results
        
            if not is_completed:
                print("Not completed here bring barge travel", order.order_id, len(barges))
                return False, tugboat_results
                
            # Create appointment info for each assigned tugboat
            appointment_info = {}
            for i in range(len(assigned_tugboats)):
                tugboat = assigned_tugboats[i]
                tugboat_id = tugboat.tugboat_id
                appointment_info[tugboat_id] = {
                    tugboat_key: assigned_tugboats[i],
                    'tugboat_id': tugboat_id,
                    'appointment_station': config_problem.APPOINTMENT_STATION_BASE_REFERENCE_ID,
                    'meeting_time': None
                }
            
            # Process barge travel
            barge_tugboat_results, late_time = self.arrival_step_travel_empty_barges(order, assigned_tugboats, appointment_info, order_trip)
            tugboat_results.extend(barge_tugboat_results)
            
            # Debug info if needed
            for tugboat_result in barge_tugboat_results:
                # print(tugboat_result['tugboat_id'])
                df = pd.DataFrame(tugboat_result['data_points'])
                # print(df)
            
        return True, tugboat_results

    # Wrapper methods that maintain backward compatibility
    def _bring_barge_travel_import(self, order, bring_down_river_barges, order_trip):
        return self._bring_barge_travel(order, bring_down_river_barges, order_trip, is_import=True)
    
    def _bring_barge_travel_export(self, order, bring_up_sea_barges, order_trip):
        return self._bring_barge_travel(order, bring_up_sea_barges, order_trip, is_import=False)
    
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
            #print("loader_last_time_lookup", order, schedule_results, loader_last_time_lookup)
            #print("schedule_results", schedule_results, loader_last_time_lookup)
            #print(loader_last_time_lookup[key])
            if rate > 0:
                active_loadings.append({
                    'loader_id': f'ld{i+1}',
                    'rate': rate,
                    'time_ready':  loader_last_time_lookup[key] + 0.25 if key   in loader_last_time_lookup else loader_last_time_lookup[key],
                    'assigned_product': 0
                })
        return active_loadings
    
    def _init_active_cranes(self, order):
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
        #print("Assignment assigned_barge_infos GGGGGGGGGGGGGGGG:", based_brage_ids)
        
        sea_tugboats =  data['sea_tugboats'] 
        all_assigned_barges = [barge_info['barge'] for barge_info in assigned_barge_infos]
        temp_river_assigned_tugboats = []
        temp_sea_assigned_tugboats = []
        temp_river_tugboat_results = []
        temp_sea_tugboat_results = []
        schedule_results = []
        round_trip_order = 1
        
        debug_barges = {}
        for barge in all_assigned_barges:
            km = self.get_river_km_barge(barge)
            debug_barges[barge.barge_id] = {'barge_id': barge.barge_id, 'before_km': km}
            #if km > config_problem.RIVER_KM:
            #    print(barge.barge_id, km)
            
        # travel barge from top river to bottom river
        # filter barges to bring down river
        bring_down_river_barges = []
        save_load = {}
        for barge in all_assigned_barges:
            station_barge = self.data["stations"][self.get_station_id_barge(barge)]
            if self.get_river_km_barge(barge) > config_problem.RIVER_KM and station_barge.water_type == WaterBody.RIVER:
                save_load[barge.barge_id] = barge.get_load(is_only_load=True)
                barge.set_load(500)
                bring_down_river_barges.append(barge)
                continue
            #print(self.barge_scheule['B_084'][-1]) if barge.barge_id == "B_084" else None
            
        #print("DEBUG_BARGE", order.order_id, len(all_assigned_barges), len(bring_down_river_barges))
        if len(bring_down_river_barges) == 0:
            #print("No barge found to bring down river")
            pass
        else:
            #print("Bring down river barge", order.order_id, [barge.barge_id for barge in bring_down_river_barges])
            isCompleted, tugboat_results = self._bring_barge_travel_import(order, bring_down_river_barges, round_trip_order)
            if not isCompleted:
                print(" Not completed here Bring down river barge", order.order_id, [barge.barge_id for barge in bring_down_river_barges])
                return False, tugboat_results
            lookup_tugboat_results = {tugboat_result['tugboat_id']: tugboat_result for tugboat_result in tugboat_results}
            
            order_barges, lookup_order_barges = order_barges_from_arrival_tugboats(data, lookup_tugboat_results)
            self.update_shedule_bring_down_barges(order, lookup_order_barges, lookup_tugboat_results)  
            self._extend_update_tugboat_results(order, tugboat_results, 0)
            temp_river_tugboat_results.extend(tugboat_results)
            self._reset_all_tugboats()
        
        for barge in all_assigned_barges:
            if barge.barge_id in save_load.keys():
                barge.set_load(save_load[barge.barge_id])
        
     
        
        
        active_cranes_infos, active_loadings_infos = self._init_active_cranes(order)    
        first_arrival_customer_datetime = None
        iteration = 0
        #print("======================================================================")
        while len(all_assigned_barges) > 0:
            # print("Rotation barge remain:", len(all_assigned_barges))
            # barges_ids = [barge.barge_id for barge in all_assigned_barges]
            # for tugboat_id, tugboat in sea_tugboats.items():
            #      print(tugboat_id, len(tugboat.assigned_barges), barges_ids)
            
            iteration += 1
            
            
            
            copy_all_assigned_barges = all_assigned_barges.copy()
            is_completed, assigned_tugboats = self.assign_barges_to_tugboats(order, sea_tugboats, copy_all_assigned_barges)
            if not is_completed or iteration > 100:
                print("Not completed here assign barge to tugboat", order.order_id, len(all_assigned_barges))
                return False, {
                              'assign_barge_infos': assigned_barge_infos,
                              'assign_river_barges':temp_river_assigned_tugboats,
                              "sea_tugboat_results": temp_sea_tugboat_results,
                              'schedule_results': schedule_results,
                              "river_tugboat_results": temp_river_tugboat_results
                              }
            
            #print("len assigned_tugboats", len(assigned_tugboats), len(copy_all_assigned_barges), len(all_assigned_barges))
            
            #get total load of assigned_tugboats
            #before_total_load_barges = sum(tugboat.get_total_load(is_only_load=True) for tugboat in assigned_tugboats)
            
            if len(assigned_tugboats) == 0:
                raise Exception("No tugboat found for order: " + str(order.order_id), len(all_assigned_barges), len(temp_sea_tugboat_results))
                #print("Order: {} No tugboat found".format(order.order_id))
                break
            
            Sea_Total_load_barges = 0
            boat_brage_ids= []
            boat_load_weights = []
            #total_load = sum(barge_info['barge'].get_load(is_only_load=True) for barge_info in assigned_barge_infos)
            for tugboat in assigned_tugboats:
                load_barges = [b.get_load(is_only_load=True) for b in tugboat.assigned_barges]
                boat_load_weights.extend(load_barges)
                boat_brage_ids.extend([b.barge_id for b in tugboat.assigned_barges])
                #print(f"Assigning barges to Tugboat XX {tugboat.tugboat_id}... {load_barges} barges: {sum(load_barges)}")
                Sea_Total_load_barges += sum(load_barges)
            
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
                #print(f"Assigning barges to Tugboat XX {tugboat.tugboat_id}... {[b.barge_id for b in tugboat.assigned_barges]} barges: {sum(load_barges)}")
                total_load += sum(load_barges) 
                
            
            #print('MM Total load: ', total_load, order.demand)
            #print("barge_ids", barge_ids, len(set(barge_ids)), len(barge_ids))
            active_cranes = active_cranes_infos[-1]
            schedule_results = schedule_carrier_order_tugboats(order, assigned_tugboats, active_cranes, late_time)
            #print(schedule_results) if order.order_id == 'o1' else None
            
            #print("tugboat_schedule_results", schedule_results[0])
            
            
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
                    'appointment_station': config_problem.APPOINTMENT_STATION_BASE_REFERENCE_ID,
                    'meeting_time': None
                }
            travel_appointment_import(self, order, lookup_sea_schedule_results, 
                                    lookup_sea_tugboat_results, appointment_info, round_trip_order    )
            
            
            
            
            
            order_barges, lookup_order_barges = order_barges_from_arrival_tugboats(data, lookup_sea_tugboat_results)
            #print("----------------------------------------------------")
            #print(len(all_assigned_barges)- len(copy_all_assigned_barges), len(order_barges), len(all_assigned_barges))
            #for tugboat in assigned_tugboats:
                #print(tugboat)
                
            
            
            
            
            for tugboat in  assigned_tugboats:
                appoint_info = appointment_info[tugboat.tugboat_id]
                tugboat_id = appoint_info['tugboat_id']
                for barge in tugboat.assigned_barges:
                    barge_info = lookup_order_barges[barge.barge_id] 
                    barge_info['appointment_station'] = appoint_info['appointment_station']
                    
            appointment_station = config_problem.APPOINTMENT_STATION_BASE_REFERENCE_ID
            river_tugboats =  data['river_tugboats'] 
            #appointment_location= (stations[appointment_station].lat, stations[appointment_station].lng)
            river_assigned_tugboats = assign_barges_to_river_tugboats(self, stations[appointment_station], order,
                                                                    data, river_tugboats, order_barges)
            #print(order_barges)
            
            #teno_barges_ids = [b['barge'].barge_id for b in order_barges]
            
            #print("order_barges:",len(order_barges), len(set(teno_barges_ids)),  teno_barges_ids)
            
            
            #print("len river_assigned_tugboats", len(river_assigned_tugboats), len(order_barges))
            
            
            
            
            River_Total_load_barges = 0
            river_boat_barges= []
            boat_load_weights = []
            river_ids = []
            #total_load = sum(barge_info['barge'].get_load(is_only_load=True) for barge_info in assigned_barge_infos)
            for tugboat in river_assigned_tugboats:
                load_barges = [b.get_load(is_only_load=True) for b in tugboat.assigned_barges]
                boat_load_weights.extend(load_barges)
                river_boat_barges.extend([b for b in tugboat.assigned_barges])
                #print(f"Assigning barges to Tugboat XX {tugboat.tugboat_id}... {[b.barge_id for b in tugboat.assigned_barges]} barges: {sum(load_barges)}")
                River_Total_load_barges += sum(load_barges)
                river_ids.append(tugboat.tugboat_id)
            #print("River_Total_load_barges", River_Total_load_barges)
            #print("Sea_Total_load_barges", Sea_Total_load_barges)
            if River_Total_load_barges == Sea_Total_load_barges:
                all_assigned_barges = copy_all_assigned_barges
                #print("Is Equals ..........................", len(all_assigned_barges),  len(copy_all_assigned_barges))
                
            num = 2
            while River_Total_load_barges != Sea_Total_load_barges:
                #print(river_ids)
                #print(len(river_boat_barges))
                all_assigned_barges_ids = [b.barge_id for b in all_assigned_barges]
                copy_all_assigned_barges = all_assigned_barges.copy()
                if len(river_boat_barges) > 1+num:
                    for i in range(num+1):
                        river_boat_barges.pop()
                else:
                    break
                for barge in river_boat_barges:
                    #print(barge.barge_id)
                    all_assigned_barges.remove(barge)
                
                for tugboat in data['sea_tugboats'].values():
                    for barge in tugboat.assigned_barges:
                        self.barge_scheule[barge.barge_id].pop()
                    tugboat.reset()
                
                
                #print("Reset tugboats=============")
                #print(self.barge_scheule['B_084'][-2])
                
                
                is_completed, assigned_tugboats = self.assign_barges_to_tugboats(order, sea_tugboats, river_boat_barges)
                tugboat_results, late_time = self.arrival_step_transport_order(order, assigned_tugboats, order_trip=round_trip_order)
                active_cranes = active_cranes_infos[-1]
                schedule_results = schedule_carrier_order_tugboats(order, assigned_tugboats, active_cranes, late_time)
                #print(schedule_results) if order.order_id == 'o1' else None
                
                #print("tugboat_schedule_results", schedule_results[0])
                
                
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
                        'appointment_station': config_problem.APPOINTMENT_STATION_BASE_REFERENCE_ID,
                        'meeting_time': None
                    }
                travel_appointment_import(self, order, lookup_sea_schedule_results, 
                                    lookup_sea_tugboat_results, appointment_info, round_trip_order    )
            
            
            
            
            
                order_barges, lookup_order_barges = order_barges_from_arrival_tugboats(data, lookup_sea_tugboat_results)
            
                #print(len(all_assigned_barges), all_assigned_barges_ids)
                
                for tugboat in  assigned_tugboats:
                    appoint_info = appointment_info[tugboat.tugboat_id]
                    tugboat_id = appoint_info['tugboat_id']
                    for barge in tugboat.assigned_barges:
                        barge_info = lookup_order_barges[barge.barge_id] 
                        barge_info['appointment_station'] = appoint_info['appointment_station']
                    
                appointment_station = config_problem.APPOINTMENT_STATION_BASE_REFERENCE_ID
                river_tugboats =  data['river_tugboats'] 
                for tugboat in data['river_tugboats'].values():
                    tugboat.reset()
                #appointment_location= (stations[appointment_station].lat, stations[appointment_station].lng)
                river_assigned_tugboats = assign_barges_to_river_tugboats(self, stations[appointment_station], order,
                                                                    data, river_tugboats, order_barges)
                
                Sea_Total_load_barges = 0
                boat_brage_ids= []
                boat_load_weights = []
                #total_load = sum(barge_info['barge'].get_load(is_only_load=True) for barge_info in assigned_barge_infos)
                for tugboat in assigned_tugboats:
                    load_barges = [b.get_load(is_only_load=True) for b in tugboat.assigned_barges]
                    boat_load_weights.extend(load_barges)
                    boat_brage_ids.extend([b.barge_id for b in tugboat.assigned_barges])
                    #print(f"Assigning barges to Tugboat XX {tugboat.tugboat_id}... {load_barges} barges: {sum(load_barges)}")
                    Sea_Total_load_barges += sum(load_barges)
                    
                River_Total_load_barges = 0
                boat_brage_ids= []
                boat_load_weights = []
                #total_load = sum(barge_info['barge'].get_load(is_only_load=True) for barge_info in assigned_barge_infos)
                for tugboat in river_assigned_tugboats:
                    load_barges = [b.get_load(is_only_load=True) for b in tugboat.assigned_barges]
                    boat_load_weights.extend(load_barges)
                    boat_brage_ids.extend([b.barge_id for b in tugboat.assigned_barges])
                    #print(f"Assigning barges to Tugboat XX {tugboat.tugboat_id}... {load_barges} barges: {sum(load_barges)}")
                    River_Total_load_barges += sum(load_barges)
                
                
                if River_Total_load_barges != Sea_Total_load_barges:
                    all_assigned_barges = copy_all_assigned_barges
                    raise Exception("River Total load barges not equal to sea total load barges", 
                                     River_Total_load_barges, Sea_Total_load_barges)
                    #num += 1
                
           
                
            
        
            
            #for 
            #print after river assigned_tugboats
            
            river_tugboat_results, river_time_lates = self.arrival_step_river_transport(order, river_assigned_tugboats, 
                                                                                        lookup_order_barges, 
                                                                                        lookup_sea_tugboat_results, 
                                                                                        round_trip_order)
     
            
            
            
            
            
            lookup_river_tugboat_results = {result['tugboat_id']: result for result in river_tugboat_results}
            self.update_barge_infos( lookup_order_barges, lookup_river_tugboat_results)
            customer_river_time_lates = travel_trought_river_import_to_customer(order, lookup_river_tugboat_results, round_trip_order)
            
            list_lates = []
            for river_tugboat in river_assigned_tugboats:
                list_lates.append(customer_river_time_lates[river_tugboat.tugboat_id])
            
            active_loadings = active_loadings_infos[-1]
            river_schedule_results = shecdule_customer_order_tugboats(order, river_assigned_tugboats, active_loadings, list_lates)
            
            if len(river_schedule_results) == 0:
                return False, {
                              'assign_barge_infos': assigned_barge_infos,
                              'assign_river_barges':temp_river_assigned_tugboats,
                              "sea_tugboat_results": temp_sea_tugboat_results,
                              'schedule_results': schedule_results,
                              "river_tugboat_results": temp_river_tugboat_results
                              }
                print("river_schedule_results", order.order_id, active_loadings, len(active_loadings), len(river_assigned_tugboats))
            
            #print("River Schedule Results:", len(river_schedule_results), 
            #             river_schedule_results) if order.order_id == 'o3' else None
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
                        (first_arrival_customer_datetime > tugboat_result['data_points'][-1].enter_datetime)):
                        first_arrival_customer_datetime = tugboat_result['data_points'][-1].enter_datetime
            
        
                    
                    #print("River Tugboat Result:", tugboat_id, first_arrival_customer_datetime, tugboat_result['data_points'][-1])
            
            update_river_travel_tugboats(order, first_arrival_customer_datetime, lookup_river_schedule_results, 
                                         lookup_river_tugboat_results, temp_river_tugboat_results, round_trip_order)
            
            
            self.update_shedule(order, lookup_order_barges, lookup_sea_tugboat_results, lookup_river_tugboat_results)
          
            temp_river_assigned_tugboats.extend(river_assigned_tugboats)
            temp_sea_tugboat_results.extend(tugboat_results)
            temp_river_tugboat_results.extend(river_tugboat_results)
            
            
            self._extend_update_tugboat_results(order, tugboat_results, round_trip_order)
            self._extend_update_tugboat_results(order, river_tugboat_results,  round_trip_order)
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
        
        
           
                
        return True, {
            'assign_barge_infos': assigned_barge_infos,
            'assign_river_barges':temp_river_assigned_tugboats,
            "sea_tugboat_results": temp_sea_tugboat_results,
            'schedule_results': schedule_results,
            "river_tugboat_results": temp_river_tugboat_results
        }
    
    def travel_export(self, order):
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
        #print("Assignment assigned_barge_infos GGGGGGGGGGGGGGGG:", based_brage_ids)
        
        river_tugboats =  data['river_tugboats'] 
        all_assigned_barges = [barge_info['barge'] for barge_info in assigned_barge_infos]
        temp_river_assigned_tugboats = []
        temp_sea_assigned_tugboats = []
        temp_river_tugboat_results = []
        temp_sea_tugboat_results = []
        schedule_results = []
        round_trip_order = 1
        
        bring_up_river_barges = []
        save_load = {}
        for barge in all_assigned_barges:
            station_barge = self.data["stations"][self.get_station_id_barge(barge)]
            if station_barge.water_type == WaterBody.SEA:
                save_load[barge.barge_id] = barge.get_load(is_only_load=True)
                barge.set_load(500)
                bring_up_river_barges.append(barge)
                continue
            
         #print("DEBUG_BARGE", order.order_id, len(all_assigned_barges), len(bring_down_river_barges))
        if len(bring_up_river_barges) == 0:
            #print("No barge found to bring up river")
            pass
        else:
            #print("Bring up river barge", order.order_id, [barge.barge_id for barge in bring_up_river_barges])
            #print("Bring up river barge", order.order_id, [self.barge_scheule[barge.barge_id][-1]['station_id'] for barge in bring_up_river_barges])
            isCompleted, tugboat_results = self._bring_barge_travel_export(order, bring_up_river_barges, order_trip=round_trip_order)
            if not isCompleted:
                return False, tugboat_results
            lookup_tugboat_results = {tugboat_result['tugboat_id']: tugboat_result for tugboat_result in tugboat_results}
            
            order_barges, lookup_order_barges = order_barges_from_arrival_tugboats(data, lookup_tugboat_results)
            self.update_shedule_bring_down_barges(order, lookup_order_barges,
                                                  lookup_tugboat_results)  
            self._extend_update_tugboat_results(order, tugboat_results, 0)
            temp_sea_tugboat_results.extend(tugboat_results)
            self._reset_all_tugboats()
            
            #result = lookup_tugboat_results['SeaTB_02']
            #print(result)

            
       
            
        for barge in all_assigned_barges:
            if barge.barge_id in save_load.keys():
                barge.set_load(save_load[barge.barge_id])
            
        active_cranes_infos, active_loadings_infos = self._init_active_cranes(order)    
        first_arrival_carrier_datetime = None
        iteration = 0
        
        while len(all_assigned_barges) > 0: 
            # print("Rotation barge remain:", len(all_assigned_barges))
            # for tugboat_id, tugboat in sea_tugboats.items():
            #     print(tugboat_id, self.get_ready_time_tugboat(tugboat))
            
            copy_all_assigned_barges = all_assigned_barges.copy()
            is_completed, river_assigned_tugboats = self.assign_barges_to_tugboats(order, river_tugboats, copy_all_assigned_barges)
            iteration += 1
            if not is_completed or iteration > 100:
                print("Not completed here assign barge to tugboat", order.order_id, len(all_assigned_barges))
                return False, {
                              'assign_barge_infos': assigned_barge_infos,
                              'assign_river_barges':temp_river_assigned_tugboats,
                              "sea_tugboat_results": temp_sea_tugboat_results,
                              'schedule_results': schedule_results,
                              "river_tugboat_results": temp_river_tugboat_results
                              }
            if len(river_assigned_tugboats) == 0:
                raise Exception("No tugboat found for order: " + str(order.order_id), len(all_assigned_barges), len(temp_sea_tugboat_results))
                #print("Order: {} No tugboat found".format(order.order_id))
                break


            
            River_Total_load_barges = 0
            boat_brage_ids= []
            boat_load_weights = []
            #total_load = sum(barge_info['barge'].get_load(is_only_load=True) for barge_info in assigned_barge_infos)
            for tugboat in river_assigned_tugboats:
                load_barges = [b.get_load(is_only_load=True) for b in tugboat.assigned_barges]
                barge_locations = [self.get_station_id_barge(b) for b in tugboat.assigned_barges]
                boat_load_weights.extend(load_barges)
                boat_brage_ids.extend([b.barge_id for b in tugboat.assigned_barges])
                #print(f"Assigning barges to Tugboat XX {tugboat.tugboat_id}... {[b.barge_id for b in tugboat.assigned_barges]} barges: {sum(load_barges)}")
                #print(f"Barge locations: {barge_locations}")
                River_Total_load_barges += sum(load_barges)
                # get barge location
                
                
            river_tugboats_results, late_times = self.arrival_step_transport_order(order, river_assigned_tugboats, order_trip=round_trip_order)

            
            active_loadings = active_loadings_infos[-1]
            river_schedule_results = shecdule_customer_order_tugboats(order, river_assigned_tugboats, active_loadings, late_times)

            active_loadings = self.__create_active_loadings(order, river_schedule_results)
            active_loadings_infos.append(active_loadings)
            
            #print("river_schedule_results", river_schedule_results[0])
            
            
            lookup_river_tugboat_results = {result['tugboat_id']: result for result in river_tugboats_results}
            lookup_river_schedule_results = {result['tugboat_schedule']['tugboat_id']: result for result in river_schedule_results}
            
            appointment_info = {}
            for i in range(len(river_tugboats_results)):
                tugboat = river_tugboats_results[i]
                tugboat_id = tugboat['tugboat_id']
                appointment_info[tugboat_id] = {
                    'river_tugboat': river_assigned_tugboats[i],
                    'tugboat_id': tugboat_id,
                    'appointment_station': config_problem.APPOINTMENT_STATION_BASE_REFERENCE_ID,
                    'meeting_time': None
                }
            travel_appointment_export(self, order, lookup_river_schedule_results, 
                                    lookup_river_tugboat_results, appointment_info, round_trip_order    )
            
            
            order_barges, lookup_order_barges = order_barges_from_arrival_tugboats(data, lookup_river_tugboat_results)
            for tugboat in  river_assigned_tugboats:
                appoint_info = appointment_info[tugboat.tugboat_id]
                tugboat_id = appoint_info['tugboat_id']
                for barge in tugboat.assigned_barges:
                    barge_info = lookup_order_barges[barge.barge_id] 
                    barge_info['appointment_station'] = appoint_info['appointment_station']
                    
            appointment_station = config_problem.APPOINTMENT_STATION_BASE_REFERENCE_ID
            sea_tugboats =  data['sea_tugboats'] 
         
            
            appointment_location= (stations[appointment_station].lat, stations[appointment_station].lng)
            sea_assigned_tugboats = assign_barges_to_sea_tugboats(self, appointment_location, order,
                                                                    data, sea_tugboats, order_barges)
            
            
           
            
            
            Sea_Total_load_barges = 0
            sea_boat_barges= []
            boat_load_weights = []
            sea_ids = []
            #total_load = sum(barge_info['barge'].get_load(is_only_load=True) for barge_info in assigned_barge_infos)
            for tugboat in sea_assigned_tugboats:
                load_barges = [b.get_load(is_only_load=True) for b in tugboat.assigned_barges]
                boat_load_weights.extend(load_barges)
                sea_boat_barges.extend([b for b in tugboat.assigned_barges])
                #print(f"Assigning barges to Tugboat XX {tugboat.tugboat_id}... {[b.barge_id for b in tugboat.assigned_barges]} barges: {sum(load_barges)}")
                Sea_Total_load_barges += sum(load_barges)
                sea_ids.append(tugboat.tugboat_id)
            
            
            if River_Total_load_barges == Sea_Total_load_barges:
                all_assigned_barges = copy_all_assigned_barges
            
            num = 2
            
            while River_Total_load_barges != Sea_Total_load_barges:
                #print(river_ids)
                #print(len(river_boat_barges))
                all_assigned_barges_ids = [b.barge_id for b in all_assigned_barges]
                copy_all_assigned_barges = all_assigned_barges.copy()
                if len(sea_boat_barges) > 1+num:
                    for i in range(num+1):
                        sea_boat_barges.pop()
                else:
                    break
                for barge in sea_boat_barges:
                    #print(barge.barge_id)
                    all_assigned_barges.remove(barge)
                
                for tugboat in data['sea_tugboats'].values():
                    for barge in tugboat.assigned_barges:
                        self.barge_scheule[barge.barge_id].pop()
                    tugboat.reset()
            
            
                is_completed, assigned_tugboats = self.assign_barges_to_tugboats(order, river_tugboats, sea_boat_barges)
                sea_tugboat_results, sea_time_lates = self.arival_step_to_sea_transport(order, assigned_tugboats, 
                                                                                        lookup_order_barges, 
                                                                                        lookup_river_tugboat_results, 
                                                                                        round_trip_order)
                
                active_cranes = active_cranes_infos[-1]
                sea_schedule_results = schedule_carrier_order_tugboats(order, sea_assigned_tugboats, active_cranes, list_lates)
                active_cranes = self.__create_active_cranes(order, sea_schedule_results)
                active_cranes_infos.append(active_cranes)  
                
                
                lookup_river_schedule_results = {result['tugboat_schedule']['tugboat_id']: result for result in river_schedule_results}
                lookup_sea_schedule_results = {result['tugboat_schedule']['tugboat_id']: result for result in sea_schedule_results}
            

                
                appointment_info = {}
                for i in range(len(river_tugboats_results)):
                    tugboat = river_tugboats_results[i]
                    tugboat_id = tugboat['tugboat_id']
                    appointment_info[tugboat_id] = {
                        'river_tugboat': river_assigned_tugboats[i],
                        'tugboat_id': tugboat_id,
                        'appointment_station': config_problem.APPOINTMENT_STATION_BASE_REFERENCE_ID,
                        'meeting_time': None
                    }
                travel_appointment_export(self, order, lookup_river_schedule_results, 
                                        lookup_river_tugboat_results, appointment_info, round_trip_order    )
                
                
                order_barges, lookup_order_barges = order_barges_from_arrival_tugboats(data, lookup_river_tugboat_results)
                
                for tugboat in  river_assigned_tugboats:
                    appoint_info = appointment_info[tugboat.tugboat_id]
                    tugboat_id = appoint_info['tugboat_id']
                    for barge in tugboat.assigned_barges:
                        barge_info = lookup_order_barges[barge.barge_id] 
                        barge_info['appointment_station'] = appoint_info['appointment_station']
                        
                appointment_station = config_problem.APPOINTMENT_STATION_BASE_REFERENCE_ID
                sea_tugboats =  data['sea_tugboats'] 
                for tugboat in sea_tugboats.values():
                    tugboat.reset()
                
                appointment_location= (stations[appointment_station].lat, stations[appointment_station].lng)
                sea_assigned_tugboats = assign_barges_to_sea_tugboats(self, appointment_location, order,
                                                                        data, sea_tugboats, order_barges)
                River_Total_load_barges = 0
                boat_brage_ids= []
                boat_load_weights = []
                #total_load = sum(barge_info['barge'].get_load(is_only_load=True) for barge_info in assigned_barge_infos)
                for tugboat in river_assigned_tugboats:
                    load_barges = [b.get_load(is_only_load=True) for b in tugboat.assigned_barges]
                    boat_load_weights.extend(load_barges)
                    boat_brage_ids.extend([b.barge_id for b in tugboat.assigned_barges])
                    #print(f"Assigning barges to Tugboat XX {tugboat.tugboat_id}... {load_barges} barges: {sum(load_barges)}")
                    River_Total_load_barges += sum(load_barges)
                
                Sea_Total_load_barges = 0
                boat_brage_ids= []
                boat_load_weights = []
                #total_load = sum(barge_info['barge'].get_load(is_only_load=True) for barge_info in assigned_barge_infos)
                for tugboat in sea_assigned_tugboats:
                    load_barges = [b.get_load(is_only_load=True) for b in tugboat.assigned_barges]
                    boat_load_weights.extend(load_barges)
                    boat_brage_ids.extend([b.barge_id for b in tugboat.assigned_barges])
                    #print(f"Assigning barges to Tugboat XX {tugboat.tugboat_id}... {load_barges} barges: {sum(load_barges)}")
                    Sea_Total_load_barges += sum(load_barges)
                
                if River_Total_load_barges != Sea_Total_load_barges:
                    all_assigned_barges = copy_all_assigned_barges.copy()
                    raise Exception("River and Sea Total Load Barges are not equal",
                                    River_Total_load_barges, Sea_Total_load_barges)
                    
            sea_tugboat_results, sea_time_lates = self.arival_step_to_sea_transport(order, sea_assigned_tugboats, 
                                                                                        lookup_order_barges, 
                                                                                        lookup_river_tugboat_results, 
                                                                                        round_trip_order)
            
            
            lookup_sea_tugboat_results = {result['tugboat_id']: result for result in sea_tugboat_results}
            self.update_barge_infos( lookup_order_barges, lookup_sea_tugboat_results)
            customer_sea_time_lates = travel_trought_sea_export_to_customer(order, lookup_sea_tugboat_results,
                                                                            round_trip_order)
            
            list_lates = []
            for sea_tugboat in sea_assigned_tugboats:
                list_lates.append(customer_sea_time_lates[sea_tugboat.tugboat_id])
                
            active_cranes = active_cranes_infos[-1]
            sea_schedule_results = schedule_carrier_order_tugboats(order, sea_assigned_tugboats, active_cranes, list_lates)
            
            if len(sea_schedule_results) == 0:
                return False, {
                    'assign_barge_infos': assigned_barge_infos,
                    'assign_river_barges':temp_river_assigned_tugboats,
                    "sea_tugboat_results": temp_sea_tugboat_results,
                    'schedule_results': schedule_results,
                    "river_tugboat_results": temp_river_tugboat_results
                }
            
            
            active_cranes = self.__create_active_cranes(order, sea_schedule_results)
            active_cranes_infos.append(active_cranes)  
            
            lookup_sea_schedule_results = {result['tugboat_schedule']['tugboat_id']: result for result in sea_schedule_results}
            
            
            update_export_river_travel_tugboats(self, order, lookup_sea_tugboat_results, lookup_river_tugboat_results)
            
            if round_trip_order == 1:
                for tugboat_id, tugboat_result in lookup_sea_tugboat_results.items():
                    if ((first_arrival_carrier_datetime is None) or 
                        (first_arrival_carrier_datetime > tugboat_result['data_points'][-1].enter_datetime)):
                        first_arrival_carrier_datetime = tugboat_result['data_points'][-1].enter_datetime
            
            update_export_sea_travel_tugboats(self, order, first_arrival_carrier_datetime, lookup_sea_schedule_results, 
                                         lookup_sea_tugboat_results, temp_sea_tugboat_results, round_trip_order)
            
         
            self.update_shedule(order, lookup_order_barges, lookup_sea_tugboat_results, lookup_river_tugboat_results)
            
            temp_river_tugboat_results.extend(river_tugboats_results)
            temp_sea_tugboat_results.extend(sea_tugboat_results)
            temp_sea_assigned_tugboats.extend(sea_assigned_tugboats)
            
            self._extend_update_tugboat_results(order, river_tugboats_results, round_trip_order)
            self._extend_update_tugboat_results(order, sea_tugboat_results,  round_trip_order)
            
            #print("Sea tugboat results", sea_tugboat_results)
            
            
            
            round_trip_order += 1    
            self._reset_all_tugboats()
        
        return True, {
            'assign_barge_infos': assigned_barge_infos,
            'assign_river_barges':temp_river_assigned_tugboats,
            "sea_tugboat_results": temp_sea_tugboat_results,
            'schedule_results': schedule_results,
            "river_tugboat_results": temp_river_tugboat_results
        }

    def insert_stop_rows(self,
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
        #print(df[df['tugboat_id'] == 'RiverTB_02'][mask].head(50))
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
        stop_rows['type_point'] = 'water_level_point'

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
    
    def insert_waiting_load_unload_rows(self, df):
        type_col = 'type'
        valid_travel_values = ('Crane-Carrier')
        # Work on a copy
        df = df.copy()

        # Ensure required columns exist
        required = { type_col}
        missing = [c for c in required if c not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        # Build condition mask
        mask = (
            df[type_col].isin(valid_travel_values)
        )
        
        original_rows = df[mask]
        to_insert_after = original_rows.copy()
        to_insert_before = original_rows.copy()

        if to_insert_after.empty:
            # Nothing to insert — return original as-is
            return df.reset_index(drop=True)
        
    def generate_schedule(self, order_ids , xs = None):
        data = self.data
        barges = data['barges']
        orders = data['orders']
        tugboats = data['tugboats']
        
        #sorted order_ids base on start_datetime
        #print("Input Order IDs", order_ids)
        order_ids = sorted(order_ids, key=lambda x: orders[x].start_datetime)
        #print("After Input Order IDs", order_ids)
        
        self.code_info.set_code(xs)
   
        all_dfs = []
        barge_dfs = []
        
        total_tugboat_weight = 0
        isSolutionCompleted = True
        for order_id in order_ids:
            order = orders[order_id]
            if order.order_type == TransportType.IMPORT:
                isCompleted, result_order1 = self.travel_import(order)
            
            else:
                isCompleted, result_order1 = self.travel_export(order)
            
            
            # try:
            #     if order.order_type == TransportType.IMPORT:
            #         isCompleted, result_order1 = self.travel_import(order)
                
            #     else:
            #         isCompleted, result_order1 = self.travel_export(order)
            # except Exception as e:
            #     print("Error in generate_schedule", e)
            #     isCompleted = False
            #     result_order1 = None
                
                #print("River tugboat results",isCompleted, result_order1['river_tugboat_results'])
                #print("Sea tugboat results",isCompleted, result_order1['sea_tugboat_results'])
            
            
            if not isCompleted:
                print("----------------------------------------------------- Order {} is not completed".format(order.order_id), order.order_type, order.demand)
                isSolutionCompleted = False
            if (result_order1 is None) or (not "assign_barge_infos" in result_order1):
                continue
            
            
            
            
            
            #print(order)
            # print("Tugboat available time for order {}".format(order.order_id), " ###################################################")
            #for tugboat_id, single_tugboat_schedule in self.tugboat_scheule.items():
                 #print(tugboat_id, single_tugboat_schedule[-1]['end_datetime'])
            
            # print("Barge available time for order {}".format(order.order_id))
            # for barge_id, single_barge_schedule in barges.items():
            #     barge_ready_time = self.get_ready_barge(single_barge_schedule)
            #     if barge_ready_time < order.start_datetime:
            #         print(barge_id, barge_ready_time)
            
            #total_weight = sum(barge.capacity for barge_id, barge in barges.items() 
            #                   if self.get_ready_barge(barge) < order.due_datetime - timedelta(days=4))
            #print(order.order_id, "order start time: {}".format(order.start_datetime))
            #print("########### Total weight for available barges: {}".format(total_weight))
            
            
            total_load_tugboat_order = 0
            assigned_barge_infos = result_order1['assign_barge_infos']
            sea_tugboat_results = result_order1['sea_tugboat_results']
            river_tugboat_results = result_order1['river_tugboat_results']
            schedule_results = result_order1['schedule_results']
            #assigned_river_barge_infos = result_order1['assign_river_barges']
        
            
            
            
            #break
            
            # Assume sea_tugboat_results is a list of tugboat dictionaries
            first_tugboat_results =sea_tugboat_results
            second_tugboat_results =river_tugboat_results
            if order.order_type == TransportType.EXPORT:
                first_tugboat_results =river_tugboat_results
                second_tugboat_results =sea_tugboat_results
            
            
            
            for tugboat in first_tugboat_results:
                df = pd.DataFrame([data_point.to_dict() for data_point in tugboat['data_points']])
                df['tugboat_id'] = tugboat['tugboat_id']  # Add tugboat ID to each row
                df['order_id'] = order.order_id
                df['water_type']= 'Sea'
                all_dfs.append(df)
                total_load_tugboat_order += tugboat['data_points'][0].total_load
                #print("      single tugboat", tugboat['tugboat_id'],tugboat.keys(), len(sea_tugboat_results))
                # if tugboat['tugboat_id'] == "RiverTB_11":
                #     print("RiverTB_11 ###################################################")
                #     #sorted df by enter_datetime
                #     df = df.sort_values(by='enter_datetime')["station_id"]
                #     print(df.head(40))
                
                
            for tugboat in second_tugboat_results:
                df = pd.DataFrame([ data_point.to_dict() for data_point in tugboat['data_points']])
                df['tugboat_id'] = tugboat['tugboat_id']  # Add tugboat ID to each row
                df['order_id'] = order.order_id
                df['water_type']= 'River'
                all_dfs.append(df)
                # if tugboat['tugboat_id'] == "SeaTB_02":
                #     print("SeaTB_02 ###################################################")
                #     #sorted df by enter_datetime
                #     df = df.sort_values(by='enter_datetime')
                #     print(df.head(40))
                
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
            
            # print("############## Order: {}, Total Load: {}".format(order.order_id, total_load_tugboat_order))
                
            df = pd.DataFrame(assigned_barge_infos)
            barge_dfs.append(df)
            #print("order_id", order_id)
            #print(df)
            #print(assigned_barge_infos)

            # Merge all into one DataFrame
        # combined_df = pd.concat(all_dfs, ignore_index=True)
            # Show the final merged DataFrame
        #print(combined_df)

        
        if len(all_dfs) == 0:
            return False, None, None
        
        #print("Length:", len(pd.concat(all_dfs, ignore_index=True)))
        df = pd.concat(all_dfs, ignore_index=True)
        df_with_stops = self.insert_stop_rows(
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
        # print("Column Datas-------------------------------------")
        # print(df_with_stops.columns)
        
        
        return isSolutionCompleted, df_with_stops, pd.concat(barge_dfs, ignore_index=True)

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
            if row['type'] in ['Barge Collection', 'Start Order Carrier', 'Appointment', 'Barge Change', 
                               'Customer Station','Barge Release', 'Carrier Station']:
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
        worksheet_timeline.freeze_panes(3, 6)
        writer.close()
        # output_df_data.to_excel('tugboat_timeline_analysis.xlsx')
        barge_df.to_excel(barge_path, index=False)

    def calculate_cost(self, tugboat_df_o, barge_df):
        
        # filter only main_type = 'TUGBOAT'
        tugboat_df = tugboat_df_o[(tugboat_df_o['type'] == 'Customer Station') | 
                                  (tugboat_df_o['type'] == 'Appointment') 
                                  #| (tugboat_df_o['type'] == 'Barge Collection')
                                  ]
        
        cost_results = {}
        data = self.data
        tugboats = data['tugboats']
        orders = data['orders']
        tugboat_df_grouped = tugboat_df.groupby(['tugboat_id', 'order_id'], as_index=False).agg({'time': 'sum', 'distance': 'sum'})
        
        tugboat_df_grouped['consumption_rate'] = np.zeros(len(tugboat_df_grouped))
        tugboat_df_grouped['soft_fuel_con'] = np.zeros(len(tugboat_df_grouped))
        tugboat_df_grouped['min_fuel_con'] = np.zeros(len(tugboat_df_grouped))
        tugboat_df_grouped['cost'] = np.zeros(len(tugboat_df_grouped))
        
        #tugboat_df_grouped['load'] = np.zeros(len(tugboat_df_grouped))
        
        for tugboat_id, tugboat in tugboats.items():
            for order_id, order in orders.items():
                tugboat_df_grouped.loc[(tugboat_df_grouped['tugboat_id'] == tugboat_id) & (tugboat_df_grouped['order_id'] == order_id), 
                                       'consumption_rate'] = tugboat.max_fuel_con
                
        tugboat_df_grouped['cost'] = tugboat_df_grouped['time'] * tugboat_df_grouped['consumption_rate']     
        
        tugboat_dfv2 = tugboat_df[(tugboat_df['type'] == 'Customer Station') | (tugboat_df['type'] == 'Appointment')]
        tugboat_df_groupedv2 = tugboat_dfv2.groupby(['tugboat_id', 'order_id'], as_index=False)
    
        for name, group in tugboat_df_groupedv2:
            tugboat_df_grouped.loc[(tugboat_df_grouped['tugboat_id'] == name[0]) & (tugboat_df_grouped['order_id'] == name[1]), 
                                       'total_load'] = (group['total_load'].sum())
        
        
        #group2
        tugboat_dfg2 = tugboat_df_o[(tugboat_df_o['type'] == 'Barge Change') | (tugboat_df_o['type'] == 'Barge Change') | 
                                  (tugboat_df_o['type'] == 'Barge Change')]
        
        cost_results = {}
        data = self.data
        tugboats = data['tugboats']
        orders = data['orders']
        tugboat_df_groupedg2 = tugboat_dfg2.groupby(['tugboat_id', 'order_id'], as_index=False).agg({'time': 'sum', 'distance': 'sum'})
        
        tugboat_df_groupedg2['consumption_rate'] = np.zeros(len(tugboat_df_groupedg2))
        tugboat_df_groupedg2['soft_fuel_con'] = np.zeros(len(tugboat_df_groupedg2))
        tugboat_df_groupedg2['min_fuel_con'] = np.zeros(len(tugboat_df_groupedg2))
        tugboat_df_groupedg2['cost'] = np.zeros(len(tugboat_df_groupedg2))
        
        #tugboat_df_grouped['load'] = np.zeros(len(tugboat_df_grouped))
        
        for tugboat_id, tugboat in tugboats.items():
            for order_id, order in orders.items():
                tugboat_df_groupedg2.loc[(tugboat_df_groupedg2['tugboat_id'] == tugboat_id) & (tugboat_df_groupedg2['order_id'] == order_id), 
                                       'consumption_rate'] = tugboat.min_fuel_con
                
        tugboat_df_groupedg2['cost'] = tugboat_df_groupedg2['time'] * tugboat_df_groupedg2['consumption_rate']     
        
        tugboat_dfg2v2 = tugboat_dfg2[(tugboat_dfg2['type'] == 'Barge Change') | 
                                      (tugboat_dfg2['type'] == 'Barge Change') | 
                                  (tugboat_dfg2['type'] == 'Barge Change')]
        tugboat_dfg2v2 = tugboat_dfg2v2.groupby(['tugboat_id', 'order_id'], as_index=False)
    
        for name, group in tugboat_dfg2v2:
            tugboat_df_groupedg2.loc[(tugboat_df_groupedg2['tugboat_id'] == name[0]) & (tugboat_df_groupedg2['order_id'] == name[1]), 
                                       'total_load'] = (group['total_load'].sum())
            
        
        
       
        #merge tugboat_df_grouped and tugboat_df_groupedg2
        #tugboat_df_grouped = pd.concat([tugboat_df_grouped, tugboat_df_groupedg2], ignore_index=True)
       
        
        return cost_results, tugboat_df_o, barge_df, tugboat_df_grouped
    
    def calculate_full_cost(self, tugboat_df, barge_df=None):
        #group tugboat_df by tugboat_id and order_id and order_trip
        tugboat_df_grouped = tugboat_df.groupby(['order_id','tugboat_id',  'order_trip'], as_index=False)
        
        #create pandas df with 
        columns = [
            "TugboatId",
            "OrderId",
            "Time",
            "Distance",
            "ConsumptionRate",
            "Cost",
            "TotalLoad",
            "StartDatetime",
            "StartPointDatetime",
            "FinishDatetime",
            "StartStationId",
            "StartPointStationId",
            "EndPointStationId",
            "UnloadLoadTime",
            "ParkingTime",
            "MoveTime",
            "OrderTrip",
            "AllTime",
        ]

        # Create an empty DataFrame with these columns
        output_df = pd.DataFrame(columns=columns)
        data = self.data
        tugboats = data['tugboats']
        orders = data['orders']
        
        for name, group in tugboat_df_grouped:
            mask = ((tugboat_df['order_id'] == name[0]) &
                    (tugboat_df['tugboat_id']   == name[1]) &
                    (tugboat_df['order_trip'] == name[2]))
            
            tugboat = tugboats[name[1]]
            order = orders[name[0]]
            #print(name)
            #fixed result not assign to output_df add new row output_df 
            startPointDatetime = group[group['type'] == 'Start Order Carrier']['enter_datetime'].min()
            if startPointDatetime is pd.NaT:
                startPointDatetime = group[group['type'] == 'Start Order Customer']['enter_datetime'].min()
            
            #print(startPointDatetime, None)
            #if NaT when start order carrier is empty
      
            if startPointDatetime is pd.NaT:
                startPointDatetime = group[group['type'] == 'Barge Change']['enter_datetime'].min()
            if startPointDatetime is pd.NaT:
                startPointDatetime = group[group['type'] == 'Destination Barge']['enter_datetime'].min()
            
            startStationId = group[group['type'] == 'Start']['name'].iloc[0].replace('River Start at ', '')
            startStationId = startStationId.replace('Start at ', '')
            
            appointment = group[group['type'] == 'Appointment']['ID']
            if len(appointment) > 0:
                endPointStationId = appointment.iloc[0]
                startPointStationId = order.start_object.station.station_id
            else:
                endPointStationId = order.des_object.station.station_id
                
                ids = group[group['type'] == 'Barge Change']['ID']
                if len(ids) > 0:
                    startPointStationId = ids.iloc[0]
                else:
                    #print(group)
                    startPointStationId = group[group['type'] == 'Destination Barge']['name'].iloc[0].split(' ')[-1]
            
            startDatetime = group['enter_datetime'].min()
            finishDatetime = group['exit_datetime'].max()
            
            #delta time hours between startDatetime and finishDatetime
            delta_time = (finishDatetime - startDatetime).total_seconds() / 3600
            
            load_unload = 0
            if len(group[group['type'] == 'Crane-Carrier']['exit_datetime']) > 0:
                load_unload = (group[group['type'] == 'Crane-Carrier']['exit_datetime'].max() - group[group['type'] == 'Crane-Carrier']['enter_datetime'].min()).total_seconds() / 3600 
            if len(group[group['type'] == 'Loader-Customer']['exit_datetime']) > 0:
                #print("Loader Customer", group)
                load_unload += (group[group['type'] == 'Loader-Customer']['exit_datetime'].max() - group[group['type'] == 'Loader-Customer']['enter_datetime'].min()).total_seconds() / 3600 
                #load_unload += (group[group['type'] == 'Loader-Customer']['exit_datetime'].max() - group[group['type'] == 'Loader-Customer']['enter_datetime'].iloc[0]).total_seconds() / 3600 - group[group['type'] == 'Customer Station']['time'].iloc[0]
            
            
            load_unload +=  group[group['type'] == 'Barge Step Release']['time'].sum()
                      
            #tugboat_df_grouped
            
            parkingTime = group[group['name'].str.contains('stop at')]['rest_time'].sum()
            #time_move = 0
            havy_time_move = group[(group['type'] == 'Customer Station') | (group['type'] == 'Carrier Station') |
                                  (group['type'] == 'Appointment') ]['time'].sum()
            soft_time_move = group[(group['type'] == 'Barge Collection') | 
                                  (group['type'] == 'Travel To Carrier') |
                                  (group['type'] == 'Barge Change')]['time'].sum()
            #time_move = group['time'].sum()
            output_df = output_df._append({
                "TugboatId": name[1],
                "OrderId": name[0],
                "Time": havy_time_move,
                "Distance": group['distance'].sum(),
                "ConsumptionRate": tugboat.max_fuel_con,
                "Cost": havy_time_move*tugboat.max_fuel_con,
                "TotalLoad": group['total_load'].max(),
                "StartDatetime": startDatetime,
                "FinishDatetime": finishDatetime,
                "StartPointDatetime": startPointDatetime,
                "StartStationId": startStationId,
                "StartPointStationId": startPointStationId,
                "EndPointStationId": endPointStationId,
                "UnloadLoadTime": load_unload,
                "ParkingTime": parkingTime,
                "MoveTime": soft_time_move,
                "OrderTrip": name[2],
                "AllTime": delta_time,
               #"UnloadLoadTime": group['unload_load_time'].max(),
                #"ParkingTime": group['parking_time'].max(),
            }, ignore_index=True)
            # output_df.loc[mask, "TugboatId"] = name[0]
            # output_df.loc[mask, "OrderId"] = name[1]
            # output_df.loc[mask, "OrderTrip"] = name[2]
            # output_df.loc[mask, "TotalLoad"] = (group['total_load'].max())
            # output_df.loc[mask, "Distance"] = (group['total_load'].sum())            
            #print(group)
        #print(output_df.head(40))
        return output_df
    
    def calculate_full_barge_cost(self, tugboat_df):
        #group barge_df by barge_id and order_id and order_trip
        tugboat_df_grouped = tugboat_df.groupby(['order_id','tugboat_id',  'order_trip'], as_index=False)
        data = self.data
        tugboats = data['tugboats']
        orders = data['orders']
        barges = data['barges']
        
        #create pandas df with 
        columns = [
            "BargeId",
            "TugboatId",
            "OrderId",
            "Time",
            "Distance",
            "Cost",
            "Load",
            "StartDatetime",
            "StartPointDatetime",
            "FinishDatetime",
            "StartStationId",
            "StartPointStationId",
            "EndPointStationId",
            "UnloadLoadTime",
            "ParkingTime",
            "MoveTime",
            "OrderTrip",
            "AllTime",
        ]
        
        output_df = pd.DataFrame(columns=columns)
        
        for name, group in tugboat_df_grouped:
            mask = ((tugboat_df['order_id'] == name[0]) &
                    (tugboat_df['tugboat_id']   == name[1]) &
                    (tugboat_df['order_trip'] == name[2]))
            
            tugboat = tugboats[name[1]]
            order = orders[name[0]]
        
            appointment = group[group['type'] == 'Appointment']
            total_load_barge = 0
            if len(appointment) > 0:
                #print appointment single first row
                object_element = appointment.iloc[0]
                total_load_barge = object_element['total_load']
            else:
                ids = group[group['type'] == 'Barge Change']
                if len(ids) > 0:
                    object_element = ids.iloc[0]
                    total_load_barge = object_element['total_load']
                else:
                    #print(group)
                    object_element = group[group['type'] == 'Destination Barge'].iloc[0]
                    total_load_barge = object_element['total_load']
            
            
            time_consumption = 0
            
            time_consumption = group[(group['type'] == 'Customer Station') | 
                                  (group['type'] == 'Appointment') ]['time'].sum()
            distance = group[(group['type'] == 'Customer Station') | 
                                  (group['type'] == 'Appointment') ]['distance'].sum()
            
            startPointDatetime = group[group['type'] == 'Start Order Carrier']['enter_datetime'].min()
            #print(startPointDatetime, None)
            #if NaT when start order carrier is empty
            if startPointDatetime is pd.NaT:
                startPointDatetime = group[group['type'] == 'Start Order Customer']['enter_datetime'].min()
            
            
            
      
            if startPointDatetime is pd.NaT:
                if order.order_type == TransportType.IMPORT:
                    startPointDatetime = group[group['type'] == 'Barge Change']['enter_datetime'].min()
                else:
                    startPointDatetime = group[group['type'] == 'Barge Collection']['enter_datetime'].min()
            if  startPointDatetime is pd.NaT:
                if order.order_type == TransportType.IMPORT:
                    startPointDatetime = group[group['type'] == 'Destination Barge']['enter_datetime'].min()
                else:
                    startPointDatetime = group[group['type'] == 'Barge Change']['enter_datetime'].min()
            if startPointDatetime is pd.NaT:
                print(group)
                raise Exception("Start Point Datetime is None")
            
            barge_ids = object_element['barge_ids'].split(',')
            if order.order_type == TransportType.EXPORT:
                
                ids = group[group['type'] == 'Carrier Station']
                if len(ids) > 0:
                    object_element = ids.iloc[0]
                    barge_ids = object_element['barge_ids'].split(',')
                #print("Barge+od", barge_ids)
            
            
            
            total_barge_weight = group[(group['type'] == 'Customer Station') | 
                                  (group['type'] == 'Appointment') ]['total_load'].sum()
            for barge_id in barge_ids: 
                sub_mask = ((tugboat_df['order_id'] == name[0]) &
                        (tugboat_df['tugboat_id']   == name[1]) &
                        (tugboat_df['order_trip'] == name[2]) &
                        (tugboat_df['barge_ids'].str.contains(barge_id)))    
                time_consumption =  0
                isFinishDatetime = False
         
                items = group[(group['name'].str.contains(barge_id)) & (group['type'] == 'Barge Step Collection') ]
                if len(items) > 0:
                    startDatetime = items['enter_datetime'].iloc[0]
                    startStationId = items['name'].iloc[0].split(' ')[-1].replace(')', '')
                    finishDatetime = group[(group['name'].str.contains(barge_id)) & (group['type'] == 'Barge Step Release')]['exit_datetime'].max()
                    isFinishDatetime = True
                else:
                    items = group[(group['name'].str.contains(barge_id)) & (group['type'] == 'Barge Change Collection')]
                    if len(items) > 0:
                        startDatetime = items['enter_datetime'].iloc[0]
                        if order.order_type == TransportType.IMPORT:
                            startStationId = items['name'].iloc[0].split(' ')[-1].replace(')', '')
                            finishDatetime = group[(group['name'].str.contains(barge_id)) & (group['type'] == 'Loader-Customer')]['exit_datetime'].max()
                        else:
                            startStationId = items['ID'].iloc[0]
                            finishDatetime = group[(group['name'].str.contains(barge_id)) & (group['type'] == 'Crane-Carrier')]['exit_datetime'].max()
                        isFinishDatetime = True
                    else:
                        #print("--------------------------")
                        #print(group)
                        items = group[(group['name'].str.contains(barge_id)) & (group['type'] == 'Barge Change Collection')]
                        startDatetime = items['enter_datetime'].iloc[0]
                        startStationId = items['name'].iloc[0].split(' ')[-1].replace(')', '')
                        finishDatetime = group[(group['name'].str.contains(barge_id)) & (group['type'] == 'Loader-Customer')]['exit_datetime'].max()
                        isFinishDatetime = True                        
                        
                items = group[(group['name'].str.contains(barge_id)) & (group['type'] == 'Crane-Carrier')]
                if len(items) > 0:
                    startPointStationId = order.start_object.station.station_id
                    #print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
                    #print(group)
                    if order.order_type == TransportType.IMPORT:
                        endPointStationId = group[(group['type'] == 'Appointment')]['ID'].iloc[0]
                    else:
                        endPointStationId = group[(group['type'] == 'Carrier Station')]['ID'].iloc[0]
                else:
                    items = group[(group['name'].str.contains(barge_id)) & (group['type'] == 'Barge Change Collection')]
                    if len(items) == 0:
                        items = group[(group['name'].str.contains(barge_id)) & (group['type'] == 'Barge Step Collection')]
                    
                    startPointStationId = items['name'].iloc[0].split(' ')[-1].replace(')', '')
                    endPointStationId = order.des_object.station.station_id
                
                
                #delta time hours between startDatetime and finishDatetime
                delta_time = (finishDatetime - startDatetime).total_seconds() / 3600
                
                
                load_unload = 0
                items = group[(group['type'] == 'Crane-Carrier') & (group['name'].str.contains(barge_id))]
                load_barge = 0
                if len(items) > 0:
                    element = items.iloc[0]
                    load_barge = element['total_load']
                    load_unload = (element['exit_datetime'] - element['enter_datetime']).total_seconds() / 3600 
                
                items = group[(group['type'] == 'Loader-Customer') & (group['name'].str.contains(barge_id))]
                if len(items) > 0:
                    element = items.iloc[0]
                    load_barge = element['total_load']
                    load_unload += (element['exit_datetime'] - element['enter_datetime']).total_seconds() / 3600 
                
                # if load_barge == 0:
                #     print("0000000000000000")
                #     print(group)
                #     print("0000000000000000")
                #     raise Exception("Load barge is 0")
                
                load_unload +=  group[(group['type'] == 'Barge Step Release') & (group['barge_ids'].str.contains(barge_id))]['time'].sum()
                        
                            
                
                parkingTime = group[(group['name'].str.contains('stop at')) & (group['barge_ids'].str.contains(barge_id))]['rest_time'].sum()
                #time_move = 0
                
                havy_time_move = group[((group['type'] == 'Customer Station') | 
                                    (group['type'] == 'Appointment') & (group['barge_ids'].str.contains(barge_id))) ]['time'].sum()
                soft_time_move = group[((group['type'] == 'Barge Collection') | 
                                (group['type'] == 'Travel To Carrier') |
                                (group['type'] == 'Barge Change')) & (group['barge_ids'].str.contains(barge_id))]['time'].sum()
                
                if not isFinishDatetime or finishDatetime is None or finishDatetime is pd.NaT or finishDatetime == '':
                    print("finishDatetime id is none ..........................................", finishDatetime)
                    print(group)
  
                output_df = output_df._append({
                    "BargeId": barge_id,
                    "TugboatId": name[1],
                    "OrderId": name[0],
                    "Time": havy_time_move,
                    "Distance": distance,
                    "Cost": havy_time_move*tugboat.max_fuel_con*load_barge/total_barge_weight,
                    "Load": load_barge,
                    "StartDatetime": startDatetime,
                    "StartPointDatetime": startPointDatetime,
                    "FinishDatetime": finishDatetime,
                    "StartStationId": startStationId,
                    "StartPointStationId": startPointStationId,
                    "EndPointStationId": endPointStationId,
                    "UnloadLoadTime": load_unload,
                    "ParkingTime": parkingTime,
                    "MoveTime": soft_time_move,
                    "OrderTrip": name[2],
                    "AllTime": delta_time,
                }, ignore_index=True)
        
            
        return output_df
                
    
    def generate_schedule_v2(self, order_ids , xs = None):
        data = self.data
        barges = data['barges']
        orders = data['orders']
        tugboats = data['tugboats']
        
        # total barge capacity
        total_barge_capacity = sum(b.capacity for b in barges.values())
        print("Total barge capacity", total_barge_capacity)
        
        # total load demand
        total_load_demand = sum(o.demand for o in orders.values())
        print("Total load demand", total_load_demand)
        
        all_orders = [orders[oid] for oid in order_ids]
        start_date = min(order.start_datetime.date() for order in all_orders)
        end_date = max(order.due_datetime.date() for order in all_orders)
        
        
        #จัดลำดับสลับไปจน barge หมด
        #ทำสลับ order import export ดูจำนวน barge ที่ว่าง
        #Step 5 days assign
        #rate assign 2000 tun/days/order
        
        #check first is import or export
        is_do_import = True
        start_travel_datetime = start_date
        #next start 5 days
        target_travel_datetime = start_travel_datetime + timedelta(days=5)
        
        
        assigned_orders = set()
        remaining_orders = set(order_ids)
        step_count = 0
        MAX_ORDER_RATE_DEMAND = 500
        print("MAX_ORDER_RATE_DEMAND:", MAX_ORDER_RATE_DEMAND)
        
        remaining_load_demand_order_ids = {}
        for order_id in order_ids:
            order = orders[order_id]
            remaining_load_demand_order_ids[order_id] = order.demand
        
        
        while remaining_orders:
            step_count += 1
            
            
            # Get orders in current time window
            current_window_orders = []
            remain_time_orders = {}
            for order_id in remaining_orders:
                order = orders[order_id]
                if start_travel_datetime <= order.start_datetime.date() <= target_travel_datetime:
                    #delta time
                    #convert target_travel_datetime date to datetime
                    target_travel_datetimev2 = datetime.combine(target_travel_datetime, datetime.min.time())
                    
                    
                    delta_time = (target_travel_datetimev2 - order.start_datetime).total_seconds() / 3600
                    print(delta_time)
                    current_window_orders.append(order_id)
                    remain_time_orders[order_id] = delta_time
                elif order.start_datetime.date() <= target_travel_datetime:
                    delta_time = 5*24
                    current_window_orders.append(order_id)
                    remain_time_orders[order_id] = delta_time
                    
            if len(current_window_orders) == 0:
                target_travel_datetime += timedelta(days=5)
                start_travel_datetime += timedelta(days=5)
                continue
                    
            print(f"\n=== STEP {step_count}: {start_travel_datetime} to {target_travel_datetime} ===")
            print(f"Orders in window: {len(current_window_orders)}")
            
            # Process by type preference
            if is_do_import:
                import_orders = [oid for oid in current_window_orders 
                                if orders[oid].order_type == TransportType.IMPORT]
                export_orders = [oid for oid in current_window_orders 
                                if orders[oid].order_type == TransportType.EXPORT]
                process_list = import_orders + export_orders
            else:
                export_orders = [oid for oid in current_window_orders 
                                if orders[oid].order_type == TransportType.EXPORT]
                import_orders = [oid for oid in current_window_orders 
                                if orders[oid].order_type == TransportType.IMPORT]
                process_list = export_orders + import_orders
            
            # Iterate assign barge until all orders assigned
            for order_id in process_list:
                order = orders[order_id]
                
                before_remain = remaining_load_demand_order_ids[order_id]
                # Check available capacity
                available_barges = [b for b in barges.values() 
                                if self.get_ready_barge(b) <= order.start_datetime]
                total_capacity = sum(b.capacity for b in available_barges)
                max_assign_order_demand = remain_time_orders[order_id]*MAX_ORDER_RATE_DEMAND
                if total_capacity >= max_assign_order_demand:
                    remaining_load_demand_order_ids[order_id] -= max_assign_order_demand
                else:
                    remaining_load_demand_order_ids[order_id] -= total_capacity
                
                
                if remaining_load_demand_order_ids[order_id] <= 0:
                    remaining_load_demand_order_ids[order_id] = 0
                    print(f"  ✓ {order_id} [{order.order_type.name}]  {before_remain} ")
                    remaining_orders.remove(order_id)
                
                elif remaining_load_demand_order_ids[order_id] > 0:
                    print(f"  ✓ {order_id} [{order.order_type.name}]  {remaining_load_demand_order_ids[order_id]}")
                    print(f"  ✗ {order_id} - Nex round", order.demand - remaining_load_demand_order_ids[order_id])
                    
                else:
                    print(f"  ✗ {order_id} - Insufficient capacity")
            
            # Move to next window
            start_travel_datetime = target_travel_datetime + timedelta(days=1)
            target_travel_datetime = start_travel_datetime + timedelta(days=5)
            is_do_import = not is_do_import
            
            # Safety breaks
            if step_count > 50 or start_travel_datetime > end_date:
                break

        print(f"\nAssigned: {len(assigned_orders)}, Remaining: {len(remaining_orders)}")
            
        
        
        
                
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        

        

        print(f"\nTimeline from {start_date} to {end_date}")

        # Create date list
        date_list = []
        current_date = start_date
        while current_date <= end_date:
            date_list.append(current_date)
            current_date += timedelta(days=1)

        # Print timeline for each order
        for order_id in order_ids:
            order = orders[order_id]
            order_start = order.start_datetime.date()
            order_end = order.due_datetime.date()
            
            timeline = ""
            for date in date_list:
                timeline += "###" if order_start <= date <= order_end else " "
            
            type_char = "I" if order.order_type == TransportType.IMPORT else "E"
            print(f"{order_id} [{type_char}] {order.demand:>6} |{timeline}|")

        # Print date markers every 5 days
        print(" " * 20 + "|", end="")
        for i, date in enumerate(date_list):
            if i % 5 == 0:
                print(date.strftime("%d"), end="")
            else:
                print(" ", end="")
        print("|")
        
        pass
    