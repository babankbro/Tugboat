# prompt: filter only sea tugboats in dic tugboat
# Define Tugboat class
from CodeVS.components.carrier import Carrier
from CodeVS.operations.travel_helper import *
from CodeVS.utility.helpers import *
from datetime import datetime 
from  CodeVS.components.water_enum import *

# def calculate_sea_move(tugboat, start_location, sea_stations, all_stations = None):
#     """
#     Calculate the movement of a sea tugboat through a series of sea stations.

#     Parameters:
#     tugboat (Tugboat): The tugboat object.
#     start_location (tuple): The (latitude, longitude) of the current location.
#     stations (list): List of station IDs in order of travel.

#     Returns:
#     dict: Travel information including total time and final location.
#     """

#     current_lat, current_lng = start_location
#     total_travel_time = 0.0

#     print("\nTugboat is moving through sea stations...\n")

#     for station_id in sea_stations:
#         if all_stations is not None and station_id not in all_stations:
#             print(f"Warning: Station {station_id} not found in station data.")
#             continue

#         station = all_stations[station_id]
#         destination_lat, destination_lng = station.lat, station.lng

#         # Calculate distance using Haversine formula
#         distance = haversine(current_lat, current_lng, destination_lat, destination_lng)

#         # Determine the tugboat's speed considering load
#         speed = tugboat.calculate_current_speed()

#         # Compute travel time (time = distance / speed)
#         travel_time = distance / speed if speed > 0 else float('inf')
#         total_travel_time += travel_time

#         print(f"Traveling to {station.name} ({station_id})")
#         print(f" - Distance: {distance:.2f} km")
#         print(f" - Speed: {speed:.2f} km/h")
#         print(f" - Travel Time: {travel_time:.2f} hours\n")

#         # Update current position
#         current_lat, current_lng = destination_lat, destination_lng

#     print(f"Total Travel Time: {total_travel_time:.2f} hours")
#     return {
#         "total_time": total_travel_time,
#         "final_location": (current_lat, current_lng)
#     }



