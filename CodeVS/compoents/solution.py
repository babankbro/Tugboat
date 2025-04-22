from CodeVS.operations.assigned_barge import *
from CodeVS.operations.transport_order import *


class Solution:
    def __init__(self, data):
        self.data = data
        self.tugboat_scheule = {}
        self.barge_scheule = {}
        self.tugboat_travel_results = {}
        
        for tugboat_id, tugboat in data['tugboats'].items():
            info = {
                'tugboat_id': tugboat.tugboat_id,
                'order_id': None,
                'start_datetime': tugboat._ready_time,
                'end_datetime': tugboat._ready_time,
                'river_km': tugboat._km,
                'water_status': tugboat._status , 
                'location': (tugboat._lat, tugboat._lng),
                'station_id': None,
                'barge_infos': [],
                 
            }
            self.tugboat_scheule[tugboat_id] = [info]
            
            self.tugboat_travel_results[tugboat.tugboat_id] = []
            
            
        for barge_id, barge in data['barges'].items():
            info = {
                'barge_id': barge.barge_id,
                'order_id': None,
                'start_datetime': barge._ready_time,
                'end_datetime': barge._ready_time,
                'river_km': barge._river_km,
                'water_status': barge._water_status, 
                'location': (barge._lat, barge._lng),
                'station_id': barge._station_id,
                    
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
            if (self.get_ready_barge(b)is None or self.get_ready_barge(b) < order_end - timedelta(days=3) ) 
        ]
        
        # sum the capacity of available barges
        total_capacity = sum(b.capacity for b in available_barges)
        print(f"AS  Total capacity: {total_capacity}")
        
        # For import orders, sort by distance to carrier
        if order.order_type == TransportType.IMPORT:
            carrier_location = (order.start_object.lat, order.start_object.lng)
            available_barges.sort(key=lambda b: 
             
                ((self.get_location_barge(b)[0] - carrier_location[0])**2 + 
                (self.get_location_barge(b)[1] - carrier_location[1])**2)**0.5)
        
        print(f"Remaining: {remaining_demand} | Available: {len(available_barges)}")
        
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
            barge.load = assign_amount
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
                print("Tugboat is not ready",order.order_id, order.due_datetime, tugboat_ready_time)  
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
    
    def arrival_step_transport_order(self, order, assigned_tugboats):
        time_boat_lates = []
        tugboat_results = []
        arrival_times = []
        for tugboat in assigned_tugboats:
            tugboat_info = self.tugboat_scheule[tugboat.tugboat_id][-1]
            
            collection_time_info = tugboat.calculate_collection_barge_time(tugboat_info, self.barge_scheule)
            travel_info = tugboat.calculate_travel_to_start_object(self.barge_scheule)
            
            first_barge_location = collection_time_info['barge_collect_infos'][0]
            tugboat_ready_time = self.get_ready_time_tugboat(tugboat)
            start_location = {
                "ID": "Start",
                'type': "Start",
                'name': "Start",
                'enter_datetime': tugboat_ready_time,
                'exit_datetime': tugboat_ready_time,
                'distance': 0,
                'time': 0,
                'speed': 0
            }
            
            barge_ready_time = tugboat_ready_time + timedelta(minutes=first_barge_location['travel_time']*60)
            barge_location ={
                "ID": "Barge",
                'type': "Barge",
                'name': "Barge Location",
                'enter_datetime': barge_ready_time,
                'exit_datetime': barge_ready_time + timedelta(minutes=collection_time_info['total_time']*60),
                'distance': first_barge_location['travel_distance'],
                'speed': tugboat.max_speed,
                'time': first_barge_location['travel_time'],
            }
            
            #if travel_info['travel_distance'] > 50:
                #raise Exception('Not on the sea')
            
            tugboat_order_results = {'tugboat_id': tugboat.tugboat_id, 
                                    "data_points" : [start_location, barge_location]}
            
            tugboat_results.append(tugboat_order_results)
            
            travel_total_time = collection_time_info['total_time'] + travel_info['travel_time']
        # print(total_time, travel_info)
            
            start_time_needed = order.start_datetime - timedelta(minutes=travel_total_time*60)
            start_time_needed = get_previous_quarter_hour(start_time_needed)
            arrival_time_needed = order.start_datetime
            time_lated_start = 0
            tugboat_ready_time = self.get_ready_time_tugboat(tugboat)
            if tugboat_ready_time > start_time_needed:
                arrival_time = tugboat_ready_time + timedelta(minutes=travel_total_time*60)
                print("arrival_time TT", arrival_time, start_time_needed, (tugboat_ready_time - start_time_needed))
                time_lated_start = (tugboat_ready_time - start_time_needed).total_seconds() / 3600
                start_time_needed = tugboat_ready_time
            else:
                arrival_time = arrival_time_needed
            
            time_boat_lates.append(time_lated_start)
            arrival_times.append(arrival_time)
            
            # process time backward from arraive time to new start time
            
            new_barge_location_exit_time = arrival_time - timedelta(minutes=travel_info['travel_time']*60)
            new_barge_location_exit_time = get_previous_quarter_hour(new_barge_location_exit_time)
            new_barge_location_enter_time = new_barge_location_exit_time - timedelta(minutes=collection_time_info['total_time']*60)
            new_barge_location_enter_time = get_previous_quarter_hour(new_barge_location_enter_time)
            new_start_location_exit_time = new_barge_location_enter_time - timedelta(minutes=first_barge_location['travel_time']*60)
            new_start_location_exit_time = get_previous_quarter_hour(new_start_location_exit_time)
            
            
            barge_location['enter_datetime'] = new_barge_location_enter_time
            barge_location['exit_datetime'] = new_barge_location_exit_time
            start_location['enter_datetime'] = new_start_location_exit_time
            start_location['exit_datetime'] = new_start_location_exit_time
            barge_location['order_distance'] = travel_info['travel_distance']
            barge_location['order_time'] = travel_info['travel_time']
            barge_location['barge_speed'] = travel_info['speed']
            barge_location['order_arrival_time'] = arrival_time
            
        #print("Time late start:", time_boat_lates)
        #print("Arrival times:", arrival_times)
        
        return tugboat_results, time_boat_lates

    def arrival_step_river_transport(self ,river_tugboats, lookup_barge_infos):
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
            
            collection_time_info = tugboat.calculate_collection_barge_time(tugboat_info, self.barge_scheule)
            tugboat_info = self.tugboat_scheule[tugboat.tugboat_id][-1]

            
            
            
            tugboat_ready_time = self.get_ready_time_tugboat(tugboat)
            
            # Create start location data point
            start_location = {
                "ID": "Start",
                'type': "Start",
                'name': "Start",
                'enter_datetime': tugboat_ready_time,
                'exit_datetime': tugboat_ready_time,
                'distance': 0,
                'time': 0,
                'speed': 0
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
            appointment_station =Travel_Helper.data['stations'][  barge_info['appointment_station']]
            barge_location = {
                "ID": appointment_station.station_id,
                'type': "Barge Change",
                'name': appointment_station.name,
                'enter_datetime': barge_ready_time,
                'exit_datetime': barge_ready_time + timedelta(minutes=collection_time_info['total_time']*60),
                'distance': first_barge_location['travel_distance'],
                'speed': tugboat.max_speed,
                'time': first_barge_location['travel_time'],
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
            
            
        #     # Update data points with calculated times
            barge_location['enter_datetime'] = new_barge_location_enter_time
            barge_location['exit_datetime'] = new_barge_location_exit_time
            start_location['enter_datetime'] = new_start_location_exit_time
            start_location['exit_datetime'] = new_start_location_exit_time
            
            # Add additional metrics
            #barge_location['order_distance'] = travel_info['travel_distance']
            #barge_location['order_time'] = travel_info['travel_time']
            #barge_location['barge_speed'] = travel_info['speed']
            #barge_location['order_arrival_time'] = arrival_time
        
        #print("River Tugboat Time Lates:", time_boat_lates)
        #print("River Tugboat Arrival Times:", arrival_times)
        
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
            end_point = tugboat_result['data_points'][-1]
            station_last = data['stations'][end_point['ID']]
            info = {
                'tugboat_id': tugboat.tugboat_id,
                'order_id': order.order_id,
                'start_datetime':end_point['enter_datetime'],
                'end_datetime': end_point['exit_datetime'],
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
            if tugboat_id== 'tbs1' :
                print(order.order_id, info['barge_infos'])
            #print("tugboat_scheule result",tugboat_id,  len( self.tugboat_scheule[tugboat_id]))
    
    def update_shedule(self, order, lookup_order_barges, 
                       lookup_sea_tugboat_results, lookup_river_tugboat_results):
        data = self.data
    
        for order_id, order_barge_info in lookup_order_barges.items():
            barge_id = order_barge_info['barge_id']
            
            start_tugboat_result = self._find_tugboat_result(barge_id, lookup_sea_tugboat_results)
            end_tugboat_result = self._find_tugboat_result(barge_id, lookup_river_tugboat_results)
            
            data_point_start = start_tugboat_result['data_points'][1]
            data_point_end = end_tugboat_result['data_points'][-1]
            station_last = data['stations'][data_point_end['ID']]
            
            info = {
                'barge_id': barge_id,
                'order_id': order.order_id,
                'start_datetime': data_point_start['enter_datetime'],
                'end_datetime': data_point_end['exit_datetime'],
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
        
    def _reset_all_tugboats(self):
        tugboats = self.data['tugboats']
        for tugboat in tugboats.values():
            tugboat.reset()
            
    
    def _extend_update_tugboat_results(self, temp_tugboat_results, tugboat_results, order_trip):
        for tugboat_result in tugboat_results:
            for data_point in tugboat_result['data_points']:
                tugboat_id = tugboat_result['tugboat_id']
                data_point['order_trip'] = order_trip
                data_point['total_load'] = sum([barge.get_load() for barge in self.data['tugboats'][tugboat_id].assigned_barges])
                data_point['barge_ids'] = [barge.barge_id for barge in self.data['tugboats'][tugboat_id].assigned_barges]
                data_point['barge_ids'] = ','.join([str(barge_id) for barge_id in data_point['barge_ids']])
                
                
        if len(temp_tugboat_results) == 0:
            temp_tugboat_results.extend(tugboat_results)
        else:
            for tugboat_result in tugboat_results:
                isFound = False
                tugboat_result['order_trip'] = order_trip
                for temp_tugboat_result in temp_tugboat_results:
                    if temp_tugboat_result['tugboat_id'] == tugboat_result['tugboat_id']:
                        isFound = True
                        temp_tugboat_result['data_points'].extend(tugboat_result['data_points'])
                        break
                if not isFound:
                    temp_tugboat_results.append(tugboat_result)
                    
     
    def travel_import(self, order):
        data = self.data
        orders = data['orders']
        barges = data['barges']
        stations = data['stations']
        
        assigned_barge_infos = self.assign_barges_to_single_order( order, barges)
        print("Assignment assigned_barge_infos:", len(assigned_barge_infos))
        assigned_barges_print = [(barge_info['barge'].barge_id, barge_info['barge'].load) for barge_info in assigned_barge_infos]
        total_load = sum(barge_info['barge'].load for barge_info in assigned_barge_infos)
        #print(assigned_barges_print)
        print('Total load: ', total_load, order.demand)
        
        sea_tugboats =  data['sea_tugboats'] 
        all_assigned_barges = [barge_info['barge'] for barge_info in assigned_barge_infos]
        temp_river_assigned_tugboats = []
        temp_sea_assigned_tugboats = []
        temp_river_tugboat_results = []
        temp_sea_tugboat_results = []
        round_trip_order = 1
        while len(all_assigned_barges) > 0:
            print("Rotation barge remain:", len(all_assigned_barges))
            for tugboat_id, tugboat in sea_tugboats.items():
                print(tugboat_id, self.get_ready_time_tugboat(tugboat))
            assigned_tugboats = self.assign_barges_to_tugboats(order, sea_tugboats, all_assigned_barges)
            print("Assignment results:", len(assigned_tugboats))
            
            
            tugboat_results, late_time = self.arrival_step_transport_order(order, assigned_tugboats)
            
            
            total_load = 0
            barge_ids = []
            for tugboat in assigned_tugboats:
                load_barges = [b.load for b in tugboat.assigned_barges]
                barge_ids.extend([b.barge_id for b in tugboat.assigned_barges])
                print(f"Assigning barges to Tugboat XX {tugboat.tugboat_id}... {load_barges} barges: {sum(load_barges)}")
                total_load += sum(load_barges) 
                
            
            print('MM Total load: ', total_load, order.demand)
            print("barge_ids", barge_ids)
            
            schedule_results = schedule_carrier_order_tugboats(order, assigned_tugboats, late_time)
            
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
            travel_appointment_import(order, lookup_sea_schedule_results, 
                                    lookup_sea_tugboat_results, appointment_info)
            
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
            
            river_tugboat_results, river_time_lates = self.arrival_step_river_transport(river_assigned_tugboats, lookup_order_barges)
            
            
            
            
            
            
            lookup_river_tugboat_results = {result['tugboat_id']: result for result in river_tugboat_results}
            self.update_barge_infos( lookup_order_barges, lookup_river_tugboat_results)
            customer_river_time_lates = travel_trought_river_import_to_customer(order, lookup_river_tugboat_results)
            
            
            list_lates = []
            for river_tugboat in river_assigned_tugboats:
                list_lates.append(customer_river_time_lates[river_tugboat.tugboat_id])
            
            
            river_schedule_results = shecdule_customer_order_tugboats(order, river_assigned_tugboats, list_lates)
            lookup_river_schedule_results = {result['tugboat_schedule']['tugboat_id']: result for result in river_schedule_results}
            
            update_sea_travel_tugboats(self,  order, lookup_sea_tugboat_results, lookup_river_tugboat_results)
            update_river_travel_tugboats(order, lookup_river_schedule_results, lookup_river_tugboat_results)
            
            
            self.update_shedule(order, lookup_order_barges, lookup_sea_tugboat_results, lookup_river_tugboat_results)
          
            temp_river_assigned_tugboats.extend(river_assigned_tugboats)
            
            
            
            self._extend_update_tugboat_results(temp_sea_tugboat_results, tugboat_results, round_trip_order)
            self._extend_update_tugboat_results(temp_river_tugboat_results, river_tugboat_results,  round_trip_order)
            round_trip_order += 1            
                        
            self._reset_all_tugboats()  
            
            
            
        
           
                
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
        for order_id, order in orders.items():
            if order.order_type != TransportType.IMPORT:
                continue
        
            #print(order)
            print("Tugboat available time for order {}".format(order.order_id))
            for tugboat_id, single_tugboat_schedule in self.tugboat_scheule.items():
                 print(tugboat_id, single_tugboat_schedule[-1]['end_datetime'])
            
            # print("Barge available time for order {}".format(order.order_id))
            # for barge_id, single_barge_schedule in barges.items():
            #     barge_ready_time = self.get_ready_barge(single_barge_schedule)
            #     if barge_ready_time < order.start_datetime:
            #         print(barge_id, barge_ready_time)
            
            total_weight = sum(barge.capacity for barge_id, barge in barges.items() if self.get_ready_barge(barge) < order.start_datetime)
            print(order.order_id, "order start time: {}".format(order.start_datetime))
            print("########### Total weight for available barges: {}".format(total_weight))
            
            
            
            
            
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
            
               
                
            df = pd.DataFrame(assigned_barge_infos)
            barge_dfs.append(df)
            #print("order_id", order_id)
            #print(df)
            #print(assigned_barge_infos)

            # Merge all into one DataFrame
        combined_df = pd.concat(all_dfs, ignore_index=True)
            # Show the final merged DataFrame
        #print(combined_df)
        combined_df.to_csv('tugboat_schedule_v2.csv', index=False)
        combined_df = pd.concat(barge_dfs, ignore_index=True)
        #print(combined_df)
        combined_df.to_csv('barges.csv', index=False)
        
        
            # break
            # print('Order 1------------------------------------------------------------:')
            # for barge_info in assigned_barge_infos:
            #     print(barge_info['barge'].barge_id, barge_info)
            
            # print()
            
            
            
            # print('Sea Travel Order1')
            # for result in sea_tugboat_results:
            #     #print(result)
            #     print("Travel for Tugboat", result['tugboat_id'], "------------------------------------")
            #     # if 'tbs1' != result['tugboat_id']:
            #     #     continue
            #     for data_point in result['data_points']:
            #         print(data_point)
            #         print()
            # """"""       
            # for result in schedule_results:
            #     print(result)
                
            
            
            
            # print('River Travel Order1')
            # for result in river_tugboat_results:
            #     #print(result)
            #     print("Travel for Tugboat", result['tugboat_id'], "------------------------------------")
            #     # if 'tbs1' != result['tugboat_id']:
            #     #     continue
            #     for data_point in result['data_points']:
            #         print(data_point)
            #         print()
            
            
            # for tugboat_id in self.tugboat_scheule:
            #     tugboat_schedule = self.tugboat_scheule[tugboat_id]
            #     if len(tugboat_schedule) <= 1:
            #         continue
            #     print("Tugboat", tugboat_id, "schedule: ")
            #     for schedule in tugboat_schedule:
                
            #         print(schedule)
            #         print()
        # total barge capacity
        print("Total barge capacity: ", sum(barge.capacity for barge in data['barges'].values()))
        print("Tugboat available time for order {}".format(order.order_id))
        for tugboat_id, single_tugboat_schedule in self.tugboat_scheule.items():
                print(tugboat_id, single_tugboat_schedule[-1]['end_datetime'])