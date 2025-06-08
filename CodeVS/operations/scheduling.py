import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import timedelta
from typing import List, Dict
from CodeVS.components.order import Order
from CodeVS.components.barge import Barge
from CodeVS.components.tugboat import Tugboat
from CodeVS.utility.helpers import *


def schedule_carrier_order_single_tugboat(order: Order, tugboat: Tugboat, 
                                 active_cranes: List[Dict] = None,
                                 tugboat_ready_time: int = 0) -> Dict:
    """
    Schedule an order for a single tugboat, updating crane ready times.
    
    Args:
        order: The order to schedule
        tugboat: Tugboat to assign
        active_cranes: List of crane states (optional)
        tugboat_ready_time: Time when tugboat becomes available (default 0)
        
    Returns:
        Schedule dictionary for the tugboat
    """
    if active_cranes is None:
        active_cranes = [{
            'crane_id': f'cr{i+1}',
            'rate': order.get_crane_rate(f'cr{i+1}'),
            'time_ready': max(tugboat_ready_time, order.get_crane_ready_time(f'cr{i+1}')),
            'assigned_product': 0
        } for i in range(7)]
    else:
        for crane in active_cranes:
            crane['time_ready'] = max(tugboat_ready_time, crane['time_ready'])
    
    # Calculate total product for this tugboat
    total_demand = sum([b.get_load(is_only_load=True) for b in tugboat.assigned_barges])
    
    # Sort barges by load (largest first)
    sorted_barges = sorted(tugboat.assigned_barges, key=lambda b: b.get_load(is_only_load=True), reverse=True)
    
    # Initialize schedules
    crane_schedule = []
    barge_schedule = []
    
    # Assign product to cranes
    remaining_product = total_demand
    barge_index = 0
    while remaining_product > 0:
        # Find next available crane considering both time_ready and rate
        def crane_score(crane):
            time_score = 1 / (crane['time_ready'] + 1)
            rate_score = crane['rate'] / max(c['rate'] for c in active_cranes)
            return 100 * time_score + 0.1 * rate_score
            
        next_crane = max(active_cranes, key=crane_score)
        
        # Assign barge load to crane
        assign_amount = sorted_barges[barge_index].get_load(is_only_load=True)
        next_crane['assigned_product'] += assign_amount
        remaining_product -= assign_amount
        time_consumed = assign_amount / next_crane['rate']
        
        # Update crane's time ready
        next_crane['time_ready'] += time_consumed
        
        # Record crane assignment
        crane_schedule.append({
            'crane_id': next_crane['crane_id'],
            'product': assign_amount,
            'rate': next_crane['rate'],
            'barge': sorted_barges[barge_index],
            'start_time': next_crane['time_ready'] - time_consumed,
            'crane_schedule': next_crane['time_ready'],
            'time_consumed': time_consumed
        })
        
        # Record barge assignment
        barge_schedule.append({
            'barge_id': sorted_barges[barge_index].barge_id,
            'product': assign_amount,
            'start_time': next_crane['time_ready'] - time_consumed,
            'end_time': next_crane['time_ready']
        })
        
        barge_index += 1
    
    # Calculate total time for this tugboat
    total_time = max(crane['crane_schedule'] for crane in crane_schedule)
    start_time = min(crane['start_time'] for crane in crane_schedule)
    max_time_barge_shedule = max(barge_info['end_time'] for barge_info in barge_schedule)
    
    
    return {
        'order_id': order.order_id,
        'tugboat_id': tugboat.tugboat_id,
        'total_time': total_time,
        'crane_schedule': crane_schedule,
        'barge_schedule': barge_schedule,
        'total_product': total_demand,
        'tugboat_schedule': {
            'tugboat_id': tugboat.tugboat_id,
            'total_time': total_time,
            'start_time': start_time,
            'end_time': max_time_barge_shedule,
            'start_datetime': get_next_quarter_hour( order.start_datetime + timedelta(minutes=60*start_time)),
            'end_datetime': get_next_quarter_hour( order.start_datetime + timedelta(minutes=60*max_time_barge_shedule))
            
        
        }
    }

