from sprite_object import *
from random import randint, random, choice

class NPC(AnimatedSprite):
    def __init__(self, game, path='Resources/sprites/npc/soldier/0.png', pos=(10.5, 5.5), scale=0.6, shift=0.38,
                 animate_time=180):
        super().__init__(game, path=path, pos=pos, scale=scale, shift=shift, animate_time=animate_time)
        self.attack_images = self.get_images(self.path + '/attack')
        self.death_images = self.get_images(self.path + '/death')
        self.idle_images = self.get_images(self.path + '/idle')
        self.pain_images = self.get_images(self.path + '/pain')
        self.walk_images = self.get_images(self.path + '/walk')

        self.attack_dist = randint(3, 6)
        self.speed = 0.02
        self.health = 100
        self.size = 10
        self.attack_damage = 10
        self.accuracy = 0.15
        self.alive = True
        self.pain = False
        self.ray_cast_value = False
        self.frame_counter = 0
        self.player_search_trigger = False

    def update(self):
        self.check_animation_time()
        self.get_sprite()
        self.run_logic()
        # self.draw_ray_cast()

    def animate_pain(self):
        self.animate(self.pain_images)
        # animate pain for one interval
        if self.animation_trigger:
            self.pain = False

    def animate_death(self):
        if not self.alive:
            if self.game.global_trigger and self.frame_counter < len(self.death_images)-1:
                self.death_images.rotate(-1)
                self.image = self.death_images[0]
                self.frame_counter += 1

    def run_logic(self):
        if self.alive:
            self.ray_cast_value = self.ray_cast_player_npc()
            self.check_hit_in_enemy()
            if self.pain:
                self.animate_pain()

            elif self.ray_cast_value:
                self.player_search_trigger = True

                if self.dist < self.attack_dist:
                    self.animate(self.attack_images)
                    self.attack()
                else:
                    self.animate(self.walk_images)
                    self.movement()

            elif self.player_search_trigger:
                self.animate(self.walk_images)
                self.movement()

            else:
                self.animate(self.idle_images)
        else:
            self.animate_death()

    def check_hit_in_enemy(self):
        if self.player.shot and self.ray_cast_value:
            if HALF_WIDTH - self.sprite_half_width < self.screen_x < HALF_WIDTH + self.sprite_half_width:
                # shot
                self.game.sound.npc_pain.play()
                self.game.sound.npc_pain.set_volume(1)
                self.player.shot = False
                self.pain = True
                self.health -= self.game.weapon.damage
                self.check_health()

    @property
    def map_pos(self):
        return int(self.x), int(self.y)



    def ray_cast_player_npc(self):
        if self.game.player.map_pos == self.map_pos:
            return True

        wall_dis_hor, wall_dis_vert = 0, 0
        player_dis_hor, player_dis_vert = 0, 0

        ox, oy = self.game.player.pos
        x_map, y_map = self.game.player.map_pos

        rayAngle = self.theta

        sin_a = math.sin(rayAngle)
        cos_a = math.cos(rayAngle)

        # horizontal
        y_hor, dy = (y_map + 1, 1) if sin_a > 0 else (y_map - 1e-6, -1)

        depth_hor = (y_hor - oy) / sin_a
        x_hor = ox + depth_hor * cos_a

        delta_depth = dy / sin_a
        dx = delta_depth * cos_a

        for i in range(MAX_DEPTH) :
            tile_hor = int(x_hor), int(y_hor)
            if tile_hor == self.map_pos:
                player_dis_hor = depth_hor
                break

            if tile_hor in self.game.map.world_map:
                wall_dis_hor = depth_hor
                break
            x_hor += dx
            y_hor += dy
            depth_hor += delta_depth


        # vertical
        x_vert, dx = (x_map + 1, 1) if cos_a > 0 else(x_map - 1e-6, -1)
        depth_vert = (x_vert - ox) / cos_a
        y_vert = oy + depth_vert * sin_a

        delta_depth = dx / cos_a
        dy = delta_depth * sin_a

        for i in range(MAX_DEPTH):
            tile_vert = int(x_vert), int(y_vert)
            if tile_vert == self.map_pos:
                player_dis_vert = depth_vert
                break
            if(tile_vert in self.game.map.world_map):
                wall_dis_vert = depth_vert
                break
            x_vert += dx
            y_vert += dy

            depth_vert += delta_depth

        player_dis = max(player_dis_vert, player_dis_hor)
        wall_dis = max(wall_dis_vert, wall_dis_hor)

        if 0 < player_dis < wall_dis or not wall_dis:
            return True
        return False

    def draw_ray_cast(self):
        pg.draw.circle(self.game.screen, 'red', (100 * self.x, 100 * self.y), 15)
        if self.ray_cast_player_npc():
            pg.draw.line(self.game.screen, 'orange', (100 * self.game.player.x, 100 * self.game.player.y),
                         (100 * self.x, 100 * self.y), 2)

    def check_health(self):
        if self.health < 1:
            self.alive = False
            self.game.sound.npc_death.play()
            self.game.sound.npc_death.set_volume(1)

    def attack(self):
        if self.animation_trigger:
            self.game.sound.npc_shot.play()
            self.game.sound.npc_shot.set_volume(1)
            if random() < self.accuracy:
                self.player.get_damage(self.attack_damage)


    def movement(self):
        next_pos = self.game.pathfinding.get_path(self.map_pos, self.game.player.map_pos)
        next_x, next_y = next_pos

        # pg.draw.rect(self.game.screen, "blue", (100 * next_x, 100 * next_y, 100, 100))

        if next_pos not in self.game.object_handler.npc_positions:
            angle = math.atan2(next_y + 0.5 - self.y, next_x + 0.5 - self.x)
            dx = math.cos(angle) * self.speed
            dy = math.sin(angle) * self.speed

            self.check_wall_collision(dx, dy)

    def check_wall(self, x, y):
        return (x, y) not in self.game.map.world_map

    def check_wall_collision(self, dx, dy):
        if self.check_wall(int(self.x + dx * self.size), int(self.y)):
            self.x += dx
        if self.check_wall(int(self.x), int(self.y + dy * self.size)):
            self.y += dy

class SoldierNPC(NPC):
    def __init__(self, game, path='resources/sprites/npc/soldier/0.png', pos=(10.5, 5.5),
                 scale=0.6, shift=0.38, animation_time=180):
        super().__init__(game, path, pos, scale, shift, animation_time)

class CacoDemonNPC(NPC):
    def __init__(self, game, path='resources/sprites/npc/caco_demon/0.png', pos=(10.5, 6.5),
                 scale=0.7, shift=0.27, animation_time=250):
        super().__init__(game, path, pos, scale, shift, animation_time)
        self.attack_dist = 1.0
        self.health = 150
        self.attack_damage = 25
        self.speed = 0.05
        self.accuracy = 0.35

class CyberDemonNPC(NPC):
    def __init__(self, game, path='resources/sprites/npc/cyber_demon/0.png', pos=(11.5, 6.0),
                 scale=1.0, shift=0.04, animation_time=210):
        super().__init__(game, path, pos, scale, shift, animation_time)
        self.attack_dist = 6
        self.health = 350
        self.attack_damage = 15
        self.speed = 0.055
        self.accuracy = 0.25