"""
bag.py
Isaac Jung

This module contains all code related to bags that hold tiles.
"""

import random


class Bag:

    def __init__(self, tiles):
        self.__tiles = tiles

    def pull(self):
        # TODO: document that this function assumes that the caller checks that it's allowed first
        if len(self.__tiles) == 0:
            return False, None
        new_troop = random.choice(self.__tiles)
        self.__tiles.remove(new_troop)
        new_troop.set_in_play(True)
        return True, new_troop
