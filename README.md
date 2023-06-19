# The Duke
### Author: Isaac Jung

I'll write more about the project as I work on it.

In short, this is a mini personal project with which to practice my Python skills,
with a focus on using [pygame](https://www.pygame.org/news) for a more involved GUI interface.

The project itself aims to implement
[a board game called The Duke](https://store.catalystgamelabs.com/products/the-duke),
starting with support for a local player vs player style of gameplay.
While I don't yet know how much effort I'll invest into this, I may eventually add a way to play against an AI
and/or some degree of online support.

The Duke is a two player strategy board game.
Originally designed by Jeremy Holcomb & Stephen McLaughlin, the rules bear some resemblance to chess,
but with more in-depth pieces and an element of randomness in the order in which these pieces come into play,
taking it from a perfect information game to something more approachable for beginners.
While the random aspect may seem uncompetitive,
it instead adds a layer of complexity that requires players to think flexibly,
resulting in every match feeling like a fresh challenge even against the same opponent.

The [full rulebook](The-Duke-Rulebook-Lo-Res_FINAL.pdf) details more about the game's mechanics,
but here is a short summary:
1. The game is played on a board consisting of a 6x6 grid of spaces. The board should be empty to start.
2. One player places their Duke tile in file c or d, along the rank closest to them, followed by two Footman tiles in any two of the three open spaces directly adjacent to their Duke.
   1. Note that all troop tiles have two sides. When placing troop tiles on the board, they must start on the side with the dark silhouhette, light background.
3. The second player does the same.
4. Both players place the rest of their troop tiles in their respective bags; the bags should be shaken to mix up the tiles.
5. Players take turns doing exactly one of the following actions:
   1. Move a troop tile: Choose one troop tile belonging to yourself and perform a valid movement with it. Afterward, that troop tile must flip to its reverse side.
   2. Place a troop tile: Draw from your bag at random, look to see what it is, then place the new troop on any open space directly adjacent to your Duke. The newly placed troop tile must start on the side with the dark silhouette, light background. If there are no open spaces directly adjacent to your Duke, you may not take this action.
6. Different types of movements exist. Please refer to the [rulebook](The-Duke-Rulebook-Lo-Res_FINAL.pdf) for a full list. All movements are capable of capturing opponent troop tiles (though it is not required to capture when moving). When a troop tile is captured, it is removed from the board and should be kept in a separate pile (one pile per player).
7. A player wins when they capture their opponent's Duke tile with any troop tile of their own (other win conditions can be introduced as well, but this is the only one that will be used for this project).

©2013 Catalyst Game Labs: The Duke is a trademark of Catalyst Game Labs. I do not claim ownership of The Duke or any of its assets used in this project.