"""
board.py
Isaac Jung

This module contains all code related to the board.
"""

import pygame
from src.constants import DISPLAY_WIDTH, BOARD


class Board:
    """Represents the physical board on which the game is played.

    The board is a 6x6 grid that can be represented as a 2D array.
    When a tile is placed on the board, it occupies one (x, y)-coordinate on this grid, or one index in the 2D array.
    """

    def __init__(self):
        self.__grid = [[None] * 6 for _ in range(6)]

    def set_tile(self, x, y, tile):
        self.__grid[x][y] = tile

    def get_tile(self, x, y):
        return self.__grid[x][y]

    def draw(self, game_display):
        """Draws the board and every tile on it to the screen

        :param game_display: main pygame.surface.Surface representing the whole game window
        """
        game_display.blit(pygame.image.load(BOARD), ((DISPLAY_WIDTH - 808) / 2, 0))
        for tile in sum(self.__grid, []):
            if tile is not None:
                tile.draw(game_display)
