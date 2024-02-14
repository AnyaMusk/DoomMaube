import pygame as pg
from settings import *
import math

class RayCasting:
    def __init__(self, game):
        self.game = game
        self.ray_cast_result = []
        self.object_to_render = []
        self.textures = self.game.object_renderer.wall_texture

    def get_objects_to_render(self):
        self.object_to_render = []
        for ray, values in enumerate(self.ray_cast_result):
            depth, proj_height, texture, offset = values

            if proj_height < HEIGHT:
                wall_column = self.textures[texture].subsurface(
                    offset * (TEXTURE_SIZE - SCALE), 0, SCALE, TEXTURE_SIZE
                )
                wall_column = pg.transform.scale(wall_column, (SCALE, proj_height))
                wall_pos = (ray * SCALE, HALF_HEIGHT - proj_height // 2)
            else:
                texture_height = TEXTURE_SIZE * HEIGHT / proj_height
                wall_column = self.textures[texture].subsurface(
                    offset * (TEXTURE_SIZE - SCALE), HALF_TEXTURE_SIZE - texture_height // 2
                    , SCALE, texture_height
                )
                wall_column = pg.transform.scale(wall_column, (SCALE, HEIGHT))
                wall_pos = (ray * SCALE, 0)

            self.object_to_render.append((depth, wall_column, wall_pos))



    def ray_cast(self):
        self.ray_cast_result = []

        ox, oy = self.game.player.pos
        x_map, y_map = self.game.player.map_pos

        texture_vert, texture_hor = 1, 1

        rayAngle = self.game.player.angle - HALF_FOV + 0.0001
        for ray in range(NUM_RAYS):
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
                if (tile_hor in self.game.map.world_map):
                    texture_hor = self.game.map.world_map[tile_hor]
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
                if(tile_vert in self.game.map.world_map):
                    texture_vert = self.game.map.world_map[tile_vert]
                    break
                x_vert += dx
                y_vert += dy

                depth_vert += delta_depth

            #depth

            if depth_vert < depth_hor:
                depth, texture = depth_vert, texture_vert
                y_vert %= 1
                offset = y_vert if(cos_a > 0) else 1 - y_vert
            else:
                depth, texture = depth_hor, texture_hor
                x_hor %= 1
                offset = 1 - x_hor if(sin_a > 0) else x_hor

            # remove fisheye
            depth *= math.cos(self.game.player.angle - rayAngle)

            # projection

            proj_height = SCREEN_DIS / (depth + 0.001)

            # ray_cast result
            self.ray_cast_result.append((depth, proj_height, texture, offset))

            # draw walls
            #
            # color = [255 / (1 + depth ** 5 * 0.00002)] * 3
            # pg.draw.rect(self.game.screen, color,
            #              (SCALE * ray, HALF_HEIGHT - proj_height // 2, SCALE, proj_height))

            # debug

            # pg.draw.line(self.game.screen, 'yellow', (ox * 100, oy * 100),
            #              (100 * ox + 100 * depth * cos_a, 100 * oy + 100 * depth * sin_a), 2)

            rayAngle += DELTA_ANGLE


    def update(self):
        self.ray_cast()
        self.get_objects_to_render()
