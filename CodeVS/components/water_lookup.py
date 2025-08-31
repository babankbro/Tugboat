import os
import sys

# Add the project root directory to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Add CodeVS directory to path
codevs_path = os.path.join(project_root, 'CodeVS')
sys.path.insert(0, codevs_path)

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple, Union
import config_problem 

class FastStationLookup:
    """
    High-performance station lookup class using numpy arrays for fast computation.
    Automatically converts any datetime to hourly format for lookup.
    """
    
    def __init__(self):
        self.df = None
        self.datetime_array = None
        self.station_arrays = {}
        self.datetime_to_index = {}
        self.available_stations = None
        self.data_loaded = False
    
    def _convert_to_hourly_format(self, datetime_input: Union[str, datetime]) -> str:
        """
        Convert any datetime input to the hourly format used in CSV (YYYY-MM-DD HH:00).
        
        Args:
            datetime_input: Can be string, datetime object, or various formats
            
        Returns:
            str: Datetime in 'YYYY-MM-DD HH:00' format
        """
        try:
            if isinstance(datetime_input, str):
                dt = pd.to_datetime(datetime_input)
            elif isinstance(datetime_input, datetime):
                dt = datetime_input
            else:
                dt = pd.to_datetime(datetime_input)
            
            # Convert to hourly format (truncate minutes and seconds) if > 30 minutes round up
            if dt.minute >= 30:
                dt = dt + timedelta(hours=1)
            hourly_dt = dt.replace(minute=0, second=0, microsecond=0)
            return hourly_dt.strftime('%Y-%m-%d %H:%M:%S')
            
        except Exception as e:
            raise ValueError(f"Could not convert datetime '{datetime_input}' to hourly format: {e}")
    
    def load_data(self, filename: str = 'level_up.csv') -> bool:
        """
        Load CSV and convert to numpy arrays for fast lookups.
        
        Args:
            filename (str): Path to the CSV file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            print("Loading CSV data...")
            # Load CSV file
            self.df = pd.read_csv(filename)
            
            self.load_data_df(self.df)
            
            return True
            
        except Exception as e:
            print(f"Error loading data: {e}")
            return False
    
    def load_data_df(self, water_df):
        self.df = water_df
        # Convert DATETIME column to string array 
        # and convert to datetime and sorted
        self.df['DATETIME'] = pd.to_datetime(self.df['DATETIME'])
        self.df = self.df.sort_values(by='DATETIME')
        
        self.datetime_array = self.df['DATETIME'].astype(str).values
        
        print(self.datetime_array[:10])
        
        # Get all available station columns
        self.available_stations = [col for col in self.df.columns if col.startswith('ST_')]
        
        print("Converting station data to numpy arrays...")
        # Convert each station column to numpy array
        self.station_arrays = {}
        for station in self.available_stations:
            self.station_arrays[station] = self.df[station].values
        
        print("Creating datetime index mapping...")
        # Create fast datetime lookup dictionary
        # Sorted by datetime , but need to convert string to datetime
        self.datetime_to_index = {dt: idx for idx, dt in enumerate(self.datetime_array)}
        #print(list(self.datetime_to_index.keys())[:10])
        
        self.data_loaded = True
        
        print(f"Data loaded successfully!")
        print(f"Records: {len(self.datetime_array):,}")
        print(f"Stations: {len(self.available_stations)}")
        print(f"Memory usage: ~{self._estimate_memory_usage():.1f} MB")
        
        return True
        
     
            
    
    def _estimate_memory_usage(self) -> float:
        """Estimate memory usage in MB."""
        if not self.data_loaded:
            return 0
        
        # Rough estimation
        datetime_size = len(self.datetime_array) * 50  # Assume avg 50 chars per datetime
        station_size = len(self.available_stations) * len(self.datetime_array) * 8  # 8 bytes per float64
        index_size = len(self.datetime_to_index) * 100  # Rough estimate for dict overhead
        
        return (datetime_size + station_size + index_size) / (1024 * 1024)
    
    def lookup_station(self, datetime_input: Union[str, datetime], station_id: str) -> Optional[Union[int, float]]:
        """
        Ultra-fast station lookup using numpy arrays.
        
        Args:
            datetime_input: Any datetime format
            station_id (str): Station ID (e.g., 'ST_002', 'ST_004')
            
        Returns:
            Optional[Union[int, float]]: Station value or None if not found
        """
        if not self.data_loaded:
            raise ValueError("Data not loaded. Call load_data() first.")
        
        if station_id not in self.available_stations:
            raise ValueError(f"Station {station_id} not found. Available stations: {self.available_stations}")
        
        try:
            # Convert to hourly format
            hourly_datetime = self._convert_to_hourly_format(datetime_input)
            
            # Fast index lookup
            #print("hourly_datetime", hourly_datetime)
            index = self.datetime_to_index.get(hourly_datetime)
            if index is None:
                return None
            
            # Fast array access
            value = self.station_arrays[station_id][index]
            
            # Return as int if it's a whole number, otherwise float
            if np.isnan(value):
                return None
            return int(value) if value == int(value) else float(value)
            
        except Exception as e:
            return None
    
    def lookup_multiple_stations(self, datetime_input: Union[str, datetime], station_ids: List[str]) -> Dict[str, Optional[Union[int, float]]]:
        """
        Fast lookup of multiple stations for a single datetime.
        
        Args:
            datetime_input: Any datetime format
            station_ids (List[str]): List of station IDs
            
        Returns:
            Dict[str, Optional[Union[int, float]]]: Dictionary mapping station IDs to values
        """
        if not self.data_loaded:
            raise ValueError("Data not loaded. Call load_data() first.")
        
        try:
            # Convert to hourly format once
            hourly_datetime = self._convert_to_hourly_format(datetime_input)
            
            # Fast index lookup once
            index = self.datetime_to_index.get(hourly_datetime)
            if index is None:
                return {station_id: None for station_id in station_ids}
            
            # Fast array access for all stations
            results = {}
            for station_id in station_ids:
                if station_id in self.available_stations:
                    value = self.station_arrays[station_id][index]
                    if np.isnan(value):
                        results[station_id] = None
                    else:
                        results[station_id] = int(value) if value == int(value) else float(value)
                else:
                    results[station_id] = None
            
            return results
            
        except Exception as e:
            return {station_id: None for station_id in station_ids}
    
    def lookup_all_stations(self, datetime_input: Union[str, datetime]) -> Dict[str, Optional[Union[int, float]]]:
        """
        Fast lookup of ALL stations for a single datetime.
        
        Args:
            datetime_input: Any datetime format
            
        Returns:
            Dict[str, Optional[Union[int, float]]]: Dictionary with all station values
        """
        return self.lookup_multiple_stations(datetime_input, self.available_stations)
    
    def lookup_time_series_vectorized(self, start_datetime: Union[str, datetime], end_datetime: Union[str, datetime], 
                                    station_ids: Union[str, List[str]]) -> Dict[str, Any]:
        """
        Vectorized time series lookup for maximum performance.
        
        Args:
            start_datetime: Start datetime (any format)
            end_datetime: End datetime (any format)
            station_ids: Single station ID or list of station IDs
            
        Returns:
            Dict with datetime array and station data arrays
        """
        if not self.data_loaded:
            raise ValueError("Data not loaded. Call load_data() first.")
        
        try:
            
            #check is string and format of start_datetime to '2025-01-01 01:00'
            
            start_dt = self._convert_to_hourly_format(start_datetime)
            end_dt = self._convert_to_hourly_format(end_datetime)
            
            
            # Convert inputs
            
            #print("start_dt", start_dt)
            #print("end_dt", end_dt)
            # Ensure station_ids is a list
            if isinstance(station_ids, str):
                station_ids = [station_ids]
            
            # Generate hourly time range
            time_range = pd.date_range(start=start_dt, end=end_dt, freq='H')
            #print("time_range", time_range)
            hourly_strings = [self._convert_to_hourly_format(dt) for dt in time_range]
            
            # Find indices for all datetimes at once
            indices = []
            valid_datetimes = []
            for dt_str in hourly_strings:
                idx = self.datetime_to_index.get(dt_str)
                if idx is not None:
                    indices.append(idx)
                    valid_datetimes.append(dt_str)
            
            if not indices:
                return {'datetimes': [], 'stations': {station: [] for station in station_ids}}
            
            # Convert to numpy array for vectorized operations
            indices_array = np.array(indices)
            
            # Extract data for all stations at once using advanced indexing
            results = {
                'datetimes': valid_datetimes,
                'stations': {}
            }
            
            for station_id in station_ids:
                if station_id in self.available_stations:
                    # Vectorized array access - much faster than loop
                    station_data = self.station_arrays[station_id][indices_array]
                    results['stations'][station_id] = station_data.tolist()
                else:
                    results['stations'][station_id] = [None] * len(indices)
            
            return results
            
        except Exception as e:
            print(f"Error in vectorized time series lookup: {e}")
            return {'datetimes': [], 'stations': {}}
    
    def bulk_lookup(self, datetime_station_pairs: List[Tuple[Union[str, datetime], str]]) -> List[Optional[Union[int, float]]]:
        """
        Perform bulk lookups for maximum efficiency.
        
        Args:
            datetime_station_pairs: List of (datetime, station_id) tuples
            
        Returns:
            List of values in same order as input pairs
        """
        if not self.data_loaded:
            raise ValueError("Data not loaded. Call load_data() first.")
        
        results = []
        
        for datetime_input, station_id in datetime_station_pairs:
            try:
                # Convert datetime
                hourly_datetime = self._convert_to_hourly_format(datetime_input)
                
                # Fast lookups
                index = self.datetime_to_index.get(hourly_datetime)
                if index is None or station_id not in self.available_stations:
                    results.append(None)
                    continue
                
                value = self.station_arrays[station_id][index]
                if np.isnan(value):
                    results.append(None)
                else:
                    results.append(int(value) if value == int(value) else float(value))
                    
            except Exception:
                results.append(None)
        
        return results
    
    def get_station_stats_fast(self, station_id: str) -> Dict[str, Any]:
        """
        Fast station statistics using numpy operations.
        
        Args:
            station_id (str): Station ID
            
        Returns:
            Dict: Station statistics
        """
        if not self.data_loaded:
            raise ValueError("Data not loaded. Call load_data() first.")
        
        if station_id not in self.available_stations:
            raise ValueError(f"Station {station_id} not found.")
        
        data = self.station_arrays[station_id]
        
        # Remove NaN values for calculations
        clean_data = data[~np.isnan(data)]
        
        return {
            'station_id': station_id,
            'count': len(clean_data),
            'mean': float(np.mean(clean_data)),
            'min': float(np.min(clean_data)),
            'max': float(np.max(clean_data)),
            'std': float(np.std(clean_data)),
            'median': float(np.median(clean_data)),
            'unique_values': sorted(np.unique(clean_data).tolist())
        }
    
    def find_values_fast(self, station_id: str, value: Union[int, float], tolerance: float = 0.0) -> List[str]:
        """
        Fast search for specific values in a station using numpy operations.
        
        Args:
            station_id (str): Station ID
            value: Value to search for
            tolerance (float): Tolerance for floating point comparison
            
        Returns:
            List[str]: List of datetimes where value was found
        """
        if not self.data_loaded:
            raise ValueError("Data not loaded. Call load_data() first.")
        
        if station_id not in self.available_stations:
            raise ValueError(f"Station {station_id} not found.")
        
        data = self.station_arrays[station_id]
        
        # Find matching indices using numpy
        if tolerance > 0:
            mask = np.abs(data - value) <= tolerance
        else:
            mask = data == value
        
        # Get matching indices
        matching_indices = np.where(mask)[0]
        
        # Return corresponding datetimes
        return [self.datetime_array[idx] for idx in matching_indices]
    
    def get_available_stations(self) -> List[str]:
        """Get all available station IDs."""
        if not self.data_loaded:
            raise ValueError("Data not loaded. Call load_data() first.")
        return self.available_stations.copy()
    
    def get_available_datetimes(self) -> List[str]:
        """Get all available datetimes."""
        if not self.data_loaded:
            raise ValueError("Data not loaded. Call load_data() first.")
        return self.datetime_array.tolist()
    
    def lookup_nearest_hours(self, datetime_input: Union[str, datetime], station_id: str, 
                           hours_before: int = 1, hours_after: int = 1) -> List[Dict[str, Any]]:
        """
        Get station values for the nearest hours around a given datetime.
        
        Args:
            datetime_input: Target datetime (any format)
            station_id (str): Station ID
            hours_before (int): Number of hours before to include
            hours_after (int): Number of hours after to include
            
        Returns:
            List[Dict]: Values for surrounding hours
        """
        try:
            # Convert to datetime object
            target_dt = pd.to_datetime(datetime_input)
            
            results = []
            
            # Get values for hours before
            for i in range(hours_before, 0, -1):
                check_dt = target_dt - timedelta(hours=i)
                value = self.lookup_station(check_dt, station_id)
                results.append({
                    'datetime': check_dt.strftime('%Y-%m-%d %H:%M:%S'),
                    'lookup_datetime': self._convert_to_hourly_format(check_dt),
                    'hours_offset': -i,
                    'value': value
                })
            
            # Get value for target hour
            value = self.lookup_station(target_dt, station_id)
            results.append({
                'datetime': target_dt.strftime('%Y-%m-%d %H:%M:%S'),
                'lookup_datetime': self._convert_to_hourly_format(target_dt),
                'hours_offset': 0,
                'value': value
            })
            
            # Get values for hours after
            for i in range(1, hours_after + 1):
                check_dt = target_dt + timedelta(hours=i)
                value = self.lookup_station(check_dt, station_id)
                results.append({
                    'datetime': check_dt.strftime('%Y-%m-%d %H:%M:%S'),
                    'lookup_datetime': self._convert_to_hourly_format(check_dt),
                    'hours_offset': i,
                    'value': value
                })
            
            return results
            
        except Exception as e:
            print(f"Error in nearest hours lookup: {e}")
            return []
    
    def get_performance_info(self) -> Dict[str, Any]:
        """Get performance and memory information."""
        if not self.data_loaded:
            return {'status': 'Data not loaded'}
        
        return {
            'records': len(self.datetime_array),
            'stations': len(self.available_stations),
            'memory_usage_mb': self._estimate_memory_usage(),
            'index_size': len(self.datetime_to_index),
            'data_structure': 'numpy arrays',
            'lookup_complexity': 'O(1) average case'
        }
    
    def lookup_previous_time_series(self, reference_datetime: Union[str, datetime], 
                               station_ids: Union[str, List[str]],
                               days_back: int = 0, hours_back: int = 0,
                               include_reference: bool = True) -> Dict[str, Any]:
        """
        Get time series data for the previous n days and m hours from a reference datetime.
        
        Args:
            reference_datetime: Reference datetime (any format) - the starting point to go back from
            station_ids: Single station ID or list of station IDs
            days_back (int): Number of days to go back (default: 0)
            hours_back (int): Number of hours to go back (default: 0)
            include_reference (bool): Whether to include the reference datetime in results
            
        Returns:
            Dict with datetime array and station data arrays for the specified time period
            
        Examples:
            # Get previous 2 days of data for ST_002
            lookup.lookup_previous_time_series('2025-01-03 15:30', 'ST_002', days_back=2)
            
            # Get previous 1 day and 12 hours for multiple stations
            lookup.lookup_previous_time_series('2025-01-03 15:30', ['ST_002', 'ST_005'], days_back=1, hours_back=12)
            
            # Get previous 48 hours only
            lookup.lookup_previous_time_series('2025-01-03 15:30', 'ST_002', hours_back=48)
        """
        if not self.data_loaded:
            raise ValueError("Data not loaded. Call load_data() first.")
        
        if days_back == 0 and hours_back == 0:
            raise ValueError("Either days_back or hours_back must be greater than 0")
        
        try:
            # Convert reference datetime to pandas datetime
            ref_dt = pd.to_datetime(reference_datetime)
            
            # Calculate total hours to go back
            total_hours_back = (days_back * 24) + hours_back
            
            # Calculate start datetime (going back from reference)
            start_dt = ref_dt - timedelta(hours=total_hours_back)
            
            # End datetime is either the reference datetime or one hour before (depending on include_reference)
            if include_reference:
                end_dt = ref_dt
            else:
                end_dt = ref_dt - timedelta(hours=1)
            
            # Ensure station_ids is a list
            if isinstance(station_ids, str):
                station_ids = [station_ids]
            
            # Validate station IDs
            invalid_stations = [s for s in station_ids if s not in self.available_stations]
            if invalid_stations:
                print(f"Warning: Invalid station IDs: {invalid_stations}")
            
            # Generate hourly time range from start to end
            time_range = pd.date_range(start=start_dt, end=end_dt, freq='H')
            
            # Convert to the format used in our lookup system
            hourly_strings = [self._convert_to_hourly_format(dt) for dt in time_range]
            
            # Find indices for all datetimes at once
            indices = []
            valid_datetimes = []
            valid_dt_objects = []
            
            for i, dt_str in enumerate(hourly_strings):
                idx = self.datetime_to_index.get(dt_str)
                if idx is not None:
                    indices.append(idx)
                    valid_datetimes.append(dt_str)
                    valid_dt_objects.append(time_range[i])
            
            if not indices:
                print(f"Warning: No data found for the specified time period")
                return {
                    'reference_datetime': reference_datetime,
                    'start_datetime': start_dt.strftime('%Y-%m-%d %H:%M:%S'),
                    'end_datetime': end_dt.strftime('%Y-%m-%d %H:%M:%S'),
                    'days_back': days_back,
                    'hours_back': hours_back,
                    'total_hours': total_hours_back,
                    'datetimes': [],
                    'datetime_objects': [],
                    'stations': {station: [] for station in station_ids},
                    'summary': {
                        'total_records': 0,
                        'time_span_hours': 0,
                        'stations_count': len(station_ids)
                    }
                }
            
            # Convert to numpy array for vectorized operations
            indices_array = np.array(indices)
            
            # Extract data for all stations at once using advanced indexing
            results = {
                'reference_datetime': reference_datetime,
                'start_datetime': start_dt.strftime('%Y-%m-%d %H:%M:%S'),
                'end_datetime': end_dt.strftime('%Y-%m-%d %H:%M:%S'),
                'days_back': days_back,
                'hours_back': hours_back,
                'total_hours': total_hours_back,
                'datetimes': valid_datetimes,
                'datetime_objects': valid_dt_objects,  # Useful for plotting
                'stations': {},
                'summary': {
                    'total_records': len(valid_datetimes),
                    'time_span_hours': len(valid_datetimes),
                    'stations_count': len(station_ids)
                }
            }
            
            # Get data for each station
            for station_id in station_ids:
                if station_id in self.available_stations:
                    # Vectorized array access - much faster than loop
                    station_data = self.station_arrays[station_id][indices_array]
                    results['stations'][station_id] = station_data.tolist()
                else:
                    results['stations'][station_id] = [None] * len(indices)
            
            return results
            
        except Exception as e:
            print(f"Error in previous time series lookup: {e}")
            return {
                'reference_datetime': reference_datetime,
                'error': str(e),
                'datetimes': [],
                'stations': {station: [] for station in (station_ids if isinstance(station_ids, list) else [station_ids])}
            }

    def get_previous_time_stats(self, reference_datetime: Union[str, datetime], 
                            station_ids: Union[str, List[str]],
                            days_back: int = 0, hours_back: int = 0) -> Dict[str, Any]:
        """
        Get statistical summary of previous time period data.
        
        Args:
            reference_datetime: Reference datetime (any format)
            station_ids: Single station ID or list of station IDs
            days_back (int): Number of days to go back
            hours_back (int): Number of hours to go back  
            
        Returns:
            Dict with statistics for each station over the time period
        """
        if not self.data_loaded:
            raise ValueError("Data not loaded. Call load_data() first.")
        
        # Get the time series data
        time_series = self.lookup_previous_time_series(
            reference_datetime, station_ids, days_back, hours_back, include_reference=True
        )
        
        if not time_series['datetimes']:
            return {'error': 'No data available for specified time period'}
        
        # Ensure station_ids is a list
        if isinstance(station_ids, str):
            station_ids = [station_ids]
        
        stats = {
            'time_period': {
                'reference_datetime': reference_datetime,
                'start_datetime': time_series['start_datetime'],
                'end_datetime': time_series['end_datetime'],
                'total_hours': time_series['total_hours'],
                'available_records': time_series['summary']['total_records']
            },
            'stations': {}
        }
        
        # Calculate stats for each station
        for station_id in station_ids:
            if station_id in time_series['stations']:
                data = np.array(time_series['stations'][station_id])
                # Remove NaN values for calculations
                clean_data = data[~np.isnan(data)]
                
                if len(clean_data) > 0:
                    stats['stations'][station_id] = {
                        'count': len(clean_data),
                        'missing_count': len(data) - len(clean_data),
                        'mean': float(np.mean(clean_data)),
                        'min': float(np.min(clean_data)),
                        'max': float(np.max(clean_data)),
                        'std': float(np.std(clean_data)),
                        'median': float(np.median(clean_data)),
                        'first_value': float(clean_data[0]) if len(clean_data) > 0 else None,
                        'last_value': float(clean_data[-1]) if len(clean_data) > 0 else None,
                        'trend': 'increasing' if len(clean_data) > 1 and clean_data[-1] > clean_data[0] else 
                                'decreasing' if len(clean_data) > 1 and clean_data[-1] < clean_data[0] else 'stable'
                    }
                else:
                    stats['stations'][station_id] = {
                        'count': 0,
                        'missing_count': len(data),
                        'error': 'No valid data points found'
                    }
        
        return stats

# Performance comparison function
def performance_benchmark(lookup_instance: FastStationLookup, num_lookups: int = 10000):
    """
    Benchmark the performance of the lookup system.
    
    Args:
        lookup_instance: Loaded FastStationLookup instance
        num_lookups (int): Number of lookups to perform
    """
    import time
    import random
    
    if not lookup_instance.data_loaded:
        print("Data not loaded for benchmark")
        return
    
    # Get sample data
    sample_datetimes = random.sample(lookup_instance.get_available_datetimes(), min(1000, len(lookup_instance.datetime_array)))
    sample_stations = random.sample(lookup_instance.available_stations, min(10, len(lookup_instance.available_stations)))
    
    print(f"Benchmarking {num_lookups:,} lookups...")
    
    # Single lookup benchmark
    start_time = time.time()
    for i in range(num_lookups):
        dt = random.choice(sample_datetimes)
        station = random.choice(sample_stations)
        lookup_instance.lookup_station(dt, station)
    single_time = time.time() - start_time
    
    # Multiple station lookup benchmark
    start_time = time.time()
    for i in range(num_lookups // 10):  # Fewer iterations since we're looking up multiple stations
        dt = random.choice(sample_datetimes)
        lookup_instance.lookup_multiple_stations(dt, sample_stations)
    multiple_time = time.time() - start_time
    
    print(f"\nPerformance Results:")
    print(f"Single lookups: {num_lookups:,} in {single_time:.3f}s = {num_lookups/single_time:,.0f} lookups/sec")
    print(f"Multiple lookups: {(num_lookups//10)*len(sample_stations):,} in {multiple_time:.3f}s = {((num_lookups//10)*len(sample_stations))/multiple_time:,.0f} lookups/sec")
    print(f"Average single lookup time: {(single_time/num_lookups)*1000:.4f} ms")

# Example usage
def example_usage():
    """Example demonstrating the fast lookup system."""
    
    print("=== High-Performance Station Lookup ===")
    lookup = FastStationLookup()
    
    if lookup.load_data(f"{config_problem.INPUT_FOLDER}/level_up.csv"):
        
        print(lookup.df.head(15))
        print(lookup.station_arrays['ST_005'][:20])
        # display 10 first keys and values
        print(list(lookup.datetime_to_index.items())[:10])
        
        print("\n=== Basic lookups ===")
        # Single station lookup 11.00 1 12.00 0.5 13.00 0
        value = lookup.lookup_station('2025-02-11 05:00:00', 'ST_025')
        print(f"ST_025 at 2025-02-11 05:00: {value}")
        
        # Multiple stations lookup
        multiple = lookup.lookup_multiple_stations(
            '2025-01-01 12:29:00',
            ['ST_001', 'ST_002', 'ST_003', 'ST_004']
        )
        print(f"Multiple stations: {multiple}")
        
        print("\n=== Vectorized time series ===")
        # Fast time series
        time_series = lookup.lookup_time_series_vectorized(
            '2025-01-01 11:31', '2025-01-01 13:00',
            ['ST_002', 'ST_005']
        )
        
        
        
        
        
        
        print(f"Time series length: {len(time_series['datetimes'])}")
        print(f"Time series datetimes: {time_series['datetimes']}")
        print(f"First 3 ST_005 values: {time_series['stations']['ST_005'][:]}")
        
        # print("\n=== Fast statistics ===")
        # stats = lookup.get_station_stats_fast('ST_002')
        # print(f"ST_002 stats: mean={stats['mean']:.2f}, min={stats['min']}, max={stats['max']}")
        
        # print("\n=== Performance info ===")
        # perf_info = lookup.get_performance_info()
        # print(f"Performance: {perf_info}")
        
        # print("\n=== Performance benchmark ===")
        
        
        # # Get previous 2 days of data for one station
        # result = lookup.lookup_previous_time_series('2025-01-03 15:30', days_back=2, station_ids='ST_002')
        # print(result)

        # # Get previous 1 day and 12 hours for multiple stations  
        # result = lookup.lookup_previous_time_series('2025-01-03 15:30', days_back=1, hours_back=12, 
        #                                         station_ids=['ST_002', 'ST_005'])
        # print(result)

        # # Get previous 48 hours only
        # result = lookup.lookup_previous_time_series('2025-01-01 15:30', hours_back=48, station_ids='ST_002')
        # print(result)

        # # Get statistics for the previous time period
        # stats = lookup.get_previous_time_stats('2025-01-01 15:30', days_back=2, station_ids=['ST_002', 'ST_005'])
        # print(stats['stations']['ST_005']['mean'])
        
        
        #performance_benchmark(lookup, 50000)

if __name__ == "__main__":
    example_usage()