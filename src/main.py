"""
main.py
Isaac Jung
Code adapted from https://pythonprogramming.net/.

This module contains the main logic for starting up the game.
"""

import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = 'hide'
import pygame
from src.game import Game
from src.display import Display
from src.constants import DISPLAY_WIDTH, DISPLAY_HEIGHT, GAME_WINDOW_ICON, GAME_WINDOW_TITLE

pygame.init()
display = Display(DISPLAY_WIDTH, DISPLAY_HEIGHT)
# display.toggle_theme()
display.draw_bg()
pygame.display.set_icon(GAME_WINDOW_ICON)
pygame.display.set_caption(GAME_WINDOW_TITLE)
clock = pygame.time.Clock()

game = Game()
crashed = False

while not crashed:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            crashed = True

    game.update(display)

    pygame.display.update()
    clock.tick(60)
    if not game.is_finished and not game.debug_flag:
        clock.tick(1)  # purposely delay, so that we can see the next line happen live
        game.take_turn()

pygame.quit()
quit()
