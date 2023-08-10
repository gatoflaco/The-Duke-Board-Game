"""
game.py
Isaac Jung

This module contains all the code related to playing a game of The Duke.
"""

from src.display import Display, Theme
from src.board import Board
from src.player import Player
from src.ai import Difficulty, AI
from src.tile import Troop
from src.util import *
from src.constants import (BUFFER, TEXT_FONT_SIZE, LARGER_FONT_SIZE, TEXT_BUFFER, OFFER_DRAW_PNG, OFFER_DRAW_SIZE,
                           FORFEIT_PNG, FORFEIT_SIZE, TILE_HELP_PNG, TILE_HELP_SIZE, TROOP_MOVEMENTS)
from copy import copy
from itertools import chain
from time import sleep, time


def get_match_type(player1, player2):
    if isinstance(player1, AI):
        if isinstance(player2, AI):
            return 'EvE'  # "environment vs environment" - AI vs AI
        return 'EvP'  # "environment vs player" - AI vs Player, where Player 1 is the AI
    elif isinstance(player2, AI):
        return 'PvE'  # "player vs environment" - Player vs AI, where Player 2 is the AI
    return 'PvP'  # "player vs player" - no AI present


class Game:
    """Holds all information pertaining to a single round of the game.

    A game consists of a board and 2 players. Each player has a bag of tiles, along with other things they keep track of
    such as captured troop tiles.
    A Game object, then, serves as an interface through which to manage the states of the board and players.
    """

    def __init__(self):
        self.__board = Board()
        self.__turn = 0
        player1 = Player(1)
        # player1 = AI(1, self, Difficulty.BEGINNER)
        player2 = Player(2)
        # player2 = AI(2, self, Difficulty.HARD)
        self.__players = (player1, player2)
        self.__match_type = get_match_type(player1, player2)
        self.__actions_taken = []  # will hold "choice" dicts
        self.__winner = None
        self.__non_meaningful_moves_counter = 0
        self.__start_time = time()
        self.__finish_time = None
        self.__finish_message = None

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
        display.draw_all()
        if not Board.ANIMATING:
            self.__board.draw(display)
        if Player.SELECTED is not None:
            if Player.SELECTED_TILE_HOVERED:
                Player.TILE_HELP_IMAGE.blit(TILE_HELP_PNG,
                                            (-TILE_HELP_SIZE, -TILE_HELP_SIZE if display.theme == Theme.DARK else 0))
            else:
                Player.TILE_HELP_IMAGE.blit(TILE_HELP_PNG, (0, -TILE_HELP_SIZE if display.theme == Theme.DARK else 0))
        for player in self.__players:
            player.update(display)
            if player.is_in_check and Player.SELECTED != player.duke and not Board.ANIMATING:
                self.__board.draw_check(display, player.duke.coords)
        if self.__board.held_tile is not None:
            self.__board.draw_held(display)
        if isinstance(Player.PLAYER, Player):
            if Player.OFFER_DRAW_HOVERED:
                Player.OFFER_DRAW_IMAGE.blit(OFFER_DRAW_PNG, (-OFFER_DRAW_SIZE,
                                                              -OFFER_DRAW_SIZE if display.theme == Theme.DARK else 0))
            else:
                Player.OFFER_DRAW_IMAGE.blit(OFFER_DRAW_PNG, (0,
                                                              -OFFER_DRAW_SIZE if display.theme == Theme.DARK else 0))
            if Player.FORFEIT_HOVERED:
                Player.FORFEIT_IMAGE.blit(FORFEIT_PNG, (-FORFEIT_SIZE,
                                                        -FORFEIT_SIZE if display.theme == Theme.DARK else 0))
            else:
                Player.FORFEIT_IMAGE.blit(FORFEIT_PNG, (0, -FORFEIT_SIZE if display.theme == Theme.DARK else 0))
        else:
            Player.OFFER_DRAW_IMAGE.blit(OFFER_DRAW_PNG, (-OFFER_DRAW_SIZE * 2,
                                                          -OFFER_DRAW_SIZE if display.theme == Theme.DARK else 0))
            Player.FORFEIT_IMAGE.blit(FORFEIT_PNG, (-FORFEIT_SIZE * 2,
                                                    -FORFEIT_SIZE if display.theme == Theme.DARK else 0))
        display.blit(Player.OFFER_DRAW_IMAGE, (BUFFER, display.height - BUFFER - OFFER_DRAW_SIZE))
        display.blit(Player.FORFEIT_IMAGE, (OFFER_DRAW_SIZE + 2 * BUFFER, display.height - BUFFER - FORFEIT_SIZE))
        if self.__turn == 0 and Player.PLAYER is not None:
            display.write('- SETUP PHASE -',
                          (display.width // 2 - 4 * LARGER_FONT_SIZE, (display.height - LARGER_FONT_SIZE) // 2),
                          False, LARGER_FONT_SIZE)
        if self.__winner is None:
            current_match_time = time() - self.__start_time
            minutes = int(current_match_time // 60)
            seconds = round(current_match_time - minutes * 60)
        else:
            display.write(self.__finish_message,
                          (display.width // 2 - (27 * len(self.__finish_message) // 100) * LARGER_FONT_SIZE,
                           (display.height - LARGER_FONT_SIZE) // 2), False, LARGER_FONT_SIZE)
            minutes = int(self.__finish_time // 60)
            seconds = round(self.__finish_time - minutes * 60)
        display.write(f'Match Time: {minutes:02d}:{seconds:02d}',
                      (BUFFER, display.height - BUFFER - OFFER_DRAW_SIZE - 2 * TEXT_FONT_SIZE - 4 * TEXT_BUFFER))
        display.write(f'Turn {self.__turn}'
                      + (f' (Player {((self.__turn + 1) % 2) + 1}\'s turn)' if self.__turn > 0 else ''),
                      (BUFFER, display.height - BUFFER - OFFER_DRAW_SIZE - TEXT_FONT_SIZE - 2 * TEXT_BUFFER))
        display.write('File / Rank:',
                      (OFFER_DRAW_SIZE + FORFEIT_SIZE + 3 * BUFFER, display.height - BUFFER - FORFEIT_SIZE))
        display.write(f'{Player.FILE}{Player.RANK}',
                      (OFFER_DRAW_SIZE + FORFEIT_SIZE + 3 * BUFFER + 5 * TEXT_BUFFER,
                       (display.height - BUFFER - FORFEIT_SIZE + TEXT_FONT_SIZE +
                        2 * TEXT_BUFFER)))

    def setup(self, display):
        with display.HANDLER_LOCK:
            display.set_help_callback(handle_help_clicked_setup, (display,))
        for player in self.__players:  # do some initial setup
            self.__actions_taken += player.setup_phase(self.__board)  # initial tile placements
            self.__board.lock_hovers()
            while Display.MUTEX.locked():
                pass
            while not Display.MUTEX.locked():
                pass  # wait for the screen to refresh at least once
            if self.__match_type[2] == 'P':  # Player 2 is a human player
                self.board.animate_rotation(display)
        for player in self.players:
            player.update_choices(self.calculate_choices(player))

    def take_turn(self, display):
        """Main gameplay loop.

        A single call will consist of the following broad steps for whichever player is up to take their turn:
            1. get player input
            2. carry out player decision on board
            3. recalculate current game state, including what both players can currently do, and if check/checkmate
        """
        while Display.MUTEX.locked():
            pass
        while not Display.MUTEX.locked():
            pass  # wait for the screen to refresh at least once
        if self.__match_type[2] == 'P' and self.__turn > 0:
            self.board.animate_rotation(display)
        self.__turn += 1
        player = self.__players[self.__turn % len(self.__players) - 1]  # player whose turn should be taken
        with display.HANDLER_LOCK:
            display.set_help_callback(handle_help_clicked_gameplay, (display, player.is_in_check))

        self.make_choice(player, player.take_turn())  # update the board based on player's choice
        self.__board.lock_hovers()
        if not isinstance(player, AI):
            Display.MUTEX.release()  # player input event handler threads will acquire() this mutex

        player.set_check(False)  # must not be in check at this point
        if check_draw_by_counter(self.__non_meaningful_moves_counter):
            return self.__end(0, 'Game over by the 50 move rule.')
        player.update_choices(self.calculate_choices(player))  # recalculate player's allowed moves
        player_attacks = get_attacks(self.calculate_choices(player, False))  # don't consider Duke safety here
        dead_position = True
        if not self.__can_only_move_duke(player):
            dead_position = False

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
            if dead_position and not self.__can_only_move_duke(other):
                dead_position = False

        if dead_position:
            self.__end(0, 'Dead position - neither player can checkmate.')

    def calculate_choices(self, player, consider_duke_safety=True, board=None, players=None):
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
        :param board: Board object of the board to be used in calculations
            When checking what would happen if a move were made, the move should be made on a copy of the permanent
            board state. Then, recalculations can be done by calling this function while passing the cloned board.
            This allows the code that was testing the move to avoid modifying the actual board.
        :param players: tuple of Player object of players to be used in calculations
            Very specifically needed when consider_duke_safety is True but the caller does not want the game state to
            be permanently modified. Then, like with the board parameter, the caller should make a copy of the players
            and pass that in here.
        :return: special dict called "choices", whose format is documented in docs/choice_formats.txt
        """
        if board is None:
            board = self.__board
        choices = {
            'pull': [],
            'act': {}
        }
        if consider_duke_safety:
            choices['pull'] = self.__calculate_valid_pull_locations(player, board, players)
        for tile in player.tiles_in_play:  # next, we calculate what this player is allowed to do
            if not isinstance(tile, Troop):
                continue  # for any tiles that are not actually Troop objects, nothing to do
            x, y = tile.coords
            choices['act'][(x, y)] = self.__calculate_allowed_actions_for_troop(player, tile, consider_duke_safety,
                                                                                board, players)
        return choices

    def __calculate_valid_pull_locations(self, player, board, players):
        """Determines all the (x, y)-coordinates where a player can play a new tile given the current board state.

        :param player: Player object of the player whose valid pull locations the game is trying to calculate
        :param board: Board object of the board to be used in calculation
        :param players: tuple of Player objects of players to be used in calculation
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
                0 <= i < 6 and 0 <= j < 6 and board.get_tile(i, j) is None and
                not self.__duke_would_be_endangered(player, {
                    'action_type': 'pull',
                    'src_location': (i, j),
                    'tile': Troop('', player.side, (i, j), True)
                }, board, players)
            )
        ]

    def __calculate_allowed_actions_for_troop(self, player, troop, consider_duke_safety, board, players):
        """Determines all the actions that a troop tile can perform given the current board state.

        :param player: Player object of the player to whom the tile belongs
        :param troop: Troop object under consideration
        :param consider_duke_safety: boolean that affects whether the Duke's safety will be taken into account
            See choices() for more details.
        :param board: Board object of the board to be used in calculation
        :param players: tuple of Player objects of players to be used in calculation
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
                dst_tile = board.get_tile(i, j)
                if (tile_is_open_or_enemy(dst_tile, player) and path_is_open(board, i, j, dx, dy)
                        and not (consider_duke_safety and self.__duke_would_be_endangered(player, {
                            'action_type': 'mov',
                            'src_location': (x, y),
                            'dst_location': (i, j)
                        }, board, players))):
                    actions['moves'].append((i, j))  # move is allowed
            elif item['move'] == 'JUMP':
                dst_tile = board.get_tile(i, j)
                if (tile_is_open_or_enemy(dst_tile, player)
                        and not (consider_duke_safety and self.__duke_would_be_endangered(player, {
                            'action_type': 'mov',
                            'src_location': (x, y),
                            'dst_location': (i, j)
                        }, board, players))):
                    actions['moves'].append((i, j))  # jump is allowed
            elif item['move'] == 'SLIDE' or item['move'] == 'JUMP SLIDE':  # jump slide actually uses same logic lol
                dst_tile = None
                it_x = 0 if dx == 0 else int(dx / abs(dx))  # e.g., when delta_x = 2, it_x = 1
                it_y = 0 if dy == 0 else int(dy / abs(dy))  # (moving in same direction as slide)
                step = 0
                cur_i = i
                cur_j = j
                while 0 <= cur_i < 6 and 0 <= cur_j < 6:
                    dst_tile = board.get_tile(cur_i, cur_j)
                    if dst_tile is not None:  # slide stops here
                        break  # consider after loop
                    if not (consider_duke_safety and self.__duke_would_be_endangered(player, {
                        'action_type': 'mov',
                        'src_location': (x, y),
                        'dst_location': (cur_i, cur_j)
                    }, board, players)):
                        actions['moves'].append((cur_i, cur_j))  # slide is allowed
                    step += 1
                    cur_i = i + step * it_x
                    cur_j = j + step * it_y
                if (0 <= cur_i < 6 and 0 <= cur_j < 6 and dst_tile is not None and dst_tile.player_side != player.side
                        and not (consider_duke_safety and self.__duke_would_be_endangered(player, {
                            'action_type': 'mov',
                            'src_location': (x, y),
                            'dst_location': (cur_i, cur_j)
                        }, board, players))):
                    actions['moves'].append((cur_i, cur_j))  # slide is allowed
            elif item['move'] == 'STRIKE':
                str_tile = board.get_tile(i, j)
                if (tile_is_enemy(str_tile, player)
                        and not (consider_duke_safety and self.__duke_would_be_endangered(player, {
                            'action_type': 'str',
                            'src_location': (x, y),
                            'str_location': (i, j)
                        }, board, players))):
                    actions['strikes'].append((i, j))  # strike is allowed
            elif item['move'] == 'COMMAND':
                cmd_tile = board.get_tile(i, j)
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
                }, board, players)):
                    actions['commands'][src_loc].append(dst_loc)  # command is allowed
        return actions

    def __duke_would_be_endangered(self, player, choice, board, players):
        """Checks the legality of taking an action in the context of the Duke's safety.

        Just like in chess, when a player is in check, they may only take actions that get out of the state.
        Additionally, a player may not make a move that self-induces check.
        This can be generalized to the following logic when considering an action:
            1. make the move
            2. see if the Duke is in check
            3. undo the move

        :param player: Player object of the player considering taking the action
        :param choice: special dict called "choice", whose format is documented in docs/choice_formats.txt
        :param board: Board object representing current board state
        :param players: tuple of Player objects of players to be used in calculations
            When None, this tells the function to use self.__players.
        :return: boolean representing whether the Duke would be endangered by the action - True is so, False if not
        """
        if choice is None:  # may occur when player does not care about considering the Duke's safety
            return True
        if players is None:
            players = self.__players
        would_be_endangered = False
        all_player_copies = []
        player_copy = None
        for p in players:  # make copies to work with
            all_player_copies.append(copy(p))
            if p == player:
                player_copy = all_player_copies[-1]  # the most recently appended is the player of interest
        all_player_copies = tuple(all_player_copies)
        board_copy = board.copy(all_player_copies)
        self.make_choice(player_copy, choice, True, board_copy, all_player_copies)  # literally make the move
        all_enemy_attacks = set()
        for other_copy in all_player_copies:  # recalculate the allowed moves for the opponent(s)
            if player_copy != other_copy:
                other_choices = self.calculate_choices(other_copy, False, board_copy, all_player_copies)
                all_enemy_attacks = all_enemy_attacks.union(get_attacks(other_choices))
        if player_copy.duke.coords in all_enemy_attacks:
            would_be_endangered = True
        self.__actions_taken.pop()  # since self.make_choice() appends, need to undo move here
        return would_be_endangered

    def make_choice(self, player, choice, considering=False, board=None, players=None):
        """Executes a given move on the board.

        The game is responsible for managing the board.
        From the Player objects' perspectives, the Tiles', the Bags', etc.... none of these actually know what the
            board state is. So this function exists to manage it whenever it needs to change.

        :param player: Player object of the player making the move
        :param choice: special dict called "choice", whose format is documented in docs/choice_formats.txt
        :param considering: boolean that should be True if the choice is experimental, i.e., not meant to be permanent
            When True, you should also include the next two parameters.
        :param board: Board object of the board to be updated
            Pass a copy of self.__board here if you don't want to modify the actual board.
        :param players: tuple of Player objects of all players in the game
            Pass a copy of self.__players here if you don't want to modify the actual players.
        """
        if board is None or players is None:
            board = self.__board
            players = self.__players
        if choice['action_type'] == 'pull':
            board.set_tile(choice['src_location'][0], choice['src_location'][1], choice['tile'])
            if not considering:
                self.__non_meaningful_moves_counter = 0  # pulling is a meaningful move
        else:
            choice['tile'] = None
            src_tile = board.get_tile(choice['src_location'][0], choice['src_location'][1])
            if choice['action_type'] != 'str':  # 'mov' or 'cmd'
                dst_tile = board.get_tile(choice['dst_location'][0], choice['dst_location'][1])
                if dst_tile is not None:  # if an enemy tile is in the destination location
                    enemy_player = players[dst_tile.player_side - 1]
                    dst_tile = enemy_player.remove_from_play(choice['dst_location'][0], choice['dst_location'][1])
                    players[player.side - 1].capture(dst_tile)
                    choice['tile'] = dst_tile
                    if not considering:
                        self.__non_meaningful_moves_counter = 0  # capturing is a meaningful move
                elif not considering:
                    self.__non_meaningful_moves_counter += 1  # movement without capturing is not considered meaningful
                if choice['action_type'] == 'mov':
                    src_tile.flip()
                else:
                    cmd_tile = board.get_tile(choice['cmd_location'][0], choice['cmd_location'][1])
                    cmd_tile.flip()
                    board.set_tile(choice['cmd_location'][0], choice['cmd_location'][1], cmd_tile)
                board.set_tile(choice['src_location'][0], choice['src_location'][1], None)
                src_tile.move(choice['dst_location'][0], choice['dst_location'][1])
                board.set_tile(choice['dst_location'][0], choice['dst_location'][1], src_tile)
            else:  # 'str'
                str_tile = board.get_tile(choice['str_location'][0], choice['str_location'][1])
                enemy_player = players[str_tile.player_side - 1]
                str_tile = enemy_player.remove_from_play(choice['str_location'][0], choice['str_location'][1])
                players[player.side - 1].capture(str_tile)
                choice['tile'] = str_tile
                if not considering:
                    self.__non_meaningful_moves_counter = 0  # striking (and capturing) is a meaningful move
                src_tile.flip()
                board.set_tile(choice['src_location'][0], choice['src_location'][1], src_tile)
                board.set_tile(choice['str_location'][0], choice['str_location'][1], None)  # funny story here
        self.__actions_taken.append(choice)  # log the choice made on this turn

    def undo_choice(self, player, board):
        """Undoes the most recent action carried out on the board.

        Note that this does NOT guarantee that other object data modified by make_choice() is undone.
        This function is most likely only ever used to undo "pretend" moves.
        If one wishes to "pretend" to make a move and then call this function to undo it, this function will only
            reset the board state. The caller would be responsible for storing necessary information before making the
            move, so that they could restore it as needed afterwards.

        :param player: Player object of the player who made the last move
        :param board: Board object of the board on which the action is being undone
        """
        choice = self.__actions_taken.pop()
        if choice['action_type'] == 'pull':
            board.set_tile(choice['src_location'][0], choice['src_location'][1], None)
        else:
            captured_tile = None
            if choice['tile'] is not None:
                captured_tile = player.undo_last_capture()
            src_tile = board.get_tile(choice['src_location'][0], choice['src_location'][1])
            if choice['action_type'] != 'str':  # 'mov' or 'cmd'
                dst_tile = board.get_tile(choice['dst_location'][0], choice['dst_location'][1])
                if choice['action_type'] == 'mov':
                    dst_tile.flip()
                else:
                    cmd_tile = board.get_tile(choice['cmd_location'][0], choice['cmd_location'][1])
                    cmd_tile.flip()
                    board.set_tile(choice['cmd_location'][0], choice['cmd_location'][1], cmd_tile)
                board.set_tile(choice['src_location'][0], choice['src_location'][1], dst_tile)
                dst_tile.move(choice['src_location'][0], choice['src_location'][1])
                board.set_tile(choice['dst_location'][0], choice['dst_location'][1], captured_tile)
            else:  # 'str'
                src_tile.flip()
                board.set_tile(choice['src_location'][0], choice['src_location'][1], src_tile)
                board.set_tile(choice['str_location'][0], choice['str_location'][1], captured_tile)

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
        self.__finish_time = time() - self.__start_time
        self.__winner = status
        if status > 0:
            self.__finish_message = f'Checkmate! {reason}'
        elif status == 0:
            self.__finish_message = f'Draw! {reason}'
