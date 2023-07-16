"""
game.py
Isaac Jung

This module contains utility functions.
"""


def convert_file_and_rank_to_coordinates(file, rank, player_side=1):
    file_mapping = {'a': -2, 'b': -1, 'c': 0, 'd': 1, 'e': 2}
    x = file_mapping.get(file)
    if x is None:
        raise ValueError("Invalid file")
    y = rank - 3
    if player_side == 1:
        return x, y
    return -x, -y


def tile_is_open_or_enemy(tile, player):
    """Checks if a "destination" tile is either empty or occupied by an enemy tile.

    :param tile: Tile object being inspected, could be None or a Tile object with a .get_player() method (Troop)
    :param player: Player object representing the player considering this tile, needed to decide if tile is an "enemy"
    :return: boolean representing whether the tile is None or an enemy - True if so, False if not
    """

    return tile is None or tile.get_player() != player.get_side()


def tile_is_enemy(tile, player):
    """Checks that a "destination" tile is specifically occupied by an enemy tile.

    :param tile: Tile object being inspected, could be None or a Tile object with a .get_player() method (Troop)
    :param player: Player object representing the player considering this tile, needed to decide if tile is an "enemy"
    :return: boolean representing whether the tile is an enemy - True if so, False if not
    """

    return tile is not None and tile.get_player() != player.get_side()


def path_is_open(board, i, j, dx, dy):
    """Checks if there is a clear path between some d at (i, j) and some s at (i-dx, y-dy),
    i.e., every tile in between is None.

    The caller should determine dx and dy based on context. For example, when inspecting the following MOVE action,
    .  .  .  .  .
    .  .  .  .  .
    .  .  s  .  .
    .  .  .  .  .
    .  .  .  .  d
    where s is the source tile and d is the intended MOVE destination, dx would be 2, and dy would be -2,
    because it would require moving 2 units right and 2 units down from s in order to get to d.

    :param board: Board object representing the current state of the board
    :param i: x-coordinate of d (see above diagram) on the actual board
        In the diagram, the x-coordinate might appear to be 2, but s might not be at (0, 0) on the actual board.
        The caller would need to determine the value of i based on the x-coordinate of s, plus dx.
    :param j: y-coordinate of d (see above diagram) on the actual board
        See the description of the param i.
    :param dx: change in x to go from s to d (see above diagram)
    :param dy: change in y to go from s to d (see above diagram)
    :return: boolean representing whether there is a clear path - True if so, False if not

    """
    it_x = 0 if dx == 0 else int(dx / abs(dx))  # e.g., when dx = 2, it_x = 1
    it_y = 0 if dy == 0 else int(dy / abs(dy))
    num_tiles = max(abs(dx), abs(dy))  # e.g., if dx = 2 and dy = 0, it would take 2 steps to reach (i, j)
    return all(tile is None for tile in [board.get_tile(i-step*it_x, j-step*it_y) for step in range(1, num_tiles)])


def get_enemy_attacks(enemy_choices):
    enemy_attacks = set()
    for x, y in enemy_choices['act']:
        for move in enemy_choices['act'][(x, y)]['moves']:
            enemy_attacks.add(move)
        for strike in enemy_choices['act'][(x, y)]['strikes']:
            enemy_attacks.add(strike)
        for command in enemy_choices['act'][(x, y)]['commands']:
            if not enemy_choices['act'][(x, y)]['commands'][command]:
                enemy_attacks.add(command)
    return enemy_attacks


def has_no_valid_choices(choices):
    if len(choices['pull']) != 0:
        return False
    for troop_loc in choices['act']:
        if len(choices['act'][troop_loc]['moves']) != 0:
            return False
        if len(choices['act'][troop_loc]['strikes']) != 0:
            return False
        for teammate_loc in choices['act'][troop_loc]['commands']:
            if len(choices['act'][troop_loc]['commands'][teammate_loc]) != 0:
                return False
    return True
