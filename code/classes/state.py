import csv
import sys

from typing import Union

sys.path.append("code/classes")
from station import Station
from connection import Connection
from route import Route


class State():
    # TODO: make list with used connections and list with unused connections
    # TODO: add route minutes to show method

    def __init__(self, stations_file_path: str, connections_file_path: str, max_number_routes: int, time_frame: int, relaxed_all_connections: bool = False, relaxed_max_routes: bool = False, relaxed_time_frame: bool = False):
        """
        Initiates State class.

        post:
            Creates list of stations, connections and routes
            Fills list of stations and connections 
            Creates constraint relaxation variables     
        """
        self.total_number_connections: int = 0

        # add relations to all other objects
        self.stations: list[object] = self._add_stations(stations_file_path)
        self.connections: list[object] = self._add_connections(
            connections_file_path)
        self.routes: list[object] = []

        self.max_number_routes: Union(int, None) = max_number_routes
        self.time_frame: Union(int, None) = time_frame

        # add parameters for quality score function
        self.quality: float = 0.0
        self.fraction_used_connections: float = 0.0
        self.number_routes: int = 0
        self.total_minutes: int = 0

        # variables for constraint relaxation
        self.relaxed_all_connections = relaxed_all_connections
        self.relaxed_time_frame = relaxed_time_frame
        self.relaxed_max_routes = relaxed_max_routes

        # route id tracker for defining the name of a route
        self.route_id_tracker: int = 1

    def __str__(self):
        """
        Gives description of the state object

        returns:
            description of the state object
        """
        return ("State object")

    def _add_stations(self, file_path: str) -> list:
        """
        Adds stations from stations.csv file to the list.

        pre: 
            file path to stations.csv

        post: 
            returns list of station objects
        """
        with open(file_path) as stations:
            stations_reader: object = csv.DictReader(stations)

            # add stations to the station list
            station_list: list = []
            for row in stations_reader:
                # check if columns are right
                assert "station" in row.keys() and "x" in row.keys() and "y" in row.keys(
                ), "Station csv should have station, y and x headers"
                new_station: object = Station(
                    row["station"], float(row["x"]), float(row["y"]))
                station_list.append(new_station)

            return station_list

    def _add_connections(self, file_path: str) -> list:
        """
        Adds connections from connections.csv to the list.

        pre: 
            file path to connections.csv

        post: 
            updates total number of connections
            returns list of connection objects and adds connections to stations
        """
        with open(file_path) as connections:
            connections_reader: object = csv.DictReader(connections)

            # add connections to connections list
            connections_list: list[object] = []
            for row in connections_reader:
                assert "station1" in row.keys() and "station2" in row.keys() and "distance" in row.keys(
                ), "connections csv should have station1, station2 and distance headers"
                # look up station object by name
                station1: object = next(
                    station for station in self.stations if station.name == row["station1"])
                station2: object = next(
                    station for station in self.stations if station.name == row["station2"])

                # add connection to connection list
                new_connection: object = Connection(
                    station1, station2, float(row["distance"]))
                connections_list.append(new_connection)

                # add connection to Station objects
                for station in self.stations:
                    if station.name == row["station1"] or station.name == row["station2"]:
                        station.add_connection(new_connection)

                self.total_number_connections += 1

            return connections_list

    def _check_number_routes(self) -> bool:
        """
        Checks if the maximum number of routes is reached.

        returns:
            True if number of routes is not reached
            False otherwise    
        """
        if not self.relaxed_max_routes and self.number_routes == self.max_number_routes:
            return False
        return True

    def add_route(self, connection: 'Connection') -> None:
        """
        Adds a new route.
        pre: 
            first connection for a route

        post: 
            creates and adds Route object to routes list

        returns:
            true if addition was succesful
            false if addition was not succesful
        """
        if self._check_number_routes():

            # determine route name
            name = f"train_{self.route_id_tracker}"
            self.route_id_tracker += 1

            # add new route to list
            new_route = Route(name, connection)
            self.routes.append(new_route)

            # update number of routes
            self.number_routes += 1

            return True
        else:
            return False

    def delete_route(self, route: 'Route'):
        """
        Deletes given route

        pre: 
            route to be deleted exists

        post:
            removes route from routes list

        returns:
            True if operation was succesful    
        """
        if route in self.routes:
            self.routes.remove(route)
            return True
        else:
            return False

    def _update_fraction_used_connections(self) -> float:
        """
        Calculates the fraction of used connections

        post:
            updates fraction of used connections

        returns:
            newest fraction of used connections
        """
        # get number of unique connections
        unique_connections = set(
            route_connection for route in self.routes for route_connection in route.route_connections)
        number_unique_connections = len(unique_connections)

        # calculate fraction
        self.fraction_used_connections = number_unique_connections / \
            self.total_number_connections

        return self.fraction_used_connections

    def _update_number_routes(self) -> int:
        """
        Updates the number of routes.

        post:
            updates number of routes

        returns:
            number of routes
        """
        updated_routes = len(self.routes)
        self.number_routes = updated_routes
        return updated_routes

    def _update_total_minutes(self) -> int:
        """
        Calculates total number of minutes of all routes.

        post:
            updates total number of minutes

        returns:
            total number of minutes     
        """

        # calculate number of minutes
        self.total_minutes = sum(
            connection.distance for route in self.routes for connection in route.route_connections)

        return self.total_minutes

    def calculate_score(self) -> float:
        """
        post: 
            calculates and updates the quality score
        returns:
            the quality score
        """
        # update all variables with methods written above
        self._update_number_routes()
        self._update_fraction_used_connections()
        self._update_total_minutes()

        self.quality = self.fraction_used_connections * 10000 - \
            (self.number_routes * 100 + self.total_minutes)
        return self.quality

    def write_output(self, file_path: str):
        """
        Writes output to output.csv according to given standard
        post: 
            writes all routes to a .csv file
            adds score to .csv file
        """

        # code source: https://www.scaler.com/topics/how-to-create-a-csv-file-in-python/
        with open(file_path, 'w') as file:
            writer = csv.writer(file)

            # write headers
            writer.writerow(['train', 'stations'])

            # write stations
            for route in self.routes:
                new_row: list = []
                new_row.append(route.name)

                stations_str: str = "[" + ", ".join(
                    station.name for station in route.route_stations) + "]"

                new_row.append(stations_str)
                writer.writerow(new_row)

            # write score
            writer.writerow(["score", self.calculate_score()])

    def routes_valid_time_frame(self) -> bool:
        """
        checks if all routes are within the given timeframe

        returns:
            true if all stations are valid      
        """
        for route in self.routes:
            if not route.is_valid_time(self.time_frame):
                return False
            return True

    def less_than_max_routes(self) -> bool:
        """
        Checks if there are not more than the max number of routes

        returns:
            True if there are less routes than the max     
        """
        if self.max_number_routes and self.number_routes > self.max_number_routes:
            return False
        return True

    def all_connections_used(self) -> bool:
        """
        Checks if all connections are used.

        returns:
            True if all connections are used     
        """
        all_connections_used = True
        for connection in self.connections:
            connection_used = False
            for route in self.routes:
                if route.is_connection_in_route(connection):
                    connection_used = True
            if not connection_used:
                all_connections_used = False
        return all_connections_used

    def is_valid_solution(self) -> dict:
        """
        Gives information about satisfaction of all constraints

        pre:
            constraint relaxation parameters (default: False) relax the three specific constraints if True

        returns:
            bool for overall constraint satisfaction     
        """

        if not self.relaxed_time_frame and not self.routes_valid_time_frame():
            return False
        if not self.relaxed_max_routes and not self.less_than_max_routes():
            return False
        if not self.relaxed_all_connections and not self.all_connections_used():
            return False
        return True

    def is_valid_solution_non_relaxed(self) -> dict:
        """
        Gives information about satisfaction of all constraints, without constraint relaxation

        returns:
            bool for overall constraint satisfaction     
        """

        if not self.routes_valid_time_frame():
            return False
        if not self.less_than_max_routes():
            return False
        if not self.all_connections_used():
            return False
        return True

    def show(self):
        """
        Gives description of the current state.

        returns:
            description with:
                all routes with their connections
                score      
        """
        result_string: str = "Routes:\n"
        for route in self.routes:
            result_string += f"- {route.name}:\n"
            for connection in route.route_connections:
                result_string += f"  - {connection}\n"
        result_string += f"Score: {self.calculate_score()}\n"
        if self.is_valid_solution():
            result_string += "The current solution is valid."
        else:
            result_string += "The current solution is not valid."
        return result_string

    def show_sleeper_string(self) -> str:
        """
        Gives string that can 'awake' the current state at any later moment

        returns:
            string with:
            - quality score
            - fraction of used connections
            - number of routes
            - total distance driven 
            - constraint relaxation values
                - all connections used
                - in time frame
                - max routes
            - routes
                - name
                - stations
            the first delimiter is \t, the second is ;, the third is : and the fourth is >
        """
        sleeper_string: str = ""

        # add quality score and parameters
        sleeper_string += f"{self.quality}\t{self.fraction_used_connections}\t{self.number_routes}\t{self.total_minutes}\t"

        # add constraint relaxation values
        sleeper_string += f"{self.relaxed_all_connections};{self.relaxed_time_frame};{self.relaxed_max_routes}\t"

        # add routes
        for r_index, route in enumerate(self.routes):
            sleeper_string += f"{route.name}:"
            for index, station in enumerate(route.route_stations):
                sleeper_string += station.name
                if index < len(route.route_stations) - 1:
                    sleeper_string += ">"
            if r_index < len(self.routes) - 1:
                sleeper_string += ";"

        return sleeper_string

    def awaken_state(self, sleeper_string: str):
        """
        'awakens' a certain state, using a sleeper string

        pre: 
            sleeper_string is string with:
            - quality score
            - fraction of used connections
            - number of routes
            - total distance driven 
            - constraint relaxation values
                - all connections used
                - in time frame
                - max routes
            - routes
                - name
                - stations
            the first delimiter is \t, the second is ;, the third is -

        post:
            updates routes, quality score and score parameter and constraint relaxation value attributes      
        """
        sleeper_data = sleeper_string.split("\t")

        # add quality score and quality score parameters
        self.quality = float(sleeper_data[0])
        self.fraction_used_connections = float(sleeper_data[1])
        self.number_routes = int(sleeper_data[2])
        self.total_minutes = float(sleeper_data[3])

        # add constraint relaxation values
        constraint_relaxation_data: list = sleeper_data[4].split(";")
        self.relaxed_all_connections = bool(constraint_relaxation_data[0])
        self.relaxed_time_frame = bool(constraint_relaxation_data[1])
        self.relaxed_max_routes = bool(constraint_relaxation_data[2])

        # add routes
        routes_data: list = sleeper_data[5].split(";")
        for index, route_data in enumerate(routes_data):
            stations_list = route_data.split(":")[1].split(">")
            connections_list: list = []
            for i in range(len(stations_list) - 1):
                for connection in self.connections:
                    if (
                        i + 1 < len(stations_list) and
                        (
                            (connection.station_1.name == stations_list[i] and connection.station_2.name == stations_list[i + 1]) or
                            (connection.station_2.name ==
                             stations_list[i] and connection.station_1.name == stations_list[i + 1])
                        )
                    ):
                        connections_list.append(connection)
            self.add_route(connections_list.pop(0))
            for connection in connections_list:
                self.routes[index].add_connection(connection)

    def show_csv_line(self, state_id: int, algorithm: str):
        """
        makes a line that can be added to data csv

        returns:
            list with:
            - state_id
            - algorithm
            - score
            - fraction_used_connections
            - number_routes
            - total_minutes
            - is_solution
            - sleeper_string       
        """

        csv_line: list = [
            state_id,
            algorithm,
            self.calculate_score(),
            self.fraction_used_connections,
            self.number_routes,
            self.total_minutes,
            self.is_valid_solution_non_relaxed(),
            self.show_sleeper_string()]

        return csv_line

    def reset(self):
        """
        Resets the state.

        post:
            empties list of routes
            resets score and score parameters
            resets relaxations     
        """

        # empty list of routes
        self.routes = []

        self.route_id_tracker = 1

        # reset relaxations
        self.relaxed_all_connections = False
        self.relaxed_max_routes = False
        self.relaxed_time_frame = False

        # reset score and score parameters
        self.quality = 0.0
        self.fraction_used_connections = 0.0
        self.number_routes = 0
        self.total_minutes = 0


if __name__ == "__main__":
    state = State("../../data/stations_holland.csv",
                  "../../data/routes_holland.csv",
                  7,
                  120)
    print(state.show())
    print(state.show_csv_line(1, "algorithm_x"))
