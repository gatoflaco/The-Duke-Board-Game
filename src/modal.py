"""
game.py
Isaac Jung

This module contains all the code related to popup modals.
"""

from pygame import display as pygame_display, RESIZABLE, SRCALPHA, Surface
from src.display import Theme
from src.constants import (MODAL_COLOR_LIGHT_MODE, MODAL_COLOR_DARK_MODE,
                           SHADER_COLOR_LIGHT_MODE, SHADER_COLOR_DARK_MODE, TITLE_BAR_HEIGHT,
                           TITLE_BAR_COLOR_LIGHT_MODE, TITLE_BAR_COLOR_DARK_MODE, MODAL_CLOSE_PNG, MODAL_CLOSE_SIZE,
                           MODAL_DONE_PNG, MODAL_DONE_WIDTH, MODAL_DONE_HEIGHT)


class ModalInstantiationError(Exception):
    pass


class Modal:
    MODAL = None  # If set, overrides main event loop. Note that only one modal may be set at a time.

    def __init__(self, title, display, width, height):
        if Modal.MODAL is not None:
            raise ModalInstantiationError('Modal.MODAL is not None. No more than one modal may be set at once.')
        self.__title = title
        self.__display = display
        self.__bg = Surface((display.width, display.height), SRCALPHA)
        self.__bg.blit(display.surface, (0, 0))
        shader = Surface((display.width, display.height))
        shader.fill(SHADER_COLOR_DARK_MODE if display.theme == Theme.DARK else SHADER_COLOR_LIGHT_MODE)
        shader.set_alpha(150)
        self.__bg.blit(shader, (0, 0))
        self.__modal = Surface((width, height + TITLE_BAR_HEIGHT), SRCALPHA)
        self.__modal.fill(MODAL_COLOR_DARK_MODE if display.theme == Theme.DARK else MODAL_COLOR_LIGHT_MODE)
        self.__title_bar = Surface((width, TITLE_BAR_HEIGHT), SRCALPHA)
        self.__title_bar.fill(TITLE_BAR_COLOR_DARK_MODE if display.theme == Theme.DARK else TITLE_BAR_COLOR_LIGHT_MODE)
        self.__modal.blit(self.__title_bar, (0, 0))
        self.__components = {
            'close': {
                'image': Surface((MODAL_CLOSE_SIZE, MODAL_CLOSE_SIZE), SRCALPHA),
                'location': self.calculate_close_location(),
                'was_hovered': False,
                'is_hovered': False,
                'hovered_handler': self.draw_close,
                'clicked_handler': self.close_modal,
                'resized_handler': self.calculate_close_location
            },
            'done': {
                'image': Surface((MODAL_DONE_WIDTH, MODAL_DONE_HEIGHT), SRCALPHA),
                'location': self.calculate_done_location(),
                'was_hovered': False,
                'is_hovered': False,
                'hovered_handler': self.draw_done,
                'clicked_handler': self.close_modal,
                'resized_handler': self.calculate_done_location
            }
        }

    def draw_all(self, display):
        display.blit(self.__bg, (0, 0))
        display.blit(self.__modal, ((display.width - self.__modal.get_width()) // 2,
                                    (display.height - self.__modal.get_height()) // 2))
        self.draw_close()
        self.draw_done()

    def draw_close(self):
        self.__components['close']['image'] = Surface((MODAL_CLOSE_SIZE, MODAL_CLOSE_SIZE), SRCALPHA)
        if not self.__components['close']['is_hovered']:
            if self.__display.theme == Theme.LIGHT:
                self.__components['close']['image'].blit(MODAL_CLOSE_PNG, (0, 0))
            elif self.__display.theme == Theme.DARK:
                self.__components['close']['image'].blit(MODAL_CLOSE_PNG, (0, -MODAL_CLOSE_SIZE))
        else:
            if self.__display.theme == Theme.LIGHT:
                self.__components['close']['image'].blit(MODAL_CLOSE_PNG, (-MODAL_CLOSE_SIZE, 0))
            elif self.__display.theme == Theme.DARK:
                self.__components['close']['image'].blit(MODAL_CLOSE_PNG, (-MODAL_CLOSE_SIZE, -MODAL_CLOSE_SIZE))
        self.__display.blit(self.__components['close']['image'], self.__components['close']['location'])

    def draw_done(self):
        self.__components['done']['image'] = Surface((MODAL_DONE_WIDTH, MODAL_DONE_HEIGHT), SRCALPHA)
        if not self.__components['done']['is_hovered']:
            if self.__display.theme == Theme.LIGHT:
                self.__components['done']['image'].blit(MODAL_DONE_PNG, (0, 0))
            elif self.__display.theme == Theme.DARK:
                self.__components['done']['image'].blit(MODAL_DONE_PNG, (0, -MODAL_DONE_HEIGHT))
        else:
            if self.__display.theme == Theme.LIGHT:
                self.__components['done']['image'].blit(MODAL_DONE_PNG, (-MODAL_DONE_WIDTH, 0))
            elif self.__display.theme == Theme.DARK:
                self.__components['done']['image'].blit(MODAL_DONE_PNG, (-MODAL_DONE_WIDTH, -MODAL_DONE_HEIGHT))
        self.__display.blit(self.__components['done']['image'], self.__components['done']['location'])

    @property
    def component_hovered(self):
        return True in [component['is_hovered'] for component in self.__components.values()]  # I hate this

    def handle_component_hovers(self, x, y):
        for component in self.__components.values():
            component['is_hovered'] = component['image'].get_rect().collidepoint(
                (x - component['location'][0], y - component['location'][1]))
            if (not component['was_hovered'] and component['is_hovered']
                    or component['was_hovered'] and not component['is_hovered']):
                component['hovered_handler']()  # only call handler when hovered state changed
            component['was_hovered'] = component['is_hovered']

    def handle_component_clicks(self):
        for component in self.__components.values():
            if component['is_hovered']:
                component['clicked_handler']()

    def calculate_close_location(self):
        return (((self.__display.width - self.__modal.get_width()) // 2 + self.__modal.get_width() - MODAL_CLOSE_SIZE
                 - (TITLE_BAR_HEIGHT - MODAL_CLOSE_SIZE) // 2),
                (self.__display.height - self.__modal.get_height()) // 2 + (TITLE_BAR_HEIGHT - MODAL_CLOSE_SIZE) // 2)

    def calculate_done_location(self):
        return ((self.__display.width - MODAL_DONE_WIDTH) // 2,
                ((self.__display.height - self.__modal.get_height()) // 2
                 + self.__modal.get_height() - 4 * MODAL_DONE_HEIGHT // 3))

    def handle_resize(self, display, game):
        game.update(display)
        self.__bg = Surface((display.width, display.height), SRCALPHA)
        self.__bg.blit(display.surface, (0, 0))
        shader = Surface((display.width, display.height))
        shader.fill(SHADER_COLOR_DARK_MODE if display.theme == Theme.DARK else SHADER_COLOR_LIGHT_MODE)
        shader.set_alpha(150)
        self.__bg.blit(shader, (0, 0))
        for component in self.__components.values():
            component['location'] = component['resized_handler']()
        self.draw_all(display)

    def close_modal(self):
        Modal.MODAL = None
