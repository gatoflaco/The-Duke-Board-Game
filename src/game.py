"""
game.py
Isaac Jung

This module contains all the code related to playing a game of The Duke.
"""
from src.board import Board


class Game:
    """Holds all information pertaining to a single round of the game.

    A game consists of a board and 2 players. Each player has a bag of tiles,
    along with other things they keep track of such as captured troop tiles.
    A Game object, then, serves as an interface through which to manage the
    states of the board and players.
    """

    def __init__(self):
        self.board = Board()

    def update(self, game_display):
        game_display.fill((255, 255, 255))
        self.board.display(game_display)
