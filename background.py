"""Background generation with infinite tileable pattern."""

import pygame
import random
from config import TILE_SIZE

WORLD_WIDTH = 5000
WORLD_HEIGHT = 5000

def create_background():
    surface = pygame.Surface((WORLD_WIDTH, WORLD_HEIGHT))

    # Load your textures
    floor1 = pygame.image.load("assets/textures/ground/ground0.png").convert()
    floor2 = pygame.image.load("assets/textures/ground/ground1.png").convert()

    # Scale to tile size
    floor1 = pygame.transform.scale(floor1, (TILE_SIZE, TILE_SIZE))
    floor2 = pygame.transform.scale(floor2, (TILE_SIZE, TILE_SIZE))

    textures = [floor1, floor2]

    for x in range(0, WORLD_WIDTH, TILE_SIZE):
        for y in range(0, WORLD_HEIGHT, TILE_SIZE):
            texture = random.choices(textures, weights=[0.6, 0.4])[0]  # 🔥 random instead of checker
            surface.blit(texture, (x, y))

    return surface, WORLD_WIDTH, WORLD_HEIGHT
