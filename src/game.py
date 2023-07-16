"""
game.py
Isaac Jung

This module contains all the code related to playing a game of The Duke.
"""

from src.board import Board
# from src.player import Player
from src.ai import AI
from src.tile import Troop
from src.util import *
from src.constants import TROOP_MOVEMENTS
from itertools import chain


class Game:
    """Holds all information pertaining to a single round of the game.

    A game consists of a board and 2 players. Each player has a bag of tiles, along with other things they keep track of
    such as captured troop tiles.
    A Game object, then, serves as an interface through which to manage the states of the board and players.
    """

    def __init__(self):
        self.__board = Board()
        self.__turn = 0
        player1 = AI(1, self)
        player2 = AI(2, self)
        self.__players = (player1, player2)
        self.__actions_taken = {}  # will hold (self.__turn: "choice") key-value pairs
        self.__winner = None
        for player in self.__players:  # do some initial setup
            for tile in player.get_tiles_in_play():
                (x, y) = tile.get_coords()
                self.__board.set_tile(x, y, tile)
            player.update_choices(self.get_choices(player))

    def get_board(self):
        return self.__board

    def get_turn(self):
        return self.__turn

    def get_players(self):
        return self.__players

    def update(self, game_display):
        """Draws the current game state to the screen.

        :param game_display: main pygame.surface.Surface representing the whole game window
        """
        game_display.fill((255, 255, 255))
        self.__board.draw(game_display)

    def take_turn(self):
        """Main gameplay loop.

        A single call will consist of the following broad steps for whichever player is up to take their turn:
            1. get player input
            2. carry out player decision on board
            3. recalculate current game state, including what both players can currently do, and if check/checkmate
        """
        self.__turn += 1
        player = self.__players[self.__turn % len(self.__players) - 1]  # player whose turn should be taken
        self.make_choice(player, player.take_turn())  # update the board based on player's choice
        player.set_check(False)  # must not be in check at this point
        player_choices = self.get_choices(player)  # recalculate player's allowed moves
        player.update_choices(player_choices)
        player_attacks = get_attacks(player_choices)
        stalemate = True
        if len(player_choices['act']) > 1 or player.has_tiles_in_bag():
            stalemate = False
        for other in self.__players:  # next, we should see what effect the move had on the opponent(s)
            if player == other:
                continue
            other_choices = self.get_choices(other)  # recalculate their allowed moves
            if has_no_valid_choices(other_choices):
                self.__winner = player
                print('Checkmate! Player', player.get_side(), 'wins!')
                return
            other.update_choices(other_choices)
            if other.get_duke().get_coords() in player_attacks:
                other.set_check(True)
            if stalemate and (len(other_choices['act']) > 1 or other.has_tiles_in_bag()):
                stalemate = False
        if stalemate:
            self.__winner = -1
            print('Stalemate! Game over! 😭')

    def get_choices(self, player, should_consider_duke_safety=True):
        """Determines everything a player can legally do, given the current board state.

        The game is responsible for telling players what they are allowed to do in a given turn.
        The take_turn() function (defined just above) operates by asking the current player to choose what they
            want to do from a set of things they CAN do.
        Therefore, after any player takes their turn (changing the board state), take_turn() then recalculates
            every player's current allowed choices. This is the method that does that calculation.

        :param player: Player object of the player whose choices the game is trying to calculate
        :param should_consider_duke_safety: boolean that affects whether the Duke's safety will be taken into account
            When the game is trying to calculate all allowed moves, it must take into account whether a given move
            would leave the player's Duke in check. If so, then that move is not actually allowed. The process of
            deciding whether a move would leave the Duke in check involves asking the opponent to recalculate what
            their attacks would be were the move to be made. This can be generalized as a call to get_choices() for
            the opponent, but in that call, there is no need to consider Duke safety, as we are only concerned with
            where the opponent can attack. In fact, if the opponent did consider its Duke safety here, it would lead
            to an infinite loop of each player calling get_choices() back and forth for each other, wanting to know
            each other's attacks. So, this boolean should be True for calls that are intended to fully recalculate
            what is allowed, but False when only concerned with where the enemy attacks are.
        :return: special dict called "choices", whose format is documented in docs/choice_formats.txt
        """
        choices = {
            'pull': [],
            'act': {}
        }
        if should_consider_duke_safety:
            choices['pull'] = self.calculate_valid_pull_locations(player)
        for tile in player.get_tiles_in_play():  # next, we calculate what this player is allowed to do
            if not isinstance(tile, Troop):
                continue  # for any tiles that are not actually Troop objects, nothing to do
            x, y = tile.get_coords()
            choices['act'][(x, y)] = self.calculate_allowed_actions_for_troop(player, tile, should_consider_duke_safety)
        return choices

    def calculate_valid_pull_locations(self, player):
        """Determines all the (x, y)-coordinates where a player can play a new tile given the current board state.

        :param player: Player object of the player whose valid pull locations the game is trying to calculate
        :return: list of tuples representing (x, y)-coordinates on the board where new tiles may be played
        """
        return [] if (player is None or not player.has_tiles_in_bag()) else [  # funny React-looking return kek
            (i, j)
            for i, j in (  # I'm something of a Python programmer myself (goofy ah list comp inside another list comp)
                list(chain.from_iterable([[(x, y + 1), (x + 1, y), (x, y - 1), (x - 1, y)] for x, y in (
                    [player.get_duke().get_coords()]
                )]))
            )
            if (  # where are your gods now
                0 <= i < 6 and 0 <= j < 6 and self.__board.get_tile(i, j) is None and
                not self.duke_would_be_endangered(player, {
                    'action_type': 'pull',
                    'src_location': (i, j),
                    'tile': Troop('', player.get_side(), (i, j), True)
                })
            )
        ]

    def calculate_allowed_actions_for_troop(self, player, troop, should_consider_duke_safety):
        """Determines all the actions that a troop tile can perform given the current board state.

        :param player: Player object of the player to whom the tile belongs
        :param troop: Troop object under consideration
        :param should_consider_duke_safety: boolean that affects whether the Duke's safety will be taken into account
            See get_choices() for more details.
        :return: special dict called "actions", whose format is documented in docs/choice_formats.txt
        """
        name = troop.get_name()
        side = troop.get_side()
        x, y = troop.get_coords()
        actions = {
            'moves': [],
            'strikes': [],
            'commands': {}
        }
        cmd_dst_locs = []
        for item in TROOP_MOVEMENTS[name]['side ' + str(side)]:
            dx, dy = convert_file_and_rank_to_coordinates(item['file'], item['rank'], player.get_side())
            i, j = x + dx, y + dy  # <--actual position on board, ^position relative to troop
            if not (0 <= i < 6 and 0 <= j < 6):  # cannot go out of bounds
                continue
            if item['move'] == 'MOVE':
                dst_tile = self.__board.get_tile(i, j)
                if (tile_is_open_or_enemy(dst_tile, player) and path_is_open(self.__board, i, j, dx, dy)
                        and not (should_consider_duke_safety and self.duke_would_be_endangered(player, {
                            'action_type': 'mov',
                            'src_location': (x, y),
                            'dst_location': (i, j)
                        }))):
                    actions['moves'].append((i, j))  # move is allowed
            elif item['move'] == 'JUMP':
                dst_tile = self.__board.get_tile(i, j)
                if (tile_is_open_or_enemy(dst_tile, player)
                        and not (should_consider_duke_safety and self.duke_would_be_endangered(player, {
                            'action_type': 'mov',
                            'src_location': (x, y),
                            'dst_location': (i, j)
                        }))):
                    actions['moves'].append((i, j))  # jump is allowed
            elif item['move'] == 'SLIDE' or item['move'] == 'JUMP SLIDE':  # jump slide actually uses same logic lol
                dst_tile = None
                it_x = 0 if dx == 0 else int(dx / abs(dx))  # e.g., when delta_x = 2, it_x = 1
                it_y = 0 if dy == 0 else int(dy / abs(dy))  # (moving in same direction as slide)
                step = 0
                cur_i = i
                cur_j = j
                while 0 <= cur_i < 6 and 0 <= cur_j < 6:
                    dst_tile = self.__board.get_tile(cur_i, cur_j)
                    if dst_tile is not None:  # slide stops here
                        break  # consider after loop
                    if not (should_consider_duke_safety and self.duke_would_be_endangered(player, {
                        'action_type': 'mov',
                        'src_location': (x, y),
                        'dst_location': (cur_i, cur_j)
                    })):
                        actions['moves'].append((cur_i, cur_j))  # slide is allowed
                    step += 1
                    cur_i = i + step * it_x
                    cur_j = j + step * it_y
                if (dst_tile is not None and dst_tile.get_player() != player.get_side()
                        and not (should_consider_duke_safety and self.duke_would_be_endangered(player, {
                            'action_type': 'mov',
                            'src_location': (x, y),
                            'dst_location': (cur_i, cur_j)
                        }))):
                    actions['moves'].append((cur_i, cur_j))  # slide is allowed
            elif item['move'] == 'STRIKE':
                str_tile = self.__board.get_tile(i, j)
                if (tile_is_enemy(str_tile, player)
                        and not (should_consider_duke_safety and self.duke_would_be_endangered(player, {
                            'action_type': 'str',
                            'src_location': (x, y),
                            'str_location': (i, j)
                        }))):
                    actions['strikes'].append((i, j))  # strike is allowed
            elif item['move'] == 'COMMAND':
                cmd_tile = self.__board.get_tile(i, j)
                if tile_is_open_or_enemy(cmd_tile, player):
                    cmd_dst_locs.append((i, j))  # whether a given teammate can go here will be determined at the end
                else:
                    actions['commands'][(i, j)] = []
        for teammate_loc in actions['commands']:
            for dst_loc in cmd_dst_locs:
                if not (should_consider_duke_safety and self.duke_would_be_endangered(player, {
                    'action_type': 'cmd',
                    'src_location': teammate_loc,
                    'dst_location': dst_loc,
                    'cmd_location': (x, y),
                })):
                    actions['commands'][teammate_loc].append(dst_loc)  # command is allowed
        return actions

    def duke_would_be_endangered(self, player, choice):
        """Checks the legality of taking an action in the context of the Duke's safety.

        Just like in chess, when a player is in check, they may only take actions that get out of the state.
        Additionally, a player may not make a move that self-induces check.
        This can be generalized to the following logic when considering an action:
            1. make the move
            2. see if the Duke is in check
            3. undo the move

        :param player: Player object of the player considering taking the action
        :param choice: special dict called "choice", whose format is documented in docs/choice_formats.txt
        :return: boolean representing whether the Duke would be endangered by the action - True is so, False if not
        """
        if choice is None:  # may occur when player does not care about considering the Duke's safety
            return True
        would_be_endangered = False
        cur_in_play = []
        for p in self.__players:  # save some states before they get modified
            cur_in_play.append(p.get_tiles_in_play().copy())
        self.make_choice(player, choice)  # literally make the move
        all_enemy_attacks = set()
        for other in self.__players:  # recalculate the allowed moves for the opponent(s)
            if player != other:
                other_choices = self.get_choices(other, False)  # will include even attacks that endanger their Duke
                all_enemy_attacks = all_enemy_attacks.union(get_attacks(other_choices))
        if player.get_duke().get_coords() in all_enemy_attacks:
            would_be_endangered = True
        for i in range(len(self.__players)):  # restore saved states
            self.__players[i].set_tiles_in_play(cur_in_play[i])
        self.undo_choice(player)
        return would_be_endangered

    def make_choice(self, player, choice):
        """Executes a given move on the board.

        The game is responsible for managing the board.
        From the Player objects' perspectives, the Tiles', the Bags', etc.... none of these actually know what the
            board state is. So this function exists to manage it whenever it needs to change.

        :param player: Player object of the player making the move
        :param choice: special dict called "choice", whose format is documented in docs/choice_formats.txt
        """
        if choice['action_type'] == 'pull':
            self.__board.set_tile(choice['src_location'][0], choice['src_location'][1], choice['tile'])
        else:
            choice['tile'] = None
            src_tile = self.__board.get_tile(choice['src_location'][0], choice['src_location'][1])
            if choice['action_type'] != 'str':  # 'mov' or 'cmd'
                dst_tile = self.__board.get_tile(choice['dst_location'][0], choice['dst_location'][1])
                if dst_tile is not None:  # if an enemy tile is in the destination location
                    enemy_player = self.__players[dst_tile.get_player() - 1]
                    dst_tile = enemy_player.remove_from_play(choice['dst_location'][0], choice['dst_location'][1])
                    self.__players[player.get_side() - 1].capture(dst_tile)
                    choice['tile'] = dst_tile
                if choice['action_type'] == 'mov':
                    src_tile.flip()
                else:
                    cmd_tile = self.__board.get_tile(choice['cmd_location'][0], choice['cmd_location'][1])
                    cmd_tile.flip()
                    self.__board.set_tile(choice['cmd_location'][0], choice['cmd_location'][1], cmd_tile)
                self.__board.set_tile(choice['src_location'][0], choice['src_location'][1], None)
                src_tile.move(choice['dst_location'][0], choice['dst_location'][1])  # TODO: check that player sees this
                self.__board.set_tile(choice['dst_location'][0], choice['dst_location'][1], src_tile)
            else:  # 'str'
                str_tile = self.__board.get_tile(choice['str_location'][0], choice['str_location'][1])
                enemy_player = self.__players[str_tile.get_player() - 1]
                str_tile = enemy_player.remove_from_play(choice['str_location'][0], choice['str_location'][1])
                self.__players[player.get_side() - 1].capture(str_tile)
                choice['tile'] = str_tile
                src_tile.flip()
                self.__board.set_tile(choice['src_location'][0], choice['src_location'][1], src_tile)
        self.__actions_taken[self.__turn] = choice  # log the choice made on this turn

    def undo_choice(self, player):
        """Undoes the most recent action carried out on the board.

        Note that this does NOT guarantee that other object data modified by make_choice() is undone.
        This function is most likely only ever used to undo "pretend" moves.
        If one wishes to "pretend" to make a move and then call this function to undo it, this function will only
            reset the board state. The caller would be responsible for storing necessary information before making the
            move, so that they could restore it as needed afterwards.

        :param player: Player object of the player who made the last move
        """
        choice = self.__actions_taken.pop(self.__turn)
        if choice['action_type'] == 'pull':
            self.__board.set_tile(choice['src_location'][0], choice['src_location'][1], None)
        else:
            captured_tile = None
            if choice['tile'] is not None:
                captured_tile = player.undo_last_capture()
            src_tile = self.__board.get_tile(choice['src_location'][0], choice['src_location'][1])
            if choice['action_type'] != 'str':  # 'mov' or 'cmd'
                dst_tile = self.__board.get_tile(choice['dst_location'][0], choice['dst_location'][1])
                if choice['action_type'] == 'mov':
                    dst_tile.flip()
                else:
                    cmd_tile = self.__board.get_tile(choice['cmd_location'][0], choice['cmd_location'][1])
                    cmd_tile.flip()
                    self.__board.set_tile(choice['cmd_location'][0], choice['cmd_location'][1], cmd_tile)
                self.__board.set_tile(choice['src_location'][0], choice['src_location'][1], dst_tile)
                dst_tile.move(choice['src_location'][0], choice['src_location'][1])
                self.__board.set_tile(choice['dst_location'][0], choice['dst_location'][1], captured_tile)
            else:  # 'str'
                src_tile.flip()
                self.__board.set_tile(choice['src_location'][0], choice['src_location'][1], src_tile)
                self.__board.set_tile(choice['str_location'][0], choice['str_location'][1], captured_tile)

    def is_finished(self):
        """Simple function to see if the game is finished.

        :return: boolean representing whether the current game has ended - True if so, False if not
        """
        return self.__winner is not None
