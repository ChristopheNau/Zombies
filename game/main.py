# Tile Based Games
# reference: https://www.youtube.com/watch?v=3UxnelT9aCo&list=PLsk-HSGFjnaGQq7ybM8Lgkh5EMxUWPm2i&index=1


import pygame as pg
from games_utils import *
import random
import os
from settings import *
from sprites import *
import time

# HUD functions
def draw_player_health(surf, x, y, pct):
    if pct < 0:
        pct = 0
    BAR_LENGTH = 100
    BAR_HEIGHT = 20
    fill = pct * BAR_LENGTH
    outline_rect = pg.Rect(x, y, BAR_LENGTH, BAR_HEIGHT)
    fill_rect = pg.Rect(x,y, fill, BAR_HEIGHT)
    if pct > 0.6:
        color = GREEN
    elif pct > 0.3:
        color = YELLOW
    else:
        color = RED
    pg.draw.rect(surf, color, fill_rect)
    pg.draw.rect(surf, WHITE, outline_rect, 2)

class Game:
    # initialize game window, etc
    def __init__(self):
        # initialize pygame and create window
        # initialize pygame (always needed)
        pg.init()
        # initialize pygame (needed when using sounds in the pygame)
        pg.mixer.init()
        # game window
        self.screen = pg.display.set_mode((WIDTH,HEIGHT))
        # tile of the game window
        pg.display.set_caption(GAMETITLE)
        # used to handle game speed and to ensure the game runs at the FPS we decide
        self.clock = pg.time.Clock()
        # keyboard repeat rate to keep player moving
        # whilst a key is pressed
        pg.key.set_repeat(500, 100)

        self.load_data()

        # all tiles that can be considered in the pathfinding algorithm
        self.passable_tiles = {}

        # reason for game over. Can be:
        # - player => player killed by zombies
        # - hostage => no more hostages left
        self.game_over_reason = ""

        # nb of hostage saved
        self.hostage_saved = 0
        self.total_hostages = 0

        # nb Zombies total / killed
        self.zombies_killed = 0
        self.total_zombies = 0

        # keep track of zombies tiles in the map to randomly re-spawn zombies
        self.zombies_location = []
        self.zombies_respawn_timer = pg.time.get_ticks()

        # the player can spawn in various locations on the map
        # the probabily of creating the player for a "player" tile
        # increases
        self.player_created = False
        self.player_create_proba = 33
        self.player_can_join_rescue_zone = False

        # variable to keep track of how long the hostages have been safe for
        self.all_hostages_safe = False
        self.countdown_win = pg.time.get_ticks()

        self.running = True

    def load_data(self):
        # set up assets folders
        game_folder = os.path.dirname(__file__)
        self.img_folder = os.path.join(game_folder, "images")
        self.sound_folder = os.path.join(game_folder, "sounds")
        self.music_folder = os.path.join(game_folder, "music")
        self.map_folder = os.path.join(game_folder, "maps")

        # load sprites from Spritesheet
        self.spritesheet_characters = Spritesheet(os.path.join(self.img_folder, SPRITESHEET_CHARACTERS))
        self.spritesheet_tiles = Spritesheet(os.path.join(self.img_folder, SPRITESHEET_TILES))
        self.spritesheet_explosions = Spritesheet(os.path.join(self.img_folder, SPRITESHEET_EXPLOSIONS))

        # sound loading
        pg.mixer.music.load(os.path.join(self.music_folder, BG_MUSIC))
        # general sound effects (level start, pick up objects)
        self.effects_sounds = {}
        for type in EFFECTS_SOUNDS:
            self.effects_sounds[type] = pg.mixer.Sound(os.path.join(self.sound_folder, EFFECTS_SOUNDS[type]))
        # gun sounds
        self.weapon_sounds = {}
        self.weapon_sounds["gun"] =[]
        for snd in WEAPON_SOUNDS_GUN:
            self.weapon_sounds["gun"].append(pg.mixer.Sound(os.path.join(self.sound_folder, snd)))
        # zombie sounds
        self.zombie_moan_sounds = []
        for snd in ZOMBIE_MOAN_SOUNDS:
            s = pg.mixer.Sound(os.path.join(self.sound_folder, snd))
            # zombie sounds are loud. Reduce their volume
            s.set_volume(0.1)
            self.zombie_moan_sounds.append(s)
        # zombie hit sound
        self.zombie_hit_sounds = []
        for snd in ZOMBIE_HIT_SOUNDS:
            self.zombie_hit_sounds.append(pg.mixer.Sound(os.path.join(self.sound_folder, snd)))
        # player hit sound
        self.player_hit_sounds = []
        for snd in PLAYER_HIT_SOUNDS:
            self.player_hit_sounds.append(pg.mixer.Sound(os.path.join(self.sound_folder, snd)))
        # hostage saved sound
        self.hostage_rescued_sound = pg.mixer.Sound(os.path.join(self.sound_folder, HOSTAGE_RESCUED_SOUND))

        # font
        self.title_font = os.path.join(self.img_folder, TITLE_FONT_NAME)
        self.hud_font = os.path.join(self.img_folder, HUD_FONT_NAME)

        # image to dim the screen
        # simple surface, same size as the screen
        # filled with black, semi transparent
        self.dim_screen = pg.Surface(self.screen.get_size()).convert_alpha()
        self.dim_screen.fill((0, 0, 0, 150))

    # start a new game
    def new(self):
        # indicate that the player hasn't been created yet
        # this is necessary on game restart
        self.player_created = False
        # put all sprites in a group, so we can easily Update them and Draw (render) them
        # use LayeredUpdate() instead of Group() to easily be able to control
        # which sprites are on top of which
        # only thing needed is to have a "_layer" property for all sprites
        self.all_sprites = pg.sprite.LayeredUpdates()
        #self.all_sprites = pg.sprite.Group()
        # group for all the walls
        self.wall_sprites = pg.sprite.Group()
        # group for removable obstacles (doors)
        self.door_sprites = pg.sprite.Group()
        # group for rescue zone
        self.rescue_sprites = pg.sprite.Group()
        # group for all the mobs
        self.mob_sprites = pg.sprite.Group()
        # group for all bullets
        self.bullet_sprites = pg.sprite.Group()
        # group for all visual effects (explosions..)
        self.effect_sprites = pg.sprite.Group()
        # group for all items the player can pick up
        self.item_sprites = pg.sprite.Group()
        # group for all hostages the player needs to save
        self.hostage_sprites = pg.sprite.Group()
        # group for all tiles
        self.tile_sprites = pg.sprite.Group()

        # create and draw the map
        # old version: uses simple text files
        #self.map = Map(os.path.join(self.map_folder, "map3.txt"))
        # new version: uses a tiled file
        self.map = TiledMap(os.path.join(self.map_folder, "level1.tmx"))
        self.map_img = self.map.make_map()
        # get the map's rectangle to be able to locate the map on the screen for where to draw it
        self.map_rect = self.map_img.get_rect()

        # get list of all tiles
        self.all_tiles = self.map.get_all_tiles()

        # go through all the object layer in the map to create the walls and spawn the player
        # the player will be blocked by
        for tile_object in self.map.tmxdata.objects:
            object_center = vec(tile_object.x + tile_object.width / 2,
                              tile_object.y + tile_object.height / 2)
            # if the object is a player => spawn the player at the object's position
            # create the player randomly in one of the possible locations on the map
            if tile_object.name == "player":
                n = random.randint(0, 101)
                if n < self.player_create_proba and not self.player_created:
                    self.player = Player(self, object_center.x, object_center.y)
                    self.player_created = True
                else:
                    # player not created for this tile
                    # increase the probability to create it for the next "player" tile
                    self.player_create_proba += 34

            # all obstacles have the name "wall" in the tmx file
            if tile_object.name == "wall":
                Obstacle(self, tile_object.x, tile_object.y, tile_object.width, tile_object.height)
            # some obstacles can be removed from the scene
            if tile_object.name in ["door", "door2"]:
                RemovableObstacle(self, tile_object.name, tile_object.x, tile_object.y, tile_object.width, tile_object.height)
            # rescue zone
            if tile_object.name == "rescue_zone":
                RescueZone(self, tile_object.x,
                           tile_object.y, tile_object.width,
                           tile_object.height)
            # spawn the zombies
            if tile_object.name == "zombie" and random.randint(0, 101) > MOB_SPAWN_PROBABILITY:
                Mob(self, object_center.x, object_center.y)
                self.total_zombies += 1
                self.zombies_location.append(object_center)
            # spawn the items
            if tile_object.name == "health" and random.randint(0, 101) < ITEM_SPAWN_PROBABILITY["health"]:
                Item(self, object_center, "health")
            if tile_object.name == "gun" and random.randint(0, 101) < ITEM_SPAWN_PROBABILITY["gun"]:
                Item(self, object_center, "gun")
            if tile_object.name == "machinegun" and random.randint(
                    0, 101) < ITEM_SPAWN_PROBABILITY["machine_gun"]:
                Item(self, object_center, "machine")
            if tile_object.name == "bullets_gun" and random.randint(
                    0, 101) < ITEM_SPAWN_PROBABILITY["bullets_gun"]:
                Item(self, object_center, "bullets_gun")
            if tile_object.name == "bullets_machine"  and random.randint(0, 101) < ITEM_SPAWN_PROBABILITY["bullets_machine"]:
                Item(self, object_center, "bullets_machine")
            # spawn the hostages
            if tile_object.name == "hostage" and random.randint(0, 101) < HOSTAGE_SPAWN_PROBABILITY:
                self.total_hostages += 1
                Hostage(self, object_center.x, object_center.y)

        # create a sprite for each tile and check with ones collide with a wall
        for tile in self.all_tiles:
            # Tiles all have the same weight (TODO: get tile's weight from the TMX file)
            Tile(self, tile[0], tile[1], 0)
        # check collision between the tiles and the walls
        # and remove the tiles that collide
        # This gives us a list of "clean" tiles that can be used in the pathfinding algorithm
        pg.sprite.groupcollide(self.wall_sprites, self.tile_sprites, False,
                               True)

        for t in self.tile_sprites:
            current = (t.rect.x // TILESIZE, t.rect.y // TILESIZE)
            #self.passable_tiles[current] = True
            self.passable_tiles[current] = {
                "passable": True,
                "weight": t.weight
            }

        # camera to follow the player
        self.camera = Camera(self.map.width, self.map.height)

        # debug layer
        self.draw_debug = False

        # variable to pause the game
        self.paused = False

        # play the level start sound
        self.effects_sounds["level_start"].play()

        # keep track of time to know when it's time
        # to recalculate the path to player
        self.pathfinding_timer = pg.time.get_ticks()
        self.assign_random_goal_to_mob_timer = pg.time.get_ticks()

        # actually start the game
        self.run()

    # calculate path to player
    def calculate_path_to_player(self):
        for mob in self.mob_sprites:
            # if mob can "smell" the player, recalculate the shortest path to the player
            if mob.target_dist.length_squared() < MOB_SEARCH_RADIUS ** 2:
                #print(f"mob chaising player in tile {self.player.get_tile()}")
                mob.chasing_player = True
                #mob.path = dijkstra_search(self, mob.get_tile(), self.player.get_tile())
                mob.path = a_star_search(self, mob.get_tile(), self.player.get_tile())
                mob.path_to_player = follow_path(self.player.get_tile(),
                                                 mob.path)
                mob.path_to_player.reverse()

    # assign a random goal to the mobs that are far from the player
    def assign_random_goal_to_mob(self):
        for mob in self.mob_sprites:
            # if mob can "smell" the player, recalculate the shortest path to the player
            if mob.target_dist.length_squared() > MOB_SEARCH_RADIUS ** 2 and not mob.chasing_player:
                random_tile = vec(random.choice(list(self.passable_tiles.keys())))
                #print(f"mob moves to random tile: {random_tile}")
                mob.path = a_star_search(self, mob.get_tile(), random_tile)
                mob.path_to_player = follow_path(random_tile, mob.path)
                mob.path_to_player.reverse()

    # game loop
    def run(self):
        self.playing = True
        # start the background music
        pg.mixer.music.play(loops=-1)
        # as long as the game is playing
        while self.playing == True:
            # keep loop running at the right speed
            # eg. if the loop takes less than 1/FPS second, wait until 1/FPS second
            self.clock.tick(FPS)
            self.dt = self.clock.tick(FPS) / 1000
            # check for events, update the sprites and draw them
            self.events()

            # update is what moves everything
            # pause the music if game is paused and
            # only update if the game is NOT paused
            if not self.paused:
                self.update()
            self.draw()

    # Game loop - updates
    def update(self):
        # re-calculate path to player for each mob
        # every 2s
        now = pg.time.get_ticks()
        if now - self.pathfinding_timer > PATHFINDING_REFRESH_TIMER:
            self.pathfinding_timer = now
            self.calculate_path_to_player()
        # move mob to a random tile if they are far from the player
        if now - self.assign_random_goal_to_mob_timer > RANDOM_GOAL_REFRESH_TIMER:
            self.assign_random_goal_to_mob_timer = now
            self.assign_random_goal_to_mob()
        # respawn zombies every once in a while
        if now - self.zombies_respawn_timer > MOB_SPAWN_DELAY:
            self.zombies_respawn_timer = now
            mob_location = random.choice(self.zombies_location)
            Mob(self, mob_location.x, mob_location.y)
            self.total_zombies += 1

        # all sprites are in a group. The line below is all we need in the Update section
        self.all_sprites.update()
        self.camera.update(self.player)

        # check collision between player and items
        hits = pg.sprite.spritecollide(self.player, self.item_sprites, False)
        for hit in hits:
            if hit.type == "health" and self.player.health < PLAYER_HEALTH:
                hit.kill()
                self.effects_sounds["health_up"].play()
                self.player.add_health(HEALTH_PACK_AMOUNT)
            # equip with the gun or add bullets if player already owns the gun
            if hit.type == "gun":
                if "gun" not in self.player.weapons_owned:
                    self.player.weapons_owned.append("gun")
                    self.player.equip("gun")
                else:
                    self.player.bullets["gun"] += BULLET_PACK_AMOUNT_GUN
                self.effects_sounds["reload_gun"].play()
                hit.kill()
            # equip with the machinegun or add bullets if player already owns the machine gun
            if hit.type == "machine":
                if "machine" not in self.player.weapons_owned:
                    self.player.weapons_owned.append("machine")
                    self.player.equip("machine")
                else:
                    self.player.bullets["machine"] += BULLET_PACK_AMOUNT_MACHINE
                    self.effects_sounds["reload_gun"].play()
                hit.kill()
            # found bullets!
            if hit.type == "bullets_gun":
                self.effects_sounds["reload_gun"].play()
                self.player.bullets["gun"] += BULLET_PACK_AMOUNT_GUN
                hit.kill()
            if hit.type == "bullets_machine":
                self.effects_sounds["reload_gun"].play()
                self.player.bullets["machine"] += BULLET_PACK_AMOUNT_MACHINE
                hit.kill()

        # check collision between mob and player's hit_rect
        hits = pg.sprite.spritecollide(self.player, self.mob_sprites, False, collide_hit_rect)
        for hit in hits:
            # player hit sound
            if random.random() < 0.7:
                random.choice(self.player_hit_sounds).play()

            self.player.health -= MOB_DAMAGE
            # stop the mob when it hit the player
            hit.vel = vec(0, 0)
            # no more player's health => game over
            if self.player.health <= 0:
                self.game_over_reason = "player"
                self.playing = False
        # move the player away from the mob that hit it
        # otherwise, the mob keeps on hitting the player for each frame
        # and the player's health decreases all at once
        if hits:
            self.player.pos += vec(MOB_KNOCKBACK, 0).rotate(-hits[0].rot)

        # collision between bullet and mob
        # when collision => remove the bullet and decrease mob's health until they die
        hits = pg.sprite.groupcollide(self.mob_sprites, self.bullet_sprites, False, True)
        for mob in hits:
            #mob.health -= GUN_PROPERTIES[self.player.current_weapon]["BULLET_DAMAGE"]
            # we may have multiple bullets on screen, from different weapons
            # check which bullet(s) hit the mob
            # to decreased its health accordingly
            for bullet in hits[mob]:
                mob.health -= bullet.damage

            # stop the mob when it's hit by a bullet
            mob.vel = vec(0,0)
            # show some mob's blood
            impact_position = (random.randint(mob.rect.topleft[0], mob.rect.topright[0]),
                                  random.randint(mob.rect.bottomleft[1], mob.rect.bottomright[1]))
            BulletImpact(self, impact_position, "mob")
            # Mob hit sound
            random.choice(self.zombie_hit_sounds).play()

        # collision between bullet and removable objects (doors, etc)
        hits = pg.sprite.groupcollide(self.door_sprites, self.bullet_sprites, False, True)
        for hit in hits:
            hit.kill()

        # collision between bullet and hostage
        # when collision => remove the bullet and decrese the hostage's health
        # if a hostage dies => game over
        hits = pg.sprite.groupcollide(self.hostage_sprites, self.bullet_sprites, False, True)
        for hit in hits:
            hit.hit()

        # collision between hostage and mob
        # when collision => hostage turns into a mob
        hits = pg.sprite.groupcollide(self.hostage_sprites,
                                      self.mob_sprites, False, False)
        for hit in hits:
            Mob(self, hit.pos.x, hit.pos.y)
            self.total_zombies += 1
            hit.kill()
            self.game_over_reason = "hostage_bit"
            self.playing = False


        # collision between hostage and rescue zone
        # when collision => hostage is saved
        hits = pg.sprite.groupcollide(self.hostage_sprites,
                                       self.rescue_sprites, False, False)
        for hit in hits:
            #print("Hostage rescued")
            hit.kill()
            self.hostage_saved += 1
            self.hostage_rescued_sound.play()
            if self.total_hostages - self.hostage_saved == 0:
                self.all_hostages_safe = True
                # all hostage are safe
                # v0 => player wins
                #self.game_over_reason = "all_hostage_rescued"
                #self.playing = False
                # v1 => start countdown and make all the zombies move towards the landing zone
                # the player only wins after the countdow expired
                #print(f"Keep the hostages safe for {HOSTAGE_RESCUED_COUNTDOWN // 1000}s to win")
                self.countdown_win = pg.time.get_ticks()
                # open all doors that might be closed
                for door in self.door_sprites:
                    door.kill()
                # all zombies move towards the player's last position
                for mob in self.mob_sprites:
                    mob.speed *= 5
                    mob.chasing_player = True
                    mob.path = a_star_search(self, mob.get_tile(), self.player.get_tile())
                    mob.path_to_player = follow_path(self.player.get_tile(),
                                                 mob.path)
                    mob.path_to_player.reverse()

        # check if all hostage have been rescued long enough
        # if so the player is allowed to join the rescue zone himself and win
        if self.all_hostages_safe == True:
            now = pg.time.get_ticks()
            if now - self.countdown_win > HOSTAGE_RESCUED_COUNTDOWN:
                self.player_can_join_rescue_zone = True


        # collision between player and rescue zone
        # when collision and all hostages are safe and player is allowed to join rescus zone => win
        if self.player_can_join_rescue_zone:
            if now - self.countdown_win > HOSTAGE_RESCUED_COUNTDOWN * 2:
                hits = pg.sprite.spritecollide(self.player, self.rescue_sprites, False, False)
                if hits:
                    self.game_over_reason = "all_hostage_rescued"
                    self.playing = False

    # Game loop - events
    def events(self):
        for event in pg.event.get():
            # check for closing the window
            if event.type == pg.QUIT:
                # stop the game
                # otherwise clicking on the red cross will not close the window
                if self.playing:
                    self.quit()
            # check for key presses
            if event.type == pg.KEYDOWN:
                # ESC closes the game
                if event.key == pg.K_ESCAPE:
                    self.quit()
                # 'p' toggle pauses the game
                if event.key == pg.K_p:
                    self.paused = not self.paused
                    if self.paused:
                        pg.mixer.music.pause()
                    else:
                        pg.mixer.music.unpause()
                # 'r' reload a bullet
                if event.key == pg.K_r:
                    if self.player.current_weapon == "gun" or self.player.current_weapon == "machine":
                        self.player.reload_gun()
                # 'e' change gun
                if event.key == pg.K_e:
                    if self.player.current_weapon != "none":
                        current = self.player.weapons_owned.index(self.player.current_weapon)
                        next = (current + 1) % len(self.player.weapons_owned)
                        self.player.current_weapon = self.player.weapons_owned[next]
                # 'h' switches the debug layer
                if event.key == pg.K_h:
                    self.draw_debug = not self.draw_debug
                # 'w' prints the list of passable tiles
                if event.key == pg.K_w:
                    for k,v in self.passable_tiles.items():
                        print(k,v)
                # 't' prints if the tile under the mouse collides with a wall
                if event.key == pg.K_t:
                    print(f"Neighbors of {self.player.get_tile()} => {find_neighbors(self, self.player.get_tile())}")
                # 'z' prints the number of zombies left
                if event.key == pg.K_z:
                    chaising_player = 0
                    for zombie in self.mob_sprites:
                        if zombie.chasing_player:
                            chaising_player += 1
                    print(f"# of zombies left {self.total_zombies} - chasing: {chaising_player}")

    # draw game's grid
    def draw_grid(self):
        # vertical lines
        for x in range(0, WIDTH, TILESIZE):
            pg.draw.line(self.screen, LIGHTGREY, (x, 0), (x, HEIGHT))
        # vertical lines
        for y in range(0, HEIGHT, TILESIZE):
            pg.draw.line(self.screen, LIGHTGREY, (0, y),(WIDTH, y))

    # Game loop - draw
    def draw(self):
        # display FPS as game's title to check game's performance (whilst developping, for ddebugging)
        #pg.display.set_caption("{:.2f}".format(self.clock.get_fps()))

        # self.screen.fill(BGCOLOR)

        # draw the map
        # applying the camera offset to it
        self.screen.blit(self.map_img, self.camera.apply_rect(self.map_rect))

        # draw the grid to visualize it easily
        # self.draw_grid()

        # all sprites are in a group. The line below is all we need in the Draw section
        #self.all_sprites.draw(self.screen)
        for sprite in self.all_sprites:
            # draw the mob's health bar
            if isinstance(sprite, Mob):
                sprite.draw_health()
            # the line below would be equivalent to what "self.all_sprites.draw(self.screen)" does
            #self.screen.blit(sprite.image, self.rect)
            # draw the sprites taking into account the offset
            self.screen.blit(sprite.image, self.camera.apply(sprite))
            # draw the sprite's hit rectangle if in debug mode
            if self.draw_debug:
                pg.draw.rect(self.screen, RED, self.camera.apply_rect(sprite.hit_rect), 1)
                pg.draw.rect(self.screen, WHITE, self.camera.apply_rect(sprite.rect), 1)

        # draw debug layer for all the walls
        if self.draw_debug:
            for wall in self.wall_sprites:
                pg.draw.rect(self.screen, RED, self.camera.apply_rect(wall.rect), 1)
            for door in self.door_sprites:
                pg.draw.rect(self.screen, RED, self.camera.apply_rect(door.rect), 1)

        # draw a rectangle around the player to visualize it
        #pg.draw.rect(self.screen, WHITE, self.camera.apply(self.player), 2)
        #pg.draw.rect(self.screen, RED, self.player.hit_rect, 2)

        # draw player's health on top of the screen
        # and not right above the player as we do for mobs
        draw_player_health(self.screen, 10, 10, self.player.health / PLAYER_HEALTH)
        # bar for bullets left
        if self.player.current_weapon != "none":
            draw_player_health(self.screen, 10, 30, self.player.bullets_loaded[self.player.current_weapon] / GUN_PROPERTIES[self.player.current_weapon]["NB_BULLETS"])

        # display number of hostages left to save
        draw_text(self.screen, f"{len(self.hostage_sprites)} hostages", self.hud_font, 30, BLACK,WIDTH - 10, HEIGHT - 50, "ne")

        if self.paused:
            # dim the screen by adding a semi-transparent dark image
            self.screen.blit(self.dim_screen, (0,0))
            # display message when game is paused
            draw_text(self.screen, "Paused", self.title_font, 105, RED, WIDTH/2, HEIGHT/2, "center")

        # displaying things on screen is a super slow process => do it only at the very end
        # once everything is ready to be displayed
        # *after* drawing everything, flip the display
        pg.display.flip()

    # splash (entry) screen
    def show_start_screen(self):
        self.screen.fill(BGCOLOR)
        draw_text(self.screen, GAMETITLE, self.title_font, 48, WHITE, WIDTH / 2, HEIGHT / 4)
        draw_text(self.screen, "Rescue the hostages", self.title_font, 40, WHITE, WIDTH / 2, HEIGHT / 4 + 50)
        draw_text(self.screen, "Arrows to move", self.title_font, 22, WHITE, WIDTH / 2,
                  HEIGHT / 2 + 20)
        draw_text(self.screen, "Space to shot", self.title_font, 22, WHITE,
                  WIDTH / 2, HEIGHT / 2 + 40)
        draw_text(self.screen, "R to reload", self.title_font, 22, WHITE,
                  WIDTH / 2, HEIGHT / 2 + 60)
        draw_text(self.screen, "E to switch weapon", self.title_font, 22, WHITE,
                  WIDTH / 2, HEIGHT / 2 + 80)
        draw_text(self.screen, "Press a key to start", self.title_font, 22, WHITE, WIDTH / 2,
                  HEIGHT * 3 / 4)
        draw_text(self.screen, "Christophe - August 2021", self.title_font, 14, YELLOW, WIDTH / 2,
                       HEIGHT - 15)
        pg.display.flip()

        wait_for_key(self)

    # Game over screen
    def show_gameover_screen(self):
        # if the user closes the game window, don't display the game over screen (otherwise the game won't quit)
        if not self.running:
            return

        # stop the game's music
        pg.mixer.music.fadeout(500)
        # play the game over music
        #pg.mixer.music.load(os.path.join(self.sound_folder, GAME_OVER_MUSIC))
        #pg.mixer.music.play(loops=-1)

        # display dim screen (partially transparent black)
        self.screen.blit(self.dim_screen, (0,0))

        draw_text(self.screen, GAME_OVER_MESSAGES[self.game_over_reason][0],
                  self.title_font, 64, WHITE, WIDTH / 2, HEIGHT / 4, "center")
        draw_text(self.screen, GAME_OVER_MESSAGES[self.game_over_reason][1], self.title_font, 47, WHITE,
                  WIDTH / 2, HEIGHT / 4 + 60, "center")
        draw_text(self.screen, "Press RETURN to play again", self.title_font, 40, WHITE, WIDTH / 2, HEIGHT / 2 + 80, "center")

        # display all graphical elements
        pg.display.flip()

        # wait for user to press the 'return' key
        wait_for_key(self, "return")

        # stop the game over music
        #pg.mixer.music.stop()

    # Quit the game
    def quit(self):
        self.playing = False
        self.running = False

if __name__  == "__main__":
    g = Game()
    g.show_start_screen()

    while g.running:
        g.new()
        g.show_gameover_screen()

    # end of the game loop => quit game
    #print("thank you for playing that game")
    pg.quit()
