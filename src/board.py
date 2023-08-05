"""
board.py
Isaac Jung

This module contains all code related to the board.
"""

from pygame import mouse, Surface
from src.display import Display, Theme
from src.player import Player
from src.tile import Tile
from src.constants import (BUFFER, TEXT_BUFFER, BOARD_PNG, BOARD_DARK_PNG, BOARD_SIZE, FILES, RANKS, HOVERED_HIGHLIGHT,
                           MOV_HIGHLIGHT, STR_HIGHLIGHT, CMD_HIGHLIGHT, TILE_SIZE, BAG_SIZE)


def highlight(display, location, color):
    """Puts a low opacity highlight over tiles at the given locations.

    Used to show the player where a selected tile can take various actions.
    Different colors should be used for different types of actions.

    :param display: Display object containing the main game window
    :param location: (x, y)-coordinates of tile over which the given highlight should be drawn on the board
    :param color: pygame.color.Color to be used for highlighting
    """
    shader = Surface((TILE_SIZE + 2, TILE_SIZE + 2))
    shader.fill(color)
    shader.set_alpha(75 if display.theme == Theme.DARK else 150)
    x = (display.width - BOARD_SIZE) // 2 + 4 + (TILE_SIZE + 6) * location[0]
    y = BOARD_SIZE - (TILE_SIZE + 6 + (TILE_SIZE + 6) * location[1])
    display.blit(shader, (x, y))


