from flask import Flask, jsonify, request
from main import test_transport_order
from initialize_data import initialize_data 
from read_data import *
from operations.travel_helper import *
from connectdb import *
import numpy as np
from components.solution import Solution
from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:3000", "http://45.82.72.96:3000"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }

})

DEBUG = os.getenv('DEBUG')

@app.route("/orders", methods=["POST", "GET"])
def calculate_all_schedule():
    try:
        # print(f"Order ID: {order_id}")
        # Similar to main.py
        carrier_df, barge_df, tugboat_df, station_df, order_df, customer_df = get_data_from_db()
        # order_df = order_df[order_df['ID']==order_id]

        data = initialize_data(carrier_df, barge_df, tugboat_df, station_df, order_df, customer_df)
        if TravelHelper._instance is None:
                TravelHelper()
                
        TravelHelper._set_data(TravelHelper._instance,  data)
        order_ids = [ order_id for order_id in data['orders'].keys()]
        #order_ids = [order_id]
        
        solution = Solution(data)
        # print(f"Data Type: {type(data)}")
        # for key, value in data.items():
        #         print(key, value, "\n")
        tugboat_df, barge_df = solution.generate_schedule(order_ids)
        cost_results, tugboat_df, barge_df, cost_df = solution.calculate_cost(tugboat_df, barge_df)
        order_ids = list(tugboat_df["order_id"].unique())
        detail = []
        for order_id in order_ids:
            order_dict= {}
            order_dict["order_id"] = order_id
            order_dict["cost"] = cost_df[cost_df["order_id"]==order_id].to_json(orient='records')
            order_dict["schedule"] = tugboat_df[tugboat_df["order_id"]==order_id].to_json(orient='records')
            detail.append(order_dict)
        if request.method=="GET":
            output_json = {
                "message": "Schedule Created",
                "detail":detail,
            }
            return jsonify(output_json), 200
        if request.method=="POST":
            # Update the database
            # Connect to db
            try:
                conn = mysql.connector.connect(
                    host=HOST,
                    port=PORT,
                    user=USER,
                    password=PASSWORD,
                    database=DATABASE_NAME
                )

                if conn.is_connected():
                    print("Connect to DB Successfully")
                    cursor = conn.cursor()
                    
                    # Get unique order id from the tugboat_df
                    order_ids = list(tugboat_df["order_id"].unique())
                    for order_id in order_ids:
                    # Remove the old record with the same ID in scheduling table and cost table
                        query_schedule = "DELETE FROM `Schedule` WHERE `order_id`=%s;"
                        query_cost = "DELETE FROM `Cost` WHERE `OrderId`=%s;"
                        cursor.execute(query_schedule, (order_id,))
                        # print(f"Executing query: {query_cost}")

                        cursor.execute(query_cost, (order_id,))
                        
                        # print("Cost Data Deleted")
                        insert_schedule_query = """
                            INSERT INTO `Schedule`(`ID`, `type`, `name`, `enter_datetime`, 
                                `exit_datetime`, `distance`, `time`, `speed`, `type_point`, `order_trip`, 
                                `total_load`, `barge_ids`, `order_distance`, `order_time`, `barge_speed`, 
                                `order_arrival_time`, `tugboat_id`, `order_id`, `water_type`) 
                            VALUES (%s,%s,%s,%s,%s,
                                %s,%s,%s,%s,%s,
                                %s,%s,%s,%s,%s,
                                %s,%s,%s,%s)
                        """
                        temp_tugboat_df = tugboat_df[tugboat_df["order_id"]==order_id]
                        temp_tugboat_df = temp_tugboat_df.replace([np.nan], [None])
                        # temp_tugboat_df = temp_tugboat_df.replace([np.nat], [None])

                        for _, row in temp_tugboat_df.iterrows():
                            # print(row)
                            cursor.execute(insert_schedule_query, (
                                row['ID'] if row["ID"] else None,
                                row['type'] if row["type"] else None,
                                row['name'] if row["name"] else None,
                                row['enter_datetime'] if row["enter_datetime"] else None,
                                row['exit_datetime'] if row["exit_datetime"] else None,
                                row['distance'] if row["distance"] else None,
                                row['time'] if row["time"] else None,
                                row['speed'] if row["speed"] else None,
                                row['type_point'] if row["type_point"] else None,
                                row['order_trip'] if row["order_trip"] else None,
                                row['total_load'] if row["total_load"] else None,
                                row['barge_ids'] if row["barge_ids"] else None,
                                row['order_distance'] if row["order_distance"]  else None,
                                row['order_time'] if row["order_time"] else None,
                                row['barge_speed'] if row["barge_speed"] else None,
                                row['order_arrival_time'] if not row["order_arrival_time"] else None,
                                row['tugboat_id'] if row["tugboat_id"] else None,
                                row['order_id'] if row["order_id"] else None,
                                row['water_type'] if row["water_type"] else None,
                            ))

                        insert_cost_query = """
                                    INSERT INTO 
                                        `Cost`(`TugboatId`, `OrderId`, `Time`, `Distance`, `ConsumptionRate`, `Cost`, `TotalLoad`) 
                                    VALUES (%s,%s,%s,%s,%s,%s,%s)
                                    """
                        temp_cost_df = cost_df[cost_df["order_id"]==order_id]
                        temp_cost_df = temp_cost_df.replace([np.nan], [None])

                        for _, row in temp_cost_df.iterrows():
                            cursor.execute(insert_cost_query,(
                                row['tugboat_id'] if row["tugboat_id"] else None,
                                row['order_id'] if row["order_id"] else None,
                                row['time'] if row["time"] else None,
                                row['distance'] if row["distance"] else None,
                                row['consumption_rate'] if row["consumption_rate"] else None,
                                row['cost'] if row["cost"] else None,
                                row['total_load'] if row["total_load"] else None,
                            ))
                        # print("New Cost Data Inserted")
                    conn.commit()
                    cursor.close()
                return jsonify({
                    "message": "schedule created",
                }), 201
            except Error as e:
                return jsonify({
                    "message": "error",
                    "detail": e
                }), 400
            finally:
                if conn and conn.is_connected():
                    conn.close()

    except Error as e:
        return jsonify({
            "message": "error",
            "detail": e
        }), 400

