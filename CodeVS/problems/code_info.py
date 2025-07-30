
from CodeVS.components.station import Station
from CodeVS.components.barge import Barge
from CodeVS.components.tugboat import Tugboat
from CodeVS.components.order import Order
from CodeVS.components.water_enum import WaterBody
import numpy as np
from datetime import timedelta

class CodeInfo:
    def __init__(self, data, solution, xs=None):
        self.data = data
        self.barges = data['barges']
        self.stations = data['stations']
        self.orders = data['orders']
        self.tugboats = data['tugboats']
    

        self.MAX_DISTANCE  = max(station.km for station in self.stations.values())
        self.MAX_SPEED = max(tugboat.max_speed for tugboat in self.tugboats.values())
        self.MAX_FUEL_CON = max(tugboat.max_fuel_con for tugboat in self.tugboats.values())
        
        self.BASED_VALUE = self.MAX_DISTANCE * self.MAX_FUEL_CON / self.MAX_SPEED
        self.FACTOR_SORTED_BARGE = 0.005
        self.FACTOR_SORTED_TUGBOAT = 0.02
    
        self.solution = solution
        
        
        self.set_code(xs)
        self.seed = 42
        
        
    def __get_distance_barge(self, b: Barge):
        delta = self.stations[self.solution.get_station_id_barge(b)].km - self.start_station.km
        distance = abs(delta)
        if self.stations[self.solution.get_station_id_barge(b)].water_type == WaterBody.RIVER and self.start_station.water_type == WaterBody.RIVER:
            pass
        elif self.start_station.water_type == WaterBody.SEA and self.stations[self.solution.get_station_id_barge(b)].water_type == WaterBody.RIVER:
            distance = self.stations[self.solution.get_station_id_barge(b)].km + self.start_station.km
        elif self.start_station.water_type == WaterBody.RIVER and self.stations[self.solution.get_station_id_barge(b)].water_type == WaterBody.SEA:
            distance = abs(self.stations[self.solution.get_station_id_barge(b)].km - self.start_station.km)
        else:
            distance = abs(self.stations[self.solution.get_station_id_barge(b)].km - self.start_station.km)
        
        return distance
    
    def __get_distance_tugboat(self, t: Tugboat):
        delta = self.stations[self.solution.get_station_id_tugboat(t)].km - self.start_station.km
        distance = abs(delta)
        if (self.stations[self.solution.get_station_id_tugboat(t)].water_type == WaterBody.RIVER and 
            self.start_station.water_type == WaterBody.RIVER):
            pass
        elif (self.start_station.water_type == WaterBody.SEA and 
              self.stations[self.solution.get_station_id_tugboat(t)].water_type == WaterBody.RIVER):
            distance = self.stations[self.solution.get_station_id_tugboat(t)].km + self.start_station.km
        elif (self.start_station.water_type == WaterBody.RIVER and 
              self.stations[self.solution.get_station_id_tugboat(t)].water_type == WaterBody.SEA):
            distance = abs(self.stations[self.solution.get_station_id_tugboat(t)].km - self.start_station.km)
        else:
            distance = abs(self.stations[self.solution.get_station_id_tugboat(t)].km - self.start_station.km)
        
        return distance
    
    def __sorted_barges(self, b: Barge):
        return self.__get_distance_barge(b)/self.MAX_DISTANCE
    
    def __sorted_tugboats(self, t: Tugboat):
        distance = self.__get_distance_tugboat(t)
        speed = t.max_speed
        consumption = t.max_fuel_con
        return (distance * consumption / speed )/self.BASED_VALUE
        #return distance
    
            
    def set_code(self, xs):
        if xs is None:
            self.code_tugboat = None
            self.code_barge = None
            self.index_code_tugboat = 0
            self.index_code_barge = 0
            self.active = False
            self.n_code_tugboat = 0
            self.n_code_barge = 0
        else:
            self.code_tugboat = xs[:len(xs)//2]
            self.code_barge = xs[len(xs)//2:]
            self.index_code_tugboat = 0
            self.index_code_barge = 0
            self.active = True
            self.n_code_tugboat = len(xs)//2
            self.n_code_barge = len(xs) - len(xs)//2
            
    def get_code_next_barge(self, order, barges, days):
        
        self.start_station = order.start_object.station
        order_start = order.start_datetime
        order_end = order.due_datetime
        available_barges = [
            b for b in barges.values() 
            #if (self.get_ready_barge(b)is None or self.get_ready_barge(b) < order_end - timedelta(days=4) ) 
            if (self.solution.get_ready_barge(b)is None or self.solution.get_ready_barge(b) < order_start + timedelta(days=days)) 
        ]
        
        if not self.active:
            return available_barges
        
        #print("Len", len(self.code_barge), self.n_code_barge)
        
        
        np.random.seed(int(self.code_barge[self.index_code_barge]*100000000))
        rxs_barges = np.random.rand(len(available_barges))  
        
        
        barge_values = np.fromiter((self.__sorted_barges(b) for b in available_barges), dtype=float)
        sorted_barge_indices = np.argsort(barge_values +self.FACTOR_SORTED_BARGE*rxs_barges)
        sorted_barges_list = np.array(available_barges, dtype=object)[sorted_barge_indices].tolist()
        
        
        self.index_code_barge += 1
        if self.index_code_barge >= self.n_code_barge:
            raise Exception("Index code barge out of range")
        
        return sorted_barges_list
        
        
    def get_code_next_tugboat(self, order, tugboats, days):
        self.start_station = order.start_object.station
        order_start = order.start_datetime
        order_end = order.due_datetime
        available_tugboats = [
            t for t in tugboats.values() 
            #if (self.get_ready_tugboat(t)is None or self.get_ready_tugboat(t) < order_end - timedelta(days=4) ) 
            if (self.solution.get_ready_time_tugboat(t)is None or self.solution.get_ready_time_tugboat(t) < order_start + timedelta(days=days)) 
        ]
        
        #check tugboat is available
        tugboat_ids = [t.tugboat_id for t in available_tugboats]
        if "SeaTB_14" in tugboat_ids:
            print(tugboat_ids)
            raise Exception("SeaTB_14 is available")
        
        
        if not self.active:
            return available_tugboats
        
        np.random.seed(int(self.code_tugboat[self.index_code_tugboat]*100000000))
        rxs_tugboats = np.random.rand(len(available_tugboats))  
        
        
        tugboat_values = np.fromiter((self.__sorted_tugboats(t) for t in available_tugboats), dtype=float)
        sorted_tugboat_indices = np.argsort(tugboat_values + self.FACTOR_SORTED_TUGBOAT*rxs_tugboats)
        sorted_tugboats_list = np.array(available_tugboats, dtype=object)[sorted_tugboat_indices].tolist()
        
        
        self.index_code_tugboat += 1
        if self.index_code_tugboat >= self.n_code_tugboat:
            raise Exception("Index code tugboat out of range")
        
        return sorted_tugboats_list