class Tugboat:
    def __init__(self, tugboat_id, name, max_capacity, 
                 max_barge, max_fuel_con, tug_type,
                 max_speed, lat, lng, status, km, ready_time=None):
        self.tugboat_id = tugboat_id
        self.name = name
        self.max_capacity = max_capacity
        self.max_barge = max_barge
        self.max_fuel_con = max_fuel_con
        self.tug_type = str_to_enum(tug_type)
        self.max_speed = max_speed
        self.min_speed = max_speed/2
        self._lat = lat
        self._lng = lng
        self._status = str_to_enum(status)
        self._km = km
        self._ready_time = datetime.strptime(ready_time, '%Y-%m-%d %H:%M:%S')
        self.assigned_barges = []
        self.current_load = 0
        self._current_order = None
        
    def reset(self):
        self.assigned_barges = []
        
    #def update_last_status(self, status):
        
        
    def get_total_load(self):
        return sum(barge.get_load() for barge in self.assigned_barges)
    
    
    
    def calculate_collection_river_barge_time(self, tugboat_info, lookup_barge_infos):
        river_km = tugboat_info['river_km']
        current_status = self.status 
        if self.status == WaterBody.SEA:
            bar_station = TravelHelper._instance.data['stations']['s0']
            river_km = - haversine(self.lat, self.lng, bar_station.lat, bar_station.lng)
        
        barges = sort_barges_by_river_distance(river_km, self.assigned_barges)
        
        
        
        total_time = 0.0  # เวลารวมเริ่มต้น
        nbarge = 0
        total_weight_barge = 0
        current_lat = self.lat
        current_lng = self.lng
        setup_time_per_barge = 0.0
        barge_collect_infos = []
        current_status = self.status
        current_km = self.km
        barge_weight = 0
        for barge in barges:
            barge_info = lookup_barge_infos[barge.barge_id][-1]
            end_station = TravelHelper._instance.data['stations'][barge_info['appointment_station']]
            tugboat_speed = self.calculate_speed(total_weight_barge, nbarge, barge_weight)
            travel_infos = {
                'start_location': (current_lat, current_lng),
                'end_location': (end_station.lat, end_station.lng),
                'speed': tugboat_speed,
                'start_km': current_km,
                'end_km': end_station.km
            }
            
            distance, travel_time, travel_steps = TravelHelper._instancel_Helper.process_travel_steps(current_status, 
                                                                WaterBody.RIVER, travel_infos)
            setup_time = barge.setup_time / 60.0  # แปลงเวลาเชื่อมต่อจากนาทีเป็นชั่วโมง
            total_time += travel_time + setup_time  # รวมเวลาเดิน
            total_weight_barge += barge.get_load()
            barge_weight += barge.weight_barge
            nbarge += 1
            current_lat = barge.lat
            current_lng = barge.lng
            
            current_km = end_station.km
            barge_collect_info = {
                "barge_id": barge.barge_id,
                "travel_time": travel_time,
                'travel_distance': distance,
                "setup_time": setup_time,
                "location": (barge.lat, barge.lng),
                'travel_steps': travel_steps,
                'start_status': current_status,
                'end_status': WaterBody.RIVER
            }
            
            current_status = WaterBody.RIVER
            
            barge_collect_infos.append(barge_collect_info)
            #print(f"Barge {barge.barge_id} - Travel Time: {travel_time:.2f} hours, Setup Time: {setup_time:.2f} hours")
        #print(f"Total Time: {total_time:.2f} hours")
        
        #print("self.assigned_barges", len(self.assigned_barges), len(barges), len(barge_collect_infos))
        return {"total_time":total_time, "last_location": (current_lat, current_lng), 
                'barge_collect_infos': barge_collect_infos }
        
        

    def calculate_collection_barge_time(self, tugboat_info, barge_infos):
        location = tugboat_info['location']
        barges = sort_barges_by_distance(location[0], location[1], self.assigned_barges, barge_infos)
        total_time = 0.0  # เวลารวมเริ่มต้น
        nbarge = 0
        total_weight_barge = 0
        current_lat, current_lng = location
        setup_time_per_barge = 0.0
        barge_collect_infos = []
        current_status = tugboat_info['water_status']
        current_km = tugboat_info['river_km']
        for barge in barges:
            barge_info =   barge_infos[barge.barge_id][-1]
            barge_river_km = barge_info['river_km']
            tugboat_speed = self.calculate_speed(total_weight_barge, nbarge, total_weight_barge)
            travel_infos = {
                'start_location': (current_lat, current_lng),
                'end_location': barge_info['location'],
                'speed': tugboat_speed,
                'start_km': current_km,
                'end_km': barge_river_km
            }
            water_status = barge_info['water_status']
            #print("EEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE", TravelHelper._instance)
            distance, travel_time, travel_steps = TravelHelper._instance.process_travel_steps(current_status, 
                                                                                              water_status, 
                                                                                              travel_infos)
            setup_time = barge.setup_time / 60.0  # แปลงเวลาเชื่อมต่อจากนาทีเป็นชั่วโมง
            total_time += travel_time + setup_time  # รวมเวลาเดิน
            total_weight_barge += barge.weight_barge
            nbarge += 1
            current_lat = barge_info['location'][0]
            current_lng = barge_info['location'][1]
            
            current_km = barge_river_km
            #if len(travel_steps) > 0:
                #print("Travel Steps TTTTTTTTTTTTTTTTTTTTT:", travel_steps)
            barge_collect_info = {
                "barge_id": barge.barge_id,
                "travel_time": travel_time,
                'travel_distance': distance,
                "setup_time": setup_time,
                "location": barge_info['location'],
                'travel_steps': travel_steps,
                'start_status': current_status,
                'end_status':water_status
            }
            current_status = water_status
            barge_collect_infos.append(barge_collect_info)
            #print(f"Barge {barge.barge_id} - Travel Time: {travel_time:.2f} hours, Setup Time: {setup_time:.2f} hours")
        #print(f"Total Time: {total_time:.2f} hours")
        return {"total_time":total_time, "last_location": (current_lat, current_lng), 
                'barge_collect_infos': barge_collect_infos }
    
    def calculate_travel_to_start_object(self, barge_scheule):
        # travel to carriers
        # compute time grab product
        # -start time
            # cr1 b1 b3  cr2 b2 b4  
        carrier = self.assigned_barges[0].current_order.start_object
        lastbarge = self.assigned_barges[-1]
        barge_info = barge_scheule[lastbarge.barge_id][-1]
        blocation = barge_info['location']
        nbarge = len(self.assigned_barges)
        base_weight_barges = self.get_total_weight_barge()
        speed_tug = self.calculate_speed(base_weight_barges, nbarge, base_weight_barges)
        travel_infos = {
                'start_location': blocation,
                'end_location': (carrier.lat, carrier.lng),
                'speed': speed_tug,
                'start_km': barge_info["river_km"],
                'end_km': None
            }
        # check instance carrier is Carrier
        if not isinstance(carrier, Carrier):
            raise Exception("Start object is not a Carrier")
        else:
            distance, travel_time, travel_steps = TravelHelper._instance.process_travel_steps(barge_info["water_status"], 
                                                                                     WaterBody.SEA, travel_infos)
        
        
        carrier_distance = distance
        base_weight_barges = self.get_total_weight_barge()
        nbarge = len(self.assigned_barges)
        
        #print("Speed Tugboat", speed_tug, base_weight_barges)
        travel_time = carrier_distance / speed_tug
        return {"travel_time":travel_time, 
                "last_location": (carrier.lat, carrier.lng),
                "speed": speed_tug,  
                "start_object": carrier,
                'travel_distance': distance,
                'steps': travel_steps}
    
    def calculate_travel_start_to_end_river_location(self, start_info, end_info, 
                                                     start_status=WaterBody.RIVER, end_status= WaterBody.RIVER):
        data = TravelHelper._instance.data
        start_km = 0
        if start_info['station'] is None:
            start_location = start_info['location']
        else:
            start_station =  start_info['station']
            start_location = (start_station.lat, start_station.lng)
            start_km = start_station.km
        end_station =  end_info['station']
        nbarge = len(self.assigned_barges)
        total_weight_barges = self.get_total_load()
        base_weight_barges = self.get_total_weight_barge()
        speed_tug = self.calculate_speed(total_weight_barges, nbarge, base_weight_barges)

        
        travel_infos = {
                'start_location': start_location,
                'end_location': (end_station.lat, end_station.lng),
                'speed': speed_tug,
                'start_km': start_km,
                'end_km': end_station.km
            }

        distance, travel_time, travel_steps = TravelHelper._instance.process_travel_steps(start_status,
                                                                                          end_status, 
                                                                                          travel_infos)
        #print("Speed Tugboat", speed_tug, base_weight_barges)
        travel_time = distance / speed_tug
        return {"travel_time":travel_time, 
                "end_location": (end_station.lat, end_station.lng),
                "speed": speed_tug,  
                "start_location": start_location,
                'travel_distance': distance,
                'steps': travel_steps}
        
    def calculate_travel_to_appointment(self, appointment_info):
        data = TravelHelper._instance.data
        # 1. get order_stations
        end_station  =  data['stations'][appointment_info['appointment_station']] 
        carrier = self.assigned_barges[0].current_order.start_object
        
        
        #print(end_station)
        
        start_info = {'station':None, 'location': (carrier.lat, carrier.lng)}
        end_info = {'station':data['stations'][appointment_info['appointment_station']], 'location': (end_station.lat, end_station.lng)}
        result = self.calculate_travel_start_to_end_river_location(start_info, end_info, 
                                                                   WaterBody.SEA, end_status = WaterBody.RIVER)
        return {"travel_time":result['travel_time'], 
                "last_location": result['end_location'],
                "speed": result['speed'],  
                "start_object": carrier,
                "start_location": result['start_location'],
                'travel_distance': result['travel_distance'],
                'steps': result['steps']}
        
    def calculate_river_to_customer(self, input_travel_info):
        # order = self.assigned_barges[0].current_order
        end_station = self.assigned_barges[0].current_order.des_object
        nbarge = len(self.assigned_barges)
        start_station = TravelHelper._instance.data['stations'][ input_travel_info['appointment_station_id']]
        total_weight_barges = self.get_total_load()
        base_weight_barges = self.get_total_weight_barge()
        speed_tug = self.calculate_speed(total_weight_barges, nbarge, base_weight_barges)
        travel_infos = {
                'start_location': (start_station.lat, start_station.lng),
                'end_location': (end_station.lat, end_station.lng),
                'speed': speed_tug,
                'start_km': start_station.km,
                'end_km': end_station.km
            }
        distance, travel_time, travel_steps = TravelHelper._instance.process_travel_steps(WaterBody.RIVER, WaterBody.RIVER, travel_infos)
        #print("Speed Tugboat", speed_tug, base_weight_barges)
        travel_time = distance / speed_tug
        return {"travel_time":travel_time, 
                "last_location": (end_station.lat, end_station.lng),
                "speed": speed_tug,  
                "start_object": start_station,
                'travel_distance': distance,
                'steps': travel_steps}
        
    def calculate_collection_product_time_with_crane_rate(self, last_lat):
        # travel to carriers
        # compute time grab product
        # -start time
            # cr1 b1 b3  cr2 b2 b4
        carrier = self.assigned_barges[0].current_order.start_object
        carrier_distance = haversine(last_lat[0], last_lat[1], carrier.lat, carrier.lng)
        base_weight_barges = self.get_total_weight_barge()
        nbarge = len(self.assigned_barges)
        speed_tug = self.calculate_speed(0, nbarge, base_weight_barges)
        print("Speed Tugboat", speed_tug, base_weight_barges)
        travel_time = carrier_distance / speed_tug
        print("Travel Time", travel_time)
        order = self.assigned_barges[0].current_order
        print("Crane Rate", order.start_datetime)
        crane_lookups = {}

        for barge in self.assigned_barges:
            if barge.crane_name not in crane_lookups:
                crane_lookups[barge.crane_name] = {}
                crane_lookups[barge.crane_name]['barges'] = [barge]
            else:
                crane_lookups[barge.crane_name]['barges'].append(barge)

        # sume load of barges each crane
        for crane_name, crane_info in crane_lookups.items():
            crane_lookups[crane_name]['total_load'] = sum(barge.load for barge in crane_info['barges'])

        max_time_grab = 0
        for crane_name, infos in crane_lookups.items():
            crane_rate = order.get_crane_rate(crane_name)
            print(f"Crane {crane_name}: crane_rate={crane_rate}", crane_lookups[crane_name]['total_load'] )
            time_crane = crane_lookups[crane_name]['total_load'] / crane_rate
            print(f"Crane {crane_name}: time_crane={time_crane}")
            if time_crane > max_time_grab:
                max_time_grab = time_crane
        print("Max Time Grab", max_time_grab)
        return {'total_time': max_time_grab + travel_time, 'time_grab': max_time_grab, 'travel_time': travel_time}

    def calculate_travel_to_estuary_river():

        pass

    def assign_barge(self, barge):
        if len(self.assigned_barges) < self.max_barge and self.get_total_load() + barge.get_load() <= self.max_capacity:
            self.assigned_barges.append(barge)
            barge.status = 'assigned'
            self.current_load += barge.get_load(is_only_load=True)
            return True
        return False

    def get_total_weight_barge(self):
        return sum(barge.weight_barge for barge in self.assigned_barges)

    def calculate_current_speed(self):
        weight_barge = self.get_total_weight_barge()

        #print(load_ratio, barge_ratio,  total_reduction_ratio, current_speed,self.min_speed, (self.max_speed - self.min_speed) * (1 - total_reduction_ratio))
        return self.calculate_speed(self.current_load, len(self.assigned_barges),  weight_barge)

    def calculate_speed(self, load, nbarge, base_load):
        max_weight =self.max_capacity +  base_load
        load_ratio = load/ max_weight if max_weight else 0
        barge_ratio = nbarge / self.max_barge if self.max_barge else 0
        total_reduction_ratio = (load_ratio + barge_ratio) / 2
        current_speed = (self.max_speed - self.min_speed) * (1 - total_reduction_ratio) + self.min_speed
        #print(load_ratio, barge_ratio,  total_reduction_ratio, current_speed,self.min_speed, (self.max_speed - self.min_speed) * (1 - total_reduction_ratio))
        return current_speed

    def __str__(self):
        return (f"Tugboat ID: {self.tugboat_id}, Name: {self.name}, Max Capacity: {self.max_capacity}, "
                f"Max Barges: {self.max_barge}, Max Fuel Consumption: {self.max_fuel_con}, Type: {self.tug_type}, "
                f"Max Speed: {self.max_speed}, Location: ({self._lat}, {self._lng}), Status: {self._status}, "
                f"KM: {self._km}, Assigned Barges: {[barge.barge_id for barge in self.assigned_barges]}")
