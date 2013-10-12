#! /usr/bin/env python2

# Basic Test Client for MechMania 19
# Copyright (c) 2013 Association for Computing Machinery at the University
# of Illinois, Urbana-Champaign. Inherits license from main MechMania 19 code.

import json
import logging
import random
import socket

from ship import Ship

# TODO (competitors): This is arbitrary but should be large enough
MAX_BUFFER = 65565

class Client(object):
    """
    A class for managing the client's connection.

    TODO (competitors): You should add the API functions you need here. You can
    remove the inheritance from object if "new style" classes freak you out, it
    isn't important.
    """

    def require_connection(func):
        """
        This is a decorator to wrap a function to require a server connection.

        func -- A Client class function with self as the first argument.
        """
        def wrapped(self, *args):
            if self.sock == None:
                logging.error("Connection not established")
            else:
                return func(self, *args)

        return wrapped

    def __init__(self, host, port, name):
        """
        Initialize a client for interacting with the game.

        host -- The hostname of the server to connect
                (e.g.  "example.com")
        port -- The port to connect on (e.g. 6969)
        name -- Unique name of the client connecting
        """
        self.host = host
        self.port = port
        self.name = name
        self.sock = None
        self.token = ""
        self.resources = 0

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        logging.info("Connection target is %s:%d", self.host, self.port)
        self.sock.connect((self.host, self.port))
        logging.info("Connection established")

    @require_connection
    def prep_game(self, shiparray):
        """
        Handle all the pre-work for game setup.

        This function won't return until the server is connected and the game
        begins. There's no real need to call it asynchronously, as you can't
        actually do anything until the server is connected.

        shiparray -- The initial positions for all ships
        """

        # Step 1: Set up the initial data payload
        payload = {'playerName': self.name}
        # TODO (competitors): This is really ugly because the main ship is
        # special cased. I'm sorry. Feel free to fix.
        payload['mainShip'] = shiparray[0].getJSON()
        payload['ships'] = [ship.getJSON() for ship in shiparray[1:]]

        # Step 2: Transmit the payload and receive the reply
        logging.info("Transmitting start package to server...")
        reply = self._send_payload(payload)

        # Step 3: Process the reply
        self._process_reply(reply, setup=True)

    def attack_forever(self):
        """
        This method does nothing remotely reasonable.

        If you want a picture of the future, imagine a boot stomping on a
        nautical battleground--forever.
        """
        self.alive = True
        while(self.alive):
            # Step 1: Construct a turn payload
            payload = {'playerToken': self.token}
            # TODO (competitors): You might want to actually keep track of which
            # ships are which
            shipactions = [{'ID': shipid, 'actionID': "F",
                'actionX': random.randint(0,99),
                'actionY': random.randint(0,99),
                'actionExtra': 0} for shipid in range(5)]
            payload['shipActions'] = shipactions

            # Step 2: Transmit turn payload and wait for the reply
            logging.info("Sending turn...")
            reply = self._send_payload(payload)

            # Step 3: Process the reply
            self._process_reply(reply)

    def _send_payload(self, payload):
        """
        Send a payload to the server and return the deserialized reply.

        payload -- Payload dictionary to send out.

        Returns a dictionary with the reply data.
        """
        logging.debug("Payload: %s", json.dumps(payload))
        # Send this information to the server
        self.sock.sendall(json.dumps(payload) + '\n')
        return json.loads(self.sock.recv(MAX_BUFFER))

    def _process_reply(self, reply, setup=False):
        """
        Process a reply from the server.

        reply -- The reply dictionary to process
        setup (default=False) -- Whether this is a new server connection
        """
        if setup:
            self.token = reply['playerToken']

        # Error
        if reply['error']:
            logging.warn('Problems with last transmit:')
            for error in reply['error']:
                logging.warn("    %s", error)
                return
            logging.warn('End errors')

        # Response code
        logging.debug("Response code: %d", reply['responseCode'])

        # Resources
        if reply['resources']:
            self.resources = reply['resources']

        # Ships
        if reply['ships']:
            for ship in reply['ships']:
                # ship['health']
                # ship['ID']
                # ship['type']
                # ship['xCoord']
                # ship['yCoord']
                # ship['orientation']
                pass

        # Ship action results
        if reply['shipActionResults']:
            for action in reply['shipActionResults']:
                # action['ID']
                # action['result']
                pass

        # Hit report
        if reply['hitReport']:
            for hit in reply['hitReport']:
                # hit['xCoord']
                # hit['yCoord']
                # hit['hit']
                pass

        # Ping report
        if reply['pingReport']:
            for ping in reply['pingReport']:
                # ping['shipID']
                # ping['distance']
                pass

def main():
    establish_logger(logging.DEBUG)
    ships = generate_ships()

    # TODO (competitors): Change the client name, update ship positions, etc.
    client = Client("localhost", 6969, "Cache Me if You Can")
    client.connect()
    client.prep_game(ships)
    # TODO (competitors): make your game do something now!
    client.attack_forever()


def establish_logger(loglevel):
    logging.basicConfig(format="%(asctime)s %(message)s",
            datefmt='%I:%M:%S %p', level=loglevel)
            # datefmt='%m/%d/%Y %I:%M:%S %p', level=loglevel)
    logging.debug("Logger initialized")

def generate_ships():
    """This generates ships non-strategically for testing purposes."""
    # Let's get some ships
    ships = []
    ships.append(Ship("M", 5, 5, "H"))
    ships.append(Ship.random_ship("D"))
    ships.append(Ship.random_ship("D"))
    ships.append(Ship.random_ship("P"))
    ships.append(Ship.random_ship("P"))
    return ships

if __name__ == "__main__":
    main()
