import random

def random_5():
    x = range(5)
    random.shuffle(x)
    return x

def bomber_pattern(x_low, y_low, x_high, y_high):
    """
    *....*....*....
    .*....*....*...
    ..*....*....*..
    """
    x_dim = x_high - x_low
    y_dim = y_high - y_low
    index_array = random_5()
    out = []
    for x in range(x_dim):
        y = index_array[x % 5]
        while y < y_dim:
            out.append((x, y))
            y += 5
    random.shuffle(out)
    return out

class BomberStrategy(object):
    def __init__(self, x_low, x_high, y_low, y_high):
        dq = bomber_pattern(x_low, x_high, y_low, y_high)
        self.dq = zip(dq, [6] * len(dq))

    def job_assign(self, ships, attack_num):
        for ship in ships:
            if ship.get_ship_type() == "D" or ship.get_ship_type() == "M":
                if ship.action == "N":
                    ship.fire(self.dq[-1][0][0], self.dq[-1][0][1])
                    self.dq[-1] = (self.dq[-1][0], self.dq[-1][1] -1)
                    attack_num -= 1
                    if self.dq[-1][1] == 0:
                        self.dq.pop()
                    if attack_num == 0:
                        return

def main():
    import numpy as np
    import operator
    test = bomber_pattern(0, 0, 25, 25)
    mat = np.empty((25, 25, ))
    mat[:] = 0
    for x, y in test:
        mat[y][x] = 1
    print mat

if __name__ == "__main__":
    main()

