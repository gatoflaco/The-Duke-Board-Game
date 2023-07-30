"""
board.py
Isaac Jung

This module contains all code related to the board.
"""

import pygame
from src.display import Theme
from src.tile import Tile
from src.constants import TEXT_BUFFER, BOARD_PNG, BOARD_DARK_PNG, BOARD_SIZE, FILES, RANKS, TILE_SIZE


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

    def draw(self, display):
        """Draws the board and every tile on it to the screen

        :param display: Display object containing the main game window
        """
        display.blit(BOARD_DARK_PNG if display.theme == Theme.DARK else BOARD_PNG,
                     ((display.width - BOARD_SIZE) // 2, 0))
        delta = TILE_SIZE + 6
        for i in range(6):
            display.write(FILES[i], ((display.width - BOARD_SIZE) // 2 + delta * i + TILE_SIZE//2 - 2,
                                     BOARD_SIZE + TEXT_BUFFER))
            display.write(RANKS[i], ((display.width - BOARD_SIZE) // 2 - TEXT_BUFFER - 10,
                                     BOARD_SIZE - delta * i - TILE_SIZE//2 - 2))
        for tile in sum(self.__grid, []):
            if isinstance(tile, Tile):
                tile.draw(display)
