import pygame as pg
from settings import *
import os
import random
import itertools
from games_utils import *
vec = pg.math.Vector2
import pytweening as tween

# check if a sprite collides with a wall
# put this method here as its used both by the mob and the player
def collide_with_walls(sprite, group, direction):
    # if moving horizontally
    if direction == 'x':
        # detect collision between the player and a wall
        # using our own collision function "collide_hit_rect"
        hits = pg.sprite.spritecollide(sprite, group, False, collide_hit_rect)
        # we hit one (or more) wall(s)
        if hits:
            #if isinstance(sprite, Player):
            #print("collision: ", sprite, group)
            # we can hit from the left side or from the right side
            #vx > 0 => we are moving to the right
            # we need to position the player to the left edge of the wall
            # problem: when the mob hits the player, we move the player back, which may push the player inside the wall because collide_with_walls checks collisions only when the player is moving
            #if sprite.vel.x > 0:
            # instead, check to see if the wall's center is > player's center
            if hits[0].rect.centerx > sprite.hit_rect.centerx:
                sprite.pos.x = hits[0].rect.left - sprite.hit_rect.width / 2
            #if sprite.vel.x < 0:
            if hits[0].rect.centerx < sprite.hit_rect.centerx:
                sprite.pos.x = hits[0].rect.right + sprite.hit_rect.width / 2
            # set horizontal speed to 0
            sprite.vel.x = 0
            # position the player to its new position
            sprite.hit_rect.centerx = sprite.pos.x

    # if moving vertically
    if direction == 'y':
        hits = pg.sprite.spritecollide(sprite, group, False, collide_hit_rect)
        # we hit one (or more) wall(s)
        if hits:
            #if sprite.vel.y > 0:
            if hits[0].rect.centery > sprite.hit_rect.centery:
                sprite.pos.y = hits[0].rect.top - sprite.hit_rect.height / 2
            #if sprite.vel.y < 0:
            if hits[0].rect.centery < sprite.hit_rect.centery:
                sprite.pos.y = hits[0].rect.bottom + sprite.hit_rect.height / 2
            # set vertical speed to 0
            sprite.vel.y = 0
            # position the player to its new position
            sprite.hit_rect.centery = sprite.pos.y


