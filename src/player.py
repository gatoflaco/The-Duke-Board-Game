"""
player.py
Isaac Jung

This module contains all code related to players in a given game of the Duke.
"""


class Player():

    def __init__(self, side):
        self.__side = side

    def get_side(self):
        return self.__side
