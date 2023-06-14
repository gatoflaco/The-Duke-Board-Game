"""
board.py
Isaac Jung

This module contains all code related to the board.
"""

import constants


class Board:

    def __init__(self, pygame, game_display):
        self.display(pygame, game_display)

    def display(self, pygame, game_display):
        game_display.blit(pygame.image.load(constants.BOARD), ((constants.DISPLAY_WIDTH-808)/2, 0))
