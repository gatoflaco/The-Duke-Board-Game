"""
game.py
Isaac Jung

This module contains all the code related to playing a game of The Duke.
"""

from src.constants import TROOP_MOVEMENTS
from src.board import Board
from src.player import Player


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
        player1 = Player(1)
        player2 = Player(2)
        self.__players = (player1, player2)
        for player in self.__players:
            for tile in player.get_tiles_in_play():
                (x, y) = tile.get_coords()
                self.__board.set_tile(x, y, tile)

    def get_turn(self):
        return self.__turn

    def update(self, game_display):
        if None in self.__players:
            return False
        game_display.fill((255, 255, 255))
        self.__board.draw(game_display)
        # for troop in list(itertools.chain.from_iterable([player.get_tiles_in_play() for player in self.__players])):
        #     troop.draw(game_display)
        return True

    def take_turn(self):
        self.__turn += 1
        player = self.__players[self.__turn % len(self.__players) - 1]  # player whose turn should be taken
        choice = player.take_turn(self.get_choices(player))
        self.make_choice(player, choice)

    def get_choices(self, player):
        # TODO: document that this is a helper function used by take_turn()
        choices = {
            'pull': {  # pull from the bag
                'is_allowed': False,
                'locations': []
            },
            'act': {}  # move an existing troop tile
            # (0, 0): {  # location of the troop itself maps to what it can do
            #     'moves': [  # list of places it can move, these should be highlighted when player clicks on troop
            #         (0, 1),
            #         (1, 1)
            #     ],
            #     'strikes': [  # list of places it can strike, should have a different visual than moves
            #         (0, 2)
            #     ]
            #     'commands': {  # leave empty if no teammates to command or all command spaces filled by teammates
            #         (1, 0): True  # True when this location has another troop belonging to same player
            #         (2, 0): False  # False when this location is empty or has an enemy troop
            #     }  # note that no (x, y)-coordinate pair should appear in more than one category
            # }
            # the above is just an example of what the format should look like for an entry in 'move'
        }
        for troop in player.get_tiles_in_play():
            if troop.get_name() == 'Duke':
                (i, j) = troop.get_coords()  # i, j will hold the Duke's (x, y)-coordinates
                choices['pull']['locations'] = [  # I'm something of a Python programmer myself (goofy ah list comp lol)
                    (x, y) for x, y in [(i, j + 1), (i + 1, j), (i, j - 1), (i - 1, j)]
                    if 0 <= x < 6 and 0 <= y < 6 and self.__board.get_tile(x, y) is None
                ]  # tl;dr fill out the list of valid (x, y)-coordinates at which a new tile could be played
                if len(choices['pull']['locations']) != 0:  # if there is at least one open place to play a new tile
                    choices['pull']['is_allowed'] = True
            # TODO: for each active troop, calculate their allowed moves based on TROOP_MOVEMENTS
        return choices

    def make_choice(self, player, choice):
        # TODO: document that this is a helper function used by take_turn()
        if choice['action_type'] == 'pull':
            self.__board.set_tile(choice['src_location'][0], choice['src_location'][1], choice['tile'])
        else:
            src_tile = self.__board.get_tile(choice['src_location'][0], choice['src_location'][1])
            if choice['action_type'] != 'str':  # 'mov' or 'cmd'
                dst_tile = self.__board.get_tile(choice['dst_location'][0], choice['dst_location'][1])
                if dst_tile is not None:  # if an enemy tile is in the destination location
                    enemy_player = dst_tile.get_player()
                    dst_tile = enemy_player.remove_from_play(choice['dst_location'][0], choice['dst_location'][1], True)
                    player.capture(dst_tile)
                self.__board.set_tile(choice['src_location'][0], choice['src_location'][1], None)
                src_tile.move(choice['dst_location'][0], choice['dst_location'][1])
                if choice['action_type'] == 'mov':
                    src_tile.flip()
                    self.__board.set_tile(choice['dst_location'][0], choice['dst_location'][2], src_tile)
                else:
                    self.__board.set_tile(choice['dst_location'][0], choice['dst_location'][2], src_tile)
                    cmd_tile = self.__board.get_tile(choice['cmd_location'][0], choice['cmd_location'][1])
                    cmd_tile.flip()
                    self.__board.set_tile(choice['cmd_location'][0], choice['cmd_location'][1], cmd_tile)
            else:  # 'str'
                str_tile = self.__board.get_tile(choice['str_location'][0], choice['str_location'][1])
                enemy_player = str_tile.get_player()
                str_tile = enemy_player.remove_from_play(choice['str_location'][0], choice['str_location'][1], True)
                player.capture(str_tile)
                src_tile.flip()
                self.__board.set_tile(choice['src_location'][0], choice['src_location'][2], src_tile)
