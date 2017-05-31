from objectmodel import ObjectModel

from tools import *


class GenericObject(MapObject):
    onP1Changed = pyqtSignal()
    p1 = Property(str, 'p1', default_set='property 1', notify=onP1Changed)

    onP2Changed = pyqtSignal()
    p2 = Property(str, 'p2', default_set='property 2', notify=onP2Changed)

    onP3Changed = pyqtSignal()
    p3 = Property(str, 'p3', default_set='property 3', notify=onP3Changed)


if __name__ == '__main__':
    model = ObjectModel(_type=GenericObject,
                        objects=[GenericObject(data=random_string()) for i in range(TOTAL_ELEMENTS)],
                        listen=True,
                        parent=None)

    for i in range(int(TEST_SIZE / 2)):
        model.append(GenericObject(data=random_string()))

    for i in range(int(TEST_SIZE / 2)):
        del model[random_idx()]

    model.apply()