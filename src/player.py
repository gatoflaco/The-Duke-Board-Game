"""
player.py
Isaac Jung

This module contains all code related to players in a given game of the Duke.
"""

from src.constants import TILE_TYPES, STARTING_TROOPS
from src.bag import Bag
from src.tile import Troop


class Player:

    def __init__(self, side):
        self.__side = side
        all_troop_names = []
        for troop_name, count in TILE_TYPES['troop'].items():  # generate a list of all troop names with duplicates
            all_troop_names.extend([troop_name] * count)
        bag_troop_names = all_troop_names.copy()
        for troop_name in STARTING_TROOPS:  # remove troop names of troops that will be played at the start
            bag_troop_names.remove(troop_name)
        bag_troops = [Troop(troop_name, self.__side) for troop_name in bag_troop_names]
        self.__in_play = []
        self.__bag = Bag(bag_troops)
        self.__captured = []
        self.setup_phase()  # TODO: don't call this here, call it after game has drawn blank board

    def setup_phase(self):
        # TODO: get rid of the next line once the next TODO is resolved
        coords = [(2, 0), (2, 1), (3, 0)] if self.__side == 1 else [(3, 5), (2, 5), (4, 5)]
        i = 0  # TODO: get rid of this once the next TODO is resolved
        for troop_name in STARTING_TROOPS:
            # TODO: get player input for coordinates instead of using hard coded ones
            self.__in_play.append(Troop(troop_name, self.__side, coords[i], True))
            i += 1

    def capture(self, tile):
        self.__captured.append(tile)

    def get_tiles_in_play(self):
        return self.__in_play

    def take_turn(self, choices):
        highlighted1 = []  # initial list of valid (x, y) locations
        highlighted2 = []  # filled out when a highlighted1 location is clicked
        highlighted3 = []  # filled out only when a highlighted2 location is a teammate to command
        # TODO: get user input on what they want to do instead of hard coding
        if choices['pull']['is_allowed']:
            (x, y) = choices['pull']['locations'][0]
            successful, tile = self.play_new_troop_tile(x, y)
            if successful:
                return {
                    'action_type': 'pull',  # must be one of 'pull', 'mov', 'str', or 'cmd'
                    'tile': tile,  # only needed when action type is 'pull'
                    'src_location': tile.get_coords()  # needed for all action types
                }  # note that this dict should look different when moving/commanding an existing troop
                # e.g., 'dst_location' is used for 'mov', 'cmd', and 'str', 'cmd_location' is used for 'cmd', etc.
            else:
                pass  # TODO? Probably need to wrap this whole thing in a loop or something
        # TODO: if choice is to move, strike, or command with an existing tile, update tile properties

    def play_new_troop_tile(self, x, y):
        # TODO: document that this function assumes that the game checks that it's allowed first
        result = self.__bag.pull()
        is_empty = not result[0]  # pull()[0] is True when successful; if False, there are no tiles left in the bag
        if is_empty:
            return False, None
        tile = result[1]
        tile.set_in_play()
        tile.move(x, y)
        self.__in_play.append(tile)
        return True, tile

    def remove_from_play(self, x, y, is_captured=False):
        tile = None
        for troop_tile in self.__in_play:
            (i, j) = troop_tile.get_coords()
            if i == x and j == y:
                tile = troop_tile
                break
        if tile is not None:
            self.__in_play.remove(tile)
            tile.set_in_play(False)
            tile.set_captured(is_captured)
        return tile
