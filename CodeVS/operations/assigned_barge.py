from datetime import timedelta
from CodeVS.components.transport_type import TransportType
from CodeVS.utility.helpers import haversine
# from CodeVS.components.solution import *

def assign_barges_to_orders(orders, barges, assigned_barge_df):
    raise NotImplementedError()
    current_used_barge_list = []
    for _, assignment in assigned_barge_df.iterrows():
        order_id = assignment['ORDER ID']
        barge_id = assignment['BARGE ID']
        load = assignment['LOAD']
        crane_name= assignment['CRANE RATE']
        used_start = assignment['USED START']
        used_end = assignment['USED END']

        if barge_id in barges:
            barge = barges[barge_id]
            barge.status = 'assigned'
            barge._current_order = orders[order_id]
            barge.load = load
            barge.crane_name = crane_name
            barge.crane_rate = barge.current_order.crane_rates[int(crane_name.replace('cr', '')) - 1]
            barge.used_start = used_start
            barge.used_end = used_end
            # Additional attributes can be set here if needed

            current_used_barge_list.append(barge)
    return current_used_barge_list


# Step 2: Assign barges to tugboats based on constraints
def assign_barges_to_all_orders(orders, barges, active_cranes):
    raise NotImplementedError
    """Assign barges to all orders considering capacity, location and time availability"""
    order_assigned_barges = {}
    
    # Sort orders by priority (import first, then export)
    sorted_orders = sorted(orders.values(), 
                         key=lambda o: 0 if o.order_type == TransportType.IMPORT else 1)
    
    for order in sorted_orders:
        order_assigned_barges[order.order_id] = assign_barges_to_single_order(
            order, barges, active_cranes
        )
            
    return order_assigned_barges

def assign_barges_to_tugboat( tugboat, order_barges):
    #print(f"Assigning barges to tugboat MM {tugboat.tugboat_id}...")

    while len(order_barges) > 0:
        barge = order_barges[0]
        if tugboat.assign_barge(barge):
            #print({'tugboat_id': tugboat.tugboat_id, 'barge_id': barge.barge_id})
            order_barges.pop(0)
        else:
            #print(f"Tugboat {tugboat.tugboat_id} cannot accommodate barge {barge.barge_id}")
            #print(len(tugboat.assigned_barges), tugboat.max_capacity)
            #order_barges.insert(0, barge)
            break
    
    
def assign_barges_to_sea_tugboats(solution, appointment_location, order, data, sea_tugboats, order_barges):
    barges = data['barges']
    assigned_barges = [barges[ barge_info['barge_id']] for barge_info in order_barges]
    assigned_tugboats = []
    
    order_start = order.start_datetime
    order_end = order.due_datetime
    
    # Filter available barges that are free during order time window and ready
    avaliable_sea_tugboats = [
        t for t in sea_tugboats.values() 
        if (solution.get_ready_time_tugboat(t)is None or solution.get_ready_time_tugboat(t) <= order_end) 
    ]
    
    # total capacity of available tugboats
    total_capacity = sum(t.max_capacity for t in avaliable_sea_tugboats)
    
    days = 1
    while total_capacity < order.demand*1.2:
        # create new available tugboats
        avaliable_sea_tugboats = [
            t for t in sea_tugboats.values() 
            if (solution.get_ready_time_tugboat(t)is None or solution.get_ready_time_tugboat(t) <= order_end + timedelta(days=days)) 
        ]
        total_capacity = sum(t.max_capacity for t in avaliable_sea_tugboats)
        days += 1
    
    # For import orders, sort by distance to carrier
    if order.order_type == TransportType.EXPORT:
        avaliable_sea_tugboats.sort(key=lambda t: 
            
            ((solution.get_location_tugboat(t)[0] - appointment_location[0])**2 + 
            (solution.get_location_tugboat(t)[1] - appointment_location[1])**2)**0.5)
    else:
        raise ValueError("Order type is not supported")
    
    #print(f" Available Tugboats: {len(avaliable_sea_tugboats)}")
    
    
    
    tugboat_ids = [tugboat.tugboat_id for tugboat in avaliable_sea_tugboats]
    #print(f"Tugboat IDs: {tugboat_ids}")
    
    for tugboat in avaliable_sea_tugboats:
        assign_barges_to_tugboat( tugboat, assigned_barges)
        
        if len(assigned_barges) == 0:
            #print("Commpleted all barges assignment VV")
            if len(tugboat.assigned_barges) != 0:
                assigned_tugboats.append(tugboat)
            break
        assigned_tugboats.append(tugboat)
    return assigned_tugboats
 