class Player(pg.sprite.Sprite):
    def __init__(self, game, x, y):
        # set the player's layer before (!) super.__init__()
        self._layer = PLAYER_LAYER
        self.groups = game.all_sprites
        pg.sprite.Sprite.__init__(self, self.groups)

        self.game = game

        # use vector instead of individual values for X and Y
        # to make things easier
        self.vel = vec(0, 0)
        self.pos = vec(x, y)

        # weapon the player carries (gun | machine)
        self.current_weapon = "none"
        # start with 0 bullets (different bullets for gun and machine gun)
        self.bullets = {"gun": 10, "machine": 0}
        # bullets in the gun
        self.bullets_loaded = {"gun": 0, "machine": 0}
        # list of the weapons that the player carries
        self.weapons_owned = []

        self.load_images()
        self.image_origin = self.player_images[self.current_weapon]
        self.image = self.image_origin
        self.rect = self.image.get_rect()
        # need to specifically set the rectangle's position to (x,y)
        # if not, the player will spawn at (0,0) and then move to its position in "update"
        # the first check made in "update" is for collisions.
        # if there is a wall at (0, 0), the player will collided with the wall, be shifted to the edge of the wall and be stuck behind it
        self.rect.center = (x, y)
        # create a 2nd rectangle only used to detect collisions
        self.hit_rect = PLAYER_HIT_RECT
        # set the collision rectangle's center at the image rectangle's center
        self.hit_rect.center = self.rect.center

        # rotation angle of the player
        # (initially pointing to the right)
        self.rot = 0

        self.last_shot = 0
        self.health = PLAYER_HEALTH

        self.reloading = 0
        self.last_reload = 0

    def load_images(self):
        self.player_images = {
          "none": self.game.spritesheet_characters.get_image(390, 132, 35, 43),
          "gun": self.game.spritesheet_characters.get_image(263, 132, 49, 43),
          "machine": self.game.spritesheet_characters.get_image(212, 176, 49, 43),
          "reload": self.game.spritesheet_characters.get_image(309, 0, 39, 43)
        }

        for j in self.player_images.keys():
            img = self.player_images[j]
            img = img.set_colorkey(BLACK)

    def add_health(self, amount):
        self.health += amount
        if self.health >= PLAYER_HEALTH:
            self.health = PLAYER_HEALTH

    def shoot(self):
        # no more bullet. Convert machinegun to gun
        #if self.weapon == "machine" and self.bullets == 0:
        #    self.weapon = "gun"
        #    self.bullets = GUN_PROPERTIES[self.weapon]["NB_BULLETS"]
        # auto reload
        #if self.weapon == "gun" and self.bullets == 0:
        #    self.reload_gun(GUN_PROPERTIES[self.weapon]["NB_BULLETS"])
        # only shoot if the player holds a gun, is not reloading and has bullets left
        if (self.current_weapon == "gun" or self.current_weapon == "machine") and self.bullets_loaded[self.current_weapon] == 0:
            self.game.effects_sounds["outofammo"].play()
        if (self.current_weapon == "gun" or self.current_weapon == "machine") and self.bullets_loaded[self.current_weapon] > 0 and self.reloading == 0:
            now = pg.time.get_ticks()
            if now - self.last_shot > GUN_PROPERTIES[self.current_weapon]["BULLET_RATE"]:
                self.last_shot = now
                # direction the player is facing
                dir = vec(1,0).rotate(-self.rot)
                # spawn a new bullet
                # need to offset the bullet's position to where the gun is,
                # instead of spawning it from the center of the player
                pos_bullet = self.pos + BARREL_OFFSET.rotate(-self.rot)
                Bullet(self.game, pos_bullet, dir, GUN_PROPERTIES[self.current_weapon]["BULLET_DAMAGE"])
                self.bullets_loaded[self.current_weapon] -= 1
                # the player moves a bit back when he fires a bullet
                self.vel = vec(-GUN_PROPERTIES[self.current_weapon]["KICKBACK"], 0).rotate(-self.rot)
                # play sound when gun fired (same sound for gun and machine gun)
                random.choice(self.game.weapon_sounds["gun"]).play()
                # muzzle flash when the bullet is fired
                MuzzleFlash(self.game, pos_bullet)

    def reload_gun(self):
        # gun already fully loaded or no bullets left for this weapon
        if self.bullets[self.current_weapon] == 0 or self.bullets_loaded[self.current_weapon] == GUN_PROPERTIES[self.current_weapon]["NB_BULLETS"]:
            return

        self.reloading = 1
        self.game.effects_sounds["reload_gun"].play()

        # if we have bullets in stock
        refill = GUN_PROPERTIES[self.current_weapon]["NB_BULLETS"] - self.bullets_loaded[self.current_weapon]
        if self.bullets[self.current_weapon] > refill:
            self.bullets_loaded[self.current_weapon] = GUN_PROPERTIES[self.current_weapon]["NB_BULLETS"]
            self.bullets[self.current_weapon] -= refill
        else:
            self.bullets_loaded[self.current_weapon] += self.bullets[self.current_weapon]
            self.bullets[self.current_weapon] = 0
        # reload animation
        self.image_origin = self.player_images["reload"]
        self.image = self.image_origin
        self.last_reload = pg.time.get_ticks()

    def get_keys(self):
        self.rot_speed = 0
        self.vel = vec(0, 0)
        keys = pg.key.get_pressed()
        # LEFT and RIGTH keys make the player rotate
        # and not move along the X axis
        if keys[pg.K_LEFT]:
            self.rot_speed = PLAYER_ROTATION_SPEED
        if keys[pg.K_RIGHT]:
            self.rot_speed = -PLAYER_ROTATION_SPEED
        # UP and DOWN keys make the player move
        # move in the direction we are facing
        # UP: move forward
        if keys[pg.K_UP]:
            self.vel = vec(PLAYER_SPEED, 0).rotate(-self.rot)
        # DOWN move backwards at half the speed we move forward
        if keys[pg.K_DOWN]:
            self.vel = vec(-PLAYER_SPEED / 2, 0).rotate(-self.rot)
        # fire a bullet
        if keys[pg.K_SPACE]:
            self.shoot()

        # if we move in diagonal, divide vx and vy by sqr(2) (Pythagore)
        # to maintain a constant speed
        #if self.vel.x != 0 and self.vel.y != 0:
        #    self.vel *= 0.7071

    def equip(self, weapon):
        self.current_weapon = weapon
        self.bullets_loaded[self.current_weapon] = GUN_PROPERTIES[self.current_weapon]["NB_BULLETS"]

    def update(self):
        #print(f"remaining bullets: gun:{self.bullets['gun']} - machine:{self.bullets['machine']}")
        self.get_keys()

        # check if reload is done
        if self.current_weapon != "none":
            if pg.time.get_ticks() - self.last_reload > GUN_PROPERTIES[self.current_weapon]["RELOAD_TIME"]:
                self.image_origin = self.player_images[self.current_weapon]
                self.image = self.image_origin
                self.reloading = 0

        self.rot = (self.rot + self.rot_speed * self.game.dt) % 360
        # rotate the image
        self.image = pg.transform.rotate(self.image_origin, self.rot).convert_alpha()
        # need the player to rotate around its center
        # => recalculate the player's rect after we have rotate the image
        # and set the new rectangle's position at the same position
        # the previous rectangle was at
        self.rect = self.image.get_rect()
        self.rect.center = self.pos

        # instead of around its corner (0,0)
        self.pos += self.vel * self.game.dt

        # check collision in X and Y directions separately
        # to be able to slide against the wall when moving in diagonale
        # we move the hit rectangle, not the image rectangle
        self.hit_rect.centerx = self.pos.x
        collide_with_walls(self, self.game.wall_sprites, 'x')
        collide_with_walls(self, self.game.door_sprites, 'x')
        self.hit_rect.centery = self.pos.y
        collide_with_walls(self, self.game.wall_sprites, 'y')
        collide_with_walls(self, self.game.door_sprites, 'x')
        # after a collision, make sure the image rectangle and hit rectangle have the same center
        self.rect.center = self.hit_rect.center

        # check for collision between player (sprite) and walls (true)
        # collideany is faster than pg.sprite.groupcollide
        # it returns true if there is a collision without information about was collided
        # if collision => undo the position change we did right above
        #if pg.sprite.spritecollideany(self, self.game.wall_sprites):
        #    self.x -= self.vx * self.game.dt
        #    self.y -= self.vy * self.game.dt
        #    self.rect.topleft = (self.x, self.y)

    # return the player's tile
    def get_tile(self):
        return self.pos // TILESIZE

