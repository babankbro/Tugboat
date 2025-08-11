import sys
import os

from CodeVS.components.water_enum import WaterBody
from CodeVS.components.transport_type import TransportType, WaterTravelType
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from CodeVS.components.station import Station
from CodeVS.utility.helpers import haversine
import CodeVS.config_problem as config_problem

# create class TravelInfo
# travel_infos = {
#                 'start_location': (current_lat, current_lng),
#                 'end_location': barge_info['location'],
#                 'speed': tugboat_speed,
#                 'start_km': current_km,
#                 'end_km': barge_river_km
#             }

class TravelInfo:
    def __init__(self, start_location, end_location, speed, start_km, end_km):
        self.start_location = start_location
        self.end_location = end_location
        self.speed = speed
        self.start_km = start_km
        self.end_km = end_km

class TravelStep:
    
    def __init__(self, data, start_location, end_location, start_id, end_id, distance, speed, water_factor1=1, water_factor2=1):
        self.data = data
        self.start_location = start_location
        self.end_location = end_location
        self.start_id = start_id
        self.end_id = end_id
        self.distance = distance
        self.base_speed = speed
        self.rest_time = 0
        self.exit_time = None
        self.arrival_time = None  
        self.start_time = None   
        self.water_factor1 = water_factor1  
        self.water_factor2 = water_factor2  
        self.water_factor = water_factor1 * water_factor2
        self.travel_speed = speed * self.water_factor
        if self.travel_speed == 0:
            self.travel_time = 0
        else:
            self.travel_time = distance / self.travel_speed
        #start_id: start_time -> travel_time -> end_id:arrival_time + stop_time -> exit_time
    
    def update_travel_time(self, date_time):
        target_station = self.data['stations'][self.end_id]
        
        lookup = self.data['water_level_down']
        direction_station_lookup = self.data['direction_station_lookup']
        
        
        if target_station.water_type == WaterBody.SEA:
            min_speed = config_problem.TRAVEL_FACTOR['SEA_TUGBOAT_BARGE_COLLECTION_MIN_SPEED'] 
            max_speed = config_problem.TRAVEL_FACTOR['SEA_TUGBOAT_BARGE_COLLECTION_MAX_SPEED'] 
            water_factor1 = config_problem.TRAVEL_FACTOR['SEA_FACTOR']
            water_factor2 = 1
        else:
            from_station = self.data['stations'][self.start_id]
            key = from_station.station_id + "->" + target_station.station_id
            if from_station.station_id == target_station.station_id:
                if from_station.water_type == WaterBody.RIVER:
                    min_speed = config_problem.TRAVEL_FACTOR['RIVER_TUGBOAT_BARGE_COLLECTION_MIN_SPEED'] 
                    max_speed = config_problem.TRAVEL_FACTOR['RIVER_TUGBOAT_BARGE_COLLECTION_MAX_SPEED'] 
                    water_factor1 = config_problem.TRAVEL_FACTOR['RIVER_FACTOR']
                    water_factor2 = 1
                else:
                    min_speed = config_problem.TRAVEL_FACTOR['SEA_TUGBOAT_BARGE_COLLECTION_MIN_SPEED'] 
                    max_speed = config_problem.TRAVEL_FACTOR['SEA_TUGBOAT_BARGE_COLLECTION_MAX_SPEED'] 
                    water_factor1 = config_problem.TRAVEL_FACTOR['SEA_FACTOR']
                    water_factor2 = 1
                
            
            elif direction_station_lookup[key] == WaterTravelType.SEA:
                min_speed = config_problem.TRAVEL_FACTOR['SEA_TUGBOAT_BARGE_COLLECTION_MIN_SPEED'] 
                max_speed = config_problem.TRAVEL_FACTOR['SEA_TUGBOAT_BARGE_COLLECTION_MAX_SPEED'] 
                water_factor1 = config_problem.TRAVEL_FACTOR['SEA_FACTOR']
                water_factor2 = 1
            else:
                min_speed = config_problem.TRAVEL_FACTOR['RIVER_TUGBOAT_BARGE_COLLECTION_MIN_SPEED'] 
                max_speed = config_problem.TRAVEL_FACTOR['RIVER_TUGBOAT_BARGE_COLLECTION_MAX_SPEED'] 
                water_factor1 = config_problem.TRAVEL_FACTOR['RIVER_FACTOR']
                water_factor2 = 1
                if direction_station_lookup[key] == WaterTravelType.RIVER_UP:
                    lookup = self.data['water_level_up']
        
        if self.end_id:
            stats = lookup.get_previous_time_stats(date_time, days_back=2, station_ids=self.end_id)
            water_factor2 = stats['stations'][self.end_id]['mean']        
 
        self.water_factor1 = water_factor1
        self.water_factor2 = water_factor2
        self.water_factor = water_factor1 * water_factor2
        self.travel_speed = min(max(min_speed, self.base_speed * self.water_factor), max_speed)
        if self.travel_speed == 0:
            self.travel_time = 0
        else:
            self.travel_time = self.distance / self.travel_speed
    
    
    def __str__(self):
        # update to display decimal 3 digits by print format
        return (f"Start Location: {self.start_location}, End Location: {self.end_location}, "
                f"Start ID: {self.start_id}, End ID: {self.end_id}, Distance: {self.distance:.3f}, "
                f"Travel Time: {self.travel_time:.3f}, Speed: {self.travel_speed:.3f}, "
                f"Water Factor: {self.water_factor:.3f}, Base Speed: {self.base_speed:.3f}, "
                f"Water Factor 1: {self.water_factor1:.3f}, Water Factor 2: {self.water_factor2:.3f}")


