#! /usr/bin/env python2

# Basic Test Client for MechMania 19
# Copyright (c) 2013 Association for Computing Machinery at the University
# of Illinois, Urbana-Champaign. Inherits license from main MechMania 19 code.

import json
import logging
import random
import socket
import string
import numpy as np

from ship import Ship

# TODO (competitors): This is arbitrary but should be large enough
MAX_BUFFER = 65565

# SERVER RESPONSE CODES
NOTIFY_RESPONSE_CODE = 100;
SUCCESS_RESPONSE_CODE = 200;
WARNING_RESPONSE_CODE = 201;
ERROR_RESPONSE_CODE = 400;
INTERRUPT_RESPONSE_CODE = 418;
WIN_RESPONSE_CODE = 9001;
LOSS_RESPONSE_CODE = -1;

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
        self._send_payload(payload)

        # Step 3: Process the reply
        reply = self._get_reply()
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
            payload['shipActions'] = []

            # Step 2: Transmit turn payload and wait for the reply
            self._send_payload(payload)

            # Step 3: Wait for turn response and process it
            reply = self._get_reply()
            self._process_reply(reply)

            # Step 4: Wait for turn notification and process it
            reply = self._get_reply()
            self._process_reply(reply)

    def _send_payload(self, payload):
        """
        Send a payload to the server

        payload -- Payload dictionary to send out.
        """
        # logging.debug("Payload: %s", json.dumps(payload))
        # Send this information to the server
        self.sock.sendall(json.dumps(payload) + '\n')

    def _get_reply(self):
        return json.loads(self.sock.recv(MAX_BUFFER))

    def _process_reply(self, reply, setup=False):
        """
        Process a reply from the server.

        This method could use a lot more intelligence. As is, it ignores almost
        everything in the reply payload.

        reply -- The reply dictionary to process
        setup (default=False) -- Whether this is a new server connection
        """
        if reply['error']:
            logging.warn("Dummy: Problem with last transmit: %s", reply['error'])
            return
        if setup:
            self.token = reply['playerToken']
        self.resources = reply['resources']

        if reply['ships']:
            for ship in reply['ships']:
                # logging.debug("ID: %d\tt: %c\tx: %d\t y: %d", ship['ID'],
                #         ship['type'], ship['xCoord'], ship['yCoord'])
                pass

def main():
    establish_logger(logging.DEBUG)
    ships = generate_ships()

    # TODO (competitors): Change the client name, update ship positions, etc.
    client = Client("localhost", 6969, "dummy")
    client.connect()
    client.prep_game(ships)
    # TODO (competitors): make your game do something now!
    client.attack_forever()


def establish_logger(loglevel):
    logging.basicConfig(format="%(asctime)s %(message)s",
            datefmt='%m/%d/%Y %I:%M:%S %p', level=loglevel)

def generate_ships():
    """Generate ships strategically"""
    ships = []

    # Grid for placing ships
    ship_grid = np.zeros(100 * 100).reshape((100, 100))

    # Spacing to leave between ships
    buf = 4

    def get_free_position(length):
        while True:
            x, y = (np.random.randint(100 - length + 1),
                    np.random.randint(100 - length + 1))
            orient = ['H', 'V'][np.random.randint(2)]

            if orient == 'H':
                x_min = max(x - buf, 0)
                x_max = min(x + length + buf, 100)
                y_min = max(y - buf, 0)
                y_max = min(y + buf, 100)
                if np.all(ship_grid[y_min:y_max][:, x_min:x_max] == 0):
                    ship_grid[y][x:(x+length)] = 1
                    return (x, y, orient)
            else:   # orient == 'V'
                x_min = max(x - buf, 0)
                x_max = min(x + buf, 100)
                y_min = max(y - buf, 0)
                y_max = min(y + length + buf, 100)
                if np.all(ship_grid[y_min:y_max][:, x_min:x_max] == 0):
                    ship_grid[y:(y+length)][:, x] = 1
                    return (x, y, orient)

    # Place main ship
    x, y, orient = get_free_position(5)
    ships.append(Ship("M",x, y, orient))

    # Number of other ships
    num_ships = 18
    num_destroyer = 6
    num_pilot = num_ships - num_destroyer

    for destroyer in range(num_destroyer):
        x, y, orient = get_free_position(4)
        ships.append(Ship("D",x, y, orient))

    for pilot in range(num_pilot):
        x, y, orient = get_free_position(2)
        ships.append(Ship("P",x, y, orient))

    return ships

if __name__ == "__main__":
    main()
