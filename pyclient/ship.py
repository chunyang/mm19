# Ship class for Python Test Client, MM19

# Copyright (c) 2013 Association for Computing Machinery at the University
# of Illinois, Urbana-Champaign. Inherits license from main MechMania 19 code.

import abc

class Ship(object):
    """
    Really bare bones ship class.

    You probably want to flesh this out a bit (for instance, use some constants
    instead of all the hard-coded things) if you're using the client for
    development.

    It's not well documented because everything is either obvious or kind of
    stupid. I'm sorry.
    """

    def __init__(self, x, y, orient, ID, health):
      self.x = x
      self.y = y
      self.orient = orient
      self.ID = ID
      self.health = health
      self.action = 'N'
      self.actionX = -1
      self.actionY = -1

    def __lt__(self, other):
        """
        Order the ships by ID
        """
        return self.ID < other.ID

    @abc.abstractmethod
    def get_ship_type(self):
        raise ValueError("No Ship Type")

    @abc.abstractmethod
    def get_ship_length(self):
        raise ValueError("No Ship Length")

    def update(self, health, x, y, orient):
        self.health = health
        self.x = x
        self.y = y
        self.orient = orient

    def set_action(self, action, x, y):
        if self.action == "N":
            self.action = action
            self.actionX = x
            self.actionY = y
            return True
        else:
            return False

    def has_work(self):
        return self.action != "N"

    def clear_action(self):
        self.action = "N"
        self.actionX = -1
        self.actionY = -1

    def get_id(self):
        return self.ID

    def occupied_cells(self):
        if self.orient == "V":
            return map(lambda y: (self.y + y, self.x), range(self.get_ship_length()))
        elif self.orient == "H":
            return map(lambda x: (self.y, self.x + x), range(self.get_ship_length()))
        else:
            raise ValueError("Unknown Orientation")

    def getInitJSON(self):
        try:
            ship_type = self.get_ship_type()
        except AttributeError:
            raise ValueError("Cannot figure out ship type")
        else:
            out = {"type":ship_type, "xCoord" : self.x, "yCoord" : self.y,
                    "orientation" : self.orient}
        return out

    def getActionJSON(self):
        out = {"ID": self.ID, "actionID": self.action,
                "actionX": self.actionX, "actionY": self.actionY,
                "actionExtra": 0}
        return out

    def move(self, x, y, orient):
        if orient == "V":
            return self.set_action("MV", x, y)
        elif orient == "H":
            return self.set_action("MH", x, y)
        else:
            raise ValueError("Unknown Orientation")

class MainShip(Ship):
    """
    Main Ship Class
    """
    def __init__ (self, xCoord, yCoord, orientation, ID=-1, health=60):
        Ship.__init__(self, xCoord, yCoord, orientation, ID, health)

    @staticmethod
    def get_ship_type():
        return 'M'

    @staticmethod
    def get_ship_length():
        return 5

    def fire(self, x, y):
        return self.set_action("F", x, y)

class Destroyer(Ship):
    """
    Destroyer Ship Class
    """
    def __init__ (self, xCoord, yCoord, orientation, ID=-1, health=40):
        Ship.__init__(self, xCoord, yCoord, orientation, ID, health)

    @staticmethod
    def get_ship_type():
        return 'D'

    @staticmethod
    def get_ship_length():
        return 4

    def fire(self, x, y):
        return self.set_action("F", x, y)

    def burst_fire(self, x, y):
        return self.set_action("B", x, y)

class Pilot(Ship):
    """
    Pilot Ship Class
    """
    def __init__ (self, xCoord, yCoord, orientation, ID=-1, health=20):
        Ship.__init__(self, xCoord, yCoord, orientation, ID, health)

    @staticmethod
    def get_ship_type():
        return 'P'

    @staticmethod
    def get_ship_length():
        return 2

    def sonar(self, x, y):
        return self.set_action("S", x, y)
