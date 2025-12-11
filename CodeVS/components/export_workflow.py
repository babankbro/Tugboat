"""
Export Workflow
Handles export operations: River (Customer) → Sea (Carrier)
"""

from CodeVS.components.base_transport_workflow import BaseTransportWorkflow
from CodeVS.components.water_enum import WaterBody
from CodeVS.operations.assigned_barge import order_barges_from_arrival_tugboats
from CodeVS.operations.scheduling import schedule_carrier_order_barges, schedule_customer_order_barges
from CodeVS.components.datapoint import DataPoint
import config_problem


class ExportWorkflow(BaseTransportWorkflow):
    """
    Export workflow: River (Customer) → Sea (Carrier)
    
    Flow:
    1. Collect empty barges → Customer area (River)
    2. Move barges → Customer locations
    3. Load cargo at Customer
    4. Transport loaded barges → Carrier (Sea location)
    5. Unload at Carrier
    """
    
    def __init__(self, solution):
        """
        Initialize export workflow
        
        Args:
            solution: Parent Solution instance
        """
        super().__init__(solution)
        
        self.workflow_type = "EXPORT"
    
    def execute_step1(self, assigned_barges):
        """
        EXPORT Step 1: Collect empty barges and bring to customer area (river)
        Barges in sea need to be brought up to river
        
        Args:
            assigned_barges: List of assigned barge information
            
        Returns:
            tuple: (tugboat_results, arrived_barges)
        """
        bring_up_sea_barges = []
        save_load = {}
      
        #import timedelta
        from datetime import timedelta
        min_order_start_time = None
        order_min_id = None
        for bargeinfo in assigned_barges:
            order_id = bargeinfo['assigned_order']
            barge_id = bargeinfo['barge'].barge_id
            barge_ready_time = self.solution.get_ready_barge(bargeinfo['barge'])
            order_start_time = self.orders[order_id].start_datetime
            target_ready_time = order_start_time - timedelta(days=config_problem.NEXT_DAY_WORK)
            if barge_ready_time < target_ready_time:
                result = self.solution.barge_scheule[barge_id][-1]
                self.solution.update_single_barge_order_scheule(order_id, barge_id,
                                                       target_ready_time, 
                                                       target_ready_time, 
                                                       result['river_km'], 
                                                       result['water_status'], 
                                                       result['location'], 
                                                       result['station_id'])
            if min_order_start_time is None:
                min_order_start_time = order_start_time
                order_min_id = order_id
            elif order_start_time < min_order_start_time:
                min_order_start_time = order_start_time
                order_min_id = order_id
                #print(order_id, barge_id, barge_ready_time, order_start_time, target_ready_time)
                #print(self.solution.barge_scheule[barge_id][-1])
        
                
                #print(order_id, tugboat_id, tugboat_ready_time, order_start_time, target_ready_time)
                #print(self.solution.tugboat_scheule[tugboat_id][-1])
                
        tugboats = self.solution.data['tugboats']
        for tugboat_id, tugboat in tugboats.items():
            tugboat_ready_time = self.solution.get_ready_time_tugboat(tugboat)
            target_ready_time = min_order_start_time - timedelta(days=config_problem.NEXT_DAY_WORK)
            if tugboat_ready_time < target_ready_time:
                
                info = self.solution.tugboat_scheule[tugboat_id][-1].copy()
                info['end_datetime'] = target_ready_time
                info['start_datetime'] = target_ready_time
                
                
                # print("You're Doing Great!")
                self.solution.tugboat_scheule[tugboat_id].append(info)

                # if order_min_id == "ODR_017":
                #     raise Exception("Order min id is ODR_017", order_min_id, min_order_start_time)
                    

        for bargeinfo in assigned_barges:
            barge = bargeinfo['barge']
            station_barge = self.data["stations"][
                self.solution.get_station_id_barge(barge)
            ]
            
            # If barge is in sea, bring it to river
            if station_barge.water_type == WaterBody.SEA:
                save_load[barge.barge_id] = barge.get_load(is_only_load=True)
                barge.set_load(500)  # Temporary load for calculation
                bring_up_sea_barges.append(bargeinfo)
        
        if len(bring_up_sea_barges) == 0:
            #print("    No barges need to be brought from sea to river")
            return None, None
        
        print(f"    Bringing {len(bring_up_sea_barges)} barges from sea to river...")
        
        # Multiple trips: Bring barges from sea to river (opposite of import)
        all_tugboat_results = []
        all_bring_up_barges = bring_up_sea_barges.copy()
        round_trip_order = self.global_step 
        iteration = 0
        
        while len(all_bring_up_barges) > 0:
            iteration += 1
            
            if iteration > 100:
                raise Exception(
                    f"Export Step 1: Exceeded max iterations ({iteration})"
                )
            
            copy_bring_up_barges = all_bring_up_barges.copy()
            
            # Bring barges from sea to river
            isCompleted, tugboat_results = self.solution._bring_barge_orders_travel_export(
                copy_bring_up_barges, order_trip=round_trip_order
            )
            #print("Iteration", iteration, isCompleted, len(tugboat_results), len(all_bring_up_barges), len(copy_bring_up_barges))
            if not isCompleted:
                # If failed, try to continue with remaining barges
                print(f"Export Step 1: Warning - Could not bring all {len(copy_bring_up_barges)} barges in trip {round_trip_order}")
                if iteration == 1:
                    # If first attempt fails completely, raise exception
                    raise Exception(
                        f"Export Step 1 failed: Could not bring any barges from sea to river"
                    )
                break
            else:
                #get all barges that are not in the list
                arrived_barge_ids = []
                for tugboat_result in tugboat_results:
                    tugboat_id = tugboat_result['tugboat_id']
                    for data_point in tugboat_result['data_points']:
                        #print(data_point)
                        if data_point.type == "Destination Barge":
                            arrived_barge_ids.extend(data_point.barge_ids)
                        
                #remove barge_id from copy_bring_up_barges
                copy_bring_up_barges = [barge_info for barge_info in copy_bring_up_barges if barge_info['barge'].barge_id not in arrived_barge_ids]
                
                    
            
            if len(tugboat_results) == 0:
                break
            
            lookup_tugboat_results = {
                tugboat_result['tugboat_id']: tugboat_result 
                for tugboat_result in tugboat_results
            }
            
            order_barges, lookup_order_barges = order_barges_from_arrival_tugboats(
                self.data, lookup_tugboat_results
            )
            
            # Update schedules for bringing barges up to river
            self.solution.update_shedule_bring_down_orders_barges(
                lookup_order_barges, lookup_tugboat_results
            )
            self.solution._extend_update_tugboat_results(tugboat_results, round_trip_order)
            self.solution._reset_all_tugboats()
            
            all_tugboat_results.extend(tugboat_results)
            all_bring_up_barges = copy_bring_up_barges
            round_trip_order += 1
        
        # Restore original load
        for barge_id in save_load:
            barge = self.barges[barge_id]
            barge.set_load(save_load[barge_id])
        
        #print(f"    Successfully positioned {len(bring_up_sea_barges)} barges")
        
        # ready_barge = self.solution.get_ready_barge( assigned_barges[0]['barge'])
        # print(ready_barge)
        # raise Exception("Ready barge")
        
        
        return all_tugboat_results, bring_up_sea_barges
    
    def execute_step2(self, assigned_barges, assigned_barge_order_ids):
        """
        EXPORT Step 2: Move barges from appointment to customer locations (river)
        Uses RIVER tugboats to transport empty barges to customers
        
        Args:
            assigned_barges: List of assigned barge information
            assigned_barge_order_ids: Dictionary mapping barge_id to order_id
            
        Returns:
            tuple: (tugboat_results, arrived_barges)
        """
        tugboats = self.river_tugboats
        self._reset_tugboats(tugboats)
        
  
        all_assigned_barges = [barge_info['barge'] for barge_info in assigned_barges]
        lookup_assigned_barges = {
            barge_info['barge'].barge_id: barge_info 
            for barge_info in assigned_barges
        }
        
        order_ids = [barge_info['assigned_order'] for barge_info in assigned_barges]
        
        # Find earliest customer location (for export, customers are the START point)
        min_order_id, min_start_datetime, start_station, max_due_datetime = \
            self._find_earliest_order(order_ids)
        
        #print(f"    Transporting {len(all_assigned_barges)} barges to customers using RIVER tugboats...")
        
        round_trip_order = self.global_step 
        iteration = 0
        all_tugboat_results = []
        arrived_barges = []
        
        
        
        save_load = {}
        for barge in all_assigned_barges:
            save_load[barge.barge_id] = barge.get_load(is_only_load=True)
            barge.set_load(barge.weight_barge)  # Temporary load for calculation
        
        
        
        
        while len(all_assigned_barges) > 0:
            iteration += 1
            
            if iteration > 100:
                raise Exception(
                    f"Export Step 2: Exceeded max iterations ({iteration})"
                )
            
            copy_all_assigned_barges = all_assigned_barges.copy()
            
            # Assign tugboats with retry logic
            is_completed, assigned_tugboats = self._assign_tugboats_with_retry(
                min_order_id, start_station, min_start_datetime,
                max_due_datetime, tugboats, copy_all_assigned_barges
            )
            
            if not is_completed:
                raise Exception("Export Step 2: Failed to assign barges to tugboats")
            
            if len(assigned_tugboats) == 0:
                break
            
            # Transport barges to customer locations
            tugboat_results, late_time = self.solution.arrival_step_transport_all_orders(
                min_order_id, start_station, min_start_datetime,
                max_due_datetime, assigned_tugboats, assigned_barge_order_ids,
                order_trip=round_trip_order, is_export=True
            )
            
            # Track arrived barges
            for tugboat_result in tugboat_results:
                tugboat_id = tugboat_result['tugboat_id']
                tugboat = self.river_tugboats[tugboat_id]
                
                for barge in tugboat.assigned_barges:
                    barge_id = barge.barge_id
                    barge_info = lookup_assigned_barges[barge_id]
                    barge_info['tugboat_id_to_customer'] = tugboat_id
                    arrived_barges.append(barge_info)
            
            all_tugboat_results.extend(tugboat_results)
            all_assigned_barges = copy_all_assigned_barges
            round_trip_order += 1
            
            # Update schedules
            lookup_tugboat_results = {
                tugboat_result['tugboat_id']: tugboat_result 
                for tugboat_result in tugboat_results
            }
            order_barges, lookup_order_barges = order_barges_from_arrival_tugboats(
                self.data, lookup_tugboat_results
            )
            self._update_schedules(
                tugboat_results, lookup_order_barges, 
                lookup_tugboat_results, round_trip_order
            )
        
        #print(f"    Successfully delivered {len(arrived_barges)} barges to customers")
        #self.solution._display_update_barges(arrived_barges, "After deliver to customer" )
        
        # if assigned_barges[0]['assigned_order'] == "ODR_017":
        #     ready_barge = self.solution.get_ready_barge( assigned_barges[0]['barge'])
        #     print(ready_barge)
        #     print(tugboat_results[0])
        #     raise Exception("Ready barge")
        
        for barge_id in save_load:
            barge = self.barges[barge_id]
            barge.set_load(save_load[barge_id])
        
        return all_tugboat_results, arrived_barges
    
    def execute_step3(self, assigned_barges, assigned_barge_order_ids,
                      lookup_order_barges, lookup_order_loading_infos):
        """
        EXPORT Step 3: Load cargo at customer locations (river)
        Customers load their goods onto barges using their loading equipment
        
        Args:
            assigned_barges: List of assigned barge information
            assigned_barge_order_ids: Dictionary mapping barge_id to order_id
            lookup_order_barges: Dictionary of order to barges mapping
            lookup_order_crane_infos: Dictionary of crane information per order (not used for export)
            
        Returns:
            tuple: (tugboat_results, arrived_barges, all_lookup_order_barges)
        """
        # Schedule customer loading for each order
        schedule_results = []
        barge_schedules = []
        lookup_barge_schedules = {}
        order_barge_lookup = {}
        
        
        
        for order_id, barge_infos in lookup_order_barges.items():
            barge_ids = [barge_info['barge'].barge_id for barge_info in barge_infos]
            
            for barge_info in barge_infos:
                lookup_barge_schedules[barge_info['barge'].barge_id] = barge_info
            order = self.orders[order_id]
            active_loader_infos = lookup_order_loading_infos[order_id]
            active_loader_info = active_loader_infos[-1]
            
            
            for barge_id in barge_ids:
                order_barge_lookup[barge_id] = order_id, active_loader_info
            
            # Schedule loading at customer location
            shedule_result = schedule_customer_order_barges(
                self.solution, order, barge_infos, active_loader_info
            )
            
            # order = self.orders[order_id]
            # active_loader_infos = lookup_order_loading_infos[order_id]
            # active_loader_info = active_loader_infos[-1]
            # for barge_id in barge_ids:
            #     order_barge_lookup[barge_id] = order_id, active_loader_info
            
            # shedule_result = schedule_customer_order_barges(
            #     self.solution, order, barge_infos, active_loader_info
            # )
            
            
            
            barge_schedules.extend(shedule_result['barge_schedule'])
       
        
        # Update barge schedules with loading times
        arrived_barges = []
        for barge_schedule in barge_schedules:
            barge_id = barge_schedule['barge_id']
            barge_info = lookup_barge_schedules[barge_id]
            order = self.orders[barge_info['assigned_order']]
            arrived_barges.append(lookup_barge_schedules[barge_id])
            # For export, loading happens at customer (des_object for export is customer)
            station = order.start_object.station
            self.solution.update_single_barge_scheule(
                order, barge_id, barge_schedule['start_datetime'], barge_schedule['end_datetime'],
                station.km, station.water_type, (station.lat, station.lng), station.station_id
            )
        
        end_date_last = barge_schedules[0]['end_datetime']
        
        # Create loader loading data points
        for barge_schedule in barge_schedules:
            barge_id = barge_schedule['barge_id']
            order_id, active_loader_info = order_barge_lookup[barge_id]
            barge_info = lookup_barge_schedules[barge_id]
            order = self.orders[barge_info['assigned_order']]
            station = order.start_object.station
            loader_info = active_loader_info[0]
            
            loader_location = DataPoint(
                ID=order.order_id,
                type="Loader-Customer",
                name=loader_info['loader_id'] + " - " + barge_id,
                enter_datetime=barge_schedule['start_datetime'],
                distance=0,
                speed=loader_info['rate'],
                time=barge_schedule['time_consumed'],
                type_point='loading_point',
                rest_time=0,
                order_trip=0,
                barge_ids=barge_id,
                station_id=station.station_id,
                order_ids=order_id,
                tugboat_id=None
            )
            loader_location.total_load = barge_schedule['product']
            loader_location.barge_ids = barge_id
            loader_location.exit_datetime = barge_schedule['end_datetime']
            schedule_results.append(loader_location)
            if end_date_last < loader_location.exit_datetime:
                end_date_last = loader_location.exit_datetime
        
        # Transport loaded barges to appointment point (prepare for sea transfer)
        tugboats = self.river_tugboats
        order_ids = [barge_info['assigned_order'] for barge_info in assigned_barges]
        min_order_id, min_start_datetime, start_station, max_due_datetime = \
            self._find_earliest_order(order_ids)
        
        all_assigned_barges = [barge_info['barge'] for barge_info in arrived_barges]
        iteration = 0
        round_trip_order = self.global_step 
        all_tugboat_results = []
        all_lookup_order_barges = {}
        all_tugboat_results.append({'data_points': schedule_results})
        #self.solution._display_update_barges(assigned_barges, "After deliver to customer" )
        
        while len(all_assigned_barges) > 0:
            iteration += 1
            copy_all_assigned_barges = all_assigned_barges.copy()
            
            is_completed, assigned_tugboats = self._assign_tugboats_with_retry(
                min_order_id, start_station, min_start_datetime,
                max_due_datetime, tugboats, copy_all_assigned_barges
            )
            
            if not is_completed or iteration > 100:
                raise Exception(
                    f"Export Step 3: Failed to assign barges to tugboats (iteration {iteration})"
                )
            
            if len(assigned_tugboats) == 0:
                break
            
            # Transport loaded barges to appointment point
            tugboat_results, late_time = self.solution.arrival_step_transport_orders_to_appointment(
                assigned_tugboats, assigned_barge_order_ids, order_trip=round_trip_order
            )
            
            lookup_tugboat_results = {
                tugboat_result['tugboat_id']: tugboat_result 
                for tugboat_result in tugboat_results
            }
            order_barges, lookup_order_barges = order_barges_from_arrival_tugboats(
                self.data, lookup_tugboat_results
            )
            
            # Track appointment stations
            lookup_target_stations = {}
            for tugboat_result in tugboat_results:
                tugboat_id = tugboat_result['tugboat_id']
                tugboat = self.data['tugboats'][tugboat_id]
                appointment_station_id = config_problem.APPOINTMENT_STATION_BASE_REFERENCE_ID
                appointment_station = self.data['stations'][appointment_station_id]
                lookup_target_stations[tugboat_id] = appointment_station_id
                for barge in tugboat.assigned_barges:
                    barge_info = lookup_order_barges[barge.barge_id]
                    barge_info['appointment_station'] = appointment_station
                    all_lookup_order_barges[barge.barge_id] = barge_info
            
            # Remove processed barges
            all_approved_barges = []
            for tugboat_result in tugboat_results:
                tugboat_id = tugboat_result['tugboat_id']
                tugboat = self.data['tugboats'][tugboat_id]
                all_approved_barges.extend(tugboat.assigned_barges)
            
            for barge in all_approved_barges:
                for barge_info in all_assigned_barges:
                    if barge_info.barge_id == barge.barge_id:
                        all_assigned_barges.remove(barge_info)
                        break
            
            all_tugboat_results.extend(tugboat_results)
            round_trip_order += 1
            
            # Update schedules
            self.solution.update_shedule_tugboats_barges(
                lookup_order_barges, lookup_tugboat_results, True, lookup_target_stations
            )
            self.solution._extend_update_tugboat_results(tugboat_results, round_trip_order)
            self.solution._reset_all_tugboats()
        
        
        return all_tugboat_results, arrived_barges, all_lookup_order_barges
    
    def execute_step4(self, assigned_barges, assigned_barge_order_ids,
                      all_lookup_order_barges, lookup_order_crane_infos):
        """
        EXPORT Step 4: Transport loaded barges from appointment to carriers (sea)
        Uses SEA tugboats to bring loaded barges to sea carriers
        
        Args:
            assigned_barges: List of assigned barge information
            assigned_barge_order_ids: Dictionary mapping barge_id to order_id
            all_lookup_order_barges: Complete order to barges mapping
            lookup_order_crane_infos: Dictionary of crane information per order
            
        Returns:
            tuple: (tugboat_results, arrived_barges)
        """
        tugboats = self.sea_tugboats
        
        order_ids = [barge_info['assigned_order'] for barge_info in assigned_barges]
        min_order_id, min_start_datetime, start_station, max_due_datetime = \
            self._find_earliest_order(order_ids)
        
        all_assigned_barges = [barge_info['barge'] for barge_info in assigned_barges]
        iteration = 0
        round_trip_order = self.global_step 
        all_tugboat_results = []
        
        while len(all_assigned_barges) > 0:
            iteration += 1
            copy_all_assigned_barges = all_assigned_barges.copy()
            
            is_completed, assigned_tugboats = self._assign_tugboats_with_retry(
                min_order_id, start_station, min_start_datetime,
                max_due_datetime, tugboats, copy_all_assigned_barges, max_days=25
            )
            
            if not is_completed or iteration > 100:
                raise Exception(
                    f"Export Step 4: Failed to assign barges to tugboats (iteration {iteration})"
                )
            
            if len(assigned_tugboats) == 0:
                break
            
            # Transport loaded barges to carrier locations (sea)
            tugboat_results, late_time = self.solution.arrival_step_transport_orders_to_end_points(
                assigned_tugboats, assigned_barge_order_ids,
                all_lookup_order_barges, round_trip_order, is_export=True
            )
            
            for tugboat_result in tugboat_results:
                tugboat_id = tugboat_result['tugboat_id']
                tugboat = self.data['tugboats'][tugboat_id]
                # print(tugboat.tugboat_id)
                # for data_point in tugboat_result['data_points']:
                #     if data_point.type == 'Travel To Carrier':
                #         #data_point.total_load = tugboat.get_load(True)
                #         total_load = sum([barge_info.get_load(True) for barge_info in tugboat.assigned_barges])
                #         print(total_load, data_point)
            
            
            all_assigned_barges = copy_all_assigned_barges
            round_trip_order += 1
            
            lookup_tugboat_results = {
                tugboat_result['tugboat_id']: tugboat_result 
                for tugboat_result in tugboat_results
            }
            order_barges, lookup_order_barges = order_barges_from_arrival_tugboats(
                self.data, lookup_tugboat_results
            )
            
            self.solution.update_shedule_tugboats_barges(
                lookup_order_barges, lookup_tugboat_results
            )
            self.solution._extend_update_tugboat_results(tugboat_results, round_trip_order)
            self.solution._reset_all_tugboats()
            all_tugboat_results.extend(tugboat_results)
        
        return all_tugboat_results, assigned_barges
    
    def execute_step5(self, lookup_order_barges, lookup_order_loading_infos):
        """
        EXPORT Step 5: Unload cargo at carrier locations (sea)
        Carriers unload goods from barges using their cranes
        
        Args:
            lookup_order_barges: Dictionary of order to barges mapping
            lookup_order_loading_infos: Dictionary of loading information per order (contains crane info)
            
        Returns:
            tuple: (loader_schedules, arrived_barges)
        """
        schedule_results = []
        barge_schedules = []
        lookup_barge_schedules = {}
        order_barge_lookup = {}
        
        for order_id, barge_infos in lookup_order_barges.items():
            barge_ids = [barge_info['barge'].barge_id for barge_info in barge_infos]
            
            for barge_info in barge_infos:
                lookup_barge_schedules[barge_info['barge'].barge_id] = barge_info
            
            order = self.orders[order_id]
            # For export, use carrier crane info (from lookup_order_loading_infos which contains crane data)
            active_crane_infos = lookup_order_loading_infos[order_id]
            active_crane_info = active_crane_infos[-1]
            lookup_crane_info = {}
            for crane_info in active_crane_info:
                lookup_crane_info[crane_info['crane_id']] = crane_info
            
            for barge_id in barge_ids:
                order_barge_lookup[barge_id] = order_id, lookup_crane_info
            
            # Schedule unloading at carrier location using cranes
            shedule_result = schedule_carrier_order_barges(
                self.solution, order, barge_infos, active_crane_info
            )
            barge_schedules.extend(shedule_result['barge_schedule'])
        
        end_date_last = barge_schedules[0]['end_datetime']
        
        # Update barge schedules and create crane unloading data points
        arrived_barges = []
        for barge_schedule in barge_schedules:
            barge_id = barge_schedule['barge_id']
            order_id, lookup_crane_info = order_barge_lookup[barge_id]
            barge_info = lookup_barge_schedules[barge_id]
            order = self.orders[barge_info['assigned_order']]
            arrived_barges.append(lookup_barge_schedules[barge_id])
            # For export, unloading happens at carrier (start_object for export is carrier)
            station = order.des_object.station
            self.solution.update_single_barge_scheule(
                order, barge_id, barge_schedule['start_datetime'], barge_schedule['end_datetime'],
                station.km, station.water_type, (station.lat, station.lng), station.station_id
            )
            crane_id = barge_schedule['crane_id']
            active_crane_info = lookup_crane_info[crane_id]
            
            crane_location = DataPoint(
                ID=order.order_id,
                type="Crane-Carrier",
                name=crane_id + " - " + barge_id,
                enter_datetime=barge_schedule['start_datetime'],
                distance=0,
                speed=active_crane_info['rate'],
                time=barge_schedule['time_consumed'],
                type_point='unloading_point',
                rest_time=0,
                order_trip=0,
                barge_ids=barge_id,
                station_id=station.station_id,
                order_ids=order_id,
                tugboat_id=None
            )
            crane_location.total_load = barge_schedule['product']
            crane_location.barge_ids = barge_id
            crane_location.exit_datetime = barge_schedule['end_datetime']
            schedule_results.append(crane_location)
            if end_date_last < crane_location.exit_datetime:
                end_date_last = crane_location.exit_datetime
        
        return schedule_results, arrived_barges