# "normal" Walls
# have their own image
# not used any longer but keep it, just in case
class Wall(pg.sprite.Sprite):
    def __init__(self, game, x, y):
        self.groups = game.all_sprites, game.wall_sprites
        pg.sprite.Sprite.__init__(self, self.groups)

        self.game = game
        self.x = x
        self.y = y

        # load wall's graphics
        self.load_images()

        #self.image = pg.Surface((TILESIZE, TILESIZE))
        #self.image.fill(GREEN)
        self.image = self.wall_images[0]
        self.rect = self.image.get_rect()
        self.rect.x = self.x * TILESIZE
        self.rect.y = self.y * TILESIZE

    def load_images(self):
        self.wall_images = [
          self.game.spritesheet_tiles.get_image(1184, 222, 64, 64),
          self.game.spritesheet_tiles.get_image(1184, 148, 64, 64),
          self.game.spritesheet_tiles.get_image(1332, 222, 64, 64)
        ]

        for img in self.wall_images:
            img = img.set_colorkey(BLACK)

# walls (obstacles) defined in the map file
# here, obstacles don't have their own image as
# obstacles are transparent ojects in a layer above the map's design
# obstacles just need a rectangle so we can have collisions
# we don't even draw them (not adding them to "game.all_sprites)
class Obstacle(pg.sprite.Sprite):
    def __init__(self, game, x, y, w, h):
        self.groups = game.wall_sprites
        pg.sprite.Sprite.__init__(self, self.groups)

        self.game = game
        self.x = x
        self.y = y

        self.rect = pg.Rect(x, y, w, h)
        #print(f"Obstacle: {self.rect}")
        self.rect.x = self.x
        self.rect.y = self.y

# some objects can be removed by shooting a bullet at them
# used to open doors
class RemovableObstacle(pg.sprite.Sprite):
    def __init__(self, game, name, x, y, w, h):
        self.groups = game.all_sprites, game.door_sprites
        pg.sprite.Sprite.__init__(self, self.groups)

        self.game = game
        self.name = name
        self.x = x
        self.y = y

        self.load_images()
        self.image = self.removable_object_images[self.name]
        self.rect = self.image.get_rect()
        self.hit_rect = self.rect
        self.rect.x = self.x
        self.rect.y = self.y

    def load_images(self):
        self.removable_object_images = {
          "door": self.game.spritesheet_tiles.get_image(1554, 296, 64, 64),
          "door2": self.game.spritesheet_tiles.get_image(1554, 370, 64, 64)
        }

        for item in self.removable_object_images.keys():
            img = self.removable_object_images[item]
            img = img.set_colorkey(BLACK)

