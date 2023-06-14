"""
main.py
Isaac Jung
Code adapted from https://pythonprogramming.net/.

This module contains the main logic for starting up the game.
"""

import pygame
import src.constants as cnst
from src.game import Game

pygame.init()

game_display = pygame.display.set_mode((cnst.DISPLAY_WIDTH, cnst.DISPLAY_HEIGHT))
pygame.display.set_icon(pygame.image.load(cnst.GAME_WINDOW_ICON))
pygame.display.set_caption(cnst.GAME_WINDOW_TITLE)
clock = pygame.time.Clock()

game = Game()
crashed = False

while not crashed:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            crashed = True

    game.update(game_display)

    pygame.display.update()
    clock.tick(60)

pygame.quit()
quit()
