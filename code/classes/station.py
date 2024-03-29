from connection import Connection


class Station():

    def __init__(self: 'Station', name: str, y: float, x: float) -> None:
        """
        initializes Station-class  

        pre: 
            name-input is a string
            x- and y-input is a float

        post:
            Station-object is created
        """

        assert isinstance(
            name, str), 'First argument (name) should be a string'

        assert isinstance(x, float) and isinstance(
            y, float), 'Second (y) and third argument (x) should both be floats'

        self.name = name
        self.x = x
        self.y = y
        self.connections: list['Connection'] = []

    def __str__(self):
        return f"Station {self.name}"

    def add_connection(self: 'Station', connection: 'Connection') -> None:
        """
        adds a connection to station  

        pre: 
            connection_input is a connection-object

        post:
            connection is added to self.connection
        """
        assert isinstance(
            connection, Connection), 'Input should be a Connection-object'

        self.connections.append(connection)

    def has_connection(self, connection: 'Connection') -> bool:
        """
        checks if a given connection is connected to the current station   

        pre: 
            connection_input is a connection-object

        returns:
            boolean stating if given connection is within self.connections
        """
        assert isinstance(
            connection, Connection), 'Input should be an Connection-object'

        return connection in self.connections

    def get_connections(self) -> list['Connection']:
        """
        returns all the connections from this station

        returns: 
            a list with all the connections
        """

        return self.connections
