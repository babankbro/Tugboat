"""
Base Transport Workflow
Abstract base class for transport workflows (Import/Export)
Contains shared functionality for both import and export operations
"""

from abc import ABC, abstractmethod
from CodeVS.operations.assigned_barge import *
from CodeVS.operations.transport_order import *
from CodeVS.operations.scheduling import *
from CodeVS.operations.travel_helper import *
import config_problem
from datetime import timedelta
import pandas as pd


class BaseTransportWorkflow(ABC):
    """
    Abstract base class for transport workflows (Import/Export)
    Contains shared functionality for both import and export operations
    """
    
    def __init__(self, solution):
        """
        Initialize workflow with reference to parent solution
        
        Args:
            solution: Parent Solution instance containing data and schedules
        """
        self.solution = solution
        self.data = solution.data
        self.orders = self.data['orders']
        self.barges = self.data['barges']
        self.stations = self.data['stations']
        self.sea_tugboats = self.data['sea_tugboats']
        self.river_tugboats = self.data['river_tugboats']
        self.workflow_type = "BASE"
    
    @abstractmethod
    def execute_step1(self, assigned_barges):
        """
        Step 1: Initial barge positioning
        
        Args:
            assigned_barges: List of assigned barge information
            
        Returns:
            tuple: (tugboat_results, arrived_barges)
        """
        pass
    
    @abstractmethod
    def execute_step2(self, assigned_barges, assigned_barge_order_ids):
        """
        Step 2: Move barges to loading/unloading location
        
        Args:
            assigned_barges: List of assigned barge information
            assigned_barge_order_ids: Dictionary mapping barge_id to order_id
            
        Returns:
            tuple: (tugboat_results, arrived_barges)
        """
        pass
    
    @abstractmethod
    def execute_step3(self, assigned_barges, assigned_barge_order_ids, 
                      lookup_order_barges, lookup_order_crane_infos):
        """
        Step 3: Loading operations
        
        Args:
            assigned_barges: List of assigned barge information
            assigned_barge_order_ids: Dictionary mapping barge_id to order_id
            lookup_order_barges: Dictionary of order to barges mapping
            lookup_order_crane_infos: Dictionary of crane information per order
            
        Returns:
            tuple: (tugboat_results, arrived_barges, all_lookup_order_barges)
        """
        pass
    
    @abstractmethod
    def execute_step4(self, assigned_barges, assigned_barge_order_ids,
                      all_lookup_order_barges, lookup_order_crane_infos):
        """
        Step 4: Transport loaded barges
        
        Args:
            assigned_barges: List of assigned barge information
            assigned_barge_order_ids: Dictionary mapping barge_id to order_id
            all_lookup_order_barges: Complete order to barges mapping
            lookup_order_crane_infos: Dictionary of crane information per order
            
        Returns:
            tuple: (tugboat_results, arrived_barges)
        """
        pass
    
    @abstractmethod
    def execute_step5(self, lookup_order_barges, lookup_order_loading_infos):
        """
        Step 5: Unloading operations
        
        Args:
            lookup_order_barges: Dictionary of order to barges mapping
            lookup_order_loading_infos: Dictionary of loading information per order
            
        Returns:
            tuple: (loader_schedules, arrived_barges)
        """
        pass
    
    def execute_workflow(self, assigned_barges, assigned_barge_order_ids,
                        lookup_order_barges, lookup_order_crane_infos,
                        lookup_order_loading_infos):
        """
        Execute complete workflow (all 5 steps)
        
        Args:
            assigned_barges: List of assigned barge information
            assigned_barge_order_ids: Dictionary mapping barge_id to order_id
            lookup_order_barges: Dictionary of order to barges mapping
            lookup_order_crane_infos: Dictionary of crane information per order
            lookup_order_loading_infos: Dictionary of loading information per order
        
        Returns:
            tuple: (all_results, final_arrived_barges, barge_dfs)
        """
        all_result_tugboats = []
        barge_dfs = []
        
        #print(f"\n{'='*60}")
        #print(f"Executing {self.workflow_type} Workflow")
        #print(f"{'='*60}")
        
        # Step 1: Initial positioning
        #print(f"  Step 1: Initial barge positioning...")
        tugboat_results, arrived_barges = self.execute_step1(assigned_barges)
        
        # Step 2: Move to loading/unloading location
        #print(f"  Step 2: Moving barges to location...")
        step2_tugboat_results, arrived_barges = self.execute_step2(
            assigned_barges, assigned_barge_order_ids
        )
        
        # Step 3: Loading operations
        
        lookup_order_infos = lookup_order_crane_infos if self.workflow_type == "IMPORT" else lookup_order_loading_infos
        
        #print(f"  Step 3: Loading operations...")
        step3_tugboat_results, arrived_barges, all_lookup_order_barges = self.execute_step3(
            assigned_barges, assigned_barge_order_ids, 
            lookup_order_barges, lookup_order_infos
        )
        
        # Step 4: Transport loaded barges
        #print(f"  Step 4: Transporting loaded barges...")
        step4_tugboat_results, arrived_barges = self.execute_step4(
            assigned_barges, assigned_barge_order_ids,
            all_lookup_order_barges, lookup_order_crane_infos
        )
        
        lookup_order_infos = lookup_order_loading_infos if self.workflow_type == "IMPORT" else lookup_order_crane_infos
        
        # Step 5: Unloading operations
        #print(f"  Step 5: Unloading operations...")
        loader_schedules, arrived_barges = self.execute_step5(
            lookup_order_barges, lookup_order_infos
        )
        
        # Collect results
        if tugboat_results is not None:
            all_result_tugboats.extend(tugboat_results)
        all_result_tugboats.extend(step2_tugboat_results)
        all_result_tugboats.extend(step3_tugboat_results)
        all_result_tugboats.extend(step4_tugboat_results)
        all_result_tugboats.append({"data_points": loader_schedules})
        
        # Create barge DataFrame
        df = pd.DataFrame(arrived_barges)
        barge_dfs.append(df)
        
        #print(f"  {self.workflow_type} Workflow completed successfully")
        #print(f"{'='*60}\n")
        
        return all_result_tugboats, arrived_barges, barge_dfs
    
    # Shared utility methods
    def _reset_tugboats(self, tugboat_dict):
        """Reset all tugboats in the given dictionary"""
        for tugboat_id in tugboat_dict:
            tugboat_dict[tugboat_id].reset()
    
    def _update_schedules(self, tugboat_results, lookup_order_barges, 
                         lookup_tugboat_results, round_trip_order):
        """Update solution schedules with tugboat results"""
        self.solution.update_shedule_tugboats_barges(
            lookup_order_barges, lookup_tugboat_results
        )
        self.solution._extend_update_tugboat_results(tugboat_results, round_trip_order)
        self.solution._reset_all_tugboats()
    
    def _find_earliest_order(self, order_ids):
        """
        Find the earliest order and its details
        
        Args:
            order_ids: List of order IDs
            
        Returns:
            tuple: (min_order_id, min_start_datetime, start_station, max_due_datetime)
        """
        min_order_id = None
        max_due_datetime = max([self.orders[oid].due_datetime for oid in order_ids])
        min_start_datetime = max_due_datetime
        start_station = None
        
        for order_id in order_ids:
            order = self.orders[order_id]
            if order.start_datetime < min_start_datetime:
                min_start_datetime = order.start_datetime
                min_order_id = order_id
                start_station = order.start_object.station
        
        return min_order_id, min_start_datetime, start_station, max_due_datetime
    
    def _assign_tugboats_with_retry(self, min_order_id, start_station, 
                                     min_start_datetime, max_due_datetime,
                                     tugboats, assigned_barges, max_days=30):
        """
        Assign tugboats with retry logic
        
        Args:
            min_order_id: Earliest order ID
            start_station: Starting station
            min_start_datetime: Earliest start datetime
            max_due_datetime: Latest due datetime
            tugboats: Dictionary of available tugboats
            assigned_barges: List of barges to assign
            max_days: Maximum days to retry (default: 30)
            
        Returns:
            tuple: (is_completed, assigned_tugboats)
        """
        is_completed = False
        travel_before_days = 0
        assigned_tugboats = []
        
        while not is_completed and travel_before_days <= max_days:
            is_completed, assigned_tugboats = \
                self.solution.assign_barges_to_tugboats_non_order(
                    min_order_id, start_station, min_start_datetime,
                    max_due_datetime, tugboats, assigned_barges,
                    travel_before_days=travel_before_days
                )
            travel_before_days += 5
        
        return is_completed, assigned_tugboats
