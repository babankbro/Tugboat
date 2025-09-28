from CodeVS.components.station import Station

class Carrier:
    def __init__(self, carrier_id, order_id, name, lat, lng, station):
        self.carrier_id = carrier_id
        self.order_id = order_id
        self.name = name
        self.lat = lat
        self.lng = lng
        self.station = station
        self.station_id = station.station_id

    def __str__(self):
        return (f"Carrier ID: {self.carrier_id}, Order ID: {self.order_id}, Name: {self.name}, "
                f"Location: ({self.lat}, {self.lng})")
