"""
constants.py
Isaac Jung

This module simply contains all the constants used by other modules.
"""

from pygame import Color, image
from json import load

# main constants
DISPLAY_WIDTH = 1452  # game window width
DISPLAY_HEIGHT = 836  # game window height
GAME_WINDOW_ICON = image.load('assets/pngs/icon_small.png')  # icon that displays in upper corner of game window
GAME_WINDOW_TITLE = 'The Duke'  # string that displays as title of game window

# display constants
BUFFER = 20
THEME_TOGGLE_PNG = image.load('assets/pngs/theme_toggle.png')
THEME_TOGGLE_WIDTH = 128  # width of a single toggler
THEME_TOGGLE_HEIGHT = 64  # height of a single toggler
SETTINGS_PNG = image.load('assets/pngs/settings.png')
SETTINGS_SIZE = 64
HELP_PNG = image.load('assets/pngs/help.png')
HELP_SIZE = 64
BG_COLOR_LIGHT_MODE = Color(232, 230, 220)
TEXT_COLOR_LIGHT_MODE = Color(15, 15, 15)
BG_COLOR_DARK_MODE = Color(56, 52, 52)
TEXT_COLOR_DARK_MODE = Color(215, 215, 225)
TEXT_FONT_SIZE = 18
TEXT_BUFFER = 6

# game constants
OFFER_DRAW_PNG = image.load('assets/pngs/draw.png')
OFFER_DRAW_SIZE = 64
FORFEIT_PNG = image.load('assets/pngs/forfeit.png')
FORFEIT_SIZE = 64

# board constants
BOARD_PNG = image.load('assets/pngs/board.png')  # png for the game board, note that dimensions must be square
BOARD_DARK_PNG = image.load('assets/pngs/board_dark.png')  # for dark mode theme
BOARD_SIZE = BOARD_PNG.get_width()  # width and height of the board
FILES = ['A', 'B', 'C', 'D', 'E', 'F']
RANKS = ['1', '2', '3', '4', '5', '6']
HOVERED_HIGHLIGHT = Color(255, 215, 0)  # gold
MOV_HIGHLIGHT = Color(0, 255, 190)  # sea green
STR_HIGHLIGHT = Color(255, 10, 10)  # red
CMD_HIGHLIGHT = Color(255, 105, 0)  # orange

# player constants
PLAYER_COLORS = [  # list of colors associated with each player
    Color(100, 150, 255),  # blue
    Color(0, 255, 25)  # green
]

# tile constants
with open('data/tiles/types.json') as f:
    TILE_TYPES = load(f)  # data structure listing all tile types
TILE_PNGS = {}  # dict mapping names of tiles to their pngs
for tile_type in TILE_TYPES:
    for tile_name in TILE_TYPES[tile_type]:
        TILE_PNGS[tile_name] = image.load('assets/pngs/tiles/' + tile_name + '.png')
TILE_SIZE = 128  # width and height of a single tile, must be small enough to fit within a single space on the board
STARTING_TROOPS = ['Duke', 'Footman', 'Footman']
with open('data/tiles/movements.json') as f:
    TROOP_MOVEMENTS = load(f)  # data structure listing all troop movements

# ai constants
with open('data/ai/troop_weights.json') as f:
    TROOP_WEIGHTS = load(f)
MEAN_PULL_WEIGHT = sum([value['1'] for value in TROOP_WEIGHTS.values()])//len(TROOP_WEIGHTS)
MIN_TURN_TIME = 2

# bag constants
BAG_PNG = image.load('assets/pngs/bag.png')  # png for player bags
BAG_SIZE = 128  # width and height of a single bag