class Board:
    """Represents the physical board on which the game is played.

    The board is a 6x6 grid that can be represented as a 2D array.
    When a tile is placed on the board, it occupies one (x, y)-coordinate on this grid, or one index in the 2D array.
    """

    def __init__(self):
        self.__grid = [[None] * 6 for _ in range(6)]
        self.__hovered = None  # coordinates of tile being hovered
        self.__held = None

    def copy(self, players):
        """Unusual implementation of self cloning that requires players to be cloned separately.

        Because players and the board they are playing on share references to their tiles, one or the other must be
        solely responsible for copying the tile objects referenced by both.

        :param players: tuple of Player objects of players whose tiles should be played on the new board
            As noted in the description, the expectation is that these Player objects are themselves copies of others.
        :return:
        """
        cls = self.__class__
        result = cls.__new__(cls)
        result.__grid = [[None] * 6 for _ in range(6)]
        for player in players:
            for tile in player.tiles_in_play:
                x, y = tile.coords
                result.set_tile(x, y, tile)
        result.__hovered = None
        return result

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
            if isinstance(tile, Tile) and self.__held != tile:
                tile.draw(display)
        if isinstance(Player.PLAYER, Player):
            if Player.PLAYER.bag_clicked:
                for location in Player.PLAYER.choices['pull']:
                    highlight(display, location, HOVERED_HIGHLIGHT)
            else:
                if isinstance(Player.COMMANDED, Tile):
                    for location in Player.PLAYER.choices['act'][Player.SELECTED.coords]['commands'][tile.coords]:
                        highlight(display, location, MOV_HIGHLIGHT)
                elif isinstance(Player.SELECTED, Tile) and Player.SELECTED.coords in Player.PLAYER.choices['act']:
                    # TODO: draw ? and x buttons on tile
                    for location in Player.PLAYER.choices['act'][Player.SELECTED.coords]['moves']:
                        highlight(display, location, MOV_HIGHLIGHT)
                    for location in Player.PLAYER.choices['act'][Player.SELECTED.coords]['strikes']:
                        highlight(display, location, STR_HIGHLIGHT)
                    for location in Player.PLAYER.choices['act'][Player.SELECTED.coords]['commands']:
                        highlight(display, location, CMD_HIGHLIGHT)
        if isinstance(self.__held, Tile):
            x, y = mouse.get_pos()
            self.__held.draw(display, x - TILE_SIZE // 2, y - TILE_SIZE // 2)
        elif self.__hovered is not None:
            highlight(display, self.__hovered, HOVERED_HIGHLIGHT)

    def lock_hovers(self):
        self.__hovered = None

    def handle_tile_hovers(self, display, x, y):
        tile_x = (x - (display.width - BOARD_SIZE) // 2 - 5) // (TILE_SIZE + 6)
        tile_y = (BOARD_SIZE - 5 - y) // (TILE_SIZE + 6)
        if not (0 <= tile_x < 6 and 0 <= tile_y < 6):
            self.__hovered = None
            return
        self.__hovered = (tile_x, tile_y)

    def handle_tile_held(self):
        if Player.SELECTED is None and self.__hovered in Player.PLAYER.choices['act']:
            self.__held = self.__grid[self.__hovered[0]][self.__hovered[1]]
            Player.SELECTED = self.__held
        elif (Player.SELECTED is not None and Player.COMMANDED is None and self.__hovered in
              Player.PLAYER.choices['act'][Player.SELECTED.coords]['commands']):
            self.__held = self.__grid[self.__hovered[0]][self.__hovered[1]]
            Player.COMMANDED = self.__held

    def handle_tile_clicked(self):
        if self.__hovered is None:  # click must have been off the board, definitely goes back one state
            if Player.COMMANDED is not None:
                Player.COMMANDED = None
            elif Player.SELECTED is not None:
                Player.SELECTED = None
        else:
            if Player.PLAYER.bag_clicked:
                if self.__hovered in Player.PLAYER.choices['pull']:
                    Player.CHOICE = {
                        'action_type': 'pull',
                        'src_location': self.__hovered,
                        'tile': None
                    }
                    Display.MUTEX.acquire()  # to be released by the game thread
                else:  # player clicked somewhere they aren't allowed to play a tile
                    pass  # in player.py, handle_clickable_clicked() should handle going back a state
            elif Player.COMMANDED is not None:  # when True, Player.SELECTED must also not be None
                if (self.__hovered in
                        Player.PLAYER.choices['act'][Player.SELECTED.coords]['commands'][Player.COMMANDED.coords]):
                    Player.CHOICE = {
                        'action_type': 'cmd',
                        'src_location': Player.SELECTED.coords,
                        'dst_location': self.__hovered,
                        'cmd_location': Player.COMMANDED.coords,
                    }
                    Display.MUTEX.acquire()  # to be released by the game thread
                else:  # player clicked somewhere they aren't allowed to command the commanded troop to move
                    Player.COMMANDED = None  # go back a state
            elif Player.SELECTED is not None:
                if Player.SELECTED.coords not in Player.PLAYER.choices['act']:  # selected tile (maybe enemy) can't act
                    Player.SELECTED = None
                elif (self.__hovered in Player.PLAYER.choices['act'][Player.SELECTED.coords]['commands'] and
                      self.__held is None):
                    Player.COMMANDED = self.__grid[self.__hovered[0]][self.__hovered[1]]
                elif self.__hovered in Player.PLAYER.choices['act'][Player.SELECTED.coords]['strikes']:
                    Player.CHOICE = {
                        'action_type': 'str',
                        'src_location': Player.SELECTED.coords,
                        'str_location': self.__hovered
                    }
                    Display.MUTEX.acquire()  # to be released by the game thread
                elif self.__hovered in Player.PLAYER.choices['act'][Player.SELECTED.coords]['moves']:
                    Player.CHOICE = {
                        'action_type': 'mov',
                        'src_location': Player.SELECTED.coords,
                        'dst_location': self.__hovered
                    }
                    Display.MUTEX.acquire()  # to be released by the game thread
                elif self.__held is not None and self.__hovered == self.__held.coords:  # player was not trying to drag
                    self.__held = None  # stop considering the clicked tile to be held
                else:  # player clicked somewhere they aren't allowed to move, strike, or command with selected troop
                    Player.SELECTED = None  # go back a state
            else:
                Player.SELECTED = self.__grid[self.__hovered[0]][self.__hovered[1]]
        if self.__held is not None:
            self.__held = None
