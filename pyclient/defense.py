import logging

class RunOnDetection(object):
    def __init__(self, ships):
        self.ship_to_move = None

    def update(self, ships, hits, scans, my_map):
        # find main ship first if it is hit or scanned
        self.ship_to_move = None
        main_ship = locate_main_ship(ships)
        for hit in hits:
            if locate_ship_by_location(ships, (hit["yCoord"], hit["xCoord"])) is main_ship:
                self.ship_to_move = main_ship

        for scan in scans:
            if locate_ship_by_ID(ships, scan["shipID"]) is main_ship:
                self.ship_to_move = main_ship

        # else move hit ship first
        for hit in hits:
            ship = locate_ship_by_location(ships, (hit["yCoord"], hit["xCoord"]))
            if ship is not None and self.ship_to_move is None:
                self.ship_to_move = ship

        # in the end, move scanned ship
        for scan in scans:
            ship = locate_ship_by_ID(ships, scan["shipID"])
            if ship is not None and self.ship_to_move is None:
                self.ship_to_move = ship

        # predict danger
        if "time space correlation" in my_map.enemy_profile:
            main_ship_danger = 0
            for y, x in main_ship.occupied_cells():
                main_ship_danger += my_map[y][x].danger
            # logging.debug("Main Ship Danger: %d", main_ship_danger)
            if main_ship_danger >= (main_ship.health / 4) and self.ship_to_move is None:
                self.ship_to_move = main_ship
                # logging.debug("Move main ship")

            for ship in ships:
                danger_to_ship = 0
                for y, x in ship.occupied_cells():
                    danger_to_ship += my_map[y][x].danger
                if danger_to_ship >= ship.health and self.ship_to_move is None:
                    self.ship_to_move = ship

        # if main ship killer, just randomly move main ship at a low probability
        if "mainship killer" in my_map.enemy_profile:
            import random
            if random.random() < 0.01 and self.ship_to_move is None:
                self.ship_to_move = main_ship

        return self.ship_to_move is not None

    def job_assign(self, ships, my_map):
        for ship in ships:
            if ship is self.ship_to_move:
                move_location = my_map.find_best_location(ship.get_ship_length())
                ship.move(*move_location)
                return 50 * ship.get_ship_length()
        return 0

def locate_main_ship(ships):
    for ship in ships:
        if ship.get_ship_type() == "M":
            return ship

def locate_ship_by_ID(ships, ID):
    for ship in ships:
        if ship.ID == ID:
            return ship

def locate_ship_by_location(ships, loc):
    for ship in ships:
        if loc in ship.occupied_cells():
            return ship

