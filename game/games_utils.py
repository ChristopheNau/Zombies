# spritesheet generator: https://spritegen.website-performance.org/
# Sound effects generated with https://sfxr.me
# Ascii banner generated with  https://www.ascii-art-generator.org/


import pygame as pg
import pytmx
from settings import *

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
        self.spritesheet = pg.image.load(filename).convert()
    
    # grab an image out of a larger spritesheet
    def get_image(self, x, y, width, height, resize_factor=1):
        image = pg.Surface((width, height))
        image.blit(self.spritesheet, (0, 0), (x, y, width, height))
        # resize the image
        # the (width, height) of new size must be integers 
        image = pg.transform.scale(image, (round(width / resize_factor), round(height / resize_factor)))
        return image
 
 
# basic version: uses a simple text file to build the map
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
                        surface.blit(tile, (x * self.tmxdata.tilewidth, 
                                y * self.tmxdata.tileheight))
    # create a surface to draw the map onto
    def make_map(self):
        temp_surface = pg.Surface((self.width, self.height))
        self.render(temp_surface)
        return temp_surface
    
        
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