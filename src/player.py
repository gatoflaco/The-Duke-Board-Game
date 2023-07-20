"""
player.py
Isaac Jung

This module contains all code related to players in a given game of the Duke.
"""

from src.bag import Bag
from src.tile import Troop
from src.constants import TILE_TYPES, STARTING_TROOPS
from random import randrange, shuffle


class Player:
    """Holds data and methods associated with a single participant in a given game.

    Each player begins by playing a Duke and two Footman tiles according to the rules of the game's setup.
    The rest of their tiles go in a bag. During gameplay, players manage their own knowledge about what troops they
    have in play, what opposing troops they have captured, where their Duke is and whether it is in check, and, most
    importantly, what moves they can legally make at any given moment. They do NOT know about the actual board state,
    or what the opponent's state currently looks like. The moves they are allowed to make is something that game.py
    should calculate and update for them every turn.

    Parameters
    ----------
    side : int
        Integer ID of the player, corresponding to which side they're on.
        There is no such thing as a player 0, so this should start at 1 and increment from there.
        Must be unique from the other player(s) in the game.
    """

    def __init__(self, side):
        self._side = side
        all_troop_names = []
        for troop_name, count in TILE_TYPES['troop'].items():  # generate a list of all troop names with duplicates
            all_troop_names.extend([troop_name] * count)
        bag_troop_names = all_troop_names.copy()
        for troop_name in STARTING_TROOPS:  # remove troop names of troops that will be played at the start
            bag_troop_names.remove(troop_name)
        bag_troops = [Troop(troop_name, self._side) for troop_name in bag_troop_names]
        self._in_play = []
        self._bag = Bag(bag_troops, side)
        self._captured = []
        self._duke = None
        self._in_check = False
        self._choices = {
            'pull': {
                'is_allowed': False,
                'locations': []
            },
            'act': {}
        }
        self.setup_phase()  # TODO: don't call this here, call it after game has drawn blank board

    def setup_phase(self):
        """Runs the setup phase for this player.

        The setup phase consists of placing the Duke in the rank closest to the player's side, in either file c or d,
            and then placing exactly two Footman tiles on any 2 of the 3 cardinally adjacent spaces next to the Duke.
        """
        # TODO: get player input for coordinates instead of using hard coded ones
        coords = [(2, 0), (2, 1), (3, 0)] if self._side == 1 else [(3, 5), (2, 5), (4, 5)]
        i = 0
        for troop_name in STARTING_TROOPS:
            self._in_play.append(Troop(troop_name, self._side, coords[i], True))
            if troop_name == 'Duke':
                self._duke = self._in_play[-1]  # the most recently added is the Duke
            i += 1

    def get_side(self):
        return self._side

    def set_tiles_in_play(self, in_play):
        self._in_play = in_play

    def get_tiles_in_play(self):
        return self._in_play

    def has_tiles_in_bag(self):
        return self._bag.num_tiles_remaining() != 0

    def capture(self, tile):
        self._captured.append(tile)

    def undo_last_capture(self):
        tile = self._captured.pop()
        tile.set_in_play()
        tile.set_captured(False)
        return tile

    def get_duke(self):
        return self._duke

    def set_check(self, in_check=True):
        self._in_check = in_check

    def is_in_check(self):
        return self._in_check

    def update_choices(self, choices):
        self._choices = choices

    def get_choices(self):
        return self._choices

    def update(self, display):
        self._bag.draw(display)

    def take_turn(self):
        """Handles the logic of getting user input on what to do for the player's turn.

        Operates based on what is currently in the self._choices dict, a special dict whose format is documented in
            docs/choice_formats.txt. The dict should contain all the things the player could legally do at the moment.
            In order for this to be true, game.py should maintain the dict for the player, updating it as needed any
            time the board state changes.

        :return: special dict called "choice", whose format is documented in docs/choice_formats.txt
        """
        highlighted1 = []  # initial list of valid (x, y) locations
        highlighted2 = []  # filled out when a highlighted1 location is clicked
        highlighted3 = []  # filled out only when a clicked highlighted2 location is a teammate to command
        # TODO: get user input on what they want to do instead of hard coding

        if len(self._choices['pull']) != 0 and randrange(0, 10) < 2:
            x, y = self._choices['pull'][0]
            tile = self.play_new_troop_tile(x, y)
            return {
                'action_type': 'pull',
                'src_location': tile.get_coords(),
                'tile': tile
            }
        else:  # MUST be at least one valid 'act' choice (otherwise game would have stopped due to checkmate)
            troop_locs = list(self._choices['act'].keys())
            shuffle(troop_locs)
            for troop_loc in troop_locs:
                for teammate_loc in self._choices['act'][troop_loc]['commands']:
                    if len(self._choices['act'][troop_loc]['commands'][teammate_loc]) != 0:
                        return {
                            'action_type': 'cmd',
                            'src_location': teammate_loc,
                            'dst_location': self._choices['act'][troop_loc]['commands'][teammate_loc][
                                randrange(0, len(self._choices['act'][troop_loc]['commands'][teammate_loc]))],
                            'cmd_location': troop_loc,
                        }
                if len(self._choices['act'][troop_loc]['strikes']) != 0:
                    return {
                        'action_type': 'str',
                        'src_location': troop_loc,
                        'str_location': self._choices['act'][troop_loc]['strikes'][
                            randrange(0, len(self._choices['act'][troop_loc]['strikes']))]
                    }
                if len(self._choices['act'][troop_loc]['moves']) != 0:
                    return {
                        'action_type': 'mov',
                        'src_location': troop_loc,
                        'dst_location': self._choices['act'][troop_loc]['moves'][
                            randrange(0, len(self._choices['act'][troop_loc]['moves']))]
                    }
        if len(self._choices['pull']):
            x, y = self._choices['pull'][0]
            tile = self.play_new_troop_tile(x, y)
            return {
                'action_type': 'pull',
                'src_location': tile.get_coords(),
                'tile': tile
            }

    def play_new_troop_tile(self, x, y):
        """Pulls a random troop from the bag and puts it into play at location (x, y).

        This function assumes that the caller first checks that the action is allowed.

        :param x: x-coordinate of location at which the new tile will be played
        :param y: y-coordinate of location at which the new tile will be played
        :return: Troop object of the troop that got pulled from the bag
        """
        tile = self._bag.pull()
        tile.set_in_play()
        tile.move(x, y)
        self._in_play.append(tile)
        return tile

    def remove_from_play(self, x, y, is_captured=True):
        """Removes the troop found at (x, y) from this player's self._in_play list.

        :param x: x-coordinate of location at which the troop-to-remove must be found
        :param y: y-coordinate of location at which the troop-to-remove must be found
        :param is_captured: boolean representing why this troop is being removed from play
            It is possible that for some reason, we might want to take a troop off the board for some reason other
            than it having been captured. In this case, override the default value of True to be False.
        :return: Troop object of the troop removed from play, or None if no troop could be found at (x, y)
        """
        tile = self.get_tile_with_coords(x, y)
        if tile is not None:
            self._in_play.remove(tile)
            tile.set_in_play(False)
            tile.set_captured(is_captured)
        return tile

    def get_tile_with_coords(self, x, y):
        """Searches for the troop in this player's self._in_play list with coordinates (x, y).

        :param x: x-coordinate of location being searched
        :param y: y-coordinate of location being searched
        :return: Troop object of the troop found at (x, y), or None if no troop could be found
        """
        for troop_tile in self._in_play:
            i, j = troop_tile.get_coords()
            if i == x and j == y:
                return troop_tile
        return None  # not found
