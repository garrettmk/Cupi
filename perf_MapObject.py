from tools import *


if __name__ == '__main__':
    random_keys = [random_string() for i in range(TOTAL_ELEMENTS)]
    base = {random_keys[i]: random_element() for i in range(TOTAL_ELEMENTS)}

    with Timer(verbose=True) as t:
        mo = MapObject(base)

        # Set some items
        for i in range(TEST_SIZE):
            mo[random.choice(random_keys)] = random_element()

        # Get some items
        for i in range(TEST_SIZE):
            try:
                x = mo[random.choice(random_keys) if random.randint(-1, 1) > 0 else random_string()]
            except KeyError:
                continue

        # Get some items using getValue
        for i in range(TEST_SIZE):
            x = mo.getValue(random.choice(random_keys) if random.randint(-1, 1) > 0 else random_string(),
                            default=None)


