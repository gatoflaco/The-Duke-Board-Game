"""
game.py
Isaac Jung

This module contains all the code related to the main UI.
"""

from pygame import display, font, RESIZABLE, SRCALPHA, Surface
from src.constants import (DISPLAY_WIDTH, DISPLAY_HEIGHT, BUFFER, THEME_TOGGLE_PNG, THEME_TOGGLE_WIDTH,
                           THEME_TOGGLE_HEIGHT, SETTINGS_PNG, SETTINGS_SIZE, HELP_PNG, HELP_SIZE, BG_COLOR_LIGHT_MODE,
                           TEXT_COLOR_LIGHT_MODE, BG_COLOR_DARK_MODE, TEXT_COLOR_DARK_MODE, TEXT_FONT_SIZE)
from enum import Enum
from threading import Lock


class Theme(Enum):
    """Enum for light/dark mode themes
    """
    LIGHT = 0
    DARK = 1

    def __invert__(self):
        return Theme(self.value ^ 1)


class Display:
    """Wrapper for pygame.display that includes the theme and some simpler interfaces.

    Parameters
    ----------
    width : int
        Width of the window in pixels.
    height : int
        Height of the window in pixels.
    theme : Theme attribute (optional; Theme.LIGHT by default)
        Affects background and text colors used.
        When not provided, defaults to a light mode theme.
    """
    MUTEX = Lock()  # used to lock screen-update calculations from happening during a screen update and vice versa
    HANDLER_LOCK = Lock()  # used specifically to protect against showing the wrong menu during transitions

    def __init__(self, width=DISPLAY_WIDTH, height=DISPLAY_HEIGHT, theme=Theme.LIGHT):
        self.__pg_display = display.set_mode((width, height), RESIZABLE)
        self.__theme = theme
        self.__components = {
            'theme_toggler': {
                'image': Surface((THEME_TOGGLE_WIDTH, THEME_TOGGLE_HEIGHT), SRCALPHA),
                'location': self.calculate_theme_toggler_location(),
                'was_hovered': False,
                'is_hovered': False,
                'hovered_handler': self.draw_theme_toggle,
                'clicked_handler': self.toggle_theme,
                'clicked_args': (),
                'resized_handler': self.calculate_theme_toggler_location
            },
            'settings': {
                'image': Surface((SETTINGS_SIZE, SETTINGS_SIZE), SRCALPHA),
                'location': self.calculate_settings_location(),
                'was_hovered': False,
                'is_hovered': False,
                'hovered_handler': self.draw_settings,
                'clicked_handler': self.change_settings,
                'clicked_args': (),
                'resized_handler': self.calculate_settings_location
            },
            'help': {
                'image': Surface((HELP_SIZE, HELP_SIZE), SRCALPHA),
                'location': self.calculate_help_location(),
                'was_hovered': False,
                'is_hovered': False,
                'hovered_handler': self.draw_help,
                'clicked_handler': self.show_help,
                'clicked_args': (),
                'resized_handler': self.calculate_help_location
            }
        }
        self.draw_all()

    @property
    def surface(self):
        return self.__pg_display

    def toggle_theme(self):
        self.HANDLER_LOCK.release()
        self.__theme = ~self.__theme
        self.draw_all()
        self.HANDLER_LOCK.acquire()

    def change_settings(self):
        print('default settings')  # TODO: handler

    def show_help(self):
        print('default help')  # TODO: handler

    @property
    def theme(self):
        return self.__theme

    def draw_all(self):
        self.draw_bg()
        self.draw_theme_toggle()
        self.draw_settings()
        self.draw_help()

    def draw_bg(self):
        self.__pg_display.fill(BG_COLOR_DARK_MODE if self.__theme == Theme.DARK else BG_COLOR_LIGHT_MODE)

    def draw_theme_toggle(self):
        self.__components['theme_toggler']['image'] = Surface((THEME_TOGGLE_WIDTH, THEME_TOGGLE_HEIGHT), SRCALPHA)
        if not self.__components['theme_toggler']['is_hovered']:
            if self.__theme == Theme.LIGHT:
                self.__components['theme_toggler']['image'].blit(THEME_TOGGLE_PNG, (0, 0))
            elif self.__theme == Theme.DARK:
                self.__components['theme_toggler']['image'].blit(THEME_TOGGLE_PNG, (0, -THEME_TOGGLE_HEIGHT))
        else:
            if self.__theme == Theme.LIGHT:
                self.__components['theme_toggler']['image'].blit(THEME_TOGGLE_PNG, (-THEME_TOGGLE_WIDTH, 0))
            elif self.__theme == Theme.DARK:
                self.__components['theme_toggler']['image'].blit(THEME_TOGGLE_PNG, (-THEME_TOGGLE_WIDTH,
                                                                                    -THEME_TOGGLE_HEIGHT))
        self.blit(self.__components['theme_toggler']['image'], self.__components['theme_toggler']['location'])

    def draw_settings(self):
        self.__components['settings']['image'] = Surface((SETTINGS_SIZE, SETTINGS_SIZE), SRCALPHA)
        if not self.__components['settings']['is_hovered']:
            if self.__theme == Theme.LIGHT:
                self.__components['settings']['image'].blit(SETTINGS_PNG, (0, 0))
            elif self.__theme == Theme.DARK:
                self.__components['settings']['image'].blit(SETTINGS_PNG, (0, -SETTINGS_SIZE))
        else:
            if self.__theme == Theme.LIGHT:
                self.__components['settings']['image'].blit(SETTINGS_PNG, (-SETTINGS_SIZE, 0))
            elif self.__theme == Theme.DARK:
                self.__components['settings']['image'].blit(SETTINGS_PNG, (-SETTINGS_SIZE, -SETTINGS_SIZE))
        self.blit(self.__components['settings']['image'], self.__components['settings']['location'])

    def draw_help(self):
        self.__components['help']['image'] = Surface((HELP_SIZE, HELP_SIZE), SRCALPHA)
        if not self.__components['help']['is_hovered']:
            if self.__theme == Theme.LIGHT:
                self.__components['help']['image'].blit(HELP_PNG, (0, 0))
            elif self.__theme == Theme.DARK:
                self.__components['help']['image'].blit(HELP_PNG, (0, -HELP_SIZE))
        else:
            if self.__theme == Theme.LIGHT:
                self.__components['help']['image'].blit(HELP_PNG, (-HELP_SIZE, 0))
            elif self.__theme == Theme.DARK:
                self.__components['help']['image'].blit(HELP_PNG, (-HELP_SIZE, -HELP_SIZE))
        self.blit(self.__components['help']['image'], self.__components['help']['location'])

    @property
    def width(self):
        return self.__pg_display.get_width()

    @property
    def height(self):
        return self.__pg_display.get_height()

    def blit(self, surface, location):
        self.__pg_display.blit(surface, location)

    def write(self, text, location, right_align=False, font_size=TEXT_FONT_SIZE):
        """Uses the blit function to write a string to the screen.

        It first draws a blank surface over the existing area, so that layers of text don't get jumbled together.

        :param text: string to be written to the screen
        :param location: (x, y)-coordinates of the pixel location of either upper-left or upper-right of text
            The right_align parameter affects whether it will be treated as the upper-left or upper-right.
        :param right_align: boolean that determines whether the location parameter represents upper-left or upper-right
            False by default, setting it to True will have it treat location as the upper-right.
        """
        font_to_use = font.Font(font.get_default_font(), font_size)
        text_surface = font.Font.render(font_to_use, text, True,
                                        TEXT_COLOR_DARK_MODE if self.__theme == Theme.DARK else TEXT_COLOR_LIGHT_MODE)
        bg = Surface((text_surface.get_width() + 2, text_surface.get_height()))
        bg.fill(BG_COLOR_DARK_MODE if self.__theme == Theme.DARK else BG_COLOR_LIGHT_MODE)
        if right_align:
            self.blit(bg, (location[0]-bg.get_width(), location[1]))
            self.blit(text_surface, (location[0]-text_surface.get_width(), location[1]))
        else:
            self.blit(bg, location)
            self.blit(text_surface, location)

    def draw(self, surface, location):
        """Uses the blit function to draw an image to the screen.

        It first draws a blank surface over the existing area, so that layers of images don't get jumbled together.

        :param surface: pygame.surface.Surface object containing the image to be drawn to the screen
        :param location: (x, y)-coordinates of the pixel location of upper left corner of tile
        """
        bg = Surface((surface.get_width(), surface.get_height()))
        bg.fill(BG_COLOR_DARK_MODE if self.__theme == Theme.DARK else BG_COLOR_LIGHT_MODE)
        self.blit(bg, location)
        self.blit(surface, location)

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
                callback = component['clicked_handler']
                args = component['clicked_args']
                with self.HANDLER_LOCK:
                    callback(*args)  # execute callback function with args

    def calculate_theme_toggler_location(self):
        return self.__pg_display.get_width() - THEME_TOGGLE_WIDTH - BUFFER, BUFFER

    def calculate_settings_location(self):
        return self.__pg_display.get_width() - THEME_TOGGLE_WIDTH - SETTINGS_SIZE - 2 * BUFFER, BUFFER

    def calculate_help_location(self):
        return self.__pg_display.get_width() - THEME_TOGGLE_WIDTH - SETTINGS_SIZE - HELP_SIZE - 3 * BUFFER, BUFFER

    def handle_resize(self, width, height):
        if width < DISPLAY_WIDTH or height < DISPLAY_HEIGHT:
            self.__pg_display = display.set_mode((DISPLAY_WIDTH, DISPLAY_HEIGHT), RESIZABLE)
        for component in self.__components.values():
            component['location'] = component['resized_handler']()
        self.draw_all()

    def set_help_callback(self, callback=None, args=None):
        if callback is None or args is None:
            self.__components['help']['clicked_handler'] = self.show_help
            self.__components['help']['clicked_args'] = ()
        else:
            self.__components['help']['clicked_handler'] = callback
            self.__components['help']['clicked_args'] = args
