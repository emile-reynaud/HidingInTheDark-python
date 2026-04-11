"""Player sprite and movement logic."""

import pygame
from config import PLAYER_SIZE, PLAYER_COLOR, PLAYER_SPEED, TILE_SIZE


class Player(pygame.sprite.Sprite):
    """Player character sprite."""
    
    COLLISION_MARGIN = 4

    def __init__(self, x, y, world_width, world_height):
        super().__init__()
        # self.image = pygame.Surface((PLAYER_SIZE, PLAYER_SIZE))
        # self.image.fill(PLAYER_COLOR)
        self.image = pygame.transform.scale(pygame.image.load('assets/textures/player/player.png').convert_alpha(), (PLAYER_SIZE, PLAYER_SIZE))
        self.rect = self.image.get_rect(center=(x, y))
        self.vel_x = 0
        self.vel_y = 0
        self.world_width = world_width
        self.world_height = world_height
        self.coin_count = 0
    
    def handle_input(self, keys):
        """Handle player movement based on input."""
        self.vel_x = 0
        self.vel_y = 0
        
        # ZQSD controls (French AZERTY)
        if keys[pygame.K_z]:  # Up
            self.vel_y = -PLAYER_SPEED
        if keys[pygame.K_s]:  # Down
            self.vel_y = PLAYER_SPEED
        if keys[pygame.K_q]:  # Left
            self.vel_x = -PLAYER_SPEED
        if keys[pygame.K_d]:  # Right
            self.vel_x = PLAYER_SPEED
    
    def update(self, wall_grid):
        """Update player position in world space with wall collisions."""
        self.rect.x += self.vel_x
        self._resolve_wall_collision('x', wall_grid)

        self.rect.y += self.vel_y
        self._resolve_wall_collision('y', wall_grid)

        self._clamp_bounds()

    def _collision_rect(self):
        margin = self.COLLISION_MARGIN
        return pygame.Rect(
            self.rect.left + margin // 2,
            self.rect.top + margin // 2,
            self.rect.width - margin,
            self.rect.height - margin,
        )

    def _resolve_wall_collision(self, direction, wall_grid):
        collision_rect = self._collision_rect()
        left = max(0, collision_rect.left // TILE_SIZE - 1)
        right = min((self.world_width // TILE_SIZE) - 1, collision_rect.right // TILE_SIZE + 1)
        top = max(0, collision_rect.top // TILE_SIZE - 1)
        bottom = min((self.world_height // TILE_SIZE) - 1, collision_rect.bottom // TILE_SIZE + 1)

        for row in range(top, bottom + 1):
            for col in range(left, right + 1):
                if wall_grid[row][col]:
                    wall_rect = pygame.Rect(col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                    if collision_rect.colliderect(wall_rect):
                        if direction == 'x':
                            if self.vel_x > 0:
                                self.rect.right = wall_rect.left
                            elif self.vel_x < 0:
                                self.rect.left = wall_rect.right
                        elif direction == 'y':
                            if self.vel_y > 0:
                                self.rect.bottom = wall_rect.top
                            elif self.vel_y < 0:
                                self.rect.top = wall_rect.bottom
                        collision_rect = self._collision_rect()

    def _clamp_bounds(self):
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > self.world_width:
            self.rect.right = self.world_width
        if self.rect.top < 0:
            self.rect.top = 0
        if self.rect.bottom > self.world_height:
            self.rect.bottom = self.world_height

    def draw(self, surface, camera):
        """Draw player on surface using camera coordinates."""
        screen_rect = camera.apply(self.rect)
        surface.blit(self.image, screen_rect)