# rescue zone => not displayed as such but used to detect collisions with hostages
class RescueZone(pg.sprite.Sprite):
    def __init__(self, game, x, y, w, h):
        self.groups = game.rescue_sprites
        pg.sprite.Sprite.__init__(self, self.groups)

        self.game = game
        self.x = x
        self.y = y

        self.rect = pg.Rect(x, y, w, h)
        self.rect.x = self.x
        self.rect.y = self.y

# All tiles in the game are a "Tile"
# Use this to detect collision with the walls and maintain a
# list of tiles that can be considered in the pathfiding algorithm
class Tile(pg.sprite.Sprite):
    def __init__(self, game, x, y, weight):
        self._layer = PLAYER_LAYER

        self.groups = game.tile_sprites
        pg.sprite.Sprite.__init__(self, self.groups)

        self.game = game
        self.x = x
        self.y = y
        self.weight = weight

        self.rect = pg.Rect(x, y, TILESIZE, TILESIZE)
        self.rect.x = self.x
        self.rect.y = self.y

class Mob(pg.sprite.Sprite):
    def __init__(self, game, x, y):
        self._layer = MOB_LAYER
        self.groups = game.all_sprites, game.mob_sprites
        pg.sprite.Sprite.__init__(self, self.groups)

        self.game = game
        self.x = x
        self.y = y

        # load mob's graphics
        self.load_images()
        # use .copy() as all mobs use the same image
        # and we modify it when addding the health bar in drow_health()
        self.image_origin = self.mob_images[0]
        self.image = self.image_origin
        self.rect = self.image.get_rect()
        # need to specifically set the rectangle's position to (x,y)
        # if not, the mob will spawn at (0,0) and then move to its position in "update"
        # if there is a wall at (0, 0), the player's hit_rect will collide with the wall, be moved to the edge of the wall and be stuck behind it
        self.rect.center = (x, y)
        # create a 2nd rectangle only used to detect collisions
        # .copy() as we have more than 1 mob
        self.hit_rect = MOB_HIT_RECT.copy()
        # set the collision rectangle's center at the image rectangle's center
        self.hit_rect.center = self.rect.center
        self.pos = vec(x, y)
        self.rect.center = self.pos
        # the mob will rotate to face the player
        self.rot = 0
        # define velocity and acceleration vectors for the mobs
        # use acceleration for more realistic mouvements
        # (the mob must slow down before it changes direction)
        self.vel = vec(0, 0)
        self.acc = vec(0, 0)

        # mob's health decreases when hit by a bullet
        self.health = MOB_HEALTH

        self.speed = random.choice(MOB_SPEEDS)

        self.target = game.player
        self.path = {}
        self.path_to_player = []

    # load all graphical elements for the mobs
    def load_images(self):
        self.mob_images = [
          self.game.spritesheet_characters.get_image(460,  0, 33, 43),
          self.game.spritesheet_characters.get_image(424,  0, 35, 43)
        ]

        for img in self.mob_images:
            img = img.set_colorkey(BLACK)

    # get the mob's current tile
    def get_tile(self):
        return self.pos // TILESIZE

    def avoid_mobs(self):
        # check each active mob
        for mob in self.game.mob_sprites:
            # except the mob we are looking at
            if mob != self:
                # distance between the 2 mobs
                dist = self.pos - mob.pos
                # each mob too close to the current mob affects its accelaration
                if 0 < dist.length() < MOB_AVOID_RADIUS:
                    self.acc += dist.normalize()

    # make zombie move followig a predefined path
    def zombie_follow_path(self):
        if len(self.path_to_player) == 0:
            return
        else:
            target_tile = vec(self.path_to_player[-1])
            target_pos =  target_tile * TILESIZE + (TILESIZE /2, TILESIZE / 2)
            #print(target_tile, target_pos)
            self.zombie_move_towards_target(target_pos)

            if self.get_tile() == target_tile:
                #print(f"Reached {target_tile} - move to the next one")
                #pg.time.delay(500)
                self.path_to_player.pop()

    # move zombie directly towards the target
    # target_pos can be a tile's pos or the player's pos
    def zombie_move_towards_target(self, target_pos):
        self.target_pos = target_pos - self.pos
        self.rot = self.target_pos.angle_to(vec(1,0))
        #print(f"Current tile: {self.get_tile()} ({self.pos}) - target tile: {target_tile} ({target_pos}) - angle: {self.rot}")

        self.image = pg.transform.rotate(self.image_origin, self.rot).convert_alpha()
        self.rect = self.image.get_rect()
        self.rect.center = self.pos

        # accelerate the mob towards the target
        # acceleration is a unique vector
        self.acc = vec(1, 0).rotate(-self.rot)
        # if we only have the mobs face the player, after a while
        # all mobs "merge"
        # if other mobs are too close (within MOB_AVOID_RADIUS), of each other, each one will influence each other's acceleration vector
        self.avoid_mobs()
        try:
            self.acc.scale_to_length(self.speed)
        except ValueError:
            pass
            #print("Can't scale to length")
            #print(f"Acceleration : {self.acc} - Speed: {self.speed}")
        #print(f"Mob: pos: {self.pos} - Tile: {self.get_tile()} - direction: {self.acc}")
        # reduce acceleration by friction
        # the faster the mob goes, the less it accelerates
        # this is needed to limit its maximum speed
        self.acc += self.vel * MOB_FRICTION
        # set the player's velocity and position using the equations of motion
        self.vel += self.acc * self.game.dt
        self.pos += self.vel * self.game.dt + 0.5 * self.acc * self.game.dt ** 2

        self.hit_rect.centerx = self.pos.x
        collide_with_walls(self, self.game.wall_sprites, "x")
        collide_with_walls(self, self.game.door_sprites, "x")
        self.hit_rect.centery = self.pos.y
        collide_with_walls(self, self.game.wall_sprites, "y")
        collide_with_walls(self, self.game.door_sprites, "y")
        self.rect.center = self.hit_rect.center

    def update(self):
        # how far is the player from the mob?
        # target_dist is a vector; .length() returns its length
        # (.length = sqrt(target_dist.x ** 2 + target_dist.y ** 2))
        # calculating sqrt() is slow.
        # use .length.squared() instead and compare it to MOB_DECTECT
        self.target_dist = self.target.pos - self.pos

        # move zombie following the predefined path
        self.zombie_follow_path()

        # if the mob is closer to the player
        # => rush towards the player
        if self.target_dist.length_squared() < MOB_DETECT_RADIUS ** 2:
            # if zombie is close to the player, stop following
            # the predefined path and rush towards the player
            #print(f"Player is close!! New target: {self.game.player.pos} - current pos: {self.pos}")
            self.zombie_move_towards_target(self.game.player.pos)

            # occasionally play a zombie moaning sounds
            # this loops runs for every FPS and every mob
            # the random number must be very low otherwise the sound would occur too often
            if random.random() < 0.002:
                random.choice(self.game.zombie_moan_sounds).play()

        if self.health <= 0:
            self.kill()
            # explosion
            Explosion(self.game, self.rect.centerx, self.rect.centery)
            # if all zombies are killed => game won
            self.game.zombies_killed += 1
            #if self.game.total_zombies - self.game.zombies_killed == 0:
            #    self.game.game_over_reason = "zombies_killed"
            #    self.game.playing = False
                

    # draw health rectangle above the mob
    def draw_health(self):
        # define color to use depending on remainign health
        if self.health > MOB_HEALTH * 0.6:
            col = GREEN
        elif self.health > MOB_HEALTH * 0.3:
            col = YELLOW
        else:
            col = RED
            width = int(self.rect.width * self.health / MOB_HEALTH)
            # health bar's position is relative to the mob, not the screen
            self.health_bar = pg.Rect(0, -3, width, 7)
            # display the bar only if the mob has been hit at least once
            if self.health < MOB_HEALTH:
                pg.draw.rect(self.image, col, self.health_bar)

