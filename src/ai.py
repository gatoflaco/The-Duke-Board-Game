"""
player.py
Isaac Jung

This module contains code implementing the AI for vs CPU games.
"""

from src.player import Player
from src.tile import Troop
from src.util import *
from src.constants import STARTING_TROOPS, TROOP_WEIGHTS, MIN_TURN_TIME
from copy import copy
from enum import Enum
from random import randrange, seed, shuffle
from sys import maxsize
from time import sleep, time


class Difficulty(Enum):
    """Serves as a sort of enum for the difficulty levels the AI can have.

    The beginner AI does not think at all, and will just make random moves.
    The easy AI makes decisions without ever considering the consequences of moves; it just utilizes generalized rules
    of thumb to rate a given decision as good or bad (e.g., if the move would capture an enemy tile, it is better than a
    move that would not).
    The normal AI does some basic consideration of whether a move would put themselves in an advantageous or
    disadvantageous position (e.g., if making the move would put their opponent in check, this is good) in addition to
    the generalized heuristics utilized by the easy AI.
    The hard AI makes lots of considerations about the consequences of an action, (e.g., if the move would allow them to
    defend an otherwise unguarded teammate that is currently under attack, this is good).
    The expert AI skips the easy AI heuristics and only scores good or bad based on the consequences of a move.
    """
    BEGINNER = 0
    EASY = 1
    NORMAL = 2
    HARD = 3
    EXPERT = 4

    def __lt__(self, other):
        if isinstance(other, Difficulty):
            return self.value < other.value
        raise NotImplementedError

    def __le__(self, other):
        if isinstance(other, Difficulty):
            return self.value <= other.value
        raise NotImplementedError

    def __gt__(self, other):
        if isinstance(other, Difficulty):
            return self.value > other.value
        raise NotImplementedError

    def __ge__(self, other):
        if isinstance(other, Difficulty):
            return self.value >= other.value
        raise NotImplementedError

    def __str__(self):
        if self.value == 0:
            return 'BEGINNER'
        if self.value == 1:
            return 'EASY'
        if self.value == 2:
            return 'NORMAL'
        if self.value == 3:
            return 'HARD'
        if self.value == 4:
            return 'EXPERT'
        return ''


