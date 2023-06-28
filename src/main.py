"""
main.py
Isaac Jung
Code adapted from https://pythonprogramming.net/.

This module contains the main logic for starting up the game.
"""

import pygame
from src.constants import DISPLAY_WIDTH, DISPLAY_HEIGHT, GAME_WINDOW_ICON, GAME_WINDOW_TITLE
from src.game import Game

pygame.init()

game_display = pygame.display.set_mode((DISPLAY_WIDTH, DISPLAY_HEIGHT))
pygame.display.set_icon(pygame.image.load(GAME_WINDOW_ICON))
pygame.display.set_caption(GAME_WINDOW_TITLE)
clock = pygame.time.Clock()

game = Game()
# game.take_turn()  # TODO: move this somewhere else, it's just for testing right now
crashed = False

while not crashed:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            crashed = True

    game.update(game_display)

    pygame.display.update()
    clock.tick(60)
    if game.get_turn() == 0:  # TODO: move this somewhere else, it's just for testing right now
        clock.tick(1)  # purposely delay, so that we can see the next line happen live
        game.take_turn()

pygame.quit()
quit()
