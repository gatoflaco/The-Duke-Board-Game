"""
player.py
Isaac Jung

This module contains all code related to players in a given game of the Duke.
"""

from pygame import SRCALPHA, Surface
from src.bag import Bag
from src.tile import Troop
from src.constants import (BUFFER, TEXT_FONT_SIZE, TEXT_BUFFER, OFFER_DRAW_SIZE, FORFEIT_SIZE, TILE_TYPES, TILE_SIZE,
                           STARTING_TROOPS, BAG_SIZE)
from copy import copy
from time import sleep


def handle_offer_draw_hovers(display, x, y):
    if Player.OFFER_DRAW_IMAGE.get_rect().collidepoint((x - BUFFER,
                                                        y - (display.height - BUFFER - OFFER_DRAW_SIZE))):
        Player.OFFER_DRAW_HOVERED = True
    else:
        Player.OFFER_DRAW_HOVERED = False


def handle_forfeit_hovers(display, x, y):
    if Player.FORFEIT_IMAGE.get_rect().collidepoint(x - (OFFER_DRAW_SIZE + 2 * BUFFER),
                                                    y - (display.height - BUFFER - FORFEIT_SIZE)):
        Player.FORFEIT_HOVERED = True
    else:
        Player.FORFEIT_HOVERED = False


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
    name : string (optional; 'Duke' by default)
        Name to be displayed in the game.
    """
    PLAYER = None  # gets set when a non-AI player is taking their turn
    FILE = '-'  # responds to player typing a letter a through f
    RANK = '-'  # responds to player typing a number 1 through 6
    SELECTED = None  # Tile object selected by the current player
    COMMANDED = None  # Tile object being commanded by SELECTED
    CHOICE = None  # holds the "choice" dict determined by UI input for the current player
    OFFER_DRAW_IMAGE = Surface((OFFER_DRAW_SIZE, OFFER_DRAW_SIZE), SRCALPHA)
    OFFER_DRAW_HOVERED = False
    FORFEIT_IMAGE = Surface((FORFEIT_SIZE, FORFEIT_SIZE), SRCALPHA)
    FORFEIT_HOVERED = False

    def __init__(self, side, name='Duke'):
        self._side = side
        self._name = name
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

    def __copy__(self):
        cls = self.__class__
        result = cls.__new__(cls)
        result._side = self._side
        result._name = self._name
        result._in_play = []
        for tile in self._in_play:
            result._in_play.append(copy(tile))
        result._bag = copy(self._bag)
        result._captured = []
        for tile in self._captured:
            result._captured.append(copy(tile))
        result._duke = None
        for troop in result._in_play:
            if troop.name == 'Duke':
                result._duke = troop
                break
        result._in_check = self._in_check
        result._choices = self._choices.copy()
        return result

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

    @property
    def side(self):
        return self._side

    @property
    def name(self):
        return self._name

    def set_tiles_in_play(self, in_play):
        self._in_play = in_play

    @property
    def tiles_in_play(self):
        return self._in_play

    @property
    def has_tiles_in_bag(self):
        return self._bag.size != 0

    @property
    def bag_clicked(self):
        return self._bag.state == Bag.SELECTED

    def capture(self, tile):
        self._captured.append(tile)

    def undo_last_capture(self):
        tile = self._captured.pop()
        tile.set_in_play()
        tile.set_captured(False)
        return tile

    @property
    def duke(self):
        return self._duke

    def set_check(self, in_check=True):
        self._in_check = in_check

    @property
    def is_in_check(self):
        return self._in_check

    def update_choices(self, choices):
        self._choices = choices
        if len(self._choices['pull']) > 0:
            self._bag.set_state(Bag.SELECTABLE)
        elif self._bag.state != Bag.EMPTY:
            self._bag.set_state(Bag.UNSELECTABLE)

    @property
    def choices(self):
        return self._choices

    def update(self, display):
        if self._side == 1:
            display.write('Player 1',
                          (display.width - BUFFER,
                           display.height - BAG_SIZE - 2 * BUFFER - 4 * TEXT_FONT_SIZE), True)
            display.write(self._name,
                          (display.width - BUFFER,
                           display.height - BAG_SIZE - 2 * BUFFER - 3 * TEXT_FONT_SIZE + TEXT_BUFFER), True)
            dx = 0
            dy = 0
            for tile in self._captured:
                tile.draw(display,
                          display.width - TILE_SIZE - BUFFER - dx,
                          (display.height - BAG_SIZE - 3 * BUFFER - 4 * TEXT_FONT_SIZE - 2 * TEXT_BUFFER - TILE_SIZE
                           - dy), True)
                dy += TILE_SIZE // 4
                if dy > TILE_SIZE * 2:
                    dx = TILE_SIZE + BUFFER
                    dy = 0
            display.draw(Surface((TILE_SIZE, TILE_SIZE), SRCALPHA), (display.width - BAG_SIZE - 2 * BUFFER - TILE_SIZE,
                                                                     display.height - TILE_SIZE - BUFFER))
            if Player.PLAYER == self:
                if Player.COMMANDED is not None:
                    Player.COMMANDED.draw(display, display.width - BAG_SIZE - 2 * BUFFER - TILE_SIZE,
                                          display.height - TILE_SIZE - BUFFER)
                elif Player.SELECTED is not None:
                    Player.SELECTED.draw(display, display.width - BAG_SIZE - 2 * BUFFER - TILE_SIZE,
                                         display.height - TILE_SIZE - BUFFER)
        else:
            display.write('Player 2',
                          (BUFFER,
                           BUFFER + BAG_SIZE + BUFFER + 2 * TEXT_FONT_SIZE))
            display.write(self._name,
                          (BUFFER,
                           BUFFER + BAG_SIZE + BUFFER + 3 * TEXT_FONT_SIZE + TEXT_BUFFER))
            dx = 0
            dy = 0
            for tile in self._captured:
                tile.draw(display,
                          BUFFER + dx,
                          BUFFER + BAG_SIZE + 2 * BUFFER + 4 * TEXT_FONT_SIZE + 2 * TEXT_BUFFER + dy, True)
                dy += TILE_SIZE // 4
                if dy > TILE_SIZE * 2:
                    dx = TILE_SIZE + BUFFER
                    dy = 0
            display.draw(Surface((TILE_SIZE, TILE_SIZE), SRCALPHA), (BAG_SIZE + 2 * BUFFER, BUFFER))
            if Player.PLAYER == self:
                if Player.COMMANDED is not None:
                    Player.COMMANDED.draw(display, BAG_SIZE + 2 * BUFFER, BUFFER)
                elif Player.SELECTED is not None:
                    Player.SELECTED.draw(display, BAG_SIZE + 2 * BUFFER, BUFFER)
        self._bag.draw(display)

    def take_turn(self):
        """Handles the logic of getting user input on what to do for the player's turn.

        Operates based on what is currently in the self._choices dict, a special dict whose format is documented in
            docs/choice_formats.txt. The dict should contain all the things the player could legally do at the moment.
            In order for this to be true, game.py should maintain the dict for the player, updating it as needed any
            time the board state changes.

        :return: special dict called "choice", whose format is documented in docs/choice_formats.txt
        """
        # TODO: get user input on what they want to do instead of hard coding
        Player.PLAYER = self
        while(Player.CHOICE is None):
            sleep(0.1)  # wait for UI input
        Player.PLAYER = None
        Player.SELECTED = None
        Player.COMMANDED = None
        choice = Player.CHOICE
        if choice['action_type'] == 'pull':  # need to actually draw the new tile here
            x, y = choice['src_location']
            choice['tile'] = self.play_new_troop_tile(x, y)
        Player.CHOICE = None
        return choice

    def play_new_troop_tile(self, x, y, tile=None):
        """Pulls a random troop from the bag and puts it into play at location (x, y).

        This function assumes that the caller first checks that the action is allowed.

        :param x: x-coordinate of location at which the new tile will be played
        :param y: y-coordinate of location at which the new tile will be played
        :param tile: Troop object of the Troop being played
            In ordinary gameplay, you cannot choose what tile to pull. However, there are some circumstances, such as
            when the AI tests what would happen if they pulled a specific piece, in which this optional parameter might
            be used.
        :return: Troop object of the troop that was played.
        """
        if not isinstance(tile, Troop):
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
        tile = self._get_tile_with_coords(x, y)
        if tile is not None:
            self._in_play.remove(tile)
            tile.set_in_play(False)
            tile.set_captured(is_captured)
        return tile

    def _get_tile_with_coords(self, x, y):
        """Searches for the troop in this player's self._in_play list with coordinates (x, y).

        :param x: x-coordinate of location being searched
        :param y: y-coordinate of location being searched
        :return: Troop object of the troop found at (x, y), or None if no troop could be found
        """
        for troop_tile in self._in_play:
            i, j = troop_tile.coords
            if i == x and j == y:
                return troop_tile
        return None  # not found

    def handle_clickable_hovers(self, display, x, y):
        self._bag.handle_bag_hovers(display, x, y, self._side)
        handle_offer_draw_hovers(display, x, y)
        handle_forfeit_hovers(display, x, y)
        # note that tile hovers are handled by the board, because you may want to hover over opponent tiles

    def handle_clickable_clicked(self):
        if self._bag.state == Bag.SELECTED:
            self._bag.set_state(Bag.SELECTABLE)
        elif self._bag.hovered:
            if self._bag.state == Bag.SELECTABLE:
                self._bag.set_state(Bag.SELECTED)
        if Player.OFFER_DRAW_HOVERED:
            pass  # TODO
        if Player.FORFEIT_HOVERED:
            pass  # TODO
