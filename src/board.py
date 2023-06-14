"""
board.py
Isaac Jung

This module contains all code related to the board.
"""

import pygame
import src.constants as cnst


class Board:
    """Represents the physical board on which the game is played.

    The board is a 6x6 grid that can be represented as a 2D array.
    When a tile is placed on the board, it occupies one space on this 6x6 grid,
    or one (x, y)-coordinate pair in the 2D array.

    Parameters
    ----------
    game_display : pygame.surface.Surface
        Object returned by whatever module executes the line of code
        pygame.display.set_mode() (most likely main.py). Whatever module does
        this is also probably traceable from wherever a Board is instantiated.
        Note that pygame.display.set_mode() will need to take dimensions large
        enough for the image of the board to be loaded.
    """

    def __init__(self):
        pass

    def display(self, game_display):
        game_display.blit(pygame.image.load(cnst.BOARD), ((cnst.DISPLAY_WIDTH - 808) / 2, 0))