class Bullet(pg.sprite.Sprite):
    def __init__(self, game, pos, direction, damage):
        self._layer = BULLET_LAYER
        self.groups = game.all_sprites, game.bullet_sprites
        pg.sprite.Sprite.__init__(self, self.groups)

        self.game = game

        self.damage = damage

        # can't use pos directly as this would update
        # the player's position each time
        # we update the bullet's position
        #self.pos = pos
        # instead, create a new vector
        self.pos = vec(pos)

        # load wall's graphics
        self.load_images()
        self.image = self.bullet_images[0]
        self.rect = self.image.get_rect()
        self.rect.center = pos

        # hit_rect is used in the main.draw to draw the debug layer
        self.hit_rect = self.rect

        # random number to spread the bullets
        # use uniform as we don't want integers
        spread = random.uniform(-GUN_PROPERTIES[self.game.player.current_weapon]["GUN_SPREAD"],
                              GUN_PROPERTIES[self.game.player.current_weapon]["GUN_SPREAD"])
        # direction is a vector
        self.vel = direction.rotate(spread) * GUN_PROPERTIES[self.game.player.current_weapon]["BULLET_SPEED"]
        # keep track of when the bullet was created to
        # know when to delete it
        self.spawn_time = pg.time.get_ticks()

    def load_images(self):
        self.bullet_images = [
          pg.image.load(os.path.join(self.game.img_folder, BULLET_IMG)).convert()
        ]

        for img in self.bullet_images:
            img = img.set_colorkey(BLACK)

    def update(self):
        self.pos += self.vel * self.game.dt
        self.rect.center = self.pos

        # delete the bullet if it hits a wall and show the impact
        if pg.sprite.spritecollideany(self, self.game.wall_sprites):
            BulletImpact(self.game, self.pos, "wall")
            self.kill()

        # delete the bullet after Xs
        if pg.time.get_ticks() - self.spawn_time > GUN_PROPERTIES[self.game.player.current_weapon]["BULLET_LIFETIME"]:
            self.kill()

