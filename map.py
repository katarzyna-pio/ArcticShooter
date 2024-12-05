import pygame
from pytmx import pytmx
from pytmx.util_pygame import load_pygame

SCREEN_WIDTH, SCREEN_HEIGHT = 910, 560
TILE_SIZE = 70


class Map:
    def __init__(self, tmx_file):
        self.display_surface = pygame.display.get_surface()
        self.enemy_spawn_points = []
        self.tmx_data = load_pygame(tmx_file)
        self.collision_tiles = pygame.sprite.Group()
        platforms_layer = self.tmx_data.get_layer_by_name("Platforms")
        max_x = max(tile[0] for tile in platforms_layer.tiles())
        self.map_width = (max_x + 1) * TILE_SIZE
        self.load_collision_tiles()
        self.load_enemy_spawn_points()

    def load_enemy_spawn_points(self):
        spawn_layer = self.tmx_data.get_layer_by_name("EnemySpawnPoints")
        if spawn_layer:
            for obj in spawn_layer:
                x, y = obj.x, obj.y
                self.enemy_spawn_points.append((x, y))

    def load_collision_tiles(self):
        platforms_layer = self.tmx_data.get_layer_by_name("Platforms")
        for x, y, image in platforms_layer.tiles():
            tile_rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
            tile = Tile(tile_rect)
            self.collision_tiles.add(tile)

    def draw_map(self, offset_x, debug=False):
        for layer in self.tmx_data.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer):
                for x, y, image in layer.tiles():
                    self.display_surface.blit(
                        image, (x * TILE_SIZE - offset_x, y * TILE_SIZE)
                    )


class Tile(pygame.sprite.Sprite):
    def __init__(self, rect):
        super().__init__()
        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE))
        self.rect = rect
