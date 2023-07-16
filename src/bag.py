"""
bag.py
Isaac Jung

This module contains all code related to bags that hold tiles.
"""

import random


class Bag:
    """Basic data structure reflecting a jumbled bag of objects.

    Halfway between a list and a set; elements in the bag are unordered, but duplicates are allowed.
    The bag is initialized with its constructor. After that, things may only be removed from the bag, never put back.

    Parameters
    ----------
    tiles: list of Tile objects
        Really, there should only be Troop objects in here, but the module is designed to be flexible.
        The list passed in for this parameter should already have its objects initialized.
    """

    def __init__(self, tiles):
        self.__tiles = tiles

    def pull(self):
        """Performs the pull action, retrieving a random object from within the bag.

        This function assumes that the caller first checks that the action is allowed.

        :return: Tile object of the tile pulled from the bag, or None if the bag is empty
        """
        if len(self.__tiles) == 0:  # game should ensure that this never happens
            return None
        new_troop = random.choice(self.__tiles)
        self.__tiles.remove(new_troop)
        new_troop.set_in_play(True)
        return new_troop

    def num_tiles_remaining(self):
        return len(self.__tiles)
