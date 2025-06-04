from CodeVS.components.water_enum import WaterBody


class Station:
    def __init__(self, station_id, type, name, lat, lng, km, cus):
        self.station_id = station_id
        self.water_type = WaterBody(type.upper())
        self.name = name
        self.lat = lat
        self.lng = lng
        self.km = km
        self.customer_name = cus

    def __str__(self):
        return (f"Station ID: {self.station_id}, Name: {self.name}, Location: ({self.lat}, {self.lng}), "
                f"KM: {self.km}, CUS: {self.customer_name}")
