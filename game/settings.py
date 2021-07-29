import pygame as pg
vec = pg.math.Vector2

GAMETITLE = "Tile Based Game"

# size of the game window
# must be evenly divisible by TILESIZE (we don't want partial squares)
WIDTH = 1024
HEIGHT = 768

# highscore file
HIGHSCORE_FILE = "highscore.txt"

# How often should the screen be refreshed
FPS = 60

# define useful colors
WHITE     = (255, 255, 255)
BLACK     = (  0,   0,   0)
RED       = (255,   0,   0)
GREEN     = (  0, 255,   0)
BLUE      = (  0,   0, 255)
YELLOW    = (255, 255,   0)
BLUEGREEN = (  0, 155, 155)
SKYBLUE   = (135, 206, 235)
LIGHTGREY = (100, 100, 100)
BROWN     = (106,  55,   5)

BGCOLOR   = BROWN

# Fonts
FONT_NAME = "ZOMBIE.TTF"

# Spritesheets
SPRITESHEET_CHARACTERS = "spritesheet_characters.png"
SPRITESHEET_TILES = "spritesheet_tiles.png"
SPRITESHEET_EXPLOSIONS = "spritesheet_explosions.png"

# size of each square on the grid
TILESIZE = 64
GRIDWIDTH = WIDTH / TILESIZE
GRIDHEIGHT = HEIGHT / TILESIZE

# Layer orders
# (the lower the number, the lower the layer in the stack)
WALL_LAYER = 1
PLAYER_LAYER = 2
MOB_LAYER = 2
HOSTAGE_LAYER = 2
BULLET_LAYER = 3
EFFECT_LAYER = 4
ITEM_LAYER = 1


# Sounds
BG_MUSIC = 'espionage.ogg'
PLAYER_HIT_SOUNDS = ['pain/8.wav', 'pain/9.wav', 'pain/10.wav', 'pain/11.wav']
ZOMBIE_MOAN_SOUNDS = ['brains2.wav', 'brains3.wav', 'zombie-roar-1.wav', 'zombie-roar-2.wav',
                      'zombie-roar-3.wav', 'zombie-roar-5.wav', 'zombie-roar-6.wav', 'zombie-roar-7.wav']
ZOMBIE_HIT_SOUNDS = ['splat-15.wav']
WEAPON_SOUNDS_GUN = ['sfx_weapon_singleshot2.wav']
EFFECTS_SOUNDS = {'level_start': 'level_start.wav',
                  'health_up': 'health_pack.wav',
                  'reload_gun': 'gun_reload.ogg',
                  'outofammo': 'outofammo.wav' 
                  }

# Player settings
PLAYER_LAYER = 2
PLAYER_SPEED = 1000
PLAYER_IMG = "manBlue_gun.png"
PLAYER_ROTATION_SPEED = 250 # in degre per second
# rectangle to be used for the collisions
# we can't use the player's rectangle as its size changes 
# when the player rotates
PLAYER_HIT_RECT = pg.Rect(0, 0, 35, 35)
# how far from the center of the sprite is the gun
BARREL_OFFSET = vec(30, 10)
PLAYER_HEALTH = 100

# Weapon settings
BULLET_IMG = "bullet.png"
GUN_PROPERTIES = {
    "gun": {
        # When the player fires a bullet, he moves back a bit
        "KICKBACK": 200, 
        # make shooting inaccurate
        "GUN_SPREAD": 5,
        # delay between bullet shots 
        "BULLET_RATE": 300, 
        "BULLET_SPEED": 1000,
        # bullet dissappears after 1s  
        "BULLET_LIFETIME": 1000, 
        # damage points to mob
        "BULLET_DAMAGE": 10,
        # initial and maximum nb of bullets that come with than gun
        "NB_BULLETS": 15,
        # how long it takes to reload the gun
        "RELOAD_TIME": 500
    },
    "machine": {
        "KICKBACK": 300, 
        "GUN_SPREAD": 15, 
        "BULLET_RATE": 100, 
        "BULLET_SPEED": 1500, 
        "BULLET_LIFETIME": 1000, 
        "BULLET_DAMAGE": 20,
        "NB_BULLETS": 50,
        "RELOAD_TIME": 3000
    },
}     
# how long the bullet impact should be displayed for
BULLETIMPACTDURATION = 50
# MUZZLE FLASH lifetime
FLASHDURATION = 50

# Mob settings
MOB_SPEEDS = [150, 120, 200, 100, 150, 150]
MOB_FRICTION = -1
MOB_HIT_RECT = pg.Rect(0, 0, 30, 30)
MOB_HEALTH = 100
MOB_DAMAGE = 10
MOB_KNOCKBACK = 20
MOB_AVOID_RADIUS = 50
# how far the mobs can see
MOB_DETECT_RADIUS = 1000

# Hostages
# how far in the hostages can see
HOSTAGE_DETECT_RADIUS = 500
HOSTAGE_SPEED = 100
HOSTAGE_FRICTION = -1
HOSTAGE_HIT_RECT = pg.Rect(0, 0, 30, 30)
HOSTAGE_AVOID_RADIUS = 75

# Explosion animation speed (delay between 2 frames in ms)
EXPLOSION_FRAMERATE = 75

# Items
# health points refill
HEALTH_PACK_AMOUNT = 20
# nb of bullets in the bullet packs
BULLET_PACK_AMOUNT_MACHINE = 25
# nb of bullets in the bullet packs
BULLET_PACK_AMOUNT_GUN = 10

# how many pixels up and down the items will jump (tweening)
BOB_RANGE = 15
# how fast the items jump up and down
BOB_SPEED = 0.4

