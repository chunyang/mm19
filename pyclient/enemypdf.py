import numpy as np
import random

class EnemyPDF(object):
    """
    A class for estimating the location of the enemy
    """

    def __init__(self):
        # Enemy probability mass
        self.grid = np.tile(np.array([[1., 0.], [0., 1.]]), [50, 50])

        self.parity_mask = np.tile(np.array([[1, 0], [0, 1]]), [50, 50])

        # Which areas do not need mass to be spread to
        self.decreased_grid = np.ones((100, 100))

        # How much mass has been lost from multiplying the mask
        self.accumulated_mass = 0

        # Construct miss mask
        self.miss_mask = 5./6 * np.ones((5, 5))
        self.miss_mask[1:4, 1:4] = 2./3
        self.miss_mask[2, 2] = 0

        # Construct scan miss mask
        self.scan_miss_mask = 5./6 * np.ones((9, 9))
        self.scan_miss_mask[1:8, 1:8] = 2./3
        self.scan_miss_mask[2:7, 2:7] = 0

    def mask_decrease(self, x, y, mask):
        width = mask.shape[0]
        radius = mask.shape[0] / 2

        if x - radius < 0:
            x_min = 0
            x_max = x + radius + 1
            mask = mask[:, (radius + x_min - x):]
        elif x + radius + 1 > 100:
            x_min = x - radius
            x_max = 100
            mask = mask[:, :(width-(x + radius + 1 - x_max))]
        else:
            x_min = x - radius
            x_max = x + radius + 1

        if y - radius < 0:
            y_min = 0
            y_max = y + radius + 1
            mask = mask[(radius + y_min - y):, :]
        elif y + radius + 1 > 100:
            y_min = y - radius
            y_max = 100
            mask = mask[:(width-(y + radius + 1 - y_max)), :]
        else:
            y_min = y - radius
            y_max = y + radius + 1

        # Mark where mass was taken from
        self.decreased_grid[y_min:y_max, x_min:x_max] = 0

        # Mask and compute lost mass
        orig_mass = np.sum(self.grid[y_min:y_max, x_min:x_max])
        self.grid[y_min:y_max, x_min:x_max] = mask * \
                self.grid[y_min:y_max, x_min:x_max]
        new_mass = np.sum(self.grid[y_min:y_max, x_min:x_max])

        self.accumulated_mass += orig_mass - new_mass

    def decrease(self, x, y):
        self.mask_decrease(x, y, self.miss_mask)

    def scan_decrease(self, x, y):
        self.mask_decrease(x, y, self.scan_miss_mask)

    def spread_mass(self):
        num = self.accumulated_mass
        denom = np.sum(self.decreased_grid)

        # Add mass back to grid
        self.grid += float(num) / denom * self.decreased_grid * \
                        self.parity_mask

        # Normalize (FIXME: this may be masking some errors)
        self.grid = self.grid / np.sum(self.grid) * 5000.

        # Reset accumulator and decrease grid
        self.decreased_grid = np.ones((100, 100))
        self.accumulated_mass = 0

        # Compute cumulative sum (should be 10000)
        # print np.sum(self.grid)

    def next_scan(self, dim=5):
        """Return most probable 5x5 area"""

        integral = np.cumsum(np.cumsum(self.grid, axis=0), axis=1)

        ys = range(100-dim)
        random.shuffle(ys)
        xs_even = range(100-dim)[::2]
        xs_odd = range(100-dim)[1::2]
        random.shuffle(xs_even)
        random.shuffle(xs_odd)

        best = float('-inf')
        best_x = 46
        best_y = 46

        for y in ys:
            if y % 2:
                xs = xs_odd
            else:
                xs = xs_even

            for x in xs:
                val = integral[y+dim, x+dim] - integral[y+dim, x] - \
                        integral[y, x+dim] + integral[y, x]

                if val > best + 1E-11:
                    best = val
                    best_x = x
                    best_y = y

        return (best_x+1, best_y+1)

    def next_hits(self, num_hits=1):
        """Return most probable cell"""

        hits = np.tile(np.array([46, 46]), (num_hits, 1))
        bests = np.ndarray.flatten(np.tile(-1, (num_hits, 1)))

        for i in range(num_hits):
            ys = range(100)
            random.shuffle(ys)
            xs_even = range(100)[::2]
            xs_odd = range(100)[1::2]
            random.shuffle(xs_even)
            random.shuffle(xs_odd)

            for y in ys:
                if y % 2:
                    xs = xs_odd
                else:
                    xs = xs_even

                for x in xs:
                    val = self.grid[y, x]

                    comp = val - 1E-11 > bests
                    if np.any(comp):
                        idx = np.nonzero(comp)[0][0]
                        bests[idx] = val
                        hits[idx, :] = np.array([x, y])

                        # Sort best hits
                        sort_idx = np.argsort(bests)
                        bests = bests[sort_idx]
                        hits = hits[sort_idx, :]

        print hits
        return [(hits[i, 0], hits[i, 1]) for i in range(num_hits)]

    def next_hit(self):
        return self.next_hits()[0]

    def show(self):
        print self.grid
        print np.max(self.grid)
