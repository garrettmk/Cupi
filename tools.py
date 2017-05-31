import cProfile
import pstats
import random
import string
import sys
import time
from unittest import TestCase

from PyQt5.QtCore import pyqtSignal

from cupi import ListObject, MapObject, Property, MongoObjectReference

TOTAL_ELEMENTS = 1000
TEST_SIZE = 500


class GenericObject(MapObject):
    __collection__ = 'generic_collection'

    p1Changed = pyqtSignal()
    p1 = Property(str, 'p1', default_set='property 1', notify=p1Changed)

    p2Changed = pyqtSignal()
    p2 = Property(str, 'p2', default_set='property 2', notify=p2Changed)

    p3Changed = pyqtSignal()
    p3 = Property(str, 'p3', default_set='property 3', notify=p3Changed)


class GenericObjectReference(MongoObjectReference):
    referencedType = GenericObject


class ProfilingTestCase(TestCase):

    def setUp(self):
        self.profile = cProfile.Profile()

    def tearDown(self):
        try:
            p = pstats.Stats(self.profile)
        except TypeError:
            return

        p.strip_dirs()
        p.sort_stats('cumtime')
        p.print_stats(15)


def random_string(length=12):
    return ''.join([random.choice(string.ascii_lowercase) for i in range(length)])


def random_idx():
    """Return a random integer between 1 and list_size."""
    return random.randrange(1, TOTAL_ELEMENTS)


def random_element():
    """Returns either an integer, a string, a 5-element list, or a 5-pair dictionary."""
    choices = [lambda: random.randrange(0, 100000),
               lambda: random_string(),
               lambda: ListObject(range(5)),
               lambda: MapObject({random_string(5):random.randrange(0, 100000) for i in range(5)}.update({'o': random_element()}))]

    return random.choice(choices)()


def get_size(obj, seen=None):
    """Recursively compute the size of an object."""
    size = sys.getsizeof(obj)

    if seen is None:
        seen = set()

    obj_id = id(obj)
    if obj_id in seen:
        return 0

    seen.add(obj_id)
    if isinstance(obj, dict):
        size += sum([get_size(v, seen) for v in obj.values()])
        size += sum([get_size(k, seen) for k in obj.keys()])
    elif hasattr(obj, '__dict__'):
        size += get_size(obj.__dict__, seen)
    elif hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes, bytearray)):
        size += sum([get_size(i, seen) for i in obj])

    return size


class Timer:
    """A context manager for timing sections of code."""
    def __init__(self, verbose=False):
        self.verbose = verbose

    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, *args):
        self.end = time.time()
        self.secs = self.end - self.start
        self.msecs = self.secs * 1000

        if self.verbose:
            print('Elapsed time: %s ms' % self.msecs)