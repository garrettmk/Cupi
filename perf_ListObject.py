from tools import *


if __name__ == '__main__':
    base = [random_element() for i in range(TOTAL_ELEMENTS)]

    with Timer(verbose=True) as t:
        lo = ListObject(base)

        # Set some items
        for i in range(TEST_SIZE):
            lo[random_idx()] = random_element()

        # Get some items
        for i in range(TEST_SIZE * 2):
            x = lo[random_idx()]
