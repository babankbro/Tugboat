import math
from datetime import datetime
from CodeVS.compoents.water_enum import *

class Barge:
    def __init__(self, barge_id, name, weight_barge, capacity, lat, lng, water_type, station_id, km, setup_time, ready_time=None):
        self.barge_id = barge_id
        self.name = name
        self.capacity = capacity
        self._lat = lat
        self._lng = lng
        self.setup_time = setup_time
        self._ready_time = datetime.strptime(ready_time, '%Y-%m-%d %H:%M:%S')
        self.assinged_status = 'available'
        self._water_status = str_to_enum(water_type)
        self._load = 0
        self._current_order = None
        self._crane_rate = 0
        self._crane_name = None
        self.assigned_tugboats = []
        self.weight_barge = weight_barge
        self._station_id = station_id
        self._river_km = km
        
    def get_load(self, is_only_load=False):
        if is_only_load:
            return self.load
        return self.load + self.weight_barge

    def __str__(self):
        return (f"Barge ID: {self.barge_id}, Name: {self.name}, LOAD: {self.load}, Capacity: {self.capacity}, "
                f"Location: ({self.lat}, {self.lng}), Setup Time: {self.setup_time} mins, "
                f"Ready Time: {self.ready_time}, Status: {self.status}")
        
    
