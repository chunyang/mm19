#! /usr/bin/env python2

# Basic Test Client for MechMania 19
# Copyright (c) 2013 Association for Computing Machinery at the University
# of Illinois, Urbana-Champaign. Inherits license from main MechMania 19 code.

import json
import logging
import random
import socket
import string
import time

import numpy as np
from ship import *
from Map import Map
from bomber import BomberStrategy
from defense import RunOnDetection

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
        self.ships = []

        self.my_map = Map(100, 100)
        self.attack_report = []

        self.strat = BomberStrategy(0,0,100,100)
        self.defense = RunOnDetection(self.ships)

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
        payload['mainShip'] = shiparray[0].getInitJSON()
        payload['ships'] = [ship.getInitJSON() for ship in shiparray[1:]]

        # Step 2: Transmit the payload and receive the reply
        logging.info("Transmitting start package to server...")
        self._send_payload(payload)


    def loop_round(self):
        """
        This method does nothing remotely reasonable.

        If you want a picture of the future, imagine a boot stomping on a
        nautical battleground--forever.
        """
        turn = 0
        self.alive = True
        while(self.alive):
            # Step 0: Wait for turn notification and process it
            reply = self._get_reply()
            self._process_notification(reply, turn)

            # Step 1: Construct a turn payload


            self.defense.update(self.ships, reply["hitReport"], reply["pingReport"])
            self.defense.job_assign(self.ships, self.my_map)

            self.strat.job_assign(self.ships, 6)

            # send payload
            payload = {'playerToken': self.token}
            shipactions = map(lambda x: x.getActionJSON(), self.ships)
            payload['shipActions'] = shipactions

            # Step 2: Transmit turn payload and wait for the reply
            logging.info("Sending turn...")
            self._send_payload(payload)

            # Step 3: Wait for turn response and process it
            reply = self._get_reply()
            self._process_reply(reply)

            turn += 1

    def _send_payload(self, payload):
        """
        Send a payload to the server

        payload -- Payload dictionary to send out.
        """
        logging.debug("Payload: %s", json.dumps(payload))
        # Send this information to the server
        self.sock.sendall(json.dumps(payload) + '\n')

    def _get_reply(self):
        reply = self.sock.recv(MAX_BUFFER)
        logging.debug("Reply: %s\n",reply)
        return json.loads(reply)

    def _process_notification(self, reply, turn, setup=False):
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
            self.ships = []
            for ship in reply['ships']:
                ship_type = ship['type']
                del ship['type']
                if ship_type == "M":
                    self.ships.append(MainShip(**ship))
                elif ship_type == "P":
                    self.ships.append(Pilot(**ship))
                elif ship_type == "D":
                    self.ships.append(Destroyer(**ship))
                else:
                    pass

        # update Map
        self.my_map.update_ship_location(self.ships)
        self.my_map.update_cell_history(turn, reply, self.ships)

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
                logging.debug("ID: %d\tt: %c\tx: %d\t y: %d", ship['ID'],
                        ship['type'], ship['xCoord'], ship['yCoord'])
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

    # TODO (competitors): Change the client name, update ship positions, etc.
    client = Client("localhost", 6969, "Cache Me if You Can")
    client.ships = generate_ships()
    #time.sleep(2)
    client.connect()
    client.prep_game(client.ships)
    # TODO (competitors): make your game do something now!
    client.loop_round()


def establish_logger(loglevel):
    logging.basicConfig(format="%(asctime)s %(message)s",
            datefmt='%I:%M:%S %p', level=loglevel)
            # datefmt='%m/%d/%Y %I:%M:%S %p', level=loglevel)
    logging.debug("Logger initialized")

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
                x_min = x - buf
                x_max = x + length + buf
                y_min = y - buf
                y_max = y + buf
                if np.all(ship_grid[y_min:y_max][:, x_min:x_max] == 0):
                    ship_grid[y][x:(x+length)] = 1
                    return (x, y, orient)
            else:   # orient == 'V'
                x_min = x - buf
                x_max = x + buf
                y_min = y - buf
                y_max = y + length + buf
                if np.all(ship_grid[y_min:y_max][:, x_min:x_max] == 0):
                    ship_grid[y:(y+length)][:, x] = 1
                    return (x, y, orient)

    # Place main ship
    x, y, orient = get_free_position(5)
    ships.append(MainShip(x, y, orient))

    # Number of other ships
    num_ships = 18
    num_destroyer = 6
    num_pilot = num_ships - num_destroyer

    for destroyer in range(num_destroyer):
        x, y, orient = get_free_position(4)
        ships.append(Destroyer(x, y, orient))

    for pilot in range(num_pilot):
        x, y, orient = get_free_position(2)
        ships.append(Pilot(x, y, orient))

    return ships

if __name__ == "__main__":
    main()
