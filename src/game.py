"""
game.py
Isaac Jung

This module contains all the code related to playing a game of The Duke.
"""

from src.board import Board
from src.player import Player
from src.tile import Troop

class Game:
    """Holds all information pertaining to a single round of the game.

    A game consists of a board and 2 players. Each player has a bag of tiles,
    along with other things they keep track of such as captured troop tiles.
    A Game object, then, serves as an interface through which to manage the
    states of the board and players.
    """

    def __init__(self):
        self.__board = Board()
        self.__turn = 0
        self.__players = (None, None)
        self.__tiles_in_play = []
        self.setup()

    def setup(self):
        player1 = Player(1)
        player2 = Player(2)
        self.__players = (player1, player2)
        # TODO: don't hardcode the following setup
        self.__tiles_in_play.append(Troop("Duke", player1.get_side(), (2, 0), True))
        self.__tiles_in_play.append(Troop("Footman", player1.get_side(), (2, 1), True))
        self.__tiles_in_play.append(Troop("Footman", player1.get_side(), (3, 0), True))
        # TODO: load up data/tiles/types.json and iterate through it to
        #  initialize all of the troops (including copies) in a loop, then
        #  store all but the initial Duke and Footman troops in each player's bag

    def update(self, game_display):
        game_display.fill((255, 255, 255))
        self.__board.display(game_display)
        for troop in self.__tiles_in_play:
            troop.draw(game_display)
