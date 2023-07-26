"""
constants.py
Isaac Jung

This module simply contains all the constants used by other modules.
"""

from pygame import Color, image
from json import load

# game constants
DISPLAY_WIDTH = 1208  # game window width, must be at least as width of BOARD_PNG + twice the width of BAG_PNG
DISPLAY_HEIGHT = 828  # game window height, must be at least the height of BOARD_PNG
GAME_WINDOW_ICON = image.load('assets/pngs/icon_small.png')  # icon that displays in upper corner of game window
GAME_WINDOW_TITLE = 'The Duke'  # string that displays as title of game window
BG_COLOR_LIGHT_MODE = Color(232, 230, 220)
TEXT_COLOR_LIGHT_MODE = Color(15, 15, 15)
BG_COLOR_DARK_MODE = Color(56, 52, 52)
TEXT_COLOR_DARK_MODE = Color(215, 215, 225)
TEXT_FONT_SIZE = 16
TEXT_BUFFER = 4

# board constants
BOARD_PNG = image.load('assets/pngs/board.png')  # png for the game board, note that dimensions must be square
BOARD_DARK_PNG = image.load('assets/pngs/board_dark.png')  # for dark mode theme
BOARD_SIZE = BOARD_PNG.get_width()  # width and height of the board
BOARD_LOCATION = ((DISPLAY_WIDTH - BOARD_SIZE) // 2, 0)  # pixel position for upper left corner of BOARD_PNG
BOARD_BUFFER = 5
FILES = ['A', 'B', 'C', 'D', 'E', 'F']
RANKS = ['1', '2', '3', '4', '5', '6']

# player constants
PLAYER_COLORS = [  # list of colors associated with each player
    Color(100, 150, 255),  # blue
    Color(255, 10, 10)  # red
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
MOV_HIGHLIGHT = Color(255, 215, 0, 50)  # gold
STR_HIGHLIGHT = Color(150, 255, 100, 50)  # green
CMD_HIGHLIGHT = Color(0, 255, 255, 50)  # cyan

# ai constants
with open('data/ai/troop_weights.json') as f:
    TROOP_WEIGHTS = load(f)
MEAN_PULL_WEIGHT = sum([value['1'] for value in TROOP_WEIGHTS.values()])//len(TROOP_WEIGHTS)

# bag constants
BAG_PNG = image.load('assets/pngs/bag.png')  # png for player bags
BAG_SIZE = 128  # width and height of a single bag
BAG_BUFFER = 20
