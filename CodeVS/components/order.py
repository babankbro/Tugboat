from datetime import datetime
from CodeVS.components.transport_type import *
import config_problem 

class Order:
    def __init__(self, order_id, order_type, start_point, des_point, product, demand, start_datetime,
                 due_datetime, loading_rate, crane_rates, crane_ready_times):
        self.order_id = order_id
        self.order_type: TransportType = str_to_enum(order_type)
        self.start_point = start_point
        self.des_point = des_point  
        self.product = product
        self.demand = demand
        self.start_datetime = datetime.strptime(start_datetime, '%Y-%m-%d %H:%M:%S')
        self.due_datetime = datetime.strptime(due_datetime, '%Y-%m-%d %H:%M:%S')
        self.loading_rate = loading_rate
        
        # Ensure we have exactly 7 crane rates, filling missing ones with 0
        self.crane_rates = list(crane_rates) + [0] * (config_problem.MAX_CRANES - len(crane_rates))
        
        # Ensure we have exactly 7 time ready values, filling missing ones with 0
        self.crane_ready_times = list(crane_ready_times) + [0] * (config_problem.MAX_CRANES - len(crane_ready_times))
        
        self.start_object = None
        self.des_object = None

    def get_crane_rate(self, crane_name):
        """Get crane rate by crane number (1-7)"""
        crane_num = int(crane_name.replace('cr', ''))
        if 1 <= crane_num <= config_problem.MAX_CRANES:
            return self.crane_rates[crane_num - 1]
        return 0

    def get_crane_ready_time(self, crane_name):
        """Get time ready by crane number (1-7)"""
        crane_num = int(crane_name.replace('cr', ''))
        if 1 <= crane_num <= config_problem.MAX_CRANES:
            return self.crane_ready_times[crane_num - 1]
        return 0

    def __str__(self):
        #raise Exception("Order __str__")
        return (f"Order ID: {self.order_id}\n"
                f"Type: {self.order_type}\n"
                f"Start Point: {self.start_point}\n"
                f"Destination Point: {self.des_point}\n"
                f"Product: {self.product}\n"
                f"Demand: {self.demand}\n"
                f"Start Datetime: {self.start_datetime}\n"
                f"Due Datetime: {self.due_datetime}\n"
                f"Loading Rate: {self.loading_rate}\n"
                f"Crane Rates: {self.crane_rates}\n"
                f"Time Ready: {self.crane_ready_times}")
