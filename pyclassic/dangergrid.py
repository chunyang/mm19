import numpy as np

from Map import Map

class DangerGrid(object):
    """
    A class for estimating the danger of locations on the board
    """

    # Size of grid
    GRID_SIZE = 100

    # Spatial variance
    SIGMA_D = 4
    VAR_D2 = 2 * SIGMA_D**2

    # Time variance
    SIGMA_T = 3
    VAR_T2 = 2 * SIGMA_T**2

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

                    y_min = max(y - 1 * DangerGrid.SIGMA_D, 0)
                    y_max = min(y + 1 * DangerGrid.SIGMA_D + 1,
                                DangerGrid.GRID_SIZE)

                    x_min = max(x - 1 * DangerGrid.SIGMA_D, 0)
                    x_max = min(x + 1 * DangerGrid.SIGMA_D + 1,
                                DangerGrid.GRID_SIZE)

                    for yy in range(y_min, y_max):
                        for xx in range(x_min, x_max):
                            # "Square" distance
                            d_dist = max(abs(yy - y), abs(xx - x))**2
                            self.grid[yy, xx] += 2 * np.exp(
                                    - d_dist/DangerGrid.VAR_D2 - \
                                        t_dist/DangerGrid.VAR_T2)

    # # Print map
    # def print_danger(self):
    #     for y in range(100):
    #         print >> sys.stderr, ''.join([str(int(round(x))) for x in self.grid[y, :]])

    def get_danger(self, ship):
        x_min = ship.x
        y_min = ship.y
        if ship.orient == 'H':
            x_max = ship.x + ship.get_ship_length()
            y_max = ship.y + 1
        else:
            x_max = ship.x + 1
            y_max = ship.y + ship.get_ship_length()

        danger = 0

        for y in range(y_min, y_max):
            for x in range(x_min, x_max):
                if self.grid[y, x] > danger:
                    danger = self.grid[y, x]

        return danger
