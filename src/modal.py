"""
game.py
Isaac Jung

This module contains all the code related to popup modals.
"""

from pygame import font, SRCALPHA, Surface
from src.display import Theme
from src.constants import (TEXT_COLOR_LIGHT_MODE, TEXT_COLOR_DARK_MODE, TEXT_FONT_SIZE, MODAL_COLOR_LIGHT_MODE,
                           MODAL_COLOR_DARK_MODE, SHADER_COLOR_LIGHT_MODE, SHADER_COLOR_DARK_MODE, TITLE_BAR_HEIGHT,
                           TITLE_BAR_COLOR_LIGHT_MODE, TITLE_BAR_COLOR_DARK_MODE, MODAL_CLOSE_PNG, MODAL_CLOSE_SIZE,
                           MODAL_DONE_PNG, MODAL_DONE_WIDTH, MODAL_DONE_HEIGHT)


class ModalInstantiationError(Exception):
    pass


class Modal:
    MODAL = None  # If set, overrides main event loop. Note that only one modal may be set at a time.

    def __init__(self, title, display, width, height):
        if Modal.MODAL is not None:
            raise ModalInstantiationError('Modal.MODAL is not None. No more than one modal may be set at once.')
        self._title = title
        self._display = display
        self._bg = Surface((display.width, display.height), SRCALPHA)
        self._bg.blit(display.surface, (0, 0))
        self._shader = Surface((display.width, display.height))
        self._shader.fill(SHADER_COLOR_DARK_MODE if display.theme == Theme.DARK else SHADER_COLOR_LIGHT_MODE)
        self._shader.set_alpha(150)
        self._bg.blit(self._shader, (0, 0))
        self._modal = Surface((width, height + TITLE_BAR_HEIGHT), SRCALPHA)
        self._modal.fill(MODAL_COLOR_DARK_MODE if display.theme == Theme.DARK else MODAL_COLOR_LIGHT_MODE)
        self._title_bar = Surface((width, TITLE_BAR_HEIGHT), SRCALPHA)
        self._title_bar.fill(TITLE_BAR_COLOR_DARK_MODE if display.theme == Theme.DARK else TITLE_BAR_COLOR_LIGHT_MODE)
        font_to_use = font.Font(font.get_default_font(), TEXT_FONT_SIZE)
        text_surface = font.Font.render(font_to_use, title, True,
                                        TEXT_COLOR_DARK_MODE if display.theme == Theme.DARK else TEXT_COLOR_LIGHT_MODE)
        self._title_bar.blit(text_surface, ((TITLE_BAR_HEIGHT - TEXT_FONT_SIZE) // 2,
                                            (TITLE_BAR_HEIGHT - TEXT_FONT_SIZE) // 2))
        self._modal.blit(self._title_bar, (0, 0))
        self._components = {
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
        for component in self._components.values():
            component['hovered_handler']()  # draws the component onto self._modal

    def draw_all(self):
        self._display.blit(self._bg, (0, 0))
        self._display.blit(self._modal, ((self._display.width - self._modal.get_width()) // 2,
                                         (self._display.height - self._modal.get_height()) // 2))

    def draw_close(self):
        self._components['close']['image'] = Surface((MODAL_CLOSE_SIZE, MODAL_CLOSE_SIZE), SRCALPHA)
        if not self._components['close']['is_hovered']:
            if self._display.theme == Theme.LIGHT:
                self._components['close']['image'].blit(MODAL_CLOSE_PNG, (0, 0))
            elif self._display.theme == Theme.DARK:
                self._components['close']['image'].blit(MODAL_CLOSE_PNG, (0, -MODAL_CLOSE_SIZE))
        else:
            if self._display.theme == Theme.LIGHT:
                self._components['close']['image'].blit(MODAL_CLOSE_PNG, (-MODAL_CLOSE_SIZE, 0))
            elif self._display.theme == Theme.DARK:
                self._components['close']['image'].blit(MODAL_CLOSE_PNG, (-MODAL_CLOSE_SIZE, -MODAL_CLOSE_SIZE))
        self._modal.blit(self._components['close']['image'], self._components['close']['location'])

    def draw_done(self):
        self._components['done']['image'] = Surface((MODAL_DONE_WIDTH, MODAL_DONE_HEIGHT), SRCALPHA)
        if not self._components['done']['is_hovered']:
            if self._display.theme == Theme.LIGHT:
                self._components['done']['image'].blit(MODAL_DONE_PNG, (0, 0))
            elif self._display.theme == Theme.DARK:
                self._components['done']['image'].blit(MODAL_DONE_PNG, (0, -MODAL_DONE_HEIGHT))
        else:
            if self._display.theme == Theme.LIGHT:
                self._components['done']['image'].blit(MODAL_DONE_PNG, (-MODAL_DONE_WIDTH, 0))
            elif self._display.theme == Theme.DARK:
                self._components['done']['image'].blit(MODAL_DONE_PNG, (-MODAL_DONE_WIDTH, -MODAL_DONE_HEIGHT))
        self._modal.blit(self._components['done']['image'], self._components['done']['location'])

    @property
    def component_hovered(self):
        return True in [component['is_hovered'] for component in self._components.values()]  # I hate this

    def handle_component_hovers(self, x, y):
        for component in self._components.values():
            component['is_hovered'] = component['image'].get_rect().collidepoint(
                (x - (self._display.width - self._modal.get_width()) // 2 - component['location'][0],
                 y - (self._display.height - self._modal.get_height()) // 2 - component['location'][1]))
            if (not component['was_hovered'] and component['is_hovered']
                    or component['was_hovered'] and not component['is_hovered']):
                component['hovered_handler']()  # only call handler when hovered state changed
            component['was_hovered'] = component['is_hovered']

    def handle_component_clicks(self):
        for component in self._components.values():
            if component['is_hovered']:
                component['clicked_handler']()

    def calculate_close_location(self):
        return (self._modal.get_width() - MODAL_CLOSE_SIZE - (TITLE_BAR_HEIGHT - MODAL_CLOSE_SIZE) // 2,
                (TITLE_BAR_HEIGHT - MODAL_CLOSE_SIZE) // 2)

    def calculate_done_location(self):
        return (self._modal.get_width() - MODAL_DONE_WIDTH) // 2, self._modal.get_height() - 4 * MODAL_DONE_HEIGHT // 3

    def handle_resize(self, game):
        game.update(self._display)
        self._bg = Surface((self._display.width, self._display.height), SRCALPHA)
        self._bg.blit(self._display.surface, (0, 0))
        self._shader = Surface((self._display.width, self._display.height))
        self._shader.fill(SHADER_COLOR_DARK_MODE if self._display.theme == Theme.DARK else SHADER_COLOR_LIGHT_MODE)
        self._shader.set_alpha(150)
        self._bg.blit(self._shader, (0, 0))
        for component in self._components.values():
            component['location'] = component['resized_handler']()
        # self.draw_all()

    def close_modal(self):
        Modal.MODAL = None