class Item(pg.sprite.Sprite):
    def __init__(self, game, pos, type):
        self._layer = ITEM_LAYER
        self.groups = game.all_sprites, game.item_sprites
        pg.sprite.Sprite.__init__(self, self.groups)

        self.game = game
        self.pos = pos
        self.type = type
        self.load_images()
        self.image = self.item_images[self.type]
        self.rect = self.image.get_rect()
        self.hit_rect = self.rect
        self.rect.center = self.pos

        # tweening function to use
        self.tween = tween.easeInOutSine
        self.step = 0
        self.dir = 1

    def load_images(self):
        self.item_images = {
          "health": pg.image.load(os.path.join(self.game.img_folder, "health_pack.png")).convert(),
          "gun": pg.image.load(os.path.join(self.game.img_folder, "gun.png")).convert(),
          "machine": pg.image.load(os.path.join(self.game.img_folder, "ak47.png")).convert(),
          "bullets_machine": pg.image.load(os.path.join(self.game.img_folder, "ammo.png")).convert(),
          "bullets_gun": pg.image.load(os.path.join(self.game.img_folder, "gun.png")).convert()
        }

        for item in self.item_images.keys():
            img = self.item_images[item]
            img = img.set_colorkey(BLACK)

    def update(self):
        # use easing/tweening to make the items more noticeable
        # ref: https://gamemechanicexplorer.com/#easing-1
        # not built-in easing function in Python. Use pytweening
        # how much do we need to move the item
        offset = BOB_RANGE * (self.tween(self.step / BOB_RANGE) - 0.5)
        self.rect.centery = self.pos.y + offset * self.dir
        self.step += BOB_SPEED
        if self.step > BOB_RANGE:
            self.step = 0
            self.dir *= -1

# Class for explosions (when mob are killed)
class Explosion(pg.sprite.Sprite):
    def __init__(self, game, x, y):
        self._layer = EFFECT_LAYER
        self.groups = game.all_sprites, game.effect_sprites
        pg.sprite.Sprite.__init__(self, self.groups)

        self.game = game
        self.x = x
        self.y = y

        # load explosion's graphics
        self.load_images()
        self.image = self.explosions_images[0]
        self.rect = self.image.get_rect()
        self.rect.center = (x,y)
        # hit rect not used but needed otherwise displaying the debug layer fails
        self.hit_rect = self.rect

        # variables for the animation
        self.frame = 0
        self.last_update = pg.time.get_ticks()
        self.frame_rate = EXPLOSION_FRAMERATE

    def load_images(self):
        self.explosions_images = [
          self.game.spritesheet_explosions.get_image(3398, 2113, 543, 547, 8),
          self.game.spritesheet_explosions.get_image(   5, 2670, 579, 575, 8),
          self.game.spritesheet_explosions.get_image( 594, 2670, 608, 561, 8),
          self.game.spritesheet_explosions.get_image(1212, 2670, 564, 588, 8),
          self.game.spritesheet_explosions.get_image(2454, 2670, 586, 629, 8),
          self.game.spritesheet_explosions.get_image(3050, 2670, 520, 554, 8),
          self.game.spritesheet_explosions.get_image(1786, 3234, 592, 566, 8)
        ]

        for img in self.explosions_images:
            img = img.set_colorkey(BLACK)

    def update(self):
        # explosion animation
        now = pg.time.get_ticks()
        if now - self.last_update > self.frame_rate:
            self.last_update = now
            self.frame += 1
            if self.frame == len(self.explosions_images):
                self.kill()
            else:
                center = self.rect.center
                self.image = self.explosions_images[self.frame]
                self.rect = self.image.get_rect()
                self.rect.center = center

