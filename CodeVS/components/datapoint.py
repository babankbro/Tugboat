from datetime import timedelta

class DataPoint:
    def __init__(self, ID, type, name, enter_datetime, distance, time, 
                 speed, type_point, rest_time, order_trip, barge_ids, station_id):
        """
        DataPoint class to replace appointment_location dictionary structure.
        
        Args:
            ID: Identifier for the data point
            type: Type of the data point (e.g., "Destination Barge")
            name: Name/description of the data point
            enter_datetime: Entry datetime
            distance: Travel distance
            time: Travel time
            speed: Travel speed
            type_point: Type of point (e.g., 'main_point')
            rest_time: Rest time at the data point
            station_id: Station ID
        """
        self.ID = ID
        self.type = type
        self.name = name
        self.enter_datetime = enter_datetime
        #self.exit_datetime = exit_datetime
        self.rest_time = rest_time
        self.start_arrival_datetime = enter_datetime + timedelta(hours=rest_time)
        self.exit_datetime = self.start_arrival_datetime + timedelta(hours=time)
        self.distance = distance
        self.time = time
        self.speed = speed
        self.type_point = type_point
        if barge_ids is None:
            self.barge_ids = []
        else:
            self.barge_ids = list(barge_ids)
        self.total_load = 0
        self.total_load_v2 = 0
        self.order_distance = 0
        self.barge_speed = 0
        self.order_arrival_time = 0
        self.order_time = 0
        self.travel_info = None
        self.order_trip = None
        self.station_id = station_id
        
        
        
    
    def to_dict(self):
        """Convert DataPoint back to dictionary format if needed for compatibility."""
        return {
            "ID": self.ID,
            'type': self.type,
            'name': self.name,
            'enter_datetime': self.enter_datetime,
            'start_arrival_datetime': self.start_arrival_datetime,
            'exit_datetime': self.exit_datetime,
            'rest_time': self.rest_time,
            'distance': self.distance,
            'time': self.time,
            'speed': self.speed,
            'type_point': self.type_point,
            'order_trip': self.order_trip,
            'barge_ids': self.barge_ids,
            'total_load': self.total_load,
            'total_load_v2': self.total_load_v2,
            'order_distance': self.order_distance,
            'order_time': self.order_time,
            'barge_speed': self.barge_speed,
            'order_arrival_time': self.order_arrival_time,
            'travel_info': self.travel_info,
            'station_id': self.station_id
        }
    
    def __repr__(self):
        return f"DataPoint(ID={self.ID}, type='{self.type}', name='{self.name}')"