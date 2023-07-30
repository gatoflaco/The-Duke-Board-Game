"""
bag.py
Isaac Jung

This module contains all code related to bags that hold tiles.
"""

from pygame import SRCALPHA, Surface
from constants import BUFFER, TEXT_FONT_SIZE, BAG_PNG, BAG_SIZE
import random


class Bag:
    """Basic data structure reflecting a jumbled bag of objects.

    Halfway between a list and a set; elements in the bag are unordered, but duplicates are allowed.
    The bag is initialized with its constructor. After that, things may only be removed from the bag, never put back.

    Parameters
    ----------
    tiles : list of Tile objects
        Really, there should only be Troop objects in here, but the module is designed to be flexible.
        The list passed in for this parameter should already have its objects initialized.
    side : int
        Integer ID of the bag, corresponding to the eponymous side in player.py's Player class.
        There is no such thing as a player 0, so this should start at 1 and increment from there.
        Must be unique from the other bag(s) in the game.
    """

    # the following is an enumeration of the bag states
    SELECTABLE = 0      # bag may be selected to enter playing-a-tile state
    SELECTED = 1        # bag is selectable, and the user is mouse-hovering over it or in playing-a-tile state
    UNSELECTABLE = 2    # bag may not be selected, but there are tiles remaining
    EMPTY = 3           # bag may not be selected because there are no tiles remaining

    def __init__(self, tiles, side):
        self.__tiles = tiles
        self.__hovered = False
        self.__side = side
        self.__state = Bag.SELECTABLE
        self.__image = Surface((BAG_SIZE, BAG_SIZE), SRCALPHA)  # creates transparent background
        self.__image.blit(BAG_PNG, (0, 0))  # draw png onto surface, cropping off extra pixels

    def pull(self):
        """Performs the pull action, retrieving a random object from within the bag.

        This function assumes that the caller first checks that the action is allowed.

        :return: Tile object of the tile pulled from the bag, or None if the bag is empty
        """
        if len(self.__tiles) == 0:  # game should ensure that this never happens
            return None
        new_troop = random.choice(self.__tiles)
        self.__tiles.remove(new_troop)
        if len(self.__tiles) == 0:
            self.set_state(Bag.EMPTY)
        new_troop.set_in_play(True)
        return new_troop

    @property
    def size(self):
        return len(self.__tiles)

    @property
    def tiles(self):
        return self.__tiles

    def set_hovered(self, hovered=True):
        self.__hovered = hovered

    def set_state(self, state):
        if state == self.__state or state not in [Bag.SELECTABLE, Bag.SELECTED, Bag.UNSELECTABLE, Bag.EMPTY]:
            return  # nothing to do
        self.__image = Surface((BAG_SIZE, BAG_SIZE), SRCALPHA)
        if state == Bag.SELECTABLE:
            self.__image.blit(BAG_PNG, (0, 0))
        elif state == Bag.SELECTED:
            self.__image.blit(BAG_PNG, (-BAG_SIZE, 0))
        elif state == Bag.UNSELECTABLE:
            self.__image.blit(BAG_PNG, (0, -BAG_SIZE))
        elif state == Bag.EMPTY:
            self.__image.blit(BAG_PNG, (-BAG_SIZE, -BAG_SIZE))
        self.__state = state

    @property
    def state(self):
        return self.__state

    def draw(self, display, x=None, y=None):
        """Draws the bag to the screen

        :param display: Display object containing the main game window
        :param x: x-coordinate of pixel location on game window of upper left corner of bag
        :param y: y-coordinate of pixel location on game window of upper left corner of bag
        """
        if x is None:
            if self.__side == 1:
                x = display.width - BAG_SIZE - BUFFER
            elif self.__side == 2:
                x = BUFFER
        if y is None:
            if self.__side == 1:
                y = display.height - BAG_SIZE - BUFFER
            elif self.__side == 2:
                y = BUFFER
        display.draw(self.__image, (x, y))
        if self.__side == 1:
            display.write('{:02d} tiles remaining'.format(len(self.__tiles)),
                          (x + BAG_SIZE, y - BUFFER - TEXT_FONT_SIZE), True)
        else:
            display.write('{:02d} tiles remaining'.format(len(self.__tiles)), (x, y + BAG_SIZE + BUFFER))