# class for bullet impacts on the walls or mobs
class BulletImpact(pg.sprite.Sprite):
    # what = wall | mob
    def __init__(self, game, pos, what="wall"):
        self._layer = EFFECT_LAYER
        self.groups = game.all_sprites, game.effect_sprites
        pg.sprite.Sprite.__init__(self, self.groups)

        self.game = game
        self.spawn_time = pg.time.get_ticks()

        self.load_images()
        self.image = random.choice(self.bulletimpact_images[what])
        self.rect = self.image.get_rect()
        self.rect.center = pos
        # hit rect not used but needed otherwise displaying the debug layer fails
        self.hit_rect = self.rect

    def load_images(self):
        self.bulletimpact_images = {"wall": [
                self.game.spritesheet_explosions.get_image( 382, 1563, 381, 346, 17),
                self.game.spritesheet_explosions.get_image( 773, 1563, 345, 374, 17),
                self.game.spritesheet_explosions.get_image(4200, 3114, 383, 360, 17),
                self.game.spritesheet_explosions.get_image(2388, 3484, 353, 383, 17)
              ],
              "mob": [
                self.game.spritesheet_explosions.get_image(1786, 3234, 592, 566, 17),
                self.game.spritesheet_explosions.get_image(3050, 2670, 520, 554, 17),
                self.game.spritesheet_explosions.get_image( 594, 2670, 608, 561, 17),
                self.game.spritesheet_explosions.get_image(1212, 2670, 564, 588, 17)
              ]
        }

        for what in self.bulletimpact_images.keys():
            for img in self.bulletimpact_images[what]:
                img = img.set_colorkey(BLACK)

    def update(self):
        if pg.time.get_ticks() - self.spawn_time > BULLETIMPACTDURATION:
            self.kill()

# Class for muzzle flash (when bullets are fired)
class MuzzleFlash(pg.sprite.Sprite):
    def __init__(self, game, pos):
        self._layer = EFFECT_LAYER
        self.groups = game.all_sprites, game.effect_sprites
        pg.sprite.Sprite.__init__(self, self.groups)

        self.game = game
        self.spawn_time = pg.time.get_ticks()

        self.load_images()
        self.image = random.choice(self.muzzleflash_images)
        self.rect = self.image.get_rect()
        self.rect.center = pos
        # hit rect not used but needed otherwise displaying the debug layer fails
        self.hit_rect = self.rect

    def load_images(self):
        self.muzzleflash_images = [
          self.game.spritesheet_explosions.get_image(3899,  565, 550, 496, 17),
          self.game.spritesheet_explosions.get_image(4019, 1071, 463, 482, 17),
          self.game.spritesheet_explosions.get_image(4019, 1563, 563, 524, 17),
          self.game.spritesheet_explosions.get_image(4019, 2097, 463, 495, 17)
        ]

        for img in self.muzzleflash_images:
            img = img.set_colorkey(BLACK)

    def update(self):
        if pg.time.get_ticks() - self.spawn_time > FLASHDURATION:
            self.kill()

