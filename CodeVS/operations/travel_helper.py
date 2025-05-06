import sys
import os

from CodeVS.compoents.water_enum import WaterBody
from CodeVS.compoents.transport_type import TransportType
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from CodeVS.compoents.station import Station
from CodeVS.utility.helpers import haversine

class TravelHelper:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(TravelHelper, cls).__new__(cls)
        return cls._instance

    def __init__(self, data=None):
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
        if start_index < end_index:
            for i in range(start_index, end_index + 1):
                result.append(self.data['station_ids'][i])
        else:
            for i in range(start_index, end_index - 1, -1):
                result.append(self.data['station_ids'][i])
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
            travel_time = distance/ speed # t = d / v
            steps.append({
                'start_location': start_station.km,
                'end_location': end_station.km,
                'start_id': start_station.station_id if start_station is not None else '-',
                'end_id': end_station.station_id if end_station is not None else '-',
                'distance': distance,
                'travel_time': travel_time,
                'speed': speed
            })
            total_distance += distance
            total_time += travel_time
        return total_distance, total_time
            
    def process_travel_steps(self, type_start_location, type_end_location, info_start_ends):
        steps = []
        total_distance = 0
        total_time = 0
        order_stations = None
        first_point = None
        if type_end_location == WaterBody.SEA and type_start_location == WaterBody.SEA:
            distance = self.get_distance_location(info_start_ends['start_location'], info_start_ends['end_location'])
            travel_time = distance/ info_start_ends['speed'] # t = d / v
            start_sea_station = self.get_sea_station(info_start_ends['start_location'])
            end_sea_station = self.get_sea_station(info_start_ends['end_location'])
            first_point = {
                'start_location': info_start_ends['start_location'],
                'end_location': info_start_ends['end_location'],
                'start_id': start_sea_station.station_id if start_sea_station is not None else '-',
                'end_id': end_sea_station.station_id if end_sea_station is not None else '-',
                'distance': distance,
                'travel_time': travel_time,
                'speed': info_start_ends['speed']
            }
            steps.append(first_point)
        
            total_distance = distance
        elif type_end_location == WaterBody.SEA and type_start_location == WaterBody.RIVER:
            #print('--------------------------------------------------- SEA - RIVER - EXPORT')
            
            start_station = self.get_next_river_station(TransportType.EXPORT, info_start_ends['start_km'])
            sea_station = self.get_sea_station(info_start_ends['end_location'])
            isContinue = False
            if sea_station is None:
                sea_station, min_distance = self.get_closest_sea_station(info_start_ends['end_location'])
                order_stations = self.get_order_stations(start_station.station_id, sea_station.station_id)
                isContinue = True
            else:
                order_stations = self.get_order_stations(start_station.station_id, sea_station.station_id)
            
            delta = start_station.km - info_start_ends['start_km']
            if delta != 0:
                distance = abs(delta)
                travel_time = distance/ info_start_ends['speed'] # t = d / v
                first_point = {
                    'start_location': info_start_ends['start_km'],
                    'end_location': start_station.km,
                    'start_id': start_station.station_id if start_station is not None else '-',
                    'end_id': sea_station.station_id if sea_station is not None else '-',
                    'distance': distance,
                    'travel_time': travel_time,
                    'speed': info_start_ends['speed']
                }
                steps.append(first_point)
                total_distance += distance
                total_time += travel_time

            td, tt = self._append_travel_steps_for_river_stations(order_stations, steps, info_start_ends['speed'])

            total_distance += td
            total_time += tt
            if isContinue:
                start_location = (sea_station.lat, sea_station.lng)
                distance = self.get_distance_location(start_location, info_start_ends['end_location'])
                travel_time = distance/ info_start_ends['speed'] # t = d / v
                steps.append({
                    'start_location': start_location,
                    'end_location': info_start_ends['end_location'],
                    'distance': distance,
                    'start_id': start_station.station_id if start_station is not None else '-',
                    'end_id': sea_station.station_id if sea_station is not None else '-',
                    'travel_time': travel_time,
                    'speed': info_start_ends['speed']
                })
                total_distance += distance
                total_time += travel_time

        elif type_end_location == WaterBody.RIVER and type_start_location == WaterBody.RIVER:
            transport_type = TransportType.EXPORT
            if info_start_ends['start_km'] < info_start_ends['end_km']:
                transport_type = TransportType.IMPORT
            start_station = self.get_next_river_station(transport_type, info_start_ends['start_km'])
            end_station = self.get_next_river_station(transport_type, info_start_ends['end_km'])
            order_stations = self.get_order_stations(start_station.station_id, end_station.station_id)
            delta = start_station.km - info_start_ends['start_km']
            if delta != 0:
                distance = abs(delta)
                travel_time = distance/ info_start_ends['speed'] # t = d / v
                first_point = {
                    'start_location': info_start_ends['start_km'],
                    'end_location': start_station.km,
                    'start_id': start_station.station_id if start_station is not None else '-',
                    'end_id': end_station.station_id if end_station is not None else '-',
                    'distance': distance,
                    'travel_time': travel_time,
                    'speed': info_start_ends['speed']
                }
                steps.append(first_point)
                total_distance += distance
                total_time += travel_time

            td, tt = self._append_travel_steps_for_river_stations(order_stations, steps, info_start_ends['speed'])
            total_distance += td
            total_time += tt
            
            
            
        elif type_end_location == WaterBody.RIVER and type_start_location == WaterBody.SEA:
            end_station = self.get_next_river_station(TransportType.IMPORT, info_start_ends['end_km'])
            bar_station = self.data['lookup_station_km'][0]
            closest_station, min_distance = self.get_closest_sea_station(info_start_ends['start_location'])
            
            distance_to_bar = haversine(closest_station.lat, closest_station.lng, bar_station.lat, bar_station.lng)
            distance_from_start_to_bar = haversine(info_start_ends['start_location'][0], 
                                                   info_start_ends['start_location'][1], 
                                                   bar_station.lat, bar_station.lng)
            
            
            
            if distance_from_start_to_bar < distance_to_bar-2:
                order_stations = self.get_order_stations(closest_station.station_id, end_station.station_id)    
            else:
                order_stations = self.get_order_stations(bar_station.station_id, end_station.station_id)
                
            start_station = self.data['stations'][order_stations[0]]
            
            distance = haversine(info_start_ends['start_location'][0], 
                              info_start_ends['start_location'][1], 
                              start_station.lat, start_station.lng)
            
            travel_time = distance/ info_start_ends['speed'] # t = d / v
            first_point = {
                    'start_location': info_start_ends['start_location'],
                    'end_location': start_station.km,
                    'start_id': closest_station.station_id if closest_station is not None else '-',
                    'end_id': end_station.station_id if end_station is not None else '-',
                    'distance': distance,
                    'travel_time': travel_time,
                    'speed': info_start_ends['speed']
                }    
            steps.append(first_point)
            total_distance += distance
            total_time += travel_time
            
            td, tt = self._append_travel_steps_for_river_stations(order_stations, steps, info_start_ends['speed'])
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
    


Travel_Helper = TravelHelper()