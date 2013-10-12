# Ship class for Python Test Client, MM19

# Copyright (c) 2013 Association for Computing Machinery at the University
# of Illinois, Urbana-Champaign. Inherits license from main MechMania 19 code.

import random

class Ship(object):
    """
    Really bare bones ship class.

    You probably want to flesh this out a bit (for instance, use some constants
    instead of all the hard-coded things) if you're using the client for
    development.

    It's not well documented because everything is either obvious or kind of
    stupid. I'm sorry.
    """

    def __init__(self, ship_type, x, y, orient, ID=0):
      self.ship_type = ship_type
      self.x = x
      self.y = y
      self.orient = orient
      self.ID = ID

    def getJSON(self):
      """Return the JSON dictionary representation of the ship."""
      out = {'xCoord': self.x, 'yCoord': self.y, 'orientation': self.orient}
      if self.ship_type is not "M":
        out['type'] = self.ship_type
      return out

    @classmethod
    def random_ship(Ship, ship_type):
      """
      Static method for placing a ship randomly.

      ship_type: The type of ship.
      """
      x = random.randint(0, 99)
      y = random.randint(0, 99)
      orient = random.choice(["H", "V"])
      return Ship(ship_type, x, y, orient)