# Class for hostages
# Hostage follow the player, are saved when they reach the rescue zone
class Hostage(pg.sprite.Sprite):
    def __init__(self, game, x, y):
        self._layer = HOSTAGE_LAYER
        self.groups = game.all_sprites, game.hostage_sprites
        pg.sprite.Sprite.__init__(self, self.groups)

        self.game = game
        self.x = x
        self.y = y

        # load graphics
        self.load_images()
        # use .copy() as all mobs use the same image
        # and we modify it when addding the health bar in drow_health()
        self.image_origin = random.choice(self.hostage_images)
        self.image = self.image_origin
        self.rect = self.image.get_rect()
        # need to specifically set the rectangle's position to (x,y)
        # if not, the hostage will spawn at (0,0) and then move to its position in "update"
        # if there is a wall at (0, 0), the player's hit_rect will collide with the wall, be moved to the edge of the wall and be stuck behind it
        self.rect.center = (x, y)

        self.hit_rect = HOSTAGE_HIT_RECT.copy()
        # set the collision rectangle's center at the image rectangle's center
        self.hit_rect.center = self.rect.center

        self.pos = vec(x, y)
        self.rect.center = self.pos

        # speed and acceleration
        # define velocity and acceleration vectors for the mobs
        # use acceleration for more realistic mouvements
        # (the mob must slow down before it changes direction)
        self.vel = vec(0, 0)
        self.acc = vec(0, 0)
        self.speed = HOSTAGE_SPEED

        # target the hostages turn to and follow
        self.target = self.game.player

        self.path_to_player = []

        # health - hostages can be killed by bullets
        self.health = HOSTAGE_HEALTH
        # variable for animation when the player is hit
        self.damaged = False

    def load_images(self):
        self.hostage_images = [
          self.game.spritesheet_characters.get_image(390, 176, 35, 43),
          self.game.spritesheet_characters.get_image(386,  44, 36, 43),
          self.game.spritesheet_characters.get_image(353, 132, 36, 43),
          self.game.spritesheet_characters.get_image(460, 132, 33, 43)
        ]

        for img in self.hostage_images:
            img = img.set_colorkey(BLACK)

    # ensure that hostage don't get too close from each other
    # and don't "merge"
    def avoid_hostages(self):
        # check each active mob
        for hostage in self.game.hostage_sprites:
            # except the hostage we are looking at
            if hostage != self:
                # distance between the 2 mobs
                dist = self.pos - hostage.pos
                # each hostage too close to the current mob affects its accelaration
                if 0 < dist.length() < HOSTAGE_AVOID_RADIUS:
                    self.acc += dist.normalize()

    # if the hostage is hit by a bullet
    def hit(self):
        self.damaged = True
        self.damage_alpha = itertools.chain(HOSTAGE_DAMAGE_ALPHA * 2)

        # stop the hostage when it's hit by a bullet
        self.vel = vec(0,0)
        # play sound when hostage is hit (same sound as when player is hit)
        random.choice(self.game.player_hit_sounds).play()
        # decrease health
        self.health -= GUN_PROPERTIES[
            self.game.player.current_weapon]["BULLET_DAMAGE"]
        # health = 0 => game over
        if self.health <= 0:
          self.game.game_over_reason = "hostage_killed"
          self.game.playing = False

    # get the mob's current tile
    def get_tile(self):
        return self.pos // TILESIZE

    def update(self):
        if self.damaged:
            try:
                self.image.fill((255, 0, 0, next(self.damage_alpha)), special_flags=pg.BLEND_MULT)
            except StopIteration:
                self.damaged = False

        # rotate the hostage to face the player
        # (player.pos - hostage.pos) = vector from hostage to player
        # vec(1,0) => X horizon
        target_dist = self.target.pos - self.pos
        # if the distance to the target is not too big
        # target_dist is a vector; .length() returns its length
        # (.length = sqrt(target_dist.x ** 2 + target_dist.y ** 2))
        # calculating sqrt() is slow.
        # use .length.squared() instead and compare it to HOSTAGE_DECTECT_RADIUS squared
        if target_dist.length_squared() < HOSTAGE_DETECT_RADIUS ** 2:
            # the hostage is too close, it stops
            if target_dist.length_squared() < 1500:
                self.vel = vec(0, 0)
            else:
                self.rot = target_dist.angle_to(vec(1,0))
                self.image = pg.transform.rotate(self.image_origin, self.rot).convert_alpha()
                self.rect = self.image.get_rect()
                self.rect.center = self.pos
                # accelerate the hostage towards the player
                # acceleration is a unique vector
                self.acc = vec(1, 0).rotate(-self.rot)

                self.avoid_hostages()

                self.acc.scale_to_length(self.speed)
                # reduce acceleration by friction
                # the faster the mob goes, the less it accelerates
                # this is needed to limit its maximum speed
                self.acc += self.vel * HOSTAGE_FRICTION
                # set the player's velocity and position using the equations of motion
                self.vel += self.acc * self.game.dt
                self.pos += self.vel * self.game.dt + 0.5 * self.acc * self.game.dt ** 2
                self.hit_rect.centerx = self.pos.x
                collide_with_walls(self, self.game.wall_sprites, "x")
                collide_with_walls(self, self.game.door_sprites, "x")
                self.hit_rect.centery = self.pos.y
                collide_with_walls(self, self.game.wall_sprites, "y")
                collide_with_walls(self, self.game.door_sprites, "y")
                self.rect.center = self.hit_rect.center

        if self.health <= 0:
            self.kill()
            # game over
            #self.game.playing = False
