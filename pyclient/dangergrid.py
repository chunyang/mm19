import numpy as np

from Map import Map

class DangerGrid(object):
    """
    A class for estimating the danger of locations on the board
    """

    # Size of grid
    GRID_SIZE = 100

    # Spatial variance
    SIGMA_D = 5
    VAR_D2 = 50

    # Time variance
    SIGMA_T = 3
    VAR_T2 = 18

    def __init__(self):
        self.grid = np.zeros((DangerGrid.GRID_SIZE, DangerGrid.GRID_SIZE))

    def update(self, turn, my_map):

        # Reset grid
        self.grid = np.zeros((DangerGrid.GRID_SIZE, DangerGrid.GRID_SIZE))

        for y in range(DangerGrid.GRID_SIZE):
            for x in range(DangerGrid.GRID_SIZE):
                for t in my_map[y][x].fired[::-1]:
                    if turn - t[0] > 3 * DangerGrid.SIGMA_T:
                        break

                    t_dist = (turn - t[0])**2

                    y_min = max(y - 3 * DangerGrid.SIGMA_D, 0)
                    y_max = min(y + 3 * DangerGrid.SIGMA_D + 1,
                                DangerGrid.GRID_SIZE)

                    x_min = max(x - 3 * DangerGrid.SIGMA_D, 0)
                    x_max = min(x + 3 * DangerGrid.SIGMA_D + 1,
                                DangerGrid.GRID_SIZE)

                    for yy in range(y_min, y_max):
                        for xx in range(x_min, x_max):
                            # "Square" distance
                            d_dist = max(abs(yy - y), abs(xx - x))**2
                            self.grid[yy, xx] += np.exp(
                                    - d_dist/DangerGrid.VAR_D2 - \
                                        t_dist/DangerGrid.VAR_T2)

    def get_danger(self, ship):
        x_min = ship.x
        y_min = ship.y
        if ship.orient == 'H':
            x_max = ship.x + ship.get_ship_length()
            y_max = ship.y
        else:
            x_max = ship.x
            y_max = ship.y + ship.get_ship_length()

        danger = 0

        for y in range(y_min, y_max):
            for x in range(x_min, x_max):
                if self.grid[y, x] > danger:
                    danger = self.grid[y, x]

        return danger
