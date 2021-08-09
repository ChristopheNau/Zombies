# spritesheet generator: https://spritegen.website-performance.org/
# Sound effects generated with https://sfxr.me
# Ascii banner generated with  https://www.ascii-art-generator.org/

import pygame as pg
import pytmx
from settings import *
from collections import deque
vec = pg.math.Vector2

# helper functions for breadth_first_search
# mobs can move left, right, up, down (no diagonals)
connections = [vec(0, -1), vec(0, 1), vec(1, 0), vec(-1, 0)]

# check if a node is in the bounds of the grid
# ie. if the grid is 10x9,
# the legal values are between 0 and 9 for x and between 0 and 8 for y
#def in_bounds(node):
#    return 0 <= node.x < WIDTH and 0 <= node.y < HEIGHT

# check if a node is not a wall
# return true if the node is not a wall
#def passable(node):
#    return node in game.passable_tiles

# find the neighbors of any given node
def find_neighbors(game, node):
    # all the node we can travel to from a given node:
    neighbors = [node + connection for connection in connections]
    # remove the neighbors that are not allowed (ie. not in bounds, in self.walls)
    # filter out the nodes not in bound
    # filter(function, list) removes the elements from "list" for which "function" return False
    #neighbors = filter(in_bounds, neighbors)
    #neighbors = filter(passable, neighbors)
    #neighbors = filter(lambda game: passable(game), neighbors)
    #neighbors = filter(passable, neighbors)

    # add variation in the order of neighbors to avoid long straight paths 
    if (node.x + node.y) % 2:
      neighbors.reverse()

    # remove neighbors which are not a "passable" tile
    new_neighbors = []
    for n in neighbors:
      if n in game.passable_tiles:
        new_neighbors.append(n)

    return new_neighbors

# convert a vector to a hashable object
# that we can use as a key for a dict()
def vec2int(v):
    return (int(v.x), int(v.y))

# visit all tiles using breadth_first_search
# calculates the path between any 2 tiles (super long)
def breadth_first_search(game, start):
    frontier = deque()
    frontier.append(start)
    # getting the list of visited tiles in not enough
    # we want to know how to get from tile to tile
    # ie. when we visit a new tile, where did we come from?
    # Path is dict() where:
    # - key = tile
    # - value = what tile we came from
    path = {}
    # we are already at "start"
    # start is a Vector (not hashable), it can't be the key for a dict
    # convert it to a tuple (int, int)
    path[vec2int(start)] = None

    while len(frontier) > 0:
        current = frontier.popleft()
        #print(f"Current: {current}")
        #print(f"neigbors: {list(self.find_neighbors(current))}")
        for next in find_neighbors(game, current):
            #print(f"next: {next}")
            if vec2int(next) not in path:
                #print(f"{next} not in path")
                frontier.append(next)
                # (current - next) is an arrow pointing from next to current
                path[vec2int(next)] = current - next
            #print(f"path: {path}")

    #for k,v in path.items():
    #    print(k,v)
    return path


# returns the path between 2 tiles
# must have calculated the breadth_first_search first
def follow_path(start, path):
    current = start
    path_to_follow = []
    path_to_follow.append(vec2int(start))
    try:
      while path[vec2int(current)] != None:
          current = current + path[vec2int(current)]
          path_to_follow.append(vec2int(current))
      path_to_follow.reverse()
      # remove last element (ie current tile)
      path_to_follow.pop()
      #print(f"Path from {start}: {path_to_follow}")
    # KeyError if no path from this tile
    except KeyError:
      pass
      #print(f"No path from {current} ({current * TILESIZE})")
    return path_to_follow

# function to wait for user to press a key
def wait_for_key(game, which_key="any"):
    # clear the event queue
    pg.event.wait()

    waiting = True
    while waiting:
        # static screen, don't need to run at a high FPS
        pg.display.set_caption("{:.2f}".format(game.clock.get_fps()))
        game.clock.tick(10)
        pg.display.set_caption("{:.2f}".format(game.clock.get_fps()))

        # wait for user's action
        for event in pg.event.get():
            # if the user closes the game window => end the waiting loop and the game
            if event.type == pg.QUIT:
                waiting = False
                game.running = False
            # if the user presses and releases any key, end the waiting loop
            if event.type == pg.KEYUP:
                if which_key == "any":
                    waiting = False
                else:
                    if event.key == pg.K_RETURN:
                        waiting = False

# function to draw text onto the screen
def draw_text(surface, text, font_name, size, color, x, y, align="nw"):
    font = pg.font.Font(font_name, size)
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect()
    if align == "nw":
        text_rect.topleft = (x, y)
    if align == "ne":
        text_rect.topright = (x, y)
    if align == "sw":
        text_rect.bottomleft = (x, y)
    if align == "se":
        text_rect.bottomright = (x, y)
    if align == "n":
        text_rect.midtop = (x, y)
    if align == "s":
        text_rect.midbottom = (x, y)
    if align == "e":
        text_rect.midright = (x, y)
    if align == "w":
        text_rect.midleft = (x, y)
    if align == "center":
        text_rect.center = (x, y)
    surface.blit(text_surface, text_rect)

# pg.sprite.spritecollide uses the sprite's image rectangle
# no matter how many other rectangle we have
# need to modify this to use the player's hit rectangle instead
# of the player's rect (as spritecollide does by default)
# one and two are the 2 sprites to check if they are colliding
def collide_hit_rect(one, two):
    return one.hit_rect.colliderect(two.rect)

