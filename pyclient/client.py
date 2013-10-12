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

from enemypdf import EnemyPDF
from dangergrid import DangerGrid
from AttackItem import AttackItem
from ReplayStack import ReplayStack

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

# MAP CONSTANTS
MIN_X = 0
MIN_Y = 0
MAX_X = 99
MAX_Y = 99

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

        self.enemypdf = EnemyPDF()
        self.danger_grid = DangerGrid()
        self.last_scan = (0,0)
        self.last_special = None
        self.attack_queue = []
        self.burst_queue = []

        # data for replay attacks
        self.replay_rate = 0.03
        self.replay_stack = ReplayStack(10)
        self.replay_check_list = []

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


            logging.debug("===PlayerRequest===")

            # Step 1: Construct a turn payload

            if(self.defense.update(self.ships, reply["hitReport"], reply["pingReport"])):
                self.last_special = "M"
            self.resources -= self.defense.job_assign(self.ships, self.my_map)

            # self.strat.job_assign(self.ships, 6)

            available_ships = [x for x in self.ships if x.has_work() == False]
            mainship = [x for x in self.ships if x.get_ship_type() == 'M'][0]
            destroyers = [x for x in available_ships if x.get_ship_type() == 'D']
            pilots = [x for x in available_ships if x.get_ship_type() == 'P']

            # always make sure there is enough resource to move main ship next round
            if (len(pilots) < 5):
                self.resources -= (5 - len(pilots)) * 50

            # Process a burst request
            if len(self.burst_queue) > 0:
                if len(destroyers) > 0:
                    if self.last_special == None and self.resources >= 250:
                        x,y = self.burst_queue.pop(0)
                        destroyer = destroyers.pop(0)
                        destroyer.burst_fire(x,y)
                        self.last_special = "B"
                        self.resources -= 250
            elif self.resources > 2500:
                if len(destroyers) > 0:
                    if self.last_special == None and self.resources >= 250:
                        x,y = self.enemypdf.next_hit()
                        destroyer = destroyers.pop(0)
                        destroyer.burst_fire(x,y)
                        self.last_special = "B"
                        self.resources -= 250

            # Process a scan request
            if self.last_special == None:
                if len(pilots) > 0 and self.resources >= 110:
                    x,y = self.enemypdf.next_scan()
                    pilot = pilots.pop(0)
                    pilot.sonar(x,y)
                    # logging.debug("Setting last_special")
                    # logging.debug("Next scan: (%s)",(x,y))
                    self.last_special = "S"
                    self.last_scan = (x,y)
                    self.resources -= 110

            # Process attack request
            if mainship.action == "N" and self.resources >= 50:
                destroyers.append(mainship)
                self.resources -= 50

            is_replay = np.random.random() < self.replay_rate
            if is_replay:
                logging.debug(self.replay_stack)
                while self.replay_stack.size() > 0:
                    attack_item = self.replay_stack.pop()
                    x,y = attack_item.coord
                    while len(destroyers) > 0 and attack_item.nAttacks > 0 and self.resources >= 50:
                        d = destroyers.pop(0)
                        d.fire(x,y)
                        self.replay_check_list.append(AttackItem((x,y),1))
                        self.resources -= 50
                        attack_item.nAttacks -= 1

                    # ran out of destroyers
                    if len(destroyers) == 0 or self.resources < 50:
                        # didn't get to finish the attack
                        if attack_item.nAttacks > 0:
                            self.replay_stack.push(attack_item)
                        break
            else:
                while len(self.attack_queue) > 0:
                    attack_item = self.attack_queue.pop(0)
                    x,y = attack_item.coord
                    while len(destroyers) > 0 and attack_item.nAttacks > 0 and self.resources >= 50:
                        d = destroyers.pop(0)
                        d.fire(x,y)
                        self.resources -= 50
                        attack_item.nAttacks -= 1

                    # ran out of destroyers
                    if len(destroyers) == 0 or self.resources < 50:
                        # didn't get to finish the attack
                        if attack_item.nAttacks > 0:
                            self.attack_queue.insert(0,attack_item)
                        break

            # if is_replay:
            #     logging.debug("replay attack! %%%f",self.replay_rate)
            #     logging.debug(self.replay_check_list)


            # if we have leftover destroyers, attack most probable point
            numPossibleAttacks = min(len(destroyers),self.resources/50)
            start_time = time.time()
            coords = self.enemypdf.next_hits(numPossibleAttacks)
            end_time = time.time()
            logging.debug("Elapsed time was %g seconds" % (end_time - start_time))
            for i in range(numPossibleAttacks):
                d = destroyers.pop(0)
                x,y = coords[i]
                d.fire(x,y)
                self.resources -= 50


            # send payload
            payload = {'playerToken': self.token}
            shipactions = map(lambda x: x.getActionJSON(), self.ships)
            payload['shipActions'] = shipactions

            # Step 2: Transmit turn payload and wait for the reply
            logging.info("Sending turn %d...",turn)
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
        # logging.debug("Payload: %s", json.dumps(payload))
        # Send this information to the server
        self.sock.sendall(json.dumps(payload) + '\n')

    def _get_reply(self):
        reply = self.sock.recv(MAX_BUFFER)
        # logging.debug("Reply: %s\n",reply)
        return json.loads(reply)

    def _process_notification(self, reply, turn, setup=False):
        """
        Process a reply from the server.

        reply -- The reply dictionary to process
        setup (default=False) -- Whether this is a new server connection
        """
        logging.debug("===ServerNotification===")
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
        # logging.debug("Response code: %d", reply['responseCode'])
        assert(reply['responseCode']==100)

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
        self.danger_grid.update(turn, self.my_map)
        logging.debug("Max Danger: %g", np.max(self.danger_grid.grid))
        logging.debug("MainShip Danger: %g",
                self.danger_grid.get_danger(self.ships[0]))

        # reset variables
        # logging.debug("Resetting last_special")
        self.last_special = None

    def _process_reply(self, reply, setup=False):
        """
        Process a reply from the server.

        reply -- The reply dictionary to process
        setup (default=False) -- Whether this is a new server connection
        """
        logging.debug("===ServerResponse===")
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
        # logging.debug("Response code: %d", reply['responseCode'])

        # Resources
        if reply['resources']:
            self.resources = reply['resources']

        # Ships
        if reply['ships']:
            for ship in reply['ships']:
                # logging.debug("ID: %d\tt: %c\tx: %d\t y: %d", ship['ID'],
                #         ship['type'], ship['xCoord'], ship['yCoord'])
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

        # update enemy pdf and queue attacks
        nAttacks = 1 # unit number of attacks per tile
        if reply['hitReport']:
            for hit in reply['hitReport']:
                x = hit['xCoord']
                y = hit['yCoord']
                # Check if it was replay attack
                is_replay = False
                if sum(cq.coord == (x,y) for cq in self.replay_check_list) > 0:
                    is_replay = True
                    self.replay_check_list.remove([cq for cq in self.replay_check_list if cq.coord == (x,y)][0])
                else:
                    self.replay_stack.push(AttackItem((x,y),6))

                # if hit, hit again until we miss
                if hit['hit'] == True:
                    self.attack_queue.insert(0,AttackItem((x,y),nAttacks))
                    if is_replay:
                        self.replay_rate *= 3
                # if not hit, we know the tile is clear; update pdf
                else:
                    self.enemypdf.decrease(x,y)
                    # add the attack to the replay queue for surprise attacks
                    if is_replay:
                        self.replay_rate /= 2


        # logging.debug(self.attack_queue)

        if reply['pingReport']:
            for ping in reply['pingReport']:
                x,y = self.last_scan
                if ping['distance'] == 0:
                    # priority attack at the coordinate
                    self.attack_queue.insert(0,AttackItem((x,y),6))
                if ping['distance'] <= 1:
                    # burst center and attack around it
                    self.burst_queue.insert(0,(x,y))
                    if x-1 >= MIN_X:
                        if y-1 >= MIN_Y:
                            self.attack_queue.append(AttackItem((x-1,y-1),nAttacks))
                        if y+1 <= MAX_Y:
                            self.attack_queue.append(AttackItem((x-1,y+1),nAttacks))
                    if x+1 <= MAX_X:
                        if y-1 >= MIN_Y:
                            self.attack_queue.append(AttackItem((x+1,y-1),nAttacks))
                        if y+1 <= MAX_Y:
                            self.attack_queue.append(AttackItem((x+1,y+1),nAttacks))
                if ping['distance'] <= 2:
                    # attack around the outer ring
                    for i in range(max(x-2,MIN_X),min(x+2,MAX_X)):
                        for j in range(max(y-2,MIN_Y),min(y+2,MAX_Y)):
                            if (i==max(x-2,MIN_X)) or (i==min(x+2,MAX_X)) \
                                or (j==max(y-2,MIN_Y)) or (j==min(y+2,MAX_Y)):
                                if i%2==0 and j%2==0:
                                    self.attack_queue.append(AttackItem((i,j),nAttacks))

        # redistribute the enemy pdf
        # logging.debug("Checking last_special: %s",str(self.last_special))
        if self.last_special == "S":
            # logging.debug("scan_decrease")
            x,y = self.last_scan
            self.enemypdf.scan_decrease(x,y)

        self.enemypdf.spread_mass()

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
    ship_grid = np.zeros((100, 100))

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
    ships.append(MainShip(x, y, orient))

    # Number of other ships
    num_ships = 18
    num_destroyer = 8
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
