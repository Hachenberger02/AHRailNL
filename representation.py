from sys import argv
import csv

# classes

class Map():
    
    def __init__(self, stations_file_path, routes_file_path):
        self.stations = self.add_stations(stations_file_path)
        self.routes = self.add_routes(routes_file_path)

    def add_stations(self, file_path):
        """pre: file path to stations.csv
        post: "returns list of station objects"""
        with open(file_path) as stations:
            stations_reader = csv.DictReader(stations)

            station_list = []
            for row in stations_reader:
                # check if columns are right
                assert "station" in row.keys() and "x" in row.keys() and "y" in row.keys(), "Station csv should have station, y and x headers"
                new_station = Station(row["station"], float(row["x"]), float(row["y"]))
                station_list.append(new_station)
            
            return station_list
        

    def add_routes(self, file_path):
        """pre: file path to routes.csv
        post: "returns list of route objects"""
        with open(file_path) as routes:
            routes_reader = csv.DictReader(routes)

            routes_list = []
            for row in routes_reader:
                assert "station1" in row.keys() and "station2" in row.keys() and "distance" in row.keys(), "Routes csv should have station1, station2 and distance headers"

                new_route = Route(row["station1"], row["station2"], int(row["distance"]))

                # add route to route list
                routes_list.append(new_route)

                # add route to Station objects
                for station in self.stations:
                    if station.name == row["station1"] or station.name == row["station2"]:
                        station.add_route(new_route)
            return routes_list

class Station():

    def __init__(self, name, x, y):
        self.name = name
        self.x = x
        self.y = y
        self.routes: list[object] = []

    def add_route(self, route):
        self.routes.append(route)


class Route():

    def __init__(self, station_1, station_2, distance):
        self.station_1 = station_1
        self.station_2 = station_2
        self.distance = distance

if __name__ == "__main__":

    # make sure a .csv is given for both stations and routes
    assert len(argv) == 3, "Usage: representation.py [file path stations.csv] [file path routes.csv]"

    # make Map object
    new_map = Map(argv[1], argv[2])
    
    
        