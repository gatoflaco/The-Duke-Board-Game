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
from src.constants import GAME_WINDOW_ICON, GAME_WINDOW_TITLE
from threading import Thread


class Global:
    CRASHED = False


def main_menu_loop():
    # TODO: make a main menu
    while True:
        game_loop()
        display.set_help_callback()
        break
    # Global.CRASHED = True  # should associate this with a quit menu option


def game_loop():
    with Display.MUTEX:
        game.setup(display)
    clock.tick(1/10)
    while not game.is_finished:
        clock.tick(1)  # purposely delay, so that we can see the next line happen live
        Display.MUTEX.acquire()
        game.take_turn(display)
        Display.MUTEX.release()


pygame.init()
display = Display()
pygame.display.set_icon(GAME_WINDOW_ICON)
pygame.display.set_caption(GAME_WINDOW_TITLE)
clock = pygame.time.Clock()

game = Game()

Thread(target=main_menu_loop, daemon=True).start()

while not Global.CRASHED:
    display.handle_component_hovers()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            # TODO: ask for confirmation, warning of potential lost progress
            Global.CRASHED = True
        if event.type == pygame.MOUSEBUTTONUP:
            if display.component_hovered:
                with Display.MUTEX:
                    display.handle_component_clicks()
        if event.type == pygame.VIDEORESIZE:
            width, height = event.size
            display.handle_resize(width, height)

    if not Display.MUTEX.locked():  # don't refresh the screen while other threads are doing calculations
        with Display.MUTEX:  # block other threads from doing calculations while the screen is being updated
            game.update(display)
    pygame.display.update()
    clock.tick(60)

pygame.quit()
quit()
