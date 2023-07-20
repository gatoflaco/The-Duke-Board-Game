"""
player.py
Isaac Jung

This module contains code implementing the AI for vs CPU games.
"""

from src.player import Player
from src.tile import Troop
from src.util import *
from src.constants import STARTING_TROOPS, TROOP_WEIGHTS
from random import randrange, shuffle


class Difficulty:
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
    """

    def __init__(self, side, game, difficulty=Difficulty.NORMAL):
        super(AI, self).__init__(side)
        self.__game = game  # AI will need access to game's functions like make_choice() and undo_choice() for scoring
        self.__difficulty = difficulty

    def setup_phase(self):
        """Runs the setup phase for an AI.

        The setup phase consists of placing the Duke in the rank closest to the player's side, in either file c or d,
            and then placing exactly two Footman tiles on any 2 of the 3 cardinally adjacent spaces next to the Duke.
        Although the AI decides where to place its tiles, it doesn't score anything here. It just randomly picks.
        """
        y = 0 if self._side == 1 else 5
        valid_duke_coords = {(2, y), (3, y)}
        duke_coords = valid_duke_coords.pop()  # randomly pick one of the valid starting places for the Duke
        for troop_name in STARTING_TROOPS:  # first, find and play the Duke
            if troop_name == 'Duke':
                self._in_play.append(Troop(troop_name, self._side, duke_coords, True))
                self._duke = self._in_play[-1]
                break
        dy = 1 if self._side == 1 else -1
        other_coords = {(duke_coords[0] - 1, y), (duke_coords[0], y + dy), (duke_coords[0] + 1, y)}
        for troop_name in STARTING_TROOPS:  # next, play other starting troops
            if troop_name == 'Duke':
                continue
            self._in_play.append(Troop(troop_name, self._side, other_coords.pop(), True))

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
        choice_list = self.__initialize_choice_list()
        shuffle(choice_list)  # for randomness
        mapping = {}
        total_score = 0
        for i in range(len(choice_list)):
            total_score += self.__score_choice(choice_list[i])
            mapping[i] = total_score
        choice = choice_list[0]  # if all choices are equally bad, this will be used (random after having shuffled)
        if total_score != 0:  # if all choices WEREN'T equally bad
            n = randrange(0, total_score)
            for i in range(len(choice_list)):
                if n < mapping[i]:  # found the choice in whose range the rng landed
                    choice = choice_list[i]
                    break
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
        :return: score for the given choice, a non-negative integer
            Larger values indicate more promise. If the score is 0, it absolutely should not be picked.
        """
        if self.__difficulty == Difficulty.BEGINNER:
            return 0    # if every choice scores 0, take_turn() should choose a random move

        score = 100

        if self.__difficulty != Difficulty.EXPERT:
            score += self.__general_heuristics(choice)

        if self.__difficulty == Difficulty.EASY:
            return score  # should not consider consequences of making the choice

        # next, pretend to make the move and see what effect it has on the game
        score += self.__consider_consequences(choice)

        return score if score >= 0 else 0  # don't return negative numbers

    def __general_heuristics(self, choice):
        """Helper for __score_choice() that makes generalizations without actually pretending to make the move.

        :param choice: special dict called "choice", whose format is documented in docs/choice_formats.txt
        :return: score for the given choice
        """
        score = 0
        board = self.__game.get_board()
        x, y = choice['src_location']
        if choice['action_type'] == 'pull':
            if self.__difficulty > Difficulty.EASY:
                score += self.__consider_trapped_duke(-1, -1, x, y)
            if self.__difficulty > Difficulty.NORMAL:
                # TODO: call function to calculate expected value of tile that would be pulled
                #  that is, sum up all (probability of pulling t * value of t on side 1) and divide for the average
                pass
        elif choice['action_type'] == 'mov':
            i, j = choice['dst_location']
            dst_tile = board.get_tile(i, j)
            if tile_is_enemy(dst_tile, self):
                score += 50  # prefer capturing enemy tiles
                if self.__difficulty > Difficulty.EASY:
                    score += TROOP_WEIGHTS[dst_tile.get_name()][str(dst_tile.get_side())]
            if self.__difficulty > Difficulty.EASY:
                score += self.__consider_trapped_duke(x, y, i, j)
            if self.__difficulty > Difficulty.NORMAL:
                pass  # call function to look at what src tile would flip to (if it becomes useless, subtract score)
        elif choice['action_type'] == 'str':
            score += 50  # prefer capturing enemy tiles
            if self.__difficulty > Difficulty.EASY:
                i, j = choice['str_location']
                str_tile = board.get_tile(i, j)
                score += TROOP_WEIGHTS[str_tile.get_name()][str(str_tile.get_side())]
            if self.__difficulty > Difficulty.NORMAL:
                pass  # call function to look at what src tile would flip to (if it becomes useless, subtract score)
        elif choice['action_type'] == 'cmd':
            i, j = choice['dst_location']
            dst_tile = board.get_tile(i, j)
            if tile_is_enemy(dst_tile, self):
                score += 50  # prefer capturing enemy tiles
                if self.__difficulty > Difficulty.EASY:
                    score += TROOP_WEIGHTS[dst_tile.get_name()][str(dst_tile.get_side())]
            if self.__difficulty > Difficulty.EASY:
                score += self.__consider_trapped_duke(x, y, i, j)
            if self.__difficulty > Difficulty.NORMAL:
                pass  # call function to look at what cmd tile would flip to (if it becomes useless, subtract score)
        # TODO: consider more context than just whether the action would capture
        #  for example, avoid trapping own Duke from moving, avoid moving Duke into a corner, etc.
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
        duke_x, duke_y = self._duke.get_coords()
        if duke_x == x and duke_y == y:  # moving tile IS the Duke
            return 0  # Duke cannot trap itself lol

        # first, consider improving score if tile is starting in the Duke's way
        if self._duke.get_side() == 1 and y == duke_y:  # if tile is currently in same rank as Duke on side 1
            distance = abs(x - duke_x) - 1  # e.g., when directly adjacent, consider distance to be 0
            score += (100 - distance * 20)  # the closer to the Duke, the more trapped, so add more
        elif self._duke.get_side() == 2 and x == duke_x:  # if tile is currently in same file as Duke on side 2
            distance = abs(y - duke_y) - 1
            score += (100 - distance * 20)

        # next, consider worsening score if tile would move into the Duke's way
        if self._duke.get_side() == 1 and j == duke_y:  # if move would end in same rank as Duke on side 1
            distance = abs(i - duke_x) - 1
            score -= (100 - distance * 20)  # the closer to the Duke, the more trapped, so subtract more
        elif self._duke.get_side() == 2 and i == duke_x:  # if move would end in same file as Duke on side 2
            distance = abs(j - duke_y) - 1
            score -= (100 - distance * 20)
        return score

    def __consider_consequences(self, choice):
        """Helper for __score_choice() that looks at what would happen if the move were made.

        :param choice: special dict called "choice", whose format is documented in docs/choice_formats.txt
        :return: score for the given choice
        """
        score = 0
        players = self.__game.get_players()
        cur_in_play = []
        for p in players:  # save some states before they get modified
            cur_in_play.append(p.get_tiles_in_play().copy())
        self.__game.make_choice(self, choice)  # literally make the move

        ai_choices = self.__game.get_choices(self, False)  # recalculate the allowed moves for the AI
        ai_attacks = get_attacks(ai_choices)  # consider what AI would then be able to attack
        # TODO: do something with knowledge of AI attacks upon making the move

        all_enemy_attacks = set()  # consider what enemies would then be able to attack
        for other in players:  # recalculate the allowed moves for the opponent(s)
            if self != other:
                other_choices = self.__game.get_choices(other, False)
                all_enemy_attacks = all_enemy_attacks.union(get_attacks(other_choices))
        # TODO: do something with knowledge of enemy attacks upon making the move

        for i in range(len(players)):  # restore saved states
            players[i].set_tiles_in_play(cur_in_play[i])
        self.__game.undo_choice(self)
        return score