# utility class for loading and parsing spritesheets
class Spritesheet:
    def __init__(self, filename):
        # load the image and convert it to a format pygame can easily manipulate (without .convert() the game would be slower)
        self.spritesheet = pg.image.load(filename).convert_alpha()

    # grab an image out of a larger spritesheet
    def get_image(self, x, y, width, height, resize_factor=1):
        #image = pg.Surface((width, height))
        image = pg.Surface([width, height], pg.SRCALPHA)

        #image = pg.Surface((width, height), pg.SRCALPHA)
        image.blit(self.spritesheet, (0, 0), (x, y, width, height))
        # resize the image
        # the (width, height) of new size must be integers
        image = pg.transform.scale(image, (round(width / resize_factor), round(height / resize_factor)))

        return image


# basic version: uses a simple text file to build the map

# Class to handle maps based on simple text files
class Map:
    def __init__(self, filename):
        # load map data
        self.data = []
        with open(filename, "rt") as f:
            for line in f:
                self.data.append(line.strip())

        # width of the map = number of columns in the map file
        self.tilewidth = len(self.data[0])
        # height of the map = nb of rows in data
        self.tileheight = len(self.data)
        # pixel width of the map
        self.width = self.tilewidth * TILESIZE
        self.height = self.tileheight * TILESIZE

# class to display tiled maps generated with Tiled (https://www.mapeditor.org/)
class TiledMap():
    def __init__(self, filename):
        # load tile file data (XML) for pygame
        # pytmx can be used with other libraries than pygame
        # pixelalpha => used to get the transparency that goes with the map
        tm = pytmx.load_pygame(filename, pixelalpha=True)
        # width of the map = how many tiles * with of each tile
        self.width = tm.width * tm.tilewidth
        self.height = tm.height * tm.tileheight
        # tmxdata holds all the map data
        self.tmxdata = tm

        # list of all tiles``
        self.all_tiles = set()

    # take a pygame surface and draw all the tiles of the map onto it
    def render(self, surface):
        # this method get the ID of a tile to define the image
        # that goes with a certain tile
        # create an alias as the command is very long
        ti = self.tmxdata.get_tile_image_by_gid

        # for each visible layer in the XML tile file
        for layer in self.tmxdata.visible_layers:
            # if the layer is properly formatted to be a Tiled Tile Layer
            # we only care about the tile layers to draw the map
            # object and image layers are used for collisions and other stuff
            if isinstance(layer, pytmx.TiledTileLayer):
                # get the position and ID of each tile in that layer
                for x, y, gid in layer:
                    # get the actual tile from the ID
                    tile = ti(gid)

                    # if it's a tile, draw (blit) it on the surface
                    # location = (x * tile_width, y * tile_height)
                    # all layers are drawn in the order they are defined in the tile file => ground layer is at the bottom, top layer is on top
                    if tile:
                        surface.blit(tile,
                              (x * self.tmxdata.tilewidth,
                              y * self.tmxdata.tileheight)
                        )

    # create a surface to draw the map onto
    def make_map(self):
        temp_surface = pg.Surface((self.width, self.height))
        self.render(temp_surface)
        return temp_surface

    # create a list of all tiles
    # usefull to detect which tiles collide with any wall or obstacle
    # (used for pathfinding)
    def get_all_tiles(self):
        ti = self.tmxdata.get_tile_image_by_gid

        # take the first visible layer
        for layer in self.tmxdata.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer):
                for x, y, gid in layer:
                    # get the actual tile from the ID
                    tile = ti(gid)

                    # if it's a tile, add it to the list of all tiles
                    # location = (x * tile_width, y * tile_height)
                    # all layers are drawn in the order they are defined in the tile file => ground layer is at the bottom, top layer is on top
                    if tile:
                        self.all_tiles.add(
                            (x * self.tmxdata.tilewidth, y * self.tmxdata.tileheight))

        return self.all_tiles





# "Camera" keeps track of how big the whole map is
# whenever the player moves, calculates the offset
# by how much the player (or any reference sprite) has shifted (with self.update(player))
# use the offset to draw everything on the screen shifted by that amount
# (with self.apply() which is used in the main draw function)
# we don't change the coordinates of any sprite.
# We just drow them in a different spot then where they think they are
class Camera():
    def __init__(self, width, height):
        self.camera = pg.Rect(0, 0, width, height)
        self.width = width
        self.height = height

    # apply the camera offset to a rectangle
    # returns the rectangle offset by the position of the camera
    # (needed to display the map)
    def apply_rect(self, rect):
        return rect.move(self.camera.topleft)

    # apply the camera offset to a sprite
    # returns the sprite offset by the position of the camera
    def apply(self, entity):
        return entity.rect.move(self.camera.topleft)

    # update camera's position when the player moves
    def update(self, target):
        x = -target.rect.centerx + int(WIDTH / 2)
        y = -target.rect.centery + int(HEIGHT / 2)

        # limit scrolling to map size
        x = min(0, x) # left
        x = max(-(self.width - WIDTH), x) # right

        y = min(0, y) # top
        y = max(-(self.height - HEIGHT), y) # right

        self.camera = pg.Rect(x, y, self.width, self.height)
