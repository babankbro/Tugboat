import sys
import os



sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from read_data import get_data_from_db
from CodeVS.components.transport_type import TransportType
from CodeVS.components.water_enum import WaterBody

from datetime import datetime, timedelta
from CodeVS.components.carrier import Carrier
from CodeVS.components.order import Order
from CodeVS.components.tugboat import Tugboat
from CodeVS.components.barge import Barge
from CodeVS.components.customer import Customer
import pandas as pd
from CodeVS.operations.assigned_barge import * 
from CodeVS.components.station import * 
import CodeVS.config_problem as config_problem


def initialize_data(carrier_df, barge_df, tugboat_df, station_df, order_df, customer_df=None):
    
    # eeeee
    stations = {
        row['ID']: Station(
            row['ID'], 
            row['TYPE'], 
            row['NAME'], 
            row['LAT'], 
            row['LNG'], 
            row['KM'], 
            row['CUS'])
        for _, row in station_df.iterrows()
    }
    #print(carrier_df['DestStationId'])
    carriers = {
        row['ID']+"_"+row['ORDER ID']: Carrier(row['ID'], row['ORDER ID'], row['NAME'],
                                               row['LAT'], row['LNG'], stations[row['StartStationId']])
        for _, row in carrier_df.iterrows()
    }
    
    # eeeee
    
    
    # Create customer objects if customer_df is provided
    customers = {}
    if customer_df is not None and not customer_df.empty:
        customers = {
            row['ID']: Customer(
                row['ID'],
                # Default order_id as None if not available
                order_id=None,
                name=row['NAME'],
                lat=row.get('LAT', 0),
                lng=row.get('LNG', 0),
                station=stations.get(row.get('STATION'), None)
            )
            for _, row in customer_df.iterrows()
        }
        print(f"Created {len(customers)} customer objects")

    orders = {
        row['ID']: Order(
            row['ID'], row['TYPE'], row['START POINT'], row['DES POINT'], row['PRODUCT'], row['DEMAND'],
            row['START DATETIME'], row['DUE DATETIME'], row['LD+ULD RATE'],
            [row['CRANE RATE1'], row['CRANE RATE2'], row['CRANE RATE3'], row['CRANE RATE4'],
            row['CRANE RATE5'], row['CRANE RATE6'], row['CRANE RATE7'], row['CRANE RATE8'], row['CRANE RATE9']],
            [row.get('TIME READY CR1', 0), row.get('TIME READY CR2', 0), row.get('TIME READY CR3', 0),
            row.get('TIME READY CR4', 0), row.get('TIME READY CR5', 0), row.get('TIME READY CR6', 0),
            row.get('TIME READY CR7', 0), row.get('TIME READY CR8', 0), row.get('TIME READY CR9', 0)]
        )
        for _, row in order_df.iterrows()
    }

    # Create customer-station mapping
    customer_station_map = {stations[sid].customer_name: stations[sid] 
                           for sid in stations if stations[sid].customer_name is not None}

    # Map order relationships
    for order_id, order in orders.items():
        if order.order_type == TransportType.IMPORT:
            order.start_object = carriers[order.start_point+"_"+order.order_id]
            order.des_object = customers[order.des_point]
        else:
            order.start_object = customers[order.start_point]
            order.des_object = carriers[order.des_point+"_"+order.order_id]

    
    # Create a dictionary of Tugboat objects with 'ID' as the key
    tugboats = {
        row['ID']: Tugboat(row['ID'], row['NAME'], row['MAX CAP'], row['MAX BARGE'], row['MAX FUEL CON'],
                        row['TYPE'], row['MAX SPEED'], row['LAT'], row['LNG'], row['STATUS'], row['KM'],
                        row.get('READY DATETIME', None))
        for _, row in tugboat_df.iterrows()
    }
    
    # Create a dictionary of Barge objects with 'ID' as the key
    barges = {
        row['ID']: Barge(row['ID'], row['NAME'], row['WEIGHT'], row['CAP'], 
                         row['LAT'], row['LNG'], row['WATER STATUS'],row['STATION'], stations[row['STATION']].km  ,row['SETUP TIME'],
                         row.get('READY DATETIME', None))
        for _, row in barge_df.iterrows()
    }
    
    
    data = {
        'carriers': carriers,
        'stations': stations,
        'orders': orders,
        'customer_station_map': customer_station_map,
        'tugboats': tugboats,
        'barges': barges,
        'customers': customers
    }
    
    # for station in data['stations'].values():
    #     print(station)
    
    station_points, distances =  create_station_points(stations)
    data['station_points'] = station_points
    
    #print(len(station_points), len(distances))
    
    lookup_distances = {}
    
    for i in range(len(station_points)-1):
        id_i = station_points[i]['ID']
        j = i + 1
        d = distances[i]
        #print(d)
        id_j = station_points[j]['ID']
        lookup_distances[(id_i, id_j)] = d
        lookup_distances[(id_j, id_i)] = d
    
    sea_tugboats = {tugboat_id: tugboat for tugboat_id, tugboat in tugboats.items() if tugboat.tug_type == WaterBody.SEA}
    data['sea_tugboats'] = sea_tugboats
    river_tugboats = {tugboat_id: tugboat for tugboat_id, tugboat in tugboats.items() if tugboat.tug_type == WaterBody.RIVER}
    data['river_tugboats'] = river_tugboats
    
    
    data['lookup_distances'] = lookup_distances
    data['station_distances'] = distances
    data['station_ids'] = [station for station in data['stations']]
    data['lookup_station_index'] = {station: i for i, station in enumerate(data['stations'])}
    data['lookup_station_km'] = {station.km:station  for station in data['stations'].values()}
    data['sea_stations'] = {station_id: station for station_id, station in stations.items() if station.water_type == WaterBody.SEA}
    data['river_stations'] = {station_id: station for station_id, station in stations.items() if station.water_type == WaterBody.RIVER}
    
    
    return data

