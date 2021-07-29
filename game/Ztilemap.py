import pygame as pg
import pytmx
from settings import *

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
        

# class to display tiled maps generated with Tiled
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