@app.route("/orders/<order_id>", methods=["POST","GET"])
def calculate_single_schedule(order_id):
    try:
        # print(f"Order ID: {order_id}")
        if order_id:
            # Similar tp main.py
            carrier_df, barge_df, tugboat_df, station_df, order_df, customer_df = get_data_from_db()
            data = initialize_data(carrier_df, barge_df, tugboat_df, station_df, order_df, customer_df)
            
            if TravelHelper._instance is None:
                TravelHelper()
                
            TravelHelper._set_data(TravelHelper._instance,  data)
            order_ids = [ order_id for order_id in data['orders'].keys() if data['orders'][order_id].order_type == TransportType.IMPORT]
            #order_ids = [order_id]
            
            solution = Solution(data)
            tugboat_df, barge_df = solution.generate_schedule(order_ids)
            result_df = tugboat_df
            filter_out_type = ['main_point']
            # for key, value in data.items():
            #         print(key, value, "\n")   
            
            # detail = []
            cost_results, tugboat_df, barge_df, cost_df = solution.calculate_cost(tugboat_df, barge_df)
            
            order_dict= {}
            order_dict["order_id"] = order_id
            order_dict["cost"] = cost_df[cost_df["order_id"]==order_id].to_json(orient='records')
            order_dict["schedule"] = tugboat_df[tugboat_df["order_id"]==order_id].to_json(orient='records')
            # detail.append(order_dict)
            if request.method=="GET":
                output_json = {
                    "message": "Schedule Created",
                    "detail":[order_dict],
                }
                return jsonify(output_json), 200
            if request.method=="POST":
                # Update the database
                # Connect to db
                try:
                    conn = mysql.connector.connect(
                        host=HOST,
                        port=PORT,
                        user=USER,
                        password=PASSWORD,
                        database=DATABASE_NAME
                    )

                    if conn.is_connected():
                        print("Connect to DB Successfully")
                        cursor = conn.cursor()

                        # Remove the old record with the same ID in scheduling table and cost table
                        query_schedule = "DELETE FROM `Schedule` WHERE `order_id`=%s;"
                        query_cost = "DELETE FROM `Cost` WHERE `OrderId`=%s;"
                        cursor.execute(query_schedule, (order_id,))
                        print(f"Executing query: {query_cost}")

                        cursor.execute(query_cost, (order_id,))
                        
                        
                        # print("Cost Data Deleted")
                        insert_schedule_query = """
                            INSERT INTO `Schedule`(`ID`, `type`, `name`, `enter_datetime`, 
                                `exit_datetime`, `distance`, `time`, `speed`, `type_point`, `order_trip`, 
                                `total_load`, `barge_ids`, `order_distance`, `order_time`, `barge_speed`, 
                                `order_arrival_time`, `tugboat_id`, `order_id`, `water_type`) 
                            VALUES (%s,%s,%s,%s,%s,
                                %s,%s,%s,%s,%s,
                                %s,%s,%s,%s,%s,
                                %s,%s,%s,%s)
                        """
                        temp_tugboat_df = tugboat_df[tugboat_df["order_id"]==order_id]
                        temp_tugboat_df = temp_tugboat_df.replace([np.nan], [None])
                        # temp_tugboat_df = temp_tugboat_df.replace([np.nat], [None])

                        for _, row in temp_tugboat_df.iterrows():
                            # print(row)
                            cursor.execute(insert_schedule_query, (
                                row['ID'] if row["ID"] else None,
                                row['type'] if row["type"] else None,
                                row['name'] if row["name"] else None,
                                row['enter_datetime'] if row["enter_datetime"] else None,
                                row['exit_datetime'] if row["exit_datetime"] else None,
                                row['distance'] if row["distance"] else None,
                                row['time'] if row["time"] else None,
                                row['speed'] if row["speed"] else None,
                                row['type_point'] if row["type_point"] else None,
                                row['order_trip'] if row["order_trip"] else None,
                                row['total_load'] if row["total_load"] else None,
                                row['barge_ids'] if row["barge_ids"] else None,
                                row['order_distance'] if row["order_distance"]  else None,
                                row['order_time'] if row["order_time"] else None,
                                row['barge_speed'] if row["barge_speed"] else None,
                                row['order_arrival_time'] if not row["order_arrival_time"] else None,
                                row['tugboat_id'] if row["tugboat_id"] else None,
                                row['order_id'] if row["order_id"] else None,
                                row['water_type'] if row["water_type"] else None,
                            ))
                            

                        insert_cost_query = """
                                    INSERT INTO 
                                        `Cost`(`TugboatId`, `OrderId`, `Time`, `Distance`, `ConsumptionRate`, `Cost`, `TotalLoad`) 
                                    VALUES (%s,%s,%s,%s,%s,%s,%s)
                                    """
                        temp_cost_df = cost_df[cost_df["order_id"]==order_id]
                        temp_cost_df = temp_cost_df.replace([np.nan], [None])

                        for _, row in temp_cost_df.iterrows():
                            cursor.execute(insert_cost_query,(
                                row['tugboat_id'] if row["tugboat_id"] else None,
                                row['order_id'] if row["order_id"] else None,
                                row['time'] if row["time"] else None,
                                row['distance'] if row["distance"] else None,
                                row['consumption_rate'] if row["consumption_rate"] else None,
                                row['cost'] if row["cost"] else None,
                                row['total_load'] if row["total_load"] else None,
                            ))
                        # print("New Cost Data Inserted")
                        conn.commit()
                        cursor.close()
                    return jsonify({
                        "message": "schedule created",
                    }), 201
                except Error as e:
                    return jsonify({
                        "message": "error",
                        "detail": e
                    }), 400
                finally:
                    if conn and conn.is_connected():
                        conn.close()

    except Error as e:
        return jsonify({
            "message": "error",
            "detail": e
        }), 400


