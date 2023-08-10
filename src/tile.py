"""
tile.py
Isaac Jung

This module contains all code related to tiles that are placed on the board.
"""

from pygame import SRCALPHA, Surface, transform
from src.constants import BOARD_SIZE, PLAYER_COLORS, TILE_PNGS, TILE_SIZE, TILE_SHADER
from copy import copy


class Tile:
    """Base class for all tiles.

    Tiles are placed on the board. Different types include troop tiles, terrain tiles, and enhanced tiles.
    All tiles must maintain coordinates on the board and have a definition for being drawn

    Parameters
    ----------
    name : string
        Name of the tile. Must match the spelling and capitalization of the associated png file in assets/pngs/tiles.
    coords : tuple of integers (optional; (0, 0) by default)
        Coordinates on the board. (0, 0) is the bottom left.
    """

    def __init__(self, name, coords=(0, 0)):
        self._name = name
        self._image = Surface((TILE_SIZE, TILE_SIZE), SRCALPHA)  # creates transparent background
        if name != '':
            self._png = TILE_PNGS[self._name]
            self._image.blit(self._png, (0, 0))  # draw png onto surface, cropping off extra pixels
        self._coords = coords
        self._player_side = 0  # represents that the tile does not belong to any player

    def __copy__(self):
        cls = self.__class__
        result = cls.__new__(cls)
        result._name = self._name
        result._png = self._png
        result._image = copy(self._image)
        result._coords = self._coords
        result._player_side = self._player_side

    @property
    def name(self):
        return self._name

    @property
    def coords(self):
        return self._coords

    @property
    def player_side(self):
        return self._player_side

    def draw(self, display, x=None, y=None, rotated=False):
        """Draws the tile to the screen

        :param display: Display object containing the main game window
        :param x: x-coordinate of pixel location on game window of upper left corner of tile
        :param y: y-coordinate of pixel location on game window of upper left corner of tile
        :param rotated: boolean that causes the tile to be drawn 180 degrees rotated when True
        """
        if (x is None or y is None) and self._player_side != 0:
            bg = Surface((TILE_SIZE + 4, TILE_SIZE + 4))
            bg.fill(PLAYER_COLORS[self._player_side - 1])
            bg_x = (display.width - BOARD_SIZE) // 2 + 3 + (TILE_SIZE + 6) * self._coords[0]
            bg_y = BOARD_SIZE - (TILE_SIZE + 7 + (TILE_SIZE + 6) * self._coords[1])
            display.blit(bg, (bg_x, bg_y))
        if x is None:
            x = (display.width - BOARD_SIZE) // 2 + 5 + (TILE_SIZE + 6) * self._coords[0]
        if y is None:
            y = BOARD_SIZE - (TILE_SIZE + 5 + (TILE_SIZE + 6) * self._coords[1])
        self._image.unlock()
        display.blit(transform.rotate(self._image, 180) if rotated else self._image, (x, y))

    @property
    def image(self):
        return self._image


class Troop(Tile):
    """Tiles that move around and capture each other.

    The game is mainly played with these tiles. The actual types of troop tiles
    are listed in data/tiles/types.json, and their movements are described in
    data/tiles/movements.json.

    Parameters
    ----------
    name : string
        Name of the troop tile. Must match the spelling and capitalization of
        the associated png file in assets/pngs/tiles, as well as within the two
        json files in data/tiles.
    player_side : int
        Needs to be set to 1 for player 1 or 2 for player 2. Represents to whom
        this troop tile belongs.
    coords : tuple of integers (optional; (0, 0) by default)
        Coordinates on the board. (0, 0) is the bottom left.
    in_play : bool (optional; False by default)
        Whether or not the troop tile has been played on the board yet. It
        starts False if it begins in the bag, but it can be initialized to true
        if the troop is being played down as the object is instantiated (for
        example, at the start of the game, players put down their Dukes and two
        Footman troops right away). It is otherwise set to true as soon as the
        unit is played, and then never again set to False (even when captured).
    """

    def __init__(self, name, player_side, coords=(0, 0), in_play=False):
        super(Troop, self).__init__(name, coords)
        self._player_side = player_side
        self.__back_image = Surface((TILE_SIZE, TILE_SIZE), SRCALPHA)
        if name != '':
            self.__back_image.blit(self._png, (-TILE_SIZE, 0))
        if self._player_side == 2:
            self._image = transform.rotate(self._image, 180)
            self.__back_image = transform.rotate(self.__back_image, 180)
        self.__in_play = in_play
        self.__is_captured = False
        self.__side = 1


    def __copy__(self):
        cls = self.__class__
        result = cls.__new__(cls)
        result._name = self._name
        result._png = self._png
        result._image = copy(self._image)
        result._coords = self._coords
        result._player_side = self._player_side
        result.__back_image = copy(self.__back_image)
        result.__in_play = self.__in_play
        result.__is_captured = self.__is_captured
        result.__side = self.__side
        return result

    def set_in_play(self, in_play=True):
        self.__in_play = in_play

    @property
    def is_in_play(self):
        return self.__in_play

    def set_captured(self, is_captured=True):
        self.__is_captured = is_captured

    @property
    def is_captured(self):
        return self.__is_captured

    @property
    def side(self):
        return self.__side

    def move(self, x, y):
        if not self.__in_play:
            return False
        self._coords = (x, y)
        return True

    def flip(self):
        self.__back_image.blit(self._image, (0, 0))
        if self.__side == 1:  # on side 1, about to flip to side 2
            self.__side = 2
            self._image.blit(self._png, (-TILE_SIZE, 0))  # take the base spritesheet and shift it into place
        else:
            self.__side = 1
            self._image.blit(self._png, (0, 0))
        if self._player_side == 2:
            self._image = transform.rotate(self._image, 180)

    def draw_back(self, display, x, y, rotated=False):
        """Draws the backside of the troop tile to the screen

        :param display: Display object containing the main game window
        :param x: x-coordinate of pixel location on game window of upper left corner of tile
        :param y: y-coordinate of pixel location on game window of upper left corner of tile
        :param rotated: boolean that causes the tile to be drawn 180 degrees rotated when True
        """
        display.blit(transform.rotate(self.__back_image, 180) if rotated else self.__back_image, (x, y))
        shader = Surface((TILE_SIZE, TILE_SIZE))
        shader.fill(TILE_SHADER)
        shader.set_alpha(150)
        display.blit(shader, (x, y))