def print_all_objects(data):

    print("Carriers:")
    for carrier in data['carriers'].values():
        print(carrier)

    print("\nStations:")
    for station in data['stations'].values():
        print(station)

    print("\nOrders:")
    for order in data['orders'].values():
        print(order)
        print(order.start_object, order.des_object)

    # Print all Tugboat objects
    print("\nTugboats:")
    tugboats = data['tugboats']
    for tugboat_id, tugboat in tugboats.items():
        print(tugboat)


    print("\nBarges:")
    for barge in data['barges'].values():
        print(barge)

    print("\nCustomers:")
    for customer in data['customers'].values():
        print(customer)

def create_station_points(stations):
    #stations = data['stations']

    # # Station data points
    # old_data_points = [
    #     {"ID": "c1", "name": "1-Koh Si Chang", "enter_datetime": datetime(2025, 3, 6, 8, 0), "exit_datetime": datetime(2025, 3, 6, 9, 0)},
    #     {"ID": "s0", "name": "1-Bangkok Bar", "enter_datetime": datetime(2025, 3, 6, 10, 30), "exit_datetime": datetime(2025, 3, 6, 11, 30)},
    #     {"ID": "s1", "name": "2-Phra Chunlachomklao Fort", "enter_datetime": datetime(2025, 3, 6, 12, 0), "exit_datetime": datetime(2025, 3, 6, 13, 0)},
    #     {"ID": "s2", "name": "3-Bang Hua Suea Pier", "enter_datetime": datetime(2025, 3, 6, 13, 30), "exit_datetime": datetime(2025, 3, 6, 14, 30)},
    #     {"ID": "s3", "name": "4-Bangkok Port", "enter_datetime": datetime(2025, 3, 6, 15, 30), "exit_datetime": datetime(2025, 3, 6, 16, 30)},
    #     {"ID": "s4", "name": "5-Royal Thai Navy HQ", "enter_datetime": datetime(2025, 3, 6, 18, 30), "exit_datetime": datetime(2025, 3, 6, 19, 30)},
    #     {"ID": "s5", "name": "Wat Choeng Len", "enter_datetime": datetime(2025, 3, 6, 22, 30), "exit_datetime": datetime(2025, 3, 6, 23, 30)},
    #     {"ID": "s6", "name": "Tai Kred", "enter_datetime": datetime(2025, 3, 7, 0, 0), "exit_datetime": datetime(2025, 3, 7, 1, 0)},
    #     {"ID": "s7", "name": "Rama IV Bridge", "enter_datetime": datetime(2025, 3, 7, 1, 30), "exit_datetime": datetime(2025, 3, 7, 2, 30)},
    #     {"ID": "s8", "name": "Rangsit Bridge (Nonthaburi)", "enter_datetime": datetime(2025, 3, 7, 4, 0), "exit_datetime": datetime(2025, 3, 7, 5, 0)},
    #     {"ID": "s9", "name": "Pathum Thani Bridge", "enter_datetime": datetime(2025, 3, 7, 7, 0), "exit_datetime": datetime(2025, 3, 7, 8, 0)},
    #     {"ID": "s10", "name": "Wat Kai Tia Pier", "enter_datetime": datetime(2025, 3, 7, 9, 30), "exit_datetime": datetime(2025, 3, 7, 10, 30)},
    #     {"ID": "s11", "name": "Sam Khok Pier", "enter_datetime": datetime(2025, 3, 7, 11, 0), "exit_datetime": datetime(2025, 3, 7, 12, 0)},
    #     {"ID": "s12", "name": "Wat Chang Yai", "enter_datetime": datetime(2025, 3, 7, 14, 0), "exit_datetime": datetime(2025, 3, 7, 15, 0)},
    #     {"ID": "s13", "name": "Bang Pa-In (District)", "enter_datetime": datetime(2025, 3, 7, 17, 30), "exit_datetime": datetime(2025, 3, 7, 18, 30)},
    #     {"ID": "s14", "name": "Wat Thong Bo", "enter_datetime": datetime(2025, 3, 7, 20, 30), "exit_datetime": datetime(2025, 3, 7, 21, 30)},
    #     {"ID": "s15", "name": "Wat Prot Sat", "enter_datetime": datetime(2025, 3, 7, 22, 0), "exit_datetime": datetime(2025, 3, 7, 23, 0)},
    #     {"ID": "s16", "name": "Wat Song Kusol Pier", "enter_datetime": datetime(2025, 3, 8, 0, 30), "exit_datetime": datetime(2025, 3, 8, 1, 30)},
    #     {"ID": "s17", "name": "Sam Yaek Wat Phanan Choeng", "enter_datetime": datetime(2025, 3, 8, 2, 0), "exit_datetime": datetime(2025, 3, 8, 3, 0)},
    #     {"ID": "s18", "name": "Pridi Bridge", "enter_datetime": datetime(2025, 3, 8, 4, 30), "exit_datetime": datetime(2025, 3, 8, 5, 30)},
    #     {"ID": "s19", "name": "Chao Phrom Market", "enter_datetime": datetime(2025, 3, 8, 7, 0), "exit_datetime": datetime(2025, 3, 8, 8, 0)},
    #     {"ID": "s20", "name": "Wat Pa Kho", "enter_datetime": datetime(2025, 3, 8, 9, 30), "exit_datetime": datetime(2025, 3, 8, 10, 30)},
    #     {"ID": "s21", "name": "Wat Mai Sommarin", "enter_datetime": datetime(2025, 3, 8, 11, 0), "exit_datetime": datetime(2025, 3, 8, 12, 0)},
    #     {"ID": "s22", "name": "Bo Phrong Bridge Pier", "enter_datetime": datetime(2025, 3, 8, 13, 30), "exit_datetime": datetime(2025, 3, 8, 14, 30)},
    #     {"ID": "s23", "name": "Wat Bandai Pier", "enter_datetime": datetime(2025, 3, 8, 17, 0), "exit_datetime": datetime(2025, 3, 8, 18, 0)},
    #     {"ID": "s24", "name": "Wat Sam Makan", "enter_datetime": datetime(2025, 3, 8, 20, 30), "exit_datetime": datetime(2025, 3, 8, 21, 30)},
    # ]


    data_points = []
    distances = []
    travel_times = []
    value_stations = list(stations.values())
    for i, station in enumerate(value_stations):
        if station.water_type == WaterBody.SEA and station.station_id != config_problem.KOH_SI_CHANG_STATION_BASE_REFERENCE_ID:
            # Skip sea stations for now
            continue
        #enter_datatime = value_stations[i]["enter_datetime"]
        #exit_datatime = value_stations[i]["exit_datetime"]
        info = {
            "ID": station.station_id,
            "name": station.name,
            'station':station
            #"enter_datetime": enter_datatime,
            #"exit_datetime": exit_datatime
        }
        data_points.append(info) 
        
        if i < len(value_stations)-1:
            next_station = list(value_stations)[i+1]
            
            
    for i in range(len(data_points)-1):
        # Calculate travel time as 1 hour per 100 km
        current_satation = data_points[i]['station']
        next_station = data_points[i+1]['station']
        distances.append(abs(current_satation.km - next_station.km))
    
    #distances[0] = 0
    #print("Data points:", data_points)
    #print("Distances:", distances)
   
    return data_points, distances

if __name__ == "__main__":
    # Example usage
    carrier_df, barge_df, tugboat_df, station_df, order_df, customer_df = get_data_from_db()
    print(carrier_df.head())
    print(barge_df.head())
    print(tugboat_df.head())
    print(station_df.head())
    print(order_df.head())
    print(customer_df.head())
    data = initialize_data(carrier_df, barge_df, tugboat_df, station_df, order_df, customer_df)
    
    print_all_objects(data)