from sys import path

path.append("code/classes")
from code.classes.state import State
from code.classes.station import Station
from code.classes.connection import Connection
from code.classes.route import Route

import random
import copy
from typing import Union


class Algorithm():
    def __init__(self, state: 'State', max_connection_returns: int = 0, heuristic_number_connections: bool = False, heuristic_route_maximalisation: bool = False, heuristic_difficult_connections: bool = False) -> None:
        self.state = state
        self.current_route_index = 0

        self.max_connection_returns = max_connection_returns

        self.heuristic_number_connections = heuristic_number_connections
        self.heuristic_route_maximalisation = heuristic_route_maximalisation
        self.heuristic_difficult_connections = heuristic_difficult_connections

    def __str__(self):
        return "Algorithm object"

    #### GENERAL METHODS ####

    def return_score(self) -> tuple[float, str]:
        """
        returns a an (extended) description of the (current) results of the algoritm

        pre: 
            self.state is an state object

        returns:
            score = a float describing the overall (quantative) score 
            description with:
                all routes with their connections
                score       

        """
        # save return variables
        score = self.state.calculate_score()
        description = self.state.show()

        return score, description

    def load_state(self, new_state: object) -> None:
        """
        loads self.state 

        pre: 
            new_state is an State-object

        post:
            self.state is new_state input
        """
        self.state = new_state

    def read_sleeper_string(self, sleeper_string: str) -> None:
        """
        reads the sleeper string and creates its state 

        pre: 
            sleeper string has the correct format  

        post:
            self.state is changed to the sleeper-string
        """

        self.state.awaken_state(sleeper_string)

    #### METHODS FOR BONUS AND MALUS POINT CALCULATION ####

    def get_total_bonus_malus(self, state) -> int:
        """
        gives sum of all plus- and minuspoints generated by enabled heuristics

        returns:
            sum of all points generated by heuristics      
        """
        total_b_m = 0

        if self.heuristic_number_connections:
            total_b_m += self.get_points_multiple_use_connections(state)

        if self.heuristic_route_maximalisation:
            total_b_m += self.minus_points_routes_maximalisation(state)

        return total_b_m

    def get_mutated_score(self, state) -> int:
        """
        mutates score of state with bonus/maluspoints generated by heuristics

        returns:
            mutated score of state     
        """
        return state.calculate_score() + self.get_total_bonus_malus(state)

    #### RANDOM METHODS ####

    def add_random_route(self) -> None:
        """
        adds a random 1-length route to the state

        pre: 
            self.state is a state object
            self.state.connections contains connection objects

        post:
            added a 1-length route to self.state.routes
        """
        self.state.add_route(random.choice(self.state.connections))

    def create_random_state(self, number_of_connections: int = 1) -> None:
        """
        randomly generates a state with random 1-length routes (default=1)

        pre: 
            number_of_connections is an integer

        post:
            self.state.routes contains specified number of 1-length routes
        """
        for new_connection in range(number_of_connections):
            # pick random connection and create route
            self.add_random_route()

    def add_random_connection(self, route_index: int = 0, choice: Union[str, None] = None) -> str:
        """
        adds a random available connection to a selected route 

        pre: 
            route_index is an integer
            a route exists with the route_index index in state.routes
            choice is either None, 'start' or 'end'  

        post:
            a connection is added (either at beginning or end) to the route

        returns:
            either ' start' or 'end' based on where the connection is added
        """

        # determine choice if not prematurely done
        if choice == None:
            choice = random.choice(['start', 'end'])

        if choice == 'start':
            new_connection = random.choice(
                self.state.routes[route_index].get_start_station().get_connections())

        elif choice == 'end':
            new_connection = random.choice(
                self.state.routes[route_index].get_end_station().get_connections())

        self.state.add_connection_to_route(
            self.state.routes[route_index], new_connection)

        return choice

    def delete_random_connection(self, route_index: int = 0, choice: Union[str, None] = None) -> str:
        """
        deletes a random available connection from a selected route

        pre: 
            route_index is an integer
            a route exists with the route_index index in state.routes
            choice is either None, 'start' or 'end'  

        post:
            a connection is deleted (either at beginning or end) from the route

        returns:
            either ' start' or 'end' based on where the connection is removed
        """
        # determine choice if not prematurely done
        if choice == None:
            choice = random.choice(['start', 'end'])

        if choice == 'start':
            self.state.delete_start_connection_from_route(
                random.choice(self.state.routes))

        elif choice == 'end':
            self.state.delete_end_connection_from_route(
                random.choice(self.state.routes))

        return choice

    def delete_random_route(self) -> None:
        route = random.choice(self.state.routes)

        self.state.delete_route(route)

    #### CONNECTION SUGGESTIONS HEURISTIC ####

    def station_has_one_unused_connection(self, state: 'State', station: 'Station') -> Union[bool, 'Connection']:
        """
        checks if station only has one unused connection

        pre: 
            station is Station object

        returns:
            unused connection
            False if there is not 1 unused connection      
        """
        assert isinstance(
            type[Station], station), "station should be a Station object"

        connections = [
            connection for connection in station.connections if connection in state.unused_connections]

        if len(connections) == 1:
            return connections[0]
        return False

    def get_connection_suggestions(self, state: 'State') -> list['Connection']:
        """
        gives all connections that connect to a station that only has that connection left, so this station can become the first in a route

        returns:
            list of all connection suggestions
            Beware! Can also return an empty list!
        """
        connection_suggestions = [self.station_has_one_unused_connection(
            station) for station in state.stations if self.station_has_one_unused_connection(station)]

        return connection_suggestions

    #### NO RETURN CONNECTION HEURISTIC ####
    def _connection_used_consecutively(self, connection: 'Connection', connection_list: list['Connection']) -> int:
        """
        checks how many times a connection is used consecutively

        returns:
            number of times a connection is in the list consecutively
        """
        result = 0
        for route_connection in connection_list:
            if connection == route_connection:
                result += 1
            else:
                break
        return result

    def connection_used_before_end(self, connection: 'Connection', route: 'Route'):
        """
        checks how many times a connection is used directly before the end of a route

        pre:
            connection is a Connection object
            route is a Route object

        returns:
            number of times a connection is used at end of route
        """
        assert isinstance(
            Connection, connection), f"connection should be a Connection object, is a {type(connection)} (value: {connection})"
        assert isinstance(
            Route, route), f"route should be a Route object, is a {type(route)} (value: {route})"
        return self._connection_used_consecutively(connection, reversed(route.route_connections))

    def connection_used_after_start(self, connection: 'Connection', route: 'Route'):
        """
        checks how many times a connection is used directly after the start of a route

        pre:
            connection is a Connection object
            route is a Route object

        returns:
            number of times a connection is used at end of route
        """
        assert isinstance(
            Connection, connection), f"connection should be a Connection object, is a {type(connection)} (value: {connection})"
        assert isinstance(
            Route, route), f"route should be a Route object, is a {type(route)} (value: {route})"
        return self._connection_used_consecutively(connection, route.route_connections)

    def get_forbidden_connection_start(self, route: 'Route', station: 'Station') -> Union['Connection', None]:
        """
        gives connection that is used too much right after the start station

        pre: 
            station is Station object
        """
        assert isinstance(
            Route, route), f"route should be a Route object, is a {type(route)} (value: {route})"

        assert isinstance(
            Station, station), f"station should be a station object, is a {type(station)} (value: {station})"

        for connection in station.connections:
            if self.max_connection_returns and self.connection_used_after_start(connection, route) >= self.max_connection_returns:
                return connection

    def get_forbidden_connection_end(self, route: 'Route', station: 'Station') -> Union['Connection', None]:
        """
        gives connection that is used too much right before the end station

        pre: 
            station is Station object

        returns:
            forbidden connection
            None if there is no forbidden connection
        """
        assert isinstance(
            Route, route), f"route should be a Route object, is a {type(route)} (value: {route})"

        assert isinstance(
            Station, station), f"station should be a station object, is a {type(station)} (value: {station})"

        for connection in station.connections:
            if self.max_connection_returns and self.connection_used_before_end(connection, route) >= self.max_connection_returns:
                return connection

    #### MINUS POINTS MULTIPLE USE CONNECTION HEURISTIC ####
    def _get_points_multiple_use_connection(self, connection: 'Connection'):
        minus_points: int = 0
        for i in range(1, connection.used):
            minus_points += int(connection.distance) * i
        return minus_points

    def get_points_multiple_use_connections(self, state: 'State') -> int:
        """
        gives the number of points a state gets for multiple use of connections in a state.

        pre:
            state is a State object

        returns:
            negative number, indicating minus points
        """
        assert isinstance(
            State, state), f"state should be a State object, is a {type(state)} (value: {state})"

        if not self.heuristic_number_connections:
            return 0

        minus_points = 0
        for connection in state.connections:
            minus_points -= self._get_points_multiple_use_connection(
                connection)
        return minus_points

    #### ROUTE MAXIMALISATION HEURISTIC ####
    def _minus_points_route_maximalisation(self, route: 'Route', timeframe: int) -> int:
        """
        gives minus points if the route is not maximalised

        pre:
            route is a Route object

        returns:
            negative integer, indicating minus points

        """
        assert isinstance(
            Route, route), f"route should be a Route object, is a {type(route)} (value: {route})"
        return timeframe - route.total_time

    def minus_points_routes_maximalisation(self, state: 'State'):
        """
        gives minus points of route maximalisation heuristic

        pre:
            state is a State object

        returns:
            negative integer, indicating minus points
        """
        assert isinstance(
            State, state), f"state should be a State object, is a {type(state)} (value: {state})"
        if not self.heuristic_route_maximalisation:
            return 0

        minus_points = 0
        for route in state.routes:
            minus_points += self._minus_points_route_maximalisation(
                route, state.time_frame)
        return minus_points

    #### DIFFICTULT CONNECTIONS HEURISTIC ####
    def connection_is_difficult(self, connection: 'Connection') -> bool:
        """
        Identifies if a connection is difficult.
        A connection is difficult if the numbers of connections at both of the stations are odd

        pre: 
            connection is Connection object

        post:
            True if connection is difficult
        """
        assert isinstance(
            Connection, connection), f"connection should be a Connection object, is a {type(connection)} (value: {connection})"
        check_station_1 = len(connection.station_1.connections) % 2
        check_station_2 = len(connection.station_2.connections) % 2
        return not (check_station_1 and check_station_2)

    def identify_difficult_connections(self, state) -> set:
        """
        Gives a list of difficult connections

        pre:
            state is a State object
        """
        assert isinstance(
            State, state), f"state should be a State object, is a {type(state)} (value: {state})"
        difficult_connections = (
            connection for connection in state.connection if self.connection_is_difficult(connection))
        return difficult_connections

    def difficult_connections_used(self, state):
        """
        Gives bonus points for used difficult connections

        pre:
            state should be a State object

        returns:
            a positive integer, indicating bonus points
        """
        assert isinstance(
            State, state), f"state should be a State object, is a {type(state)} (value: {state})"

        if not self.heuristic_difficult_connections:
            return 0

        difficult_connections = self.identify_difficult_connections(state)

        bonus_points = 0
        for connection in state.used_connections:
            if connection in difficult_connections:
                bonus_points += connection.distance
        return bonus_points
