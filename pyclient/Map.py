import numpy as np

class Cell(object):
    """
    Map Cell
    """
    def __init__(self):
        self.ship = False
        self.fired = []
        self.scanned = []


class Map(object):
    """
    Map Class
    2D array, Map[y][x]
    """
    def __init__(self, xdim, ydim):
        self.xdim = xdim
        self.ydim = ydim
        self.max_fire = 0
        self.fire_rate = []
        self.fire_histo = []
        self.fire_scatter = []
        self.enemy_profile = set()
        self.enemy_profile_detail = dict()
        self.__list__ = [ [Cell() for i in xrange(xdim)] for j in xrange(ydim) ]

    def __getitem__(self, key):
        return self.__list__[key]

    def update_ship_location(self, ShipArray):
        # wipe the board first
        for y in self.__list__:
            for x in y:
                x.ship = False

        # update with current ship location
        map(self.add_ship, ShipArray)


    def add_ship(self, ship):
        if (self.test_add_ship(ship)):
            map(self.set_location_occupy, ship.occupied_cells())
        else:
            raise ValueError("Ship Overlap")

    def set_location_occupy(self, loc):
        y = loc[0]
        x = loc[1]
        self.__list__[y][x].ship = True

    def test_add_ship(self, ship):
        return all(map(self.test_location_occupy, ship.occupied_cells()))

    def test_location_occupy(self, loc):
        return not self.__list__[loc[0]][loc[1]].ship

    def update_cell_history(self, turn, reply, ShipArray):
        self.charactorize_enemy(turn, reply)
        for hit in reply["hitReport"]:
            self.__list__[hit["yCoord"]][hit["xCoord"]].fired.append((turn, hit["hit"]));
        for scan in reply["pingReport"]:
            for ship in ShipArray:
                if ship.ID == scan["shipID"]:
                    map(lambda x: self.__list__[x[0]][x[1]].scanned.append(turn), ship.occupied_cells())

    def find_best_location(self, length):
        buf = 4
        while True:
            x, y = (np.random.randint(100 - length + 1),
                    np.random.randint(100 - length + 1))
            orient = ['H', 'V'][np.random.randint(2)]
            found = True
            if orient == 'H':
                x_min = max(x - buf, 0)
                x_max = min(x + length + buf, 100)
                y_min = max(y - buf, 0)
                y_max = min(y + buf, 100)
            else:   # orient == 'V'
                x_min = max(x - buf, 0)
                x_max = min(x + buf, 100)
                y_min = max(y - buf, 0)
                y_max = min(y + length + buf, 100)

            for yy in xrange(y_min, y_max):
                for xx in xrange(x_min, x_max):
                    if self.__list__[yy][xx].ship:
                        found = False

            if found:
                return (x, y, orient)

    def charactorize_enemy(self, turn, reply):
        # fire rate
        fire_rate = len(reply["hitReport"])
        self.max_fire = max(fire_rate, self.max_fire)
        self.fire_rate.append(fire_rate)
        fire_histo = dict()
        # max fire in one location in a single round
        if fire_rate != 0:
            for fire in reply["hitReport"]:
                try:
                    histo = fire_histo[frozenset(fire)]
                except KeyError:
                    fire_histo[frozenset(fire)] = 1
                else:
                    fire_histo[frozenset(fire)] = histo + 1
            self.fire_histo.append(max(fire_histo.values()))
        else:
            self.fire_histo.append(0)
        # repeat hit
        habitual_offender = False
        for hit in reply["hitReport"]:
            if len(self.__list__[hit["yCoord"]][hit["xCoord"]].fired) != 0:
                habitual_offender = True

        # time space correlation
        strong_ts_correlation = False
        for hit in reply["hitReport"]:
            xCoord = hit["xCoord"]
            yCoord = hit["yCoord"]
            x_min = max(xCoord - 5, 0)
            x_max = min(xCoord + 5, 100)
            y_min = max(yCoord - 5, 0)
            y_max = min(yCoord + 5, 100)
            turn_old = turn - 10
            for y in xrange(y_max - y_min):
                for x in xrange(x_max - x_min):
                    fired = self.__list__[y+y_min][x+x_min].fired
                    if len(fired) != 0 and fired[-1][0] >= turn_old:
                        strong_ts_correlation = True

        # hit scan correlation
        strong_hs_correlation = False
        for hit in reply["hitReport"]:
            xCoord = hit["xCoord"]
            yCoord = hit["yCoord"]
            x_min = max(xCoord - 5, 0)
            x_max = min(xCoord + 5, 100)
            y_min = max(yCoord - 5, 0)
            y_max = min(yCoord + 5, 100)
            turn_old = turn - 2
            for y in xrange(y_max - y_min):
                for x in xrange(x_max - x_min):
                    scanned = self.__list__[y+y_min][x+x_min].scanned
                    if len(scanned) != 0 and scanned[-1] >= turn_old:
                        strong_hs_correlation = True

        # set profiler
        if fire_histo >= 4:
            self.enemy_profile |= set("destroyer killer")
            self.enemy_profile_detail["destroyer killer"] = turn
        if fire_histo >= 6:
            self.enemy_profile |= set("mainship killer")
            self.enemy_profile_detail["mainship killer"] = turn
        if habitual_offender:
            self.enemy_profile |= set("habitual offender")
            self.enemy_profile_detail["habitual offender"] = turn
        if strong_hs_correlation:
            self.enemy_profile |= set("hit scan correlation")
            self.enemy_profile_detail["hit scan correlation"] = turn
        if strong_ts_correlation:
            self.enemy_profile |= set("time space correlation")
            self.enemy_profile_detail["time space correlation"] = turn

        # reset the profile if the behavier is not observed in 200 turn
        for key, value in self.enemy_profile_detail.items():
            if turn - value > 200:
                self.enemy_profile -= key
