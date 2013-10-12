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
        for hit in reply["hitReport"]:
            self.__list__[hit["yCoord"]][hit["xCoord"]].fired.append((turn, hit["hit"]));
        for scan in reply["pingReport"]:
            for ship in ShipArray:
                if ship.ID == scan["shipID"]:
                    map(lambda x: self.__list__[x[0]][x[1]].scanned.append(turn), ship.occupied_cells())