class AI(Player):
    """Special type of Player that is not controlled by user input, but algorithmic decision-making instead.

    Parameters
    ----------
    side : int
        Integer ID of the player, corresponding to which side they're on.
        There is no such thing as a player 0, so this should start at 1 and increment from there.
        Must be unique from the other player(s) in the game.
    game : Game object
        Reference to own Game in which the AI was instantiated.
        Needed so that the AI can ask the game to carry out some computations for it, such as pretend moves.
    difficulty : Difficulty attribute (optional; Difficulty.NORMAL by default)
        Difficulty level of the AI. Affects how much thought goes into move scoring.
    rng_seed : int (optional; random.randrange(random.maxsize) by default)
        Seed used for randomness. In theory, if two AI played each other with the same seeds, the game would play out
        exactly the same every time.
    """

    def __init__(self, side, game, difficulty=Difficulty.NORMAL, rng_seed=randrange(maxsize)):
        super(AI, self).__init__(side, str(difficulty) + ' CPU')
        self.__game = game  # AI will need access to game's functions like make_choice() and undo_choice() for scoring
        self.__difficulty = difficulty
        self.__seed = rng_seed
        seed(self.__seed)
        print('Player', self._side, 'seed:', self.__seed)

    def __copy__(self):
        cls = self.__class__
        result = cls.__new__(cls)
        result._side = self._side
        result._name = self._name
        result._in_play = []
        for tile in self._in_play:
            result._in_play.append(copy(tile))
        result._bag = copy(self._bag)
        result._captured = []
        for tile in self._captured:
            result._captured.append(copy(tile))
        result._duke = None
        for troop in result._in_play:
            if troop.name == 'Duke':
                result._duke = troop
                break
        result._in_check = self._in_check
        result._choices = self._choices.copy()
        result.__game = self.__game
        result.__difficulty = self.__difficulty
        result.__seed = self.__seed
        return result

    def setup_phase(self, board):
        """Runs the setup phase for an AI.

        The setup phase consists of placing the Duke in the rank closest to the player's side, in either file c or d,
            and then placing exactly two Footman tiles on any 2 of the 3 cardinally adjacent spaces next to the Duke.
        Although the AI decides where to place its tiles, it doesn't score anything here. It just randomly picks.

        :param board: Board object on which setup phase should occur
        :return: list of special dicts called "choice", whose format is documented in docs/choice_formats.txt
        """
        tic = time()  # for keeping the AI from making a decision too quickly (it can be jarring lol)
        choice_list = []
        y = 0 if self._side == 1 else 5
        valid_duke_coords = [(2, y), (3, y)]
        duke_coords = valid_duke_coords.pop(randrange(len(valid_duke_coords)))  # randomly pick Duke starting place
        for troop_name in STARTING_TROOPS:  # first, find and play the Duke
            if troop_name == 'Duke':
                self._in_play.append(Troop(troop_name, self._side, duke_coords, True))
                self._duke = self._in_play[-1]
                choice_list.append({
                    'action_type': 'pull',
                    'src_location': duke_coords,
                    'tile': self._in_play[-1]
                })
                toc = time()
                dif = toc - tic
                if dif < MIN_TURN_TIME / 3:
                    sleep(MIN_TURN_TIME / 3 - dif)
                tic = toc
                board.set_tile(duke_coords[0], duke_coords[1], self._in_play[-1])
                break
        dy = 1 if self._side == 1 else -1
        other_coords = [(duke_coords[0] - 1, y), (duke_coords[0], y + dy), (duke_coords[0] + 1, y)]
        for troop_name in STARTING_TROOPS:  # next, play other starting troops
            if troop_name == 'Duke':
                continue
            coords = other_coords.pop(randrange(len(other_coords)))
            self._in_play.append(Troop(troop_name, self._side, coords, True))
            choice_list.append({
                'action_type': 'pull',
                'src_location': coords,
                'tile': self._in_play[-1]
            })
            toc = time()
            dif = toc - tic
            if dif < MIN_TURN_TIME / 3:
                sleep(MIN_TURN_TIME / 3 - dif)
            tic = toc
            board.set_tile(coords[0], coords[1], self._in_play[-1])
        return choice_list

    @property
    def seed(self):
        return self.__seed

    def take_turn(self):
        """Handles the logic of taking AI's turn.

        Operates based on what is currently in the self._choices dict, a special dict whose format is documented in
            docs/choice_formats.txt. The dict should contain all the things the AI could legally do at the moment. In
            order for this to be true, game.py should maintain the dict for the AI, updating it as needed any time the
            board state changes.
        The AI's implementation is extremely naive. It makes subjective scoring decisions for every possible move in
            self._choices, but in the end, rng will determine what it will do; that is, even if it scores a decision
            very low, there is a possibility that it will pick it anyway.
        Basically, we fill it out a mapping of every possible choice to some integer, following this algorithm:
            1. initialize total_score to 0
            2. determine a scoring for the first choice, increment total_score by that much, then assign the current
                value of total_score to the value of that choice in the mapping
            3. repeat step 2 for the next choice, and the next, and so on, until all choices have been assigned a score
        Once the mapping is complete, we do the following:
            1. generate a random number n in [0, total_score)
            2. iterate through the mapping by value, in numerical order, checking if n < value
            3. as soon as n < value, return that choice

        :return: special dict called "choice", whose format is documented in docs/choice_formats.txt
        """
        tic = time()
        choice_list = self.__initialize_choice_list()
        shuffle(choice_list)  # for randomness
        mapping = {}
        total_score = 0
        for i in range(len(choice_list)):
            score = self.__score_choice(choice_list[i])
            if score == -1:  # score of -1 means to absolutely pick this choice right away
                if self.__difficulty > Difficulty.EASY:
                    return self.__return_choice(choice_list[i], tic)
                score = 1000
            total_score += score
            mapping[i] = score
        if total_score == 0:  # when total score is 0, this means all choices are equally bad
            return self.__return_choice(choice_list[0], tic)  # if all choices are equally bad, this will be random

        # next, we bias the scores towards the average - the easier the difficulty, the closer to the average we shift
        # this will make easier difficulties have a more uniform score distribution
        # i.e., the easier difficulties will artificially increase their odds of making poorly-scored choices
        average_score = sum(value for value in mapping.values()) // len(mapping)
        cur_total = 0.0
        n = randrange(0, total_score)  # roll the rng
        choice = None
        for i in range(len(choice_list)):
            choice = choice_list[i]
            cur_total += round(((mapping[i] * 10 * self.__difficulty.value + average_score)
                                / (10 * self.__difficulty.value + 1)), 2)
            if n < cur_total:  # found the choice in whose range the rng landed
                break
        return self.__return_choice(choice, tic)

    def __return_choice(self, choice, tic):
        """Small helper function for that should be called by take_turn() when ready to return a choice.

        :param choice: special dict called "choice", whose format is documented in docs/choice_formats.txt
        :param tic: time.time() value that should have been generated at the top of take_turn()
        :return: special dict called "choice", whose format is documented in docs/choice_formats.txt
            It may be updated if the choice was to pull.
        """
        toc = time()
        dif = toc - tic
        if dif < MIN_TURN_TIME:
            sleep(MIN_TURN_TIME - dif)
        if choice['action_type'] == 'pull':  # need to actually draw the new tile here
            x, y = choice['src_location']
            choice['tile'] = self.play_new_troop_tile(x, y)
        return choice

    def __initialize_choice_list(self):
        """Creates a list of choice dicts that the AI can score in its take_turn() function.

        The AI's take_turn() overrides that of its parent class, Player. Check the docstring for the AI take_turn()
            function for an understanding of how this function is meant to be used.

        :return: list of special dicts called "choice", whose format is documented in docs/choice_formats.txt
        """
        choice_list = []
        for location in self._choices['pull']:
            choice_list.append({
                'action_type': 'pull',
                'src_location': location,
                'tile': Troop('', self._side, location, True)
            })
        for troop_loc in self._choices['act']:
            for dst_loc in self._choices['act'][troop_loc]['moves']:
                choice_list.append({
                    'action_type': 'mov',
                    'src_location': troop_loc,
                    'dst_location': dst_loc
                })
            for str_loc in self._choices['act'][troop_loc]['strikes']:
                choice_list.append({
                    'action_type': 'str',
                    'src_location': troop_loc,
                    'str_location': str_loc
                })
            for teammate_loc in self._choices['act'][troop_loc]['commands']:
                for dst_loc in self._choices['act'][troop_loc]['commands'][teammate_loc]:
                    choice_list.append({
                        'action_type': 'cmd',
                        'src_location': teammate_loc,
                        'dst_location': dst_loc,
                        'cmd_location': troop_loc,
                    })
        return choice_list

    def __score_choice(self, choice):
        """Carries out the bulk of the scoring logic for a given choice.

        :param choice: special dict called "choice", whose format is documented in docs/choice_formats.txt
        :return: score for the given choice, a non-negative integer (or -1)
            Larger values indicate more promise. If the score is 0, it absolutely should not be picked.
            -1 is a special case that tells the caller that the choice actually SHOULD be picked, over anything else.
        """
        score = 0
        #if self.__difficulty == Difficulty.BEGINNER:
        #    return score    # if every choice scores 0, take_turn() should choose a random move
        score += self.__general_heuristics(choice)

        # next, pretend to make the move and see what effect it has on the game
        if choice['action_type'] == 'pull':  # special handling for pull
            pull_scores = []
            total = 0
            non_checkmate_count = 0
            for tile in self._bag.tiles:
                choice['tile'] = Troop(tile.name, self._side, choice['src_location'], True)
                pull_scores.append(self.__consider_consequences(choice))
                if pull_scores[-1] != -1:
                    total += pull_scores[-1]
                    non_checkmate_count += 1
            if non_checkmate_count == 0:  # literally anything that gets pulled will checkmate the opponent
                return -1  # special int that tells caller that they should definitely make this choice
            average_score = total // non_checkmate_count
            for i in range(len(pull_scores)):
                if pull_scores[i] == -1:  # pulling this tile would checkmate
                    pull_scores[i] = average_score * 2
            score_to_add = sum(pull_scores) // len(pull_scores)  # expected value of pulling
        else:
            score_to_add = self.__consider_consequences(choice)
        if score_to_add == -1:  # -1 represents that you should choose this move over everything else
            return -1
        score += score_to_add

        return score if score >= 0 else 0  # don't return negative numbers

    def __general_heuristics(self, choice):
        """Helper for __score_choice() that makes generalizations without actually pretending to make the move.

        :param choice: special dict called "choice", whose format is documented in docs/choice_formats.txt
        :return: score for the given choice
        """
        score = 0
        board = self.__game.board
        x, y = choice['src_location']
        if choice['action_type'] == 'pull':
            score += self.__consider_trapped_duke(-1, -1, x, y)
            # TODO: call function to calculate expected value of tile that would be pulled
            #  that is, sum up all (probability of pulling t * value of t on side 1) and divide for the average
        elif choice['action_type'] == 'mov':
            i, j = choice['dst_location']
            dst_tile = board.get_tile(i, j)
            if tile_is_enemy(dst_tile, self):
                score += 50  # prefer capturing enemy tiles
                score += TROOP_WEIGHTS[dst_tile.name][str(dst_tile.side)]
            score += self.__consider_trapped_duke(x, y, i, j)
            # TODO: call function to look at what src tile would flip to (if it becomes useless, subtract score)
        elif choice['action_type'] == 'str':
            score += 50  # prefer capturing enemy tiles
            i, j = choice['str_location']
            str_tile = board.get_tile(i, j)
            score += TROOP_WEIGHTS[str_tile.name][str(str_tile.side)]
            # TODO: call function to look at what src tile would flip to (if it becomes useless, subtract score)
        elif choice['action_type'] == 'cmd':
            i, j = choice['dst_location']
            dst_tile = board.get_tile(i, j)
            if tile_is_enemy(dst_tile, self):
                score += 50  # prefer capturing enemy tiles
                score += TROOP_WEIGHTS[dst_tile.name][str(dst_tile.side)]
            score += self.__consider_trapped_duke(x, y, i, j)
            # TODO: call function to look at what cmd tile would flip to (if it becomes useless, subtract score)
        # TODO: consider more context than just whether the action would capture
        #  for example, avoid moving Duke into a corner, etc.
        return score

    def __consider_trapped_duke(self, x, y, i, j):
        """Helper for __general_heuristics() that looks to see if moving a tile would block the Duke.

        :param x: x-coordinate of moving tile
        :param y: y-coordinate of moving tile
        :param i: x-coordinate of location to which tile is moving
        :param j: y-coordinate of location to which tile is moving
        :return: score in range [-100, 100] (in increments of 20)
            larger negative score means Duke gets trapped worse, 0 means Duke is not trapped at all
        """
        score = 0
        duke_x, duke_y = self._duke.coords
        if duke_x == x and duke_y == y:  # moving tile IS the Duke
            return 0  # Duke cannot trap itself lol

        # first, consider improving score if tile is starting in the Duke's way
        if self._duke.side == 1 and y == duke_y:  # if tile is currently in same rank as Duke on side 1
            distance = abs(x - duke_x) - 1  # e.g., when directly adjacent, consider distance to be 0
            score += (200 - distance * 40)  # the closer to the Duke, the more trapped, so add more
        elif self._duke.side == 2 and x == duke_x:  # if tile is currently in same file as Duke on side 2
            distance = abs(y - duke_y) - 1
            score += (200 - distance * 40)

        # next, consider worsening score if tile would move into the Duke's way
        if self._duke.side == 1 and j == duke_y:  # if move would end in same rank as Duke on side 1
            distance = abs(i - duke_x) - 1
            score -= (200 - distance * 40)  # the closer to the Duke, the more trapped, so subtract more
        elif self._duke.side == 2 and i == duke_x:  # if move would end in same file as Duke on side 2
            distance = abs(j - duke_y) - 1
            score -= (200 - distance * 40)
        return score

    def __consider_consequences(self, choice):
        """Helper for __score_choice() that looks at what would happen if the move were made.

        :param choice: special dict called "choice", whose format is documented in docs/choice_formats.txt
        :return: score for the given choice
        """
        score = 0
        players = self.__game.players
        original_attacks = get_attacks(self.choices)
        original_enemy_attacks = set()
        for other in players:
            if self != other:
                original_enemy_attacks.union(get_attacks(other.choices))
        all_player_copies = []
        ai_copy = None
        for p in players:  # save some states before they get modified
            all_player_copies.append(copy(p))
            if p == self:
                ai_copy = all_player_copies[-1]  # the most recently appended is the player of interest
        all_player_copies = tuple(all_player_copies)
        board_copy = self.__game.board.copy(all_player_copies)

        if choice['action_type'] == 'pull':  # note that calling this function with a pull action requires a specific \
            x, y = choice['src_location']    # troop type being tested; that is, choice['tile'].name should not be ''
            ai_copy.play_new_troop_tile(x, y, choice['tile'])  # this loc is why the above must be true
            score += TROOP_WEIGHTS[choice['tile'].name]['1']
        ai_copy.__game.make_choice(ai_copy, choice, True, board_copy, all_player_copies)  # literally make the move
        ai_copy.update_choices(ai_copy.__game.calculate_choices(ai_copy, True, board_copy, all_player_copies))
        new_attacks = get_attacks(ai_copy.choices)
        ai_attacks = get_attacks(ai_copy.__game.calculate_choices(ai_copy, False, board_copy))  # no Duke safety here
        all_enemy_attacks = set()  # consider what enemies would then be able to attack
        for other_copy in all_player_copies:  # recalculate the allowed moves for the opponent(s)
            if score == -1:
                break
            if ai_copy == other_copy:
                continue
            other_copy.update_choices(ai_copy.__game.calculate_choices(other_copy, True, board_copy, all_player_copies))
            if other_copy.duke.coords in ai_attacks:
                other_copy.set_check(True)
            if other_copy.is_in_check:
                if has_no_valid_choices(other_copy.choices):  # this move checkmates!
                    score = -1
                    continue
                score += 200
            for tile in other_copy.tiles_in_play:  # conveniently ignores a captured tile
                if tile.coords in original_attacks and tile.coords not in new_attacks:
                    score -= 100  # enemy troop was previously under threat, but no longer
                if tile.coords in new_attacks and tile.coords not in original_attacks:
                    score += 100  # enemy troop was not previously under threat, and now it is
            all_enemy_attacks = all_enemy_attacks.union(get_attacks(other_copy.choices))
        if score != -1:  # consider if the move increased/decreased the number of friendly troops under attack
            for tile in ai_copy.tiles_in_play:
                if tile.coords in original_enemy_attacks and tile.coords not in all_enemy_attacks:
                    score += 100
                elif tile.coords in all_enemy_attacks and tile.coords not in original_enemy_attacks:
                    score -= 100

        ai_copy.__game.undo_choice(ai_copy, board_copy)
        return score
