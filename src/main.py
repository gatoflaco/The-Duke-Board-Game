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
from src.constants import DISPLAY_WIDTH, DISPLAY_HEIGHT, GAME_WINDOW_ICON, GAME_WINDOW_TITLE, CPU_BOUND_MUTEX
import threading


def main_menu_loop():
    # TODO: make a main menu
    while True:
        game_loop()
        crashed = True
        break


def game_loop():
    while not game.is_finished and not game.debug_flag:
        clock.tick(1)  # purposely delay, so that we can see the next line happen live
        game.take_turn()


pygame.init()
display = Display(DISPLAY_WIDTH, DISPLAY_HEIGHT)
pygame.display.set_icon(GAME_WINDOW_ICON)
pygame.display.set_caption(GAME_WINDOW_TITLE)
clock = pygame.time.Clock()

game = Game()
crashed = False
previous_theme_toggle_hovered = False

threading.Thread(target=main_menu_loop, daemon=True).start()

while not crashed:
    theme_toggle_hovered = display.theme_toggle_hovered
    if not previous_theme_toggle_hovered and theme_toggle_hovered:
        display.handle_theme_toggle_hovered()
    elif previous_theme_toggle_hovered and not theme_toggle_hovered:
        display.handle_theme_toggle_unhovered()
    previous_theme_toggle_hovered = theme_toggle_hovered

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            crashed = True
        if event.type == pygame.MOUSEBUTTONUP:
            if theme_toggle_hovered:
                with CPU_BOUND_MUTEX:
                    display.toggle_theme()

    if not CPU_BOUND_MUTEX.locked():
        game.update(display)
    pygame.display.update()
    clock.tick(60)

pygame.quit()
quit()
