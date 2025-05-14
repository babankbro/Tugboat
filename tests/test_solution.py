import sys
import os


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from datetime import timedelta, datetime
import pandas as pd
from CodeVS.read_data import *
from CodeVS.initialize_data import initialize_data, print_all_objects
from CodeVS.operations.assigned_barge import *
from CodeVS.operations.scheduling import *
from CodeVS.operations.transport_order import *
from CodeVS.operations.travel_helper import *
from CodeVS.compoents.solution import Solution

@pytest.fixture 
def test_data():
    data = initialize_data(carrier_df, station_df, order_df, tugboat_df, barge_df)
    TravelHelper()
    TravelHelper._set_data(TravelHelper._instance,  data)
    return {'data': data,
            'TravelHelper': TravelHelper._instance}

                   
def test_distance_sea_sea(test_data):
    data = test_data['data']
    start_station = data['stations']['c1']
    end_station = data['stations']['s0']
    start_location = (start_station.lat, start_station.lng)
    end_location = (end_station.lat, end_station.lng)
    start_station = (13.18310799,	100.8126384)
    end_station = (13.4717077924905, 100.595846778158)
    distance = TravelHelper._instance.get_distance_location(start_location, end_location)
    assert int(distance) == 39
                                                                                
def test_solution_schedule(test_data):
    solution = Solution(test_data['data'])
    tugboat_df, barge_df =  solution.generate_schedule()
    
    filtered_df = tugboat_df[
                            ((tugboat_df['tugboat_id'] == 'tbs1') & (tugboat_df['type'] == 'Appointment')) 
                            &  ((tugboat_df['order_id'] == 'o1') | (tugboat_df['order_id'] == 'o1'))
                            & (tugboat_df['order_trip'] == 1)
                            #& (tugboat_df['distance'] > 60)
                            #(tugboat_df['distance'] > 60)
                            ]
    print(filtered_df)
    filtered_df2 = tugboat_df[
                            ((tugboat_df['tugboat_id'] == 'tbs1') & (tugboat_df['type'] == 'Barge Collection')) 
                            &  ((tugboat_df['order_id'] == 'o1') | (tugboat_df['order_id'] == 'o1'))
                            & (tugboat_df['order_trip'] == 2)
                            #& (tugboat_df['distance'] > 60)
                            #(tugboat_df['distance'] > 60)
                            ]
    
    
    assert int(filtered_df.iloc[0]['distance']) == int(filtered_df2.iloc[0]['distance'])
    
def test_travel_process(test_data):
    data = test_data['data']
    tugboats  = data['tugboats']
    tugboat = tugboats['tbs1']
    station_barge = data['stations']['c1']
    end_station = data['stations']['s2']
    travel_infos = {
                'start_location': (tugboat._lat, tugboat._lng),
                'end_location': (end_station.lat, end_station.lng),
                'speed': 10,
                'start_km': 0,
                'end_km': 20
            }
    distance, travel_time, travel_steps = TravelHelper._instance.process_travel_steps(WaterBody.SEA, 
                                                                                      WaterBody.RIVER, travel_infos)
    print("Distance #######################################", distance)
    assert int(distance) == 59
      
    
    
    
    
    
