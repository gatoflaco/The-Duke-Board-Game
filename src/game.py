"""
game.py
Isaac Jung

This module contains all the code related to playing a game of The Duke.
"""

from src.board import Board
# from src.player import Player
from src.ai import Difficulty, AI
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
        player1 = AI(1, self, Difficulty.HARD)
        player2 = AI(2, self, Difficulty.BEGINNER)
        self.__players = (player1, player2)
        self.__actions_taken = {}  # will hold (self.__turn: "choice") key-value pairs
        self.__winner = None
        self.__non_meaningful_moves_counter = 0
        for player in self.__players:  # do some initial setup
            for tile in player.tiles_in_play:
                (x, y) = tile.coords
                self.__board.set_tile(x, y, tile)
            player.update_choices(self.calculate_choices(player))
        self.debug_flag = False

    @property
    def board(self):
        return self.__board

    @property
    def turn(self):
        return self.__turn

    @property
    def players(self):
        return self.__players

    def update(self, display):
        """Draws the current game state to the screen.

        :param display: Display object containing the main game window
        """
        self.__board.draw(display)
        for player in self.__players:
            player.update(display)

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
        if check_stalemate_by_counter(self.__non_meaningful_moves_counter):
            return self.__end(0, '50 turns have gone by without any new pieces being pulled or captured.')
        player.update_choices(self.calculate_choices(player))  # recalculate player's allowed moves
        player_attacks = get_attacks(self.calculate_choices(player, False))  # don't consider Duke safety here
        stalemate = True
        if not self.__can_only_move_duke(player):
            stalemate = False
        for other in self.__players:  # next, we should see what effect the move had on the opponent(s)
            if player == other:
                continue
            other_choices = self.calculate_choices(other)  # recalculate their allowed moves
            if other.duke.coords in player_attacks:
                other.set_check(True)
            if has_no_valid_choices(other_choices):
                if other.is_in_check:
                    return self.__end(player.side, 'Player ' + str(player.side) + ' wins!')
                else:
                    return self.__end(0, 'Stalemate by player ' + str(other.side) + ' having no valid moves.')
            other.update_choices(other_choices)
            if stalemate and not self.__can_only_move_duke(other):
                stalemate = False
        if stalemate:
            self.__end(0, 'Dead position - neither player can checkmate.')

    def calculate_choices(self, player, consider_duke_safety=True):
        """Determines everything a player can legally do, given the current board state.

        The game is responsible for telling players what they are allowed to do in a given turn.
        The take_turn() function (defined just above) operates by asking the current player to choose what they
            want to do from a set of things they CAN do.
        Therefore, after any player takes their turn (changing the board state), take_turn() then recalculates
            every player's current allowed choices. This is the method that does that calculation.

        :param player: Player object of the player whose choices the game is trying to calculate
        :param consider_duke_safety: boolean that affects whether the Duke's safety will be taken into account
            When the game is trying to calculate all allowed moves, it must take into account whether a given move
            would leave the player's Duke in check. If so, then that move is not actually allowed. The process of
            deciding whether a move would leave the Duke in check involves asking the opponent to recalculate what
            their attacks would be were the move to be made. This can be generalized as a call to choices() for
            the opponent, but in that call, there is no need to consider Duke safety, as we are only concerned with
            where the opponent can attack. In fact, if the opponent did consider its Duke safety here, it would lead
            to an infinite loop of each player calling choices() back and forth for each other, wanting to know
            each other's attacks. So, this boolean should be True for calls that are intended to fully recalculate
            what is allowed, but False when only concerned with where the enemy attacks are.
        :return: special dict called "choices", whose format is documented in docs/choice_formats.txt
        """
        choices = {
            'pull': [],
            'act': {}
        }
        if consider_duke_safety:
            choices['pull'] = self.__calculate_valid_pull_locations(player)
        for tile in player.tiles_in_play:  # next, we calculate what this player is allowed to do
            if not isinstance(tile, Troop):
                continue  # for any tiles that are not actually Troop objects, nothing to do
            x, y = tile.coords
            choices['act'][(x, y)] = self.__calculate_allowed_actions_for_troop(player, tile, consider_duke_safety)
        return choices

    def __calculate_valid_pull_locations(self, player):
        """Determines all the (x, y)-coordinates where a player can play a new tile given the current board state.

        :param player: Player object of the player whose valid pull locations the game is trying to calculate
        :return: list of tuples representing (x, y)-coordinates on the board where new tiles may be played
        """
        return [] if (player is None or not player.has_tiles_in_bag) else [  # funny React-looking return kek
            (i, j)
            for i, j in (  # I'm something of a Python programmer myself (goofy ah list comp inside another list comp)
                list(chain.from_iterable([[(x, y + 1), (x + 1, y), (x, y - 1), (x - 1, y)] for x, y in (
                    [player.duke.coords]
                )]))
            )
            if (  # where are your gods now
                0 <= i < 6 and 0 <= j < 6 and self.__board.get_tile(i, j) is None and
                not self.__duke_would_be_endangered(player, {
                    'action_type': 'pull',
                    'src_location': (i, j),
                    'tile': Troop('', player.side, (i, j), True)
                })
            )
        ]

    def __calculate_allowed_actions_for_troop(self, player, troop, consider_duke_safety):
        """Determines all the actions that a troop tile can perform given the current board state.

        :param player: Player object of the player to whom the tile belongs
        :param troop: Troop object under consideration
        :param consider_duke_safety: boolean that affects whether the Duke's safety will be taken into account
            See choices() for more details.
        :return: special dict called "actions", whose format is documented in docs/choice_formats.txt
        """
        name = troop.name
        side = troop.side
        x, y = troop.coords
        actions = {
            'moves': [],
            'strikes': [],
            'commands': {}
        }
        cmd_dst_locs = []
        for item in TROOP_MOVEMENTS[name]['side ' + str(side)]:
            dx, dy = convert_file_and_rank_to_coordinates(item['file'], item['rank'], player.side)
            i, j = x + dx, y + dy  # <--actual position on board, ^position relative to troop
            if not (0 <= i < 6 and 0 <= j < 6):  # cannot go out of bounds
                continue
            if item['move'] == 'MOVE':
                dst_tile = self.__board.get_tile(i, j)
                if (tile_is_open_or_enemy(dst_tile, player) and path_is_open(self.__board, i, j, dx, dy)
                        and not (consider_duke_safety and self.__duke_would_be_endangered(player, {
                            'action_type': 'mov',
                            'src_location': (x, y),
                            'dst_location': (i, j)
                        }))):
                    actions['moves'].append((i, j))  # move is allowed
            elif item['move'] == 'JUMP':
                dst_tile = self.__board.get_tile(i, j)
                if (tile_is_open_or_enemy(dst_tile, player)
                        and not (consider_duke_safety and self.__duke_would_be_endangered(player, {
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
                    if not (consider_duke_safety and self.__duke_would_be_endangered(player, {
                        'action_type': 'mov',
                        'src_location': (x, y),
                        'dst_location': (cur_i, cur_j)
                    })):
                        actions['moves'].append((cur_i, cur_j))  # slide is allowed
                    step += 1
                    cur_i = i + step * it_x
                    cur_j = j + step * it_y
                if (0 <= cur_i < 6 and 0 <= cur_j < 6 and dst_tile is not None and dst_tile.player_side != player.side
                        and not (consider_duke_safety and self.__duke_would_be_endangered(player, {
                            'action_type': 'mov',
                            'src_location': (x, y),
                            'dst_location': (cur_i, cur_j)
                        }))):
                    actions['moves'].append((cur_i, cur_j))  # slide is allowed
            elif item['move'] == 'STRIKE':
                str_tile = self.__board.get_tile(i, j)
                if (tile_is_enemy(str_tile, player)
                        and not (consider_duke_safety and self.__duke_would_be_endangered(player, {
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
                    actions['commands'][(i, j)] = []  # add new src_loc key
        for src_loc in actions['commands']:
            for dst_loc in cmd_dst_locs:
                if not (consider_duke_safety and self.__duke_would_be_endangered(player, {
                    'action_type': 'cmd',
                    'src_location': src_loc,
                    'dst_location': dst_loc,
                    'cmd_location': (x, y),
                })):
                    actions['commands'][src_loc].append(dst_loc)  # command is allowed
        return actions

    def __duke_would_be_endangered(self, player, choice):
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
            cur_in_play.append(p.tiles_in_play.copy())
        self.make_choice(player, choice, True)  # literally make the move
        all_enemy_attacks = set()
        for other in self.__players:  # recalculate the allowed moves for the opponent(s)
            if player != other:
                other_choices = self.calculate_choices(other, False)  # will include attacks that endanger their Duke
                all_enemy_attacks = all_enemy_attacks.union(get_attacks(other_choices))
        if player.duke.coords in all_enemy_attacks:
            would_be_endangered = True
        for i in range(len(self.__players)):  # restore saved states
            self.__players[i].set_tiles_in_play(cur_in_play[i])
        self.undo_choice(player)
        return would_be_endangered

    def make_choice(self, player, choice, considering=False):
        """Executes a given move on the board.

        The game is responsible for managing the board.
        From the Player objects' perspectives, the Tiles', the Bags', etc.... none of these actually know what the
            board state is. So this function exists to manage it whenever it needs to change.

        :param player: Player object of the player making the move
        :param choice: special dict called "choice", whose format is documented in docs/choice_formats.txt
        :param considering: boolean that should be True if the choice is expected to be undone later
        """
        if choice['action_type'] == 'pull':
            self.__board.set_tile(choice['src_location'][0], choice['src_location'][1], choice['tile'])
            if not considering:
                self.__non_meaningful_moves_counter = 0  # pulling is a meaningful move
        else:
            choice['tile'] = None
            src_tile = self.__board.get_tile(choice['src_location'][0], choice['src_location'][1])
            if choice['action_type'] != 'str':  # 'mov' or 'cmd'
                dst_tile = self.__board.get_tile(choice['dst_location'][0], choice['dst_location'][1])
                if dst_tile is not None:  # if an enemy tile is in the destination location
                    enemy_player = self.__players[dst_tile.player_side - 1]
                    dst_tile = enemy_player.remove_from_play(choice['dst_location'][0], choice['dst_location'][1])
                    self.__players[player.side - 1].capture(dst_tile)
                    choice['tile'] = dst_tile
                    if not considering:
                        self.__non_meaningful_moves_counter = 0  # capturing is a meaningful move
                        if enemy_player.duke.is_captured:
                            print(choice)
                            return False
                elif not considering:
                    self.__non_meaningful_moves_counter += 1  # movement without capturing is not considered meaningful
                if choice['action_type'] == 'mov':
                    src_tile.flip()
                else:
                    cmd_tile = self.__board.get_tile(choice['cmd_location'][0], choice['cmd_location'][1])
                    cmd_tile.flip()
                    self.__board.set_tile(choice['cmd_location'][0], choice['cmd_location'][1], cmd_tile)
                self.__board.set_tile(choice['src_location'][0], choice['src_location'][1], None)
                src_tile.move(choice['dst_location'][0], choice['dst_location'][1])
                self.__board.set_tile(choice['dst_location'][0], choice['dst_location'][1], src_tile)
            else:  # 'str'
                str_tile = self.__board.get_tile(choice['str_location'][0], choice['str_location'][1])
                enemy_player = self.__players[str_tile.player_side - 1]
                str_tile = enemy_player.remove_from_play(choice['str_location'][0], choice['str_location'][1])
                self.__players[player.side - 1].capture(str_tile)
                choice['tile'] = str_tile
                if not considering:
                    self.__non_meaningful_moves_counter = 0  # striking (and capturing) is a meaningful move
                    if enemy_player.duke.is_captured:
                        print(choice)
                        return False
                src_tile.flip()
                self.__board.set_tile(choice['src_location'][0], choice['src_location'][1], src_tile)
        self.__actions_taken[self.__turn] = choice  # log the choice made on this turn
        return True

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

    @property
    def is_finished(self):
        return self.__winner is not None

    def __can_only_move_duke(self, player):
        """Checks if a given player is capable of no action aside from potentially moving their Duke.

        This assists in one of the stalemate checks, when both players have only their Dukes + potential dead pieces.
        The problem of determining dead pieces is challenging, and this function tries to be safe and assume a piece
        is NOT dead unless very obvious conditions are met. There are many edge cases in which pieces could be said
        to be dead, but they are too much work to find and/or the claim is too subjective (e.g., saying that they are
        theoretically dead is based on an assumption that neither player makes a mistake, and the setup is complex
        enough that it is no longer trivial to see how NOT to make a mistake). Consider the following board state:
        6  Dr21  L22   .  Pi11   .   F12

        5    .    .    .    .  Pi11   .

        4    .    .    .    .    .    .

        3    .  Du22   .    .    .    .

        2    .    .  Du11   .    .    .

        1    .    .    .    .    .    .

             A    B    C    D    E    F
        Here, player 1's troops are:
        - C2: Duke, side 1
        - D6: Pikeman, side 1
        - E5: Pikeman, side 1
        - F6: Footman, side 2
        Player 2's troops are:
        - A6: Dragoon, side 1
        - B3: Duke, side 2
        - B6: Longbowman, side 2
        A human could identify that this is a stalemate, because no pieces other than the Dukes should ever be able to
        move.
        This function, however, will think that A6, E5, and F6 are not dead pieces. A6 is dead because its only move is
        to B6, which is occupied by a dead piece. While we could reasonably detect that without adding too much extra
        work, E5 and F6 demonstrate a more complicated issue. They are blocking each other. In short, this function will
        only claim that the Duke is the only piece that can move when it is absolutely certain.

        :param player: Player object of the player inspecting their options
        :return: boolean that is True when it is known for certain that only the player's Duke can take action
            A return value of False simply means that it is uncertain. It could be true that the Duke is the only
            piece that can take action, but the function just couldn't be sure of this fact.
        """
        if player.has_tiles_in_bag:
            return False
        for tile in player.tiles_in_play:
            name = tile.name
            if name == 'Duke':
                continue
            x, y = tile.coords
            cmd_src_troops = []
            cmd_dst_locs = []
            checked_other_side = False
            for item in TROOP_MOVEMENTS[name]['side ' + str(tile.side)]:
                dx, dy = convert_file_and_rank_to_coordinates(item['file'], item['rank'], player.side)
                i, j = x + dx, y + dy  # <--actual position on board, ^position relative to troop
                if 0 <= i < 6 and 0 <= j < 6 and item['move'] in ['MOVE', 'JUMP', 'SLIDE', 'JUMP_SLIDE']:
                    return False  # at least one troop found that is not a dead piece
                if 0 <= i < 6 and 0 <= j < 6 and item['move'] == 'COMMAND':
                    cmd_tile = self.__board.get_tile(i, j)
                    if tile_is_open_or_enemy(cmd_tile, player):
                        cmd_dst_locs.append((i, j))
                    else:
                        cmd_src_troops.append(cmd_tile)
                for teammate in cmd_src_troops:
                    for dst_loc in cmd_dst_locs:
                        for itemt in TROOP_MOVEMENTS[teammate.name]['side ' + str(teammate.side)]:
                            dxt, dyt = convert_file_and_rank_to_coordinates(itemt['file'], itemt['rank'], player.side)
                            it, jt = dst_loc[0] + dxt, dst_loc[1] + dyt
                            if 0 <= it < 6 and 0 <= jt < 6 and itemt['move'] in ['MOVE', 'JUMP', 'SLIDE', 'JUMP_SLIDE']:
                                return False  # can command a teammate such that teammate is not a dead piece
                if (not checked_other_side and len(cmd_dst_locs) > 0 and 0 <= i < 6 and 0 <= j < 6
                        and item['move'] == 'COMMAND'):
                    for itemo in TROOP_MOVEMENTS[name]['side ' + str(((tile.side - 1) ^ 1) + 1)]:
                        dxo, dyo = convert_file_and_rank_to_coordinates(itemo['file'], itemo['rank'], player.side)
                        io, jo = x + dxo, y + dyo
                        if 0 <= io < 6 and 0 <= jo < 6 and itemo['move'] in ['MOVE', 'JUMP', 'SLIDE', 'JUMP_SLIDE']:
                            return False  # can command a teammate such that teammate is not a dead piece
                    checked_other_side = True
        return True  # couldn't find any non-Duke troops that weren't dead pieces

    def __end(self, status, reason=''):
        """Handles a game over condition.

        :param status: integer representing who won
            1 for player 1, 2 for player 2, 0 for a draw (including stalemate), -1 for any other reason.
        :param reason: string representing a message to print out to inform players on why the game is over
        """
        self.__winner = status
        if status > 0:
            print('Checkmate!', reason)
        elif status == 0:
            print('Draw!', reason)
        for player in self.__players:
            if isinstance(player, AI):
                print('Player', player.side, 'seed:', player.seed)
