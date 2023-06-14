"""
main.py
Isaac Jung
Code adapted from https://pythonprogramming.net/.

This module contains the main logic for starting up the game.
"""

import constants
import pygame
from board import Board

pygame.init()

game_display = pygame.display.set_mode((constants.DISPLAY_WIDTH, constants.DISPLAY_HEIGHT))
pygame.display.set_icon(pygame.image.load(constants.GAME_WINDOW_ICON))
pygame.display.set_caption(constants.GAME_WINDOW_TITLE)

black = (0, 0, 0)
white = (255, 255, 255)

clock = pygame.time.Clock()
crashed = False

# x = (display_width * 0.45)
# y = (display_height * 0.8)

while not crashed:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            crashed = True

    game_display.fill(white)
    board = Board(pygame, game_display)

    pygame.display.update()
    clock.tick(60)

pygame.quit()
quit()