@app.route("/orders/multiple", methods=["POST"])
def calculate_multiple_schedules():
    try:
        # Get order_ids from request body
        request_data = request.get_json()
        if not request_data or 'order_ids' not in request_data:
            return jsonify({
                "message": "error",
                "detail": "Missing order_ids in request body"
            }), 400
        
        order_ids = request_data['order_ids']
        if not isinstance(order_ids, list) or len(order_ids) == 0:
            return jsonify({
                "message": "error",
                "detail": "order_ids must be a non-empty list"
            }), 400
        
        # Get data from database
        carrier_df, barge_df, tugboat_df, station_df, order_df, customer_df = get_data_from_db()
        data = initialize_data(carrier_df, barge_df, tugboat_df, station_df, order_df, customer_df)
        
        if TravelHelper._instance is None:
            TravelHelper()
            
        TravelHelper._set_data(TravelHelper._instance, data)
        
        # Process only the specified order_ids
        solution = Solution(data)
        tugboat_df, barge_df = solution.generate_schedule(order_ids)
        cost_results, tugboat_df, barge_df, cost_df = solution.calculate_cost(tugboat_df, barge_df)
        
        # Prepare response details
        detail = []
        for order_id in order_ids:
            # Check if the order_id exists in the results
            if order_id in tugboat_df["order_id"].unique():
                order_dict = {}
                order_dict["order_id"] = order_id
                order_dict["cost"] = cost_df[cost_df["order_id"]==order_id].to_json(orient='records')
                order_dict["schedule"] = tugboat_df[tugboat_df["order_id"]==order_id].to_json(orient='records')
                detail.append(order_dict)
            else:
                # Order might not exist or couldn't be processed
                detail.append({
                    "order_id": order_id,
                    "error": "Order not found or could not be processed"
                })
        
        # Connect to database for updates
        try:
            conn = mysql.connector.connect(
                host=HOST,
                port=PORT,
                user=USER,
                password=PASSWORD,
                database=DATABASE_NAME
            )

            if conn.is_connected():
                print("Connected to DB Successfully")
                cursor = conn.cursor()
                
                # Clear all results in Schedule and Cost tables before calculating new schedules
                query_clear_schedule = "DELETE FROM `Schedule`"
                query_clear_cost = "DELETE FROM `Cost`"
                cursor.execute(query_clear_schedule)
                cursor.execute(query_clear_cost)
                print("All previous schedule and cost records cleared")
                
                # Filter order_ids that were successfully processed
                valid_order_ids = [order_id for order_id in order_ids if order_id in tugboat_df["order_id"].unique()]
                
                if valid_order_ids:
                    # No need to delete specific records as we've cleared all tables already
                    
                    # Prepare batch inserts for Schedule table
                    insert_schedule_query = """
                        INSERT INTO `Schedule`(`ID`, `type`, `name`, `enter_datetime`, 
                            `exit_datetime`, `distance`, `time`, `speed`, `type_point`, `order_trip`, 
                            `total_load`, `barge_ids`, `order_distance`, `order_time`, `barge_speed`, 
                            `order_arrival_time`, `tugboat_id`, `order_id`, `water_type`) 
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """
                    
                    # Filter and prepare all schedule records
                    schedule_records = []
                    for order_id in valid_order_ids:
                        temp_tugboat_df = tugboat_df[tugboat_df["order_id"]==order_id]
                        temp_tugboat_df = temp_tugboat_df.replace([np.nan], [None])
                        
                        for _, row in temp_tugboat_df.iterrows():
                            schedule_records.append((
                                row['ID'] if row["ID"] else None,
                                row['type'] if row["type"] else None,
                                row['name'] if row["name"] else None,
                                row['enter_datetime'] if row["enter_datetime"] else None,
                                row['exit_datetime'] if row["exit_datetime"] else None,
                                row['distance'] if row["distance"] else None,
                                row['time'] if row["time"] else None,
                                row['speed'] if row["speed"] else None,
                                row['type_point'] if row["type_point"] else None,
                                row['order_trip'] if row["order_trip"] else None,
                                row['total_load'] if row["total_load"] else None,
                                row['barge_ids'] if row["barge_ids"] else None,
                                row['order_distance'] if row["order_distance"] else None,
                                row['order_time'] if row["order_time"] else None,
                                row['barge_speed'] if row["barge_speed"] else None,
                                row['order_arrival_time'] if not row["order_arrival_time"] else None,
                                row['tugboat_id'] if row["tugboat_id"] else None,
                                row['order_id'] if row["order_id"] else None,
                                row['water_type'] if row["water_type"] else None,
                            ))
                    
                    # Batch insert schedule records
                    if schedule_records:
                        cursor.executemany(insert_schedule_query, schedule_records)
                    
                    # Prepare batch inserts for Cost table
                    insert_cost_query = """
                        INSERT INTO `Cost`(`TugboatId`, `OrderId`, `Time`, `Distance`, 
                            `ConsumptionRate`, `Cost`, `TotalLoad`) 
                        VALUES (%s,%s,%s,%s,%s,%s,%s)
                    """
                    
                    # Filter and prepare all cost records
                    cost_records = []
                    for order_id in valid_order_ids:
                        temp_cost_df = cost_df[cost_df["order_id"]==order_id]
                        temp_cost_df = temp_cost_df.replace([np.nan], [None])
                        
                        for _, row in temp_cost_df.iterrows():
                            cost_records.append((
                                row['tugboat_id'] if row["tugboat_id"] else None,
                                row['order_id'] if row["order_id"] else None,
                                row['time'] if row["time"] else None,
                                row['distance'] if row["distance"] else None,
                                row['consumption_rate'] if row["consumption_rate"] else None,
                                row['cost'] if row["cost"] else None,
                                row['total_load'] if row["total_load"] else None,
                            ))
                    
                    # Batch insert cost records
                    if cost_records:
                        cursor.executemany(insert_cost_query, cost_records)
                    
                    conn.commit()
                
                cursor.close()
                
            return jsonify({
                "message": "schedules created",
                "detail": detail
            }), 201
            
        except Error as e:
            return jsonify({
                "message": "error",
                "detail": str(e)
            }), 400
        finally:
            if conn and conn.is_connected():
                conn.close()

    except Exception as e:
        return jsonify({
            "message": "error",
            "detail": str(e)
        }), 400

if __name__ == 'main':
    app.run(debug=DEBUG, host="0.0.0.0")
    #flask --app app run --debug