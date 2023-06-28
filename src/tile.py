"""
tile.py
Isaac Jung

This module contains all code related to tiles that are placed on the board.
"""

import pygame
from src.constants import DISPLAY_WIDTH, BOARD_SIZE, TILE_SIZE


class Tile:
    """Base class for all tiles.

    Tiles are placed on the board. Different types include troop tiles,
    terrain tiles, and enhanced tiles. All tiles must maintain coordinates
    on the board and have a definition for being drawn

    Parameters
    ----------
    name : string
        Name of the tile. Must match the spelling and capitalization of the
        associated png file in assets/pngs/tiles.
    coords : tuple of integers (optional; (0, 0) by default)
        Coordinates on the board. (0, 0) is the bottom left.
    """

    def __init__(self, name, coords=(0, 0)):
        self.name = name
        self.image = pygame.image.load('assets/pngs/tiles/' + self.name + '.png')
        self.image.fill((0, 0, 0, 0), (128, 0, 256, 128))
        self.coords = coords

    def get_name(self):
        return self.name

    def get_coords(self):
        return self.coords

    def draw(self, game_display):
        x = int((DISPLAY_WIDTH - BOARD_SIZE) / 2) + 5 + (TILE_SIZE + 6) * self.coords[0]
        y = BOARD_SIZE - (TILE_SIZE + 5 + (TILE_SIZE + 6) * self.coords[1])
        game_display.blit(self.image, (x, y))


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
        self.__player_side = player_side
        self.__in_play = in_play
        self.__is_captured = False
        self.__side = 1

    def set_in_play(self, in_play=True):
        self.__in_play = in_play

    def set_captured(self, is_captured=True):
        self.__is_captured = is_captured

    def get_player(self):
        return self.__player_side

    def move(self, x, y):
        if not self.__in_play:
            return False
        self.coords = (x, y)
        return True

    def flip(self):
        self.image = pygame.image.load('assets/pngs/tiles/' + self.name + '.png')  # reload image
        if self.__side == 1:  # on side 1, about to flip to side 2
            self.__side = 2
            self.image.scroll(-TILE_SIZE, 0)  # copies the area on the right over to the area on the left
        else:
            self.__side = 1
        self.image.fill((0, 0, 0, 0), (TILE_SIZE, 0, TILE_SIZE*2, TILE_SIZE))  # covers the 128x128 area on the right

    def draw(self, game_display):
        if self.__player_side == 1:
            super(Troop, self).draw(game_display)
        else:
            # TODO: figure out how to rotate the png 180 degrees and then draw it
            pass