class TravelHelper:
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        #print("TravelHelper new")
        if cls._instance is None:
            cls._instance = super(TravelHelper, cls).__new__(cls)
        return cls._instance

    def __init__(self, data=None):
        #print("TravelHelper initialized")
        if not hasattr(self, 'initialized'):  # Ensure __init__ is only called once
            self.data = data
            self.initialized = True
            
    def _set_data(self, data):
        self.data = data
        
    def get_next_river_station(self, transport_type, km):
        station = self.data['lookup_station_km'][0]
        if km in self.data['lookup_station_km'] and self.data['lookup_station_km'][km].water_type == WaterBody.RIVER:
            station = self.data['lookup_station_km'][km]
            
        elif transport_type == TransportType.EXPORT:
            for key_km in sorted(self.data['lookup_station_km'].keys()):
                if km > key_km and self.data['lookup_station_km'][key_km].water_type == WaterBody.RIVER:
                    station = self.data['lookup_station_km'][key_km]     
                else:
                    break      
        elif transport_type == TransportType.IMPORT:
            for key_km in sorted(self.data['lookup_station_km'].keys()):
                if km < key_km and self.data['lookup_station_km'][key_km].water_type == WaterBody.RIVER:
                    station = self.data['lookup_station_km'][key_km]
                    break
          
        return station
    
    def get_closest_sea_station(self, location):
        lat, lng = location
        #print("########### Start", lat, lng)
        closest_station = None
        min_distance = float('inf')
        #print(self.data)
        for stationid, station in self.data['sea_stations'].items():
            # distance = haversine(lat, lng, station.lat, station.lng)
            d = haversine(lat, lng, station.lat, station.lng) 
            if d < min_distance:
                min_distance = d
                closest_station = station           
        return closest_station, min_distance
    
    def get_sea_station(self, location):
        closest_station, dis = self.get_closest_sea_station(location)
        if dis < 0.5:
            return closest_station
        return None
        
        
        
        # if transport_type == TransportType.IMPORT:
        #     return self.data['next_import_station']
        # elif transport_type == TransportType.EXPORT:
        #     return self.data['next_export_station']
    
    def get_order_stations(self, start_station_id, end_station_id):
        start_index = self.data['lookup_station_index'][start_station_id]
        end_index = self.data['lookup_station_index'][end_station_id]
        #print(start_station_id, start_index, end_station_id, end_index)
        result = []
        key_station = config_problem.KOH_SI_CHANG_STATION_BASE_REFERENCE_ID + "-"
        if start_index < end_index:
            for i in range(start_index, end_index + 1):
                if key_station in self.data['station_ids'][i]:
                    continue
                result.append(self.data['station_ids'][i])
        else:
            for i in range(start_index, end_index - 1, -1):
                if key_station in self.data['station_ids'][i]:
                    continue
                result.append(self.data['station_ids'][i])
                
        if key_station in end_station_id:
            if key_station not in result:
                result.append(config_problem.KOH_SI_CHANG_STATION_BASE_REFERENCE_ID)
            result.append(end_station_id)
            
        return result

    def convert_pos_to_latlng(self, location):
        if isinstance(location, Station):
            start_pos = (location.lat, location.lng)
        elif isinstance(location, (list, tuple)) and len(location) == 2:
            start_pos = location
        else:
            raise ValueError("start_location must be a list or tuple with two elements (lat, lng)")
        return start_pos

    def get_distance_station(self, start_station, end_station):
        if start_station.water_type == WaterBody.SEA and end_station.water_type == WaterBody.SEA:
            return abs(start_station.km - end_station.km)
        if start_station.water_type == WaterBody.RIVER and end_station.water_type == WaterBody.SEA :
            key = (start_station.station_id, config_problem.KOH_SI_CHANG_STATION_BASE_REFERENCE_ID)
            station_c01 = self.data['stations'][config_problem.KOH_SI_CHANG_STATION_BASE_REFERENCE_ID]
            lookup_distances = self.data['lookup_distances']
            distance = lookup_distances[key]
            return distance +  abs(station_c01.km - end_station.km)

        key = (start_station.station_id,end_station.station_id)
        lookup_distances = self.data['lookup_distances']
        distance = lookup_distances[key]
        return distance

    def get_distance_location(self, start_location, end_location):
        start_pos = start_location
        end_pos = end_location
        distance = haversine(start_pos[0], start_pos[1], end_pos[0], end_pos[1])
        return distance
    
    def _append_travel_steps_for_river_stations(self, order_stations, steps, speed):
        total_distance = 0
        total_time = 0
        for i in range(len(order_stations) - 1):
            start_station = self.data['stations'][order_stations[i]]
            end_station = self.data['stations'][order_stations[i + 1]]
            distance = self.get_distance_station(start_station, end_station)
            if (config_problem.KOH_SI_CHANG_STATION_BASE_REFERENCE_ID in start_station.station_id 
                and config_problem.KOH_SI_CHANG_STATION_BASE_REFERENCE_ID in end_station.station_id):
                print(f"{config_problem.KOH_SI_CHANG_STATION_BASE_REFERENCE_ID} Station found in river travel steps", distance)
            travel_time = distance/ speed # t = d / v
            # steps.append({
            #     'start_location': start_station.km,
            #     'end_location': end_station.km,
            #     'start_id': start_station.station_id if start_station is not None else '-',
            #     'end_id': end_station.station_id if end_station is not None else '-',
            #     'distance': distance,
            #     'travel_time': travel_time,
            #     'speed': speed
            # })
            step = TravelStep(self.data, start_station.km, end_station.km, 
                              start_station.station_id, end_station.station_id, 
                              distance, speed)
            steps.append(step)
            total_distance += distance
            total_time += travel_time
        return total_distance, total_time
            
    def process_travel_steps(self, type_start_location, type_end_location, info_start_ends:TravelInfo):
        
        #check type in info_start_ends is TravelInfo
        if not isinstance(info_start_ends, TravelInfo):
            raise ValueError("info_start_ends is not TravelInfo")
    
        
        steps = []
        total_distance = 0
        total_time = 0
        order_stations = None
        first_point = None
        if type_start_location == WaterBody.SEA and type_end_location == WaterBody.SEA:
            distance = self.get_distance_location(info_start_ends.start_location, info_start_ends.end_location)
            travel_time = distance/ info_start_ends.speed # t = d / v
            start_sea_station = self.get_sea_station(info_start_ends.start_location)
            end_sea_station = self.get_sea_station(info_start_ends.end_location)
            # first_point = {
            #     'start_location': info_start_ends['start_location'],
            #     'end_location': info_start_ends['end_location'],
            #     'start_id': start_sea_station.station_id if start_sea_station is not None else '-',
            #     'end_id': end_sea_station.station_id if end_sea_station is not None else '-',
            #     'distance': distance,
            #     'travel_time': travel_time,
            #     'speed': info_start_ends['speed']
            # }
            start_location = info_start_ends.start_location
            end_location = info_start_ends.end_location
            start_id = start_sea_station.station_id if start_sea_station is not None else '-'
            end_id = end_sea_station.station_id if end_sea_station is not None else '-'
                
            first_step = TravelStep(self.data, start_location, end_location, 
                                    start_id, end_id, 
                                    distance, info_start_ends.speed)
            steps.append(first_step)
        
            total_distance = distance
        elif type_start_location == WaterBody.RIVER  and type_end_location == WaterBody.SEA:
            #print('--------------------------------------------------- SEA - RIVER - EXPORT')
            
            start_station = self.get_next_river_station(TransportType.EXPORT, info_start_ends.start_km)
            sea_station = self.get_sea_station(info_start_ends.end_location)
            isContinue = False
            if sea_station is None:
                sea_station, min_distance = self.get_closest_sea_station(info_start_ends.end_location)
                order_stations = self.get_order_stations(start_station.station_id, sea_station.station_id)
                isContinue = True
            else:
                order_stations = self.get_order_stations(start_station.station_id, sea_station.station_id)
            
            delta = start_station.km - info_start_ends.start_km
            if delta != 0:
                distance = abs(delta)
                travel_time = distance/ info_start_ends.speed # t = d / v
                # first_point = {
                #     'start_location': info_start_ends['start_km'],
                #     'end_location': start_station.km,
                #     'start_id': start_station.station_id if start_station is not None else '-',
                #     'end_id': sea_station.station_id if sea_station is not None else '-',
                #     'distance': distance,
                #     'travel_time': travel_time,
                #     'speed': info_start_ends['speed']
                # }
                # steps.append(first_point)
                start_id = start_station.station_id if start_station is not None else '-'
                end_id = sea_station.station_id if sea_station is not None else '-'
                first_step = TravelStep(self.data, info_start_ends.start_km, start_station.km, 
                                        start_id, end_id, 
                                        distance,  info_start_ends.speed)
                steps.append(first_step)
                total_distance += distance
                total_time += travel_time
            
            td, tt = self._append_travel_steps_for_river_stations(order_stations, steps, info_start_ends.speed)
            # print("order_stations -------------- ",order_stations, td)
            # for step in steps:
            #     print(step['start_location'], step['end_location'], step['distance'], step['travel_time'], step['speed'])
            total_distance += td
            total_time += tt
            if isContinue:
                start_location = (sea_station.lat, sea_station.lng)
                distance = self.get_distance_location(start_location, info_start_ends.end_location)
                travel_time = distance/ info_start_ends.speed # t = d / v
                # steps.append({
                #     'start_location': start_location,
                #     'end_location': info_start_ends['end_location'],
                #     'distance': distance,
                #     'start_id': start_station.station_id if start_station is not None else '-',
                #     'end_id': sea_station.station_id if sea_station is not None else '-',
                #     'travel_time': travel_time,
                #     'speed': info_start_ends['speed']
                # })
                start_id = start_station.station_id if start_station is not None else '-'
                end_id = sea_station.station_id if sea_station is not None else '-'
                step = TravelStep(self.data, start_location, info_start_ends.end_location, 
                                  start_id, end_id, 
                                  distance, info_start_ends.speed)
                steps.append(step)
                total_distance += distance
                total_time += travel_time

        elif type_end_location == WaterBody.RIVER and type_start_location == WaterBody.RIVER:
            transport_type = TransportType.EXPORT
            if info_start_ends.start_km < info_start_ends.end_km:
                transport_type = TransportType.IMPORT
            start_station = self.get_next_river_station(transport_type, info_start_ends.start_km)
            end_station = self.get_next_river_station(transport_type, info_start_ends.end_km)
            order_stations = self.get_order_stations(start_station.station_id, end_station.station_id)
            delta = start_station.km - info_start_ends.start_km
            if delta != 0:
                distance = abs(delta)
                travel_time = distance/ info_start_ends.speed # t = d / v
                # first_point = {
                #     'start_location': info_start_ends['start_km'],
                #     'end_location': start_station.km,
                #     'start_id': start_station.station_id if start_station is not None else '-',
                #     'end_id': end_station.station_id if end_station is not None else '-',
                #     'distance': distance,
                #     'travel_time': travel_time,
                #     'speed': info_start_ends['speed']
                # }
                start_id = start_station.station_id if start_station is not None else '-'
                end_id = end_station.station_id if end_station is not None else '-'
                first_step = TravelStep(self.data, info_start_ends.start_km, start_station.km, 
                                        start_id, end_id, 
                                        distance, info_start_ends.speed)
                steps.append(first_step)
                total_distance += distance
                total_time += travel_time
            else:
                
                # first_point = {
                #     'start_location': info_start_ends['start_km'],
                #     'end_location': start_station.km,
                #     'start_id': start_station.station_id if start_station is not None else '-',
                #     'end_id': end_station.station_id if end_station is not None else '-',
                #     'distance': 0,
                #     'travel_time': 0,
                #     'speed': 0
                # }
                start_id = start_station.station_id if start_station is not None else '-'
                end_id = end_station.station_id if end_station is not None else '-'
                first_step = TravelStep(self.data, info_start_ends.start_km, start_station.km, 
                                        start_id, end_id, 
                                        0, info_start_ends.speed)
                if (start_id == end_id):
                    steps.append(first_step)
                

            td, tt = self._append_travel_steps_for_river_stations(order_stations, steps, info_start_ends.speed)
            total_distance += td
            total_time += tt
                     
        elif type_start_location == WaterBody.SEA and type_end_location == WaterBody.RIVER:
            end_station = self.get_next_river_station(TransportType.IMPORT, info_start_ends.end_km)
            bar_station = self.data['lookup_station_km'][0]
            closest_station, min_distance = self.get_closest_sea_station(info_start_ends.start_location)
            
            distance_to_bar = haversine(closest_station.lat, closest_station.lng, bar_station.lat, bar_station.lng)
            distance_from_start_to_bar = haversine(info_start_ends.start_location[0], 
                                                   info_start_ends.start_location[1], 
                                                   bar_station.lat, bar_station.lng)
            
            
            
            if distance_from_start_to_bar < distance_to_bar-2:
                order_stations = self.get_order_stations(closest_station.station_id, end_station.station_id)    
            else:
                order_stations = self.get_order_stations(bar_station.station_id, end_station.station_id)
                
            start_station = self.data['stations'][order_stations[0]]
            
            distance = haversine(info_start_ends.start_location[0], 
                              info_start_ends.start_location[1], 
                              start_station.lat, start_station.lng)
            
            travel_time = distance/ info_start_ends.speed # t = d / v
            step = TravelStep(self.data, info_start_ends.start_location, start_station.km, 
                              closest_station.station_id, order_stations[0], 
                              distance, info_start_ends.speed)
            # first_point = {
            #         'start_location': info_start_ends['start_location'],
            #         'end_location': start_station.km,
            #         'start_id': closest_station.station_id if closest_station is not None else '-',
            #         'end_id': order_stations[0],
            #         'distance': distance,
            #         'travel_time': travel_time,
            #         'speed': info_start_ends['speed']
            #     }    
            #rint("Debugging SEA - RIVER Step", order_stations)
            start_id = closest_station.station_id if closest_station is not None else '-'
            end_id = order_stations[0]
            step = TravelStep(self.data, info_start_ends.start_location, start_station.km, 
                              start_id, end_id, 
                              distance, info_start_ends.speed)
            
            # total_distance += distance
            # total_time += travel_time
            order_stations = [station_id for station_id in order_stations 
                    if (self.data['stations'][station_id].water_type == WaterBody.RIVER or 
                        (station_id == start_station.station_id or station_id == end_station.station_id))]
            # result contian station id if want to remove that station water_type == WaterBody.SEA
            
            #print("After Debugging SEA - RIVER Step", order_stations)
            
            steps.append(step)
            total_distance += distance
            total_time += travel_time
            
            td, tt = self._append_travel_steps_for_river_stations(order_stations, 
                                                                  steps, info_start_ends.speed)
            total_distance += td
            total_time += tt
            
            #print("order_stations -------------- ",order_stations, total_distance, total_time)
          
        else:
            print(type_start_location)
            print(type_end_location)
            print(info_start_ends)
            raise Exception("Invalid water body type")
        
        
        
        # if order_stations is not None and 'c1' in order_stations:
        #     print("----------------------------------- Test")
        #     print(order_stations)
        #     print("\tSteps:", len(steps))
        #     for step in steps:
        #         print(step['start_location'], step['end_location'], step['distance'], step['travel_time'], step['speed'])
            
        #     print('Total distance:', total_distance, 'total time:', total_time)
        
        #if len(steps) != 0:
        #print("STEPs ---------------", first_point, steps)
        return total_distance, total_time, steps
    