def assign_barges_to_river_tugboats(solution, appointment_location, order, data, river_tugboats, order_barges):
    barges = data['barges']
    assigned_barges = [barges[ barge_info['barge_id']] for barge_info in order_barges]
    assigned_tugboats = []
    
    order_start = order.start_datetime
    order_end = order.due_datetime
    
    # Filter available barges that are free during order time window and ready
    avaliable_river_tugboats = [
        t for t in river_tugboats.values() 
        if (solution.get_ready_time_tugboat(t)is None or solution.get_ready_time_tugboat(t) <= order_end) 
    ]
    
    # total capacity of available tugboats
    total_capacity = sum(t.max_capacity for t in avaliable_river_tugboats)
    
    days = 1
    while total_capacity < order.demand*1.2:
        # create new available tugboats
        avaliable_river_tugboats = [
            t for t in river_tugboats.values() 
            if (solution.get_ready_time_tugboat(t)is None or solution.get_ready_time_tugboat(t) <= order_end + timedelta(days=days)) 
        ]
        total_capacity = sum(t.max_capacity for t in avaliable_river_tugboats)
        days += 1
        #print(f"Total capacity: {total_capacity}, days: {days}, order demand: {order.demand}")
    
    # For import orders, sort by distance to carrier
    if order.order_type == TransportType.IMPORT:
        avaliable_river_tugboats.sort(key=lambda t: 
            
            ((solution.get_location_tugboat(t)[0] - appointment_location[0])**2 + 
            (solution.get_location_tugboat(t)[1] - appointment_location[1])**2)**0.5)
    
    #print(f" Available Tugboats: {len(avaliable_river_tugboats)}")
    
    
    
    tugboat_ids = [tugboat.tugboat_id for tugboat in avaliable_river_tugboats]
    #print(f"Tugboat IDs: {tugboat_ids}")
    
    for tugboat in avaliable_river_tugboats:
        assign_barges_to_tugboat( tugboat, assigned_barges)
        
        if len(assigned_barges) == 0:
            #print("Commpleted all barges assignment VV")
            if len(tugboat.assigned_barges) != 0:
                assigned_tugboats.append(tugboat)
            break
        assigned_tugboats.append(tugboat)
    return assigned_tugboats

def order_barges_from_arrival_tugboats(data, lookup_tugboat_results):
    order_barges = []
    lookup_order_barges = {}
    for tugboat_id in lookup_tugboat_results:
        #print(tugboat_id)
        result_tugboat = lookup_tugboat_results[tugboat_id]
        tugboat = data['tugboats'][tugboat_id]
        for barge in tugboat.assigned_barges:
            info = {
                'barge': barge,
                'barge_id': barge.barge_id,
                'tugboat_id': tugboat.tugboat_id,
                'location': result_tugboat['data_points'][-1]["ID"],
                'arrival_appointment_datetime': result_tugboat['data_points'][-1]['enter_datetime']
            }
            order_barges.append(info)
            lookup_order_barges[barge.barge_id] = info
            
    # sorted order barges by arrival time
    order_barges.sort(key=lambda b: b['arrival_appointment_datetime'])
    return order_barges, lookup_order_barges

