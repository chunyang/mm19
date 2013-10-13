#!/usr/bin/env python2

import sys

import numpy as np
from ship import *
from client import generate_ships

if __name__ == "__main__":
    grid = np.zeros(100*100).reshape((100, 100))

    ships = generate_ships()
    for ship in ships:
        if ship.get_ship_type() == 'M':
            ship_type = 1
            ship_length = MainShip.get_ship_length()
        elif ship.get_ship_type() == 'D':
            ship_type = 2
            ship_length = Destroyer.get_ship_length()
        else:
            ship_type = 3
            ship_length = Pilot.get_ship_length()

        if ship.orient == 'H':
            grid[ship.y][ship.x:(ship.x+ship_length)] = ship_type
        else:
            grid[ship.y:(ship.y+ship_length)][:, ship.x] = ship_type

    # Print map
    # for y in range(100):
    #     for x in range(100):
    #         if grid[y][x] == 0:
    #             sys.stdout.write('.')
    #         elif grid[y][x] == 1:
    #             sys.stdout.write('M')
    #         elif grid[y][x] == 2:
    #             sys.stdout.write('D')
    #         elif grid[y][x] == 3:
    #             sys.stdout.write('P')
    #     print ''
