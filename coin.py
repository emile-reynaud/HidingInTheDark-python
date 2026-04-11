"""Coin generation and drawing utilities."""

import random

import pygame
from config import TILE_SIZE, COIN_COLOR, COIN_SIZE

def generate_coin_grid(world_width, world_height, wall_grid):
    """Generate a grid of coins for the world, avoiding walls."""
    coin_grid = [[0 for _ in range(world_width // TILE_SIZE)] for _ in range(world_height // TILE_SIZE)]
    
    for y in range(len(coin_grid)):
        for x in range(len(coin_grid[0])):
            if not wall_grid[y][x]:  # Only place coins where there are no walls
                if random.random() < 0.1:  # 10% chance to place a coin
                    coin_grid[y][x] = 1
    
    return coin_grid

class Coin(pygame.sprite.Sprite):
    """Coin sprite for collectible items."""
    
    def __init__(self, col, row):
        super().__init__()
        # self.image = pygame.Surface((COIN_SIZE, COIN_SIZE), pygame.SRCALPHA).convert_alpha()
        # self.image.fill((0, 0, 0, 0))  # Fully transparent background
        # pygame.draw.circle(self.image, COIN_COLOR, (COIN_SIZE // 2, COIN_SIZE // 2), COIN_SIZE // 2)
        self.image = pygame.transform.scale(pygame.image.load('assets/textures/coin/coin.png').convert_alpha(), (COIN_SIZE, COIN_SIZE))
        self.rect = self.image.get_rect()
        self.col = col
        self.row = row
        self.rect.topleft = (col * TILE_SIZE + (TILE_SIZE - COIN_SIZE) // 2,
                             row * TILE_SIZE + (TILE_SIZE - COIN_SIZE) // 2)
    
    def draw(self, surface, camera, alpha=255):
        """Draw the coin on the given surface with camera offset."""
        coin_image = self.image.copy()
        coin_image.set_alpha(alpha)
        screen_x = self.rect.x - camera.x
        screen_y = self.rect.y - camera.y
        surface.blit(coin_image, (screen_x, screen_y))