def schedule_carrier_order_tugboats(order: Order, tugboats: List[Tugboat],  active_cranes, tugboat_ready_times: List[float] = None) -> List[Dict]:
    """
    Schedule an order across multiple tugboats, updating crane ready times between assignments.
    
    Args:
        order: The order to schedule
        tugboats: List of tugboats to assign
        
    Returns:
        List of schedule dictionaries for each tugboat
    """
    schedules = []
    
    if tugboat_ready_times is None:
        tugboat_ready_times = [0]*len(tugboats)
     
    # Initialize crane states
    
    
    for i, tugboat in enumerate(tugboats):
        schedule = schedule_carrier_order_single_tugboat(order, tugboat, 
                                                 active_cranes, tugboat_ready_times[i])
        schedules.append(schedule)
        #print(f"Schedule for Tugboat GG {tugboat.tugboat_id}:", tugboat_ready_times[i])
    
    # print("\nActive Cranes:", tugboat_ready_times)
    # for crane in active_cranes:
    #     print(crane)
    
    return schedules


def schedule_customer_order_single_tugboat(order: Order, tugboat: Tugboat, 
                                 active_cranes: List[Dict] = None,
                                 tugboat_ready_time: int = 0) -> Dict:
    
    # Calculate total product for this tugboat
    total_demand = sum([b.get_load(is_only_load=True) for b in tugboat.assigned_barges])
    
    # Sort barges by load (largest first)
    sorted_barges = sorted(tugboat.assigned_barges, key=lambda b: b.get_load(is_only_load=True), reverse=True)
    
    # Initialize schedules
    loader_schedule = []
    barge_schedule = []
    
    # Assign product to cranes
    remaining_product = total_demand
    barge_index = 0
    while remaining_product > 0:
        # Find next available crane considering both time_ready and rate
        def loader_score(loader):
            time_score = 1 / (loader['time_ready'] + 1)
            rate_score = loader['rate'] / max(c['rate'] for c in active_cranes)
            return 100 * time_score + 0.1 * rate_score
            
        next_crane = max(active_cranes, key=loader_score)
        
        # Assign barge load to crane
        assign_amount = sorted_barges[barge_index].get_load(is_only_load=True)
        next_crane['assigned_product'] += assign_amount
        remaining_product -= assign_amount
        time_consumed = assign_amount / next_crane['rate']
        
        # Update crane's time ready
        next_crane['time_ready'] += time_consumed
        #print(next_crane)
        # Record crane assignment
        loader_schedule.append({
            'loader_id': next_crane['loader_id'],
            'product': assign_amount,
            'rate': next_crane['rate'],
            'barge': sorted_barges[barge_index],
            'start_time': next_crane['time_ready'] - time_consumed,
            'loader_schedule': next_crane['time_ready'],
            'time_consumed': time_consumed
        })
        
        # Record barge assignment
        barge_schedule.append({
            'barge_id': sorted_barges[barge_index].barge_id,
            'product': assign_amount,
            'start_time': next_crane['time_ready'] - time_consumed,
            'end_time': next_crane['time_ready']
        })
        
        barge_index += 1
    
    # Calculate total time for this tugboat
    total_time = max(crane['loader_schedule'] for crane in loader_schedule)
    start_time = min(crane['start_time'] for crane in loader_schedule)
    max_time_barge_shedule = max(barge_info['end_time'] for barge_info in barge_schedule)
    
    
    return {
        'order_id': order.order_id,
        'tugboat_id': tugboat.tugboat_id,
        'total_time': total_time,
        'loader_schedule': loader_schedule,
        'barge_schedule': barge_schedule,
        'total_product': total_demand,
        'tugboat_schedule': {
            'tugboat_id': tugboat.tugboat_id,
            'total_time': total_time,
            'start_time': start_time,
            'end_time': start_time + max_time_barge_shedule,
            #'start_datetime': get_next_quarter_hour( order.due_datetime + timedelta(minutes=60*start_time)),
            #'end_datetime': get_next_quarter_hour( order.due_datetime + timedelta(minutes=60*max_time_barge_shedule))
        }
    }

def shecdule_customer_order_tugboats(order: Order, tugboats: List[Tugboat], active_loadings, tugboat_ready_times: List[float] = None) -> List[Dict]:
   
    
    schedules = []
    
    
    
    for i, tugboat in enumerate(tugboats):
        schedule = schedule_customer_order_single_tugboat(order, tugboat, 
                                                 active_loadings, tugboat_ready_times[i])
        schedules.append(schedule)
        #print(f"Schedule for Tugboat XX {tugboat.tugboat_id}:", tugboat_ready_times[i])
    
    
    
    return schedules
