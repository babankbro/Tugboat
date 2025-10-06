# prompt: filter only sea tugboats in dic tugboat
# Define Tugboat class
from CodeVS.components.carrier import Carrier
from CodeVS.components.customer import Customer
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
                 max_speed, min_speed, lat, lng, status, km, station, ready_time=None):
        self.tugboat_id = tugboat_id
        self.name = name
        self.max_capacity = max_capacity
        self.max_barge = max_barge
        self.max_fuel_con = max_fuel_con
        self.soft_fuel_con = max_fuel_con/2
        self.min_fuel_con = max_fuel_con/4
        self.tug_type = str_to_enum(tug_type)
        self.max_speed = max_speed
        self.min_speed = min_speed
        self._lat = lat
        self._lng = lng
        self._status = str_to_enum(status)
        self._km = km
        #check format '%Y-%m-%d %H:%M:%S' or '%Y-%m-%d %H:%M'
        try:
            self._ready_time = datetime.strptime(ready_time, '%Y-%m-%d %H:%M:%S')
        except:
            self._ready_time = datetime.strptime(ready_time, '%Y-%m-%d %H:%M')
        self.assigned_barges = []
        self.current_load = 0
        self._current_order = None
        self.start_station = station
        
    def reset(self):
        self.assigned_barges = []
        
    #def update_last_status(self, status):
        
        
    def get_total_load(self, is_only_load=False):
        return sum(barge.get_load(is_only_load=is_only_load) for barge in self.assigned_barges)
    
    
    
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
        #station_id = tugboat_info['station_id']
        #station = self.data['stations'][station_id]
        location =tugboat_info['location']
        barges = sort_barges_by_distance(location[0], location[1], self.assigned_barges, barge_infos)
        total_time = 0.0  # เวลารวมเริ่มต้น
        nbarge = 0
        total_weight_barge = 0
        current_lat, current_lng = location
        setup_time_per_barge = 0.0
        barge_collect_infos = []
        current_status = tugboat_info['water_status']
        current_km = tugboat_info['river_km']
        total_distance = 0
        total_setup_time = 0
        barge_ids = []
        start_id = tugboat_info['station_id']
        #print("Station iD:######################", start_id)
        for barge in barges:
            barge_info =   barge_infos[barge.barge_id][-1]
            barge_river_km = barge_info['river_km']
            #print("B_038 ##############", barge_info['station_id'], barge_info['river_km']) if barge.barge_id == 'B_038' else None
            
            tugboat_speed = self.calculate_speed(total_weight_barge, nbarge, total_weight_barge)
            # travel_infos = {
            #     'start_location': (current_lat, current_lng),
            #     'end_location': barge_info['location'],
            #     'speed': tugboat_speed,
            #     'start_km': current_km,
            #     'end_km': barge_river_km
            # }
            travel_info = TravelInfo((current_lat, current_lng), 
                                     (barge_info['location'][0], barge_info['location'][1]), 
                                     tugboat_speed, current_km, barge_river_km,
                                     start_id=start_id, end_id=barge_info['station_id'])
            # print("TravelInfo Display", str(travel_info)) if barge.barge_id == 'B_084' else None
            water_status = barge_info['water_status']
            #print("EEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE", TravelHelper._instance)
     
          
            distance, travel_time, travel_steps = TravelHelper._instance.process_travel_steps(current_status, 
                                                                                              water_status, 
                                                                                              travel_info)
            
            #print("Travel Steps #########################:", str(travel_steps[0])) if self.tugboat_id == 'RiverTB_11' and barge.barge_id == 'B_032' else None
            #print("Travel Steps #########################:", barge_info) if self.tugboat_id == 'RiverTB_11' and barge.barge_id == 'B_032' else None
            # if barge.barge_id == 'B_038' and self.tugboat_id == 'SeaTB_02':
            #      for travel_step in travel_steps:
            #          print(travel_step)
            
            #print("Travel Steps:", travel_infos['start_location'], travel_infos['end_location'], travel_steps) if self.tugboat_id == 'SeaTB_05' and barge.barge_id == 'B_150' else None
                
            
            setup_time = barge.setup_time / 60.0  # แปลงเวลาเชื่อมต่อจากนาทีเป็นชั่วโมง
            total_time += travel_time + setup_time  # รวมเวลาเดิน
            total_weight_barge += barge.weight_barge
            nbarge += 1
            current_lat = barge_info['location'][0]
            current_lng = barge_info['location'][1]
            
            current_km = barge_river_km
            barge_ids.append(barge.barge_id)
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
                'end_status':water_status,
                'barge_ids': list(barge_ids)
            }
            
            total_distance += distance
            total_setup_time += setup_time
            start_id = barge_info['station_id']
            current_status = water_status
            barge_collect_infos.append(barge_collect_info)
            #print(f"Barge {barge.barge_id} - Travel Time: {travel_time:.2f} hours, Setup Time: {setup_time:.2f} hours")
        #print(f"Total Time: {total_time:.2f} hours")
        return {"total_time":total_time, "last_location": (current_lat, current_lng), "total_distance": total_distance, 
                'total_setup_time': total_setup_time,
                'barge_collect_infos': barge_collect_infos }
    
    def calculate_travel_first_barge(self, barge_scheule):
        # travel to carriers
        # compute time grab product
        # -start time
        # cr1 b1 b3  cr2 b2 b4  
        order = self.assigned_barges[0].current_order
        return self.calculate_travel_to_single_start_object(order, barge_scheule)
    
    
    def calculate_travel_to_single_start_object(self, order, barge_scheule):
        
        start_object = order.start_object
        lastbarge = self.assigned_barges[-1]
        barge_info = barge_scheule[lastbarge.barge_id][-1]
        blocation = barge_info['location']
        #print("Barge Info Carrier:", barge_info)
        nbarge = len(self.assigned_barges)
        base_weight_barges = self.get_total_weight_barge()
        speed_tug = self.calculate_speed(base_weight_barges, nbarge, base_weight_barges)
        # travel_infos = {
        #         'start_location': blocation,
        #         'end_location': (start_object.lat, start_object.lng),
        #         'speed': speed_tug,
        #         'start_km': barge_info["river_km"],
        #         'end_km': start_object.km if isinstance(start_object, Customer) else None
        #     }
        # check instance carrier is Carrier
        
        
        if (isinstance(start_object, Carrier) and order.order_type == TransportType.IMPORT):
            travel_infos = TravelInfo(blocation, 
                                  (start_object.lat, start_object.lng), 
                                  speed_tug, barge_info["river_km"], start_object.station.km if isinstance(start_object, Carrier) else None,
                                  start_id=barge_info["station_id"], end_id=start_object.station_id
                                  )
            end_status = start_object.station.water_type
            distance, travel_time, travel_steps = TravelHelper._instance.process_travel_steps(barge_info["water_status"], 
                                                                                     end_status, travel_infos)
        elif (isinstance(start_object, Customer) and order.order_type == TransportType.EXPORT):
            travel_infos = TravelInfo(blocation, 
                                  (start_object.lat, start_object.lng), 
                                  speed_tug, barge_info["river_km"], start_object.km if isinstance(start_object, Customer) else None,
                                  start_id=barge_info["station_id"], end_id=start_object.station_id
                                  )
            end_status = start_object.station.water_type
            #print("Start Object: #######################", start_object.station_id, barge_info["station_id"], barge_info["water_status"], end_status)
            distance, travel_time, travel_steps = TravelHelper._instance.process_travel_steps(barge_info["water_status"], 
                                                                                     end_status, travel_infos)
        else:
            raise Exception("Start object is not a Carrier or Customer")
        
        carrier_distance = distance
        base_weight_barges = self.get_total_weight_barge()
        nbarge = len(self.assigned_barges)
        
        #print("Speed Tugboat", speed_tug, base_weight_barges)
        travel_time = carrier_distance / speed_tug
        return {"travel_time":travel_time, 
                "last_location": (start_object.lat, start_object.lng),
                "speed": speed_tug,  
                "start_object": start_object,
                'travel_distance': distance,
                'travel_steps': travel_steps,
                'order_id': order.order_id}
    
    
    def calculate_travel_to_multiple_start_objects(self, barge_scheule):
        orders  =[ ]
        for barge in self.assigned_barges:
            if barge.current_order in orders:
                continue
            orders.append(barge.current_order)
        start_order = orders[0]
        result = self.calculate_travel_to_single_start_object(start_order, barge_scheule)
        if len(set(orders)) == 1:
            return result
        Nbarge = len(self.assigned_barges)
        base_weight_barges = 0
        for barge in self.assigned_barges:
            if barge.current_order == start_order:
                Nbarge -= 1
            else:
                base_weight_barges += barge.weight_barge 
        
        order_ids = [order.order_id for order in orders]
        print("Tugboat calculate_travel_to_multiple_start_objects", order_ids)
        for step in result['travel_steps']:
            step.order_id = start_order.order_id
        result['order_ids'] = [result['order_id']]
        last_order = start_order
        for order in orders[1:]:
            start_object = order.start_object
            speed_tug = self.calculate_speed(base_weight_barges, Nbarge, base_weight_barges)
            start_location = (last_order.start_object.lat, last_order.start_object.lng)
            
            if (isinstance(start_object, Carrier) and order.order_type == TransportType.IMPORT):
                travel_infos = TravelInfo(start_location, 
                                    (start_object.lat, start_object.lng), 
                                    speed_tug, last_order.start_object.station.km ,start_object.station.km if isinstance(start_object, Carrier) else None,
                                    start_id=last_order.start_object.station.station_id, end_id=start_object.station.station_id
                                    )
                end_status = start_object.station.water_type
                distance, travel_time, travel_steps = TravelHelper._instance.process_travel_steps(last_order.start_object.station.water_type, 
                                                                                        end_status, travel_infos)
            elif (isinstance(start_object, Customer) and order.order_type == TransportType.EXPORT):
                travel_infos = TravelInfo(start_location, 
                                    (start_object.lat, start_object.lng), 
                                    speed_tug, last_order.start_object.station.km ,start_object.km if isinstance(start_object, Customer) else None,
                                    start_id=last_order.start_object.station.station_id, end_id=start_object.station.station_id
                                    )
                end_status = start_object.station.water_type
                #print("Start Object: #######################", start_object.station_id, barge_info["station_id"], barge_info["water_status"], end_status)
                distance, travel_time, travel_steps = TravelHelper._instance.process_travel_steps(last_order.start_object.station.water_type, 
                                                                                        end_status, travel_infos)
            else:
                raise Exception("Start object is not a Carrier or Customer")
            

            carrier_distance = distance
            for barge in self.assigned_barges:
                if barge.current_order == order:
                    Nbarge -= 1
                    base_weight_barges -= barge.weight_barge 
            
            for step in travel_steps:
                step.order_id = order.order_id
            
            #print("Speed Tugboat", speed_tug, base_weight_barges)
            travel_time = carrier_distance / speed_tug
            result2 = {"travel_time":travel_time, 
                    "last_location": (start_object.lat, start_object.lng),
                    "speed": speed_tug,  
                    "start_object": start_object,
                    'travel_distance': distance,
                    'travel_steps': travel_steps,
                    'order_id': order.order_id}
            #combine result and result2 by adding the values of the same keys
            result['travel_time'] += result2['travel_time']
            result['travel_distance'] += result2['travel_distance']
            result['travel_steps'] += result2['travel_steps']
            result['speed'] = result['travel_distance']/result['travel_time'] if result['travel_time'] != 0 else 0
            result['order_ids'].append(result2['order_id'])
            
        
        return result
            

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
        # print("TUG SPEED", speed_tug) if self.tugboat_id == 'SeaTB_04' else None
        # print("--------", total_weight_barges, nbarge, base_weight_barges) if self.tugboat_id == 'SeaTB_04' else None
        # if self.tugboat_id == 'SeaTB_04':
        #     base_load = base_weight_barges
        #     load = total_weight_barges
        #     max_weight =self.max_capacity +  base_load
        #     load_ratio = load/ max_weight if max_weight else 0
        #     barge_ratio = nbarge / self.max_barge if self.max_barge else 0
        #     total_reduction_ratio = (load_ratio + barge_ratio) / 2
        #     current_speed = (self.max_speed - self.min_speed) * (1 - total_reduction_ratio) + self.min_speed
        #     print("Min speed", self.min_speed, "Max speed", self.max_speed)
            
        #     print(load_ratio, barge_ratio, total_reduction_ratio, current_speed)
        
        
        # travel_infos = {
        #         'start_location': start_location,
        #         'end_location': (end_station.lat, end_station.lng),
        #         'speed': speed_tug,
        #         'start_km': start_km,
        #         'end_km': end_station.km
        #     }
        travel_infos = TravelInfo(start_location, (end_station.lat, end_station.lng), speed_tug, start_km, end_station.km)
        
        #print("Travel infos", start_info['station'])
        
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
                'travel_steps': travel_steps}
        
    def calculate_travel_to_appointment(self, appointment_info):
        data = TravelHelper._instance.data
        # 1. get order_stations
        end_station  =  data['stations'][appointment_info['appointment_station']] 
        carrier = self.assigned_barges[0].current_order.start_object
        
        order = self.assigned_barges[0].current_order
        
        
        #print(end_station)
        
        if order.order_type == TransportType.IMPORT:
            #
            start_info = {'station':None, 'location': (carrier.lat, carrier.lng)}
        else:
            customer = self.assigned_barges[0].current_order.start_object
            start_info = {'station':customer.station, 'location': (customer.station.lat, customer.station.lng)}
            #print("Start info ############################", customer.station_id)
        
        
        
        end_info = {'station':data['stations'][appointment_info['appointment_station']], 'location': (end_station.lat, end_station.lng)}
        
        if order.order_type == TransportType.IMPORT:
            result = self.calculate_travel_start_to_end_river_location(start_info, end_info, 
                                                                       WaterBody.SEA, end_status = WaterBody.RIVER)
        else:
            result = self.calculate_travel_start_to_end_river_location(start_info, end_info, 
                                                                       WaterBody.RIVER, end_status = WaterBody.RIVER)
        
        # for step in result['travel_steps']:
        #     print(step)
        
        return {"travel_time":result['travel_time'], 
                "last_location": result['end_location'],
                "speed": result['speed'],  
                "start_object": carrier,
                "start_location": result['start_location'],
                'travel_distance': result['travel_distance'],
                'travel_steps': result['travel_steps']}
        
    def calculate_river_to_customer(self, input_travel_info):
        # order = self.assigned_barges[0].current_order
        end_station = self.assigned_barges[0].current_order.des_object
        nbarge = len(self.assigned_barges)
        start_station = TravelHelper._instance.data['stations'][ input_travel_info['appointment_station_id']]
        total_weight_barges = self.get_total_load()
        base_weight_barges = self.get_total_weight_barge()
        speed_tug = self.calculate_speed(total_weight_barges, nbarge, base_weight_barges)
        # travel_infos = {
        #         'start_location': (start_station.lat, start_station.lng),
        #         'end_location': (end_station.lat, end_station.lng),
        #         'speed': speed_tug,
        #         'start_km': start_station.km,
        #         'end_km': end_station.km
        #     }
        
        travel_infos = TravelInfo((start_station.lat, start_station.lng), 
                                  (end_station.lat, end_station.lng), 
                                  speed_tug, start_station.km, end_station.km, start_station.station_id, end_station.station_id)
        
        distance, travel_time, travel_steps = TravelHelper._instance.process_travel_steps(WaterBody.RIVER, WaterBody.RIVER,
                                                                                          travel_infos)
        #print("Speed Tugboat", speed_tug, base_weight_barges)
        travel_time = distance / speed_tug
        return {"travel_time":travel_time, 
                "last_location": (end_station.lat, end_station.lng),
                "speed": speed_tug,  
                "start_object": start_station,
                'travel_distance': distance,
                'travel_steps': travel_steps}
        
        
    def calculate_river_to_carrier(self, input_travel_info):
        end_station = self.assigned_barges[0].current_order.des_object.station
        nbarge = len(self.assigned_barges)
        start_station = TravelHelper._instance.data['stations'][ input_travel_info['appointment_station_id']]
        total_weight_barges = self.get_total_load()
        base_weight_barges = self.get_total_weight_barge()
        speed_tug = self.calculate_speed(total_weight_barges, nbarge, base_weight_barges)
        # travel_infos = {
        #         'start_location': (start_station.lat, start_station.lng),
        #         'end_location': (end_station.lat, end_station.lng),
        #         'speed': speed_tug,
        #         'start_km': start_station.km,
        #         'end_km': end_station.km
        #     }
        
        travel_infos = TravelInfo((start_station.lat, start_station.lng), 
                                  (end_station.lat, end_station.lng), 
                                  speed_tug, start_station.km, end_station.km, 
                                  start_station.station_id, end_station.station_id)
        
        distance, travel_time, travel_steps = TravelHelper._instance.process_travel_steps(WaterBody.RIVER, WaterBody.SEA, travel_infos)
        #print("Speed Tugboat", speed_tug, base_weight_barges)
        travel_time = distance / speed_tug
        return {"travel_time":travel_time, 
                "last_location": (end_station.lat, end_station.lng),
                "speed": speed_tug,  
                "start_object": start_station,
                'travel_distance': distance,
                'travel_steps': travel_steps}
        
        
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
        nofactor_speed = self._calculate_speed_no_factor(load, nbarge, base_load)
        return nofactor_speed
    
    
    def _calculate_speed_no_factor(self, load, nbarge, base_load):
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
