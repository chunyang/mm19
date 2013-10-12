# Ship class for Python Test Client, MM19

# Copyright (c) 2013 Association for Computing Machinery at the University
# of Illinois, Urbana-Champaign. Inherits license from main MechMania 19 code.

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

    def get_ship_type(self):
        raise ValueError("No Ship Type")

    def update(self, health, x, y, orient):
        self.health = health
        self.x = x
        self.y = y
        self.orient = orient

    def set_action(self, action, x, y):
        self.action = action
        self.actionX = x
        self.actionY = y

    def clear_action(self):
        self.action = "N"
        self.actionX = -1
        self.actionY = -1

    def get_id(self):
        return self.ID

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
            self.action = "MV"
        else if orient == "H"
            self.action = "MH"
        else
            raise ValueError("Unknown Orientation")

        self.actionX = x
        self.actionY = y


class MainShip(Ship):
    """
    Main Ship Class
    """
    def __init__ (self, x, y, orient, ID):
        Ship.__init__(self, x, y, orient, ID, 60)

    def get_ship_type(self):
        return 'M'

    def fire(self, x, y):
        self.action = "F"
        self.actionX = x
        self.actionY = y

class Destroyer(Ship):
    """
    Destroyer Ship Class
    """
    def __init__ (self, x, y, orient, ID):
        Ship.__init__(self, x, y, orient, ID, 40)

    def get_ship_type(self):
        return 'D'

    def fire(self, x, y):
        self.action = "F"
        self.actionX = x
        self.actionY = y

    def burst_fire(self, x, y):
        self.action = "B"
        self.actionX = x
        self.actionY = y

class Pilot(Ship):
    """
    Pilot Ship Class
    """
    def __init__ (self, x, y, orient, ID):
        Ship.__init__(self, x, y, orient, ID, 40)

    def get_ship_type(self):
        return 'P'

    def sonar(self, x, y):
        self.action = "S"
        self.actionX = x
        self.actionY = y
