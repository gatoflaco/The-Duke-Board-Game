"""
board.py
Isaac Jung

This module contains all code related to the board.
"""

from pygame import mouse, SRCALPHA, Surface, transform
from src.display import Display, Theme
from src.player import Player
from src.tile import Tile
from src.util import convert_board_x_coordinate_to_file, convert_board_y_coordinate_to_rank
from src.constants import (TEXT_BUFFER, BOARD_PNG, BOARD_DARK_PNG, BOARD_SIZE, FILES, RANKS, HOVERED_HIGHLIGHT,
                           MOV_HIGHLIGHT, STR_HIGHLIGHT, CMD_HIGHLIGHT, CHECK_PNG, TILE_SIZE)
from time import sleep


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
    ANIMATING = False  # used to prevent redrawing the board during an animation

    def __init__(self):
        self.__grid = [[None] * 6 for _ in range(6)]
        self.__hovered = None  # coordinates of tile being hovered
        self.__held = None
        self.__mirrored = False

    def copy(self, players):
        """Unusual implementation of self cloning that requires players to be cloned separately.

        Because players and the board they are playing on share references to their tiles, one or the other must be
        solely responsible for copying the tile objects referenced by both. This function assumes that the Player
        objects will make copies of the Tile objects on the board, therefore the caller should first make copies of the
        Player objects, and pass those copies to this function.

        :param players: tuple of Player objects of players whose tiles should be played on the new board
            As noted in the description, the expectation is that these Player objects are themselves copies of others.
        :return: Board object of the copied board
        """
        cls = self.__class__
        result = cls.__new__(cls)
        result.__grid = [[None] * 6 for _ in range(6)]
        for player in players:
            for tile in player.tiles_in_play:
                x, y = tile.coords
                result.set_tile(x, y, tile)
        result.__hovered = self.__hovered
        result.__held = self.__held
        result.__mirrored = self.__mirrored
        return result

    def set_tile(self, x, y, tile):
        self.__grid[x][y] = tile

    def get_tile(self, x, y):
        return self.__grid[x][y]

    @property
    def hovered(self):
        return self.__hovered

    def set_held(self, tile):
        self.__held = tile

    @property
    def held_tile(self):
        return self.__held

    def mirror(self):
        self.__mirrored = not self.__mirrored

    @property
    def is_mirrored(self):
        return self.__mirrored

    def animate_rotation(self, display):
        """Shows an animation of the board rotating.

        Code adapted from https://www.pygame.org/wiki/RotateCenter.

        :param display: Display object containing the main game window
        """
        with Display.MUTEX:  # waits for current frame to finish drawing
            Board.ANIMATING = True  # tells other modules not to draw the board (other things may still be rendered)
        current_board_image = Surface((BOARD_SIZE, BOARD_SIZE), SRCALPHA)
        current_board_image.blit(display.surface, ((BOARD_SIZE - display.width) // 2, 0))
        for angle in range(1, 181, 2):
            orig_rect = current_board_image.get_rect()
            rot_image = transform.rotate(current_board_image, angle)
            rot_rect = orig_rect.copy()
            rot_rect.center = rot_image.get_rect().center
            rot_image = rot_image.subsurface(rot_rect).copy()
            display.blit(rot_image, ((display.width - BOARD_SIZE) // 2, 0))
            sleep(1 / 720)
        self.__mirrored = not self.is_mirrored  # flip internal state
        Board.ANIMATING = False  # allow other modules to start drawing the board again

    def draw_check(self, display, duke_coords):
        duke_x, duke_y = duke_coords  # Duke's coordinates on the grid
        x, y = (duke_x + 1, duke_y) if not self.__mirrored else (6 - duke_x, 5 - duke_y)  # coords could be mirrored
        display.blit(CHECK_PNG, ((display.width - BOARD_SIZE) // 2 + 5 + (TILE_SIZE + 6) * x - CHECK_PNG.get_size()[0],
                                 BOARD_SIZE - (TILE_SIZE + 5 + (TILE_SIZE + 6) * y)))

    def draw_held(self, display):
        x, y = mouse.get_pos()
        self.__held.draw(display, x - TILE_SIZE // 2, y - TILE_SIZE // 2, self.__mirrored)

    def draw(self, display):
        """Draws the board and every tile on it to the screen.

        After drawing the base board and tiles on it, this function also draws highlights over a live player's selected
        options. Other functions are responsible for updating the state variables associated with this feature.

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
                selected = Player.SELECTED
                commanded = Player.COMMANDED
                if isinstance(commanded, Tile):
                    for location in Player.PLAYER.choices['act'][selected.coords]['commands'][commanded.coords]:
                        highlight(display, location, MOV_HIGHLIGHT)
                elif isinstance(selected, Tile) and selected.coords in Player.PLAYER.choices['act']:
                    for location in Player.PLAYER.choices['act'][selected.coords]['moves']:
                        highlight(display, location, MOV_HIGHLIGHT)
                    for location in Player.PLAYER.choices['act'][selected.coords]['strikes']:
                        highlight(display, location, STR_HIGHLIGHT)
                    for location in Player.PLAYER.choices['act'][selected.coords]['commands']:
                        highlight(display, location, CMD_HIGHLIGHT)
            if self.__hovered is not None:
                highlight(display, self.__hovered, HOVERED_HIGHLIGHT)
        if self.__mirrored:
            current_board_image = Surface((BOARD_SIZE, BOARD_SIZE), SRCALPHA)
            current_board_image.blit(display.surface, ((BOARD_SIZE - display.width) // 2, 0))
            display.blit(transform.rotate(current_board_image, 180), ((display.width - BOARD_SIZE) // 2, 0))

    def lock_hovers(self):
        self.__hovered = None

    def handle_tile_hovers(self, display, x, y):
        tile_x = (x - (display.width - BOARD_SIZE) // 2 - 5) // (TILE_SIZE + 6)
        tile_y = (BOARD_SIZE - 5 - y) // (TILE_SIZE + 6)
        if not (0 <= tile_x < 6 and 0 <= tile_y < 6):
            self.__hovered = None
            Player.FILE = '-'
            Player.RANK = '-'
            return
        self.__hovered = (tile_x, tile_y) if not self.__mirrored else (5 - tile_x, 5 - tile_y)
        Player.FILE = convert_board_x_coordinate_to_file(tile_x)
        Player.RANK = convert_board_y_coordinate_to_rank(tile_y)

    def handle_tile_held(self):
        if Player.SETUP:
            return
        if (Player.SELECTED is not None and Player.SELECTED.coords in Player.PLAYER.choices['act'] and self.__hovered in
                Player.PLAYER.choices['act'][Player.SELECTED.coords]['commands']):
            if Player.COMMANDED is not None:
                if Player.COMMANDED.coords == self.__hovered:
                    self.__held = None
                elif Player.SELECTED.coords == self.__hovered:
                    self.__held = self.__grid[self.__hovered[0]][self.__hovered[1]]
                    Player.SELECTED = self.__held
                    Player.COMMANDED = None
            else:
                self.__held = self.__grid[self.__hovered[0]][self.__hovered[1]]
                Player.COMMANDED = self.__held
        elif self.__hovered in Player.PLAYER.choices['act']:
            if Player.COMMANDED is None and Player.SELECTED is not None and Player.SELECTED.coords == self.__hovered:
                self.__held = None
            else:
                self.__held = self.__grid[self.__hovered[0]][self.__hovered[1]]
                Player.SELECTED = self.__held
                Player.COMMANDED = None

    def handle_tile_clicked(self):
        if self.__hovered is None:  # click must have been off the board, definitely goes back one state
            if Player.COMMANDED is not None:
                Player.COMMANDED = None
            elif Player.SELECTED is not None:
                Player.SELECTED = None
        else:
            if Player.PLAYER.bag_clicked:
                if self.__hovered in Player.PLAYER.choices['pull']:
                    Player.PLAYER = None
                    Player.CHOICE = {
                        'action_type': 'pull',
                        'src_location': self.__hovered,
                        'tile': None
                    }
                    Display.MUTEX.acquire()  # to be released by the game thread
                elif Player.SETUP:  # during setup, bag should be set to clicked state throughout
                    return  # don't release the held tile
                else:  # player clicked somewhere they aren't allowed to play a tile (and it's not the setup phase)
                    pass  # in player.py, handle_clickable_clicked() should handle going back a state
            elif Player.COMMANDED is not None:  # when True, Player.SELECTED must also not be None
                if (self.__hovered in
                        Player.PLAYER.choices['act'][Player.SELECTED.coords]['commands'][Player.COMMANDED.coords]):
                    Player.PLAYER = None
                    Player.CHOICE = {
                        'action_type': 'cmd',
                        'src_location': Player.COMMANDED.coords,
                        'dst_location': self.__hovered,
                        'cmd_location': Player.SELECTED.coords,
                    }
                    Display.MUTEX.acquire()  # to be released by the game thread
                elif self.__held is not None and self.__hovered == self.__held.coords:  # player was not trying to drag
                    pass
                else:  # player clicked somewhere they aren't allowed to command the commanded troop to move
                    Player.COMMANDED = None  # go back a state
            elif Player.SELECTED is not None:
                if Player.SELECTED.coords not in Player.PLAYER.choices['act']:  # selected tile (maybe enemy) can't act
                    Player.SELECTED = None
                elif (self.__hovered in Player.PLAYER.choices['act'][Player.SELECTED.coords]['commands'] and
                      self.__held is None):
                    Player.COMMANDED = self.__grid[self.__hovered[0]][self.__hovered[1]]
                elif self.__hovered in Player.PLAYER.choices['act'][Player.SELECTED.coords]['strikes']:
                    Player.PLAYER = None
                    Player.CHOICE = {
                        'action_type': 'str',
                        'src_location': Player.SELECTED.coords,
                        'str_location': self.__hovered
                    }
                    Display.MUTEX.acquire()  # to be released by the game thread
                elif self.__hovered in Player.PLAYER.choices['act'][Player.SELECTED.coords]['moves']:
                    Player.PLAYER = None
                    Player.CHOICE = {
                        'action_type': 'mov',
                        'src_location': Player.SELECTED.coords,
                        'dst_location': self.__hovered
                    }
                    Display.MUTEX.acquire()  # to be released by the game thread
                elif self.__held is not None and self.__hovered == self.__held.coords:  # player was not trying to drag
                    pass
                else:  # player clicked somewhere they aren't allowed to move, strike, or command with selected troop
                    Player.SELECTED = None  # go back a state
            else:
                Player.SELECTED = self.__grid[self.__hovered[0]][self.__hovered[1]]
        self.__held = None  # stop considering the clicked tile to be held

    def handle_escape_key_pressed(self):
        if Player.SETUP or self.__held is not None:
            return  # don't take esc key inputs while dragging a tile
        elif Player.COMMANDED is not None:
            Player.COMMANDED = None
        elif Player.SELECTED is not None:
            Player.SELECTED = None
