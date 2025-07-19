from CodeVS.components.station import Station

class Customer:
    def __init__(self, customer_id, order_id, name, lat, lng, station):
        self.customer_id = customer_id
        self.order_id = order_id
        self.name = name
        self.lat = lat
        self.lng = lng
        self.station = station
        self.km = station.km
        self.station_id = station.station_id

    def __str__(self):
        return (f"Customer ID: {self.customer_id}, Order ID: {self.order_id}, Name: {self.name}, "
                f"Location: ({self.lat}, {self.lng}), KM: {self.km}, Station ID: {self.station_id}")