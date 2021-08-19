# Zombies
This is a simple Tile Based Game to experiment with the basic concepts of game development. Based on the excellent tutorial by [KidsCanCode on YouTube](https://www.youtube.com/watch?v=3UxnelT9aCo&list=PLsk-HSGFjnaGQq7ybM8Lgkh5EMxUWPm2i&index=1)

## Required libraries
* pygame
* pytmx
* pytweening

## Key features
* tile based game
* A* algorithm for pathfinding
* random player start position
* random amount and location for hostages, ennemies and items
* cheat mode (*TODO*)

## Tools used
* Maps generated with Tiled (https://www.mapeditor.org/)
* Sound effects generated with [sfxr.me](https://sfxr.me)
* Most art taken from [opengameart.org](https://opengameart.org)

## Controls:
- Arrows to move
- 'Space' to fire
- 'r' to reload
- 'e' to switch weapons

## Goal of the game 
locate and bring all the hostage back to the rescue zone. 
You win the game by either killing all the zombies or rescuing all the hostages, and escaping yourself.
The player can escape only if all the hostages have been rescued and stayed long enough in the rescue zone
