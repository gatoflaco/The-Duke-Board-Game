"""
game.py
Isaac Jung

This module contains all the code related to popup modals.
"""

from pygame import SRCALPHA, Surface
from src.display import Theme
from src.constants import (MODAL_COLOR_LIGHT_MODE, MODAL_COLOR_DARK_MODE, SHADER_COLOR_LIGHT_MODE,
                           SHADER_COLOR_DARK_MODE, TITLE_BAR_HEIGHT, MODAL_CLOSE_PNG, MODAL_CLOSE_SIZE, MODAL_DONE_PNG,
                           MODAL_DONE_WIDTH, MODAL_DONE_HEIGHT)


def close_modal():
    Modal.MODAL = None


class Modal:
    MODAL = None  # If set, overrides main event loop. Note that only one modal may be set at a time.

    def __init(self, title, display, width, height):
        self.__title = title
        self.__bg = Surface((display.width, display.height), SRCALPHA)
        self.__bg.blit(display, (0, 0))
        shader = Surface((display.width, display.height))
        shader.fill(SHADER_COLOR_DARK_MODE if display.theme == Theme.DARK else SHADER_COLOR_LIGHT_MODE)
        shader.set_alpha(150)
        self.__bg.blit(shader, (0, 0))
        self.__modal = Surface((width, height + TITLE_BAR_HEIGHT), SRCALPHA)
        self.__modal.fill(MODAL_COLOR_DARK_MODE if display.theme == Theme.DARK else MODAL_COLOR_LIGHT_MODE)
        self.__title_bar = Surface((width, TITLE_BAR_HEIGHT), SRCALPHA)
        self.__components = {
            'close': {
                'image': Surface((MODAL_CLOSE_SIZE, MODAL_CLOSE_SIZE), SRCALPHA),
                'location': self.calculate_close_location(),
                'was_hovered': False,
                'is_hovered': False,
                'hovered_handler': self.draw_close,
                'clicked_handler': close_modal,
                'resized_handler': self.calculate_close_location
            },
            'done': {
                'image': Surface((MODAL_DONE_WIDTH, MODAL_DONE_HEIGHT), SRCALPHA),
                'location': self.calculate_done_location(),
                'was_hovered': False,
                'is_hovered': False,
                'hovered_handler': self.draw_done,
                'clicked_handler': close_modal,
                'clicked_args': (),
                'resized_handler': self.calculate_done_location
            }
        }

    def draw(self, display):
        display.blit()

    def draw_close(self):
        pass

    def draw_done(self):
        pass

    def calculate_close_location(self):
        pass

    def calculate_done_location(self):
        pass
