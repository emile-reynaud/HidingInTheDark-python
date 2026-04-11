"""Player sprite and movement logic."""

import pygame
from config import *


class Player(pygame.sprite.Sprite):
    """Player character sprite."""
    
    COLLISION_MARGIN = 4

    def __init__(self, x, y, world_width, world_height):
        super().__init__()
        # self.image = pygame.Surface((PLAYER_SIZE, PLAYER_SIZE))
        # self.image.fill(PLAYER_COLOR)
        self.image = pygame.transform.scale(pygame.image.load('assets/textures/player/player.png').convert_alpha(), (PLAYER_SIZE, PLAYER_SIZE))
        self.rect = self.image.get_rect(center=(x, y))

        self.font = pygame.font.Font("assets/fonts/Kenney Mini.ttf", 12)

        self.vel_x = 0
        self.vel_y = 0
        self.world_width = world_width
        self.world_height = world_height
        self.coin_count = 0

        self.max_health = 100
        self.health = self.max_health
        self.invulnerable = False
        self.invulnerability_timer = 0
        self.invulnerability_duration = 100  # milliseconds
        self.attack = 10
        self.defense = 5
        self.speed = PLAYER_SPEED
        self.level = 1
        self.experience = 0
        self.experience_to_next_level = 100

        self.score = 0
    
    def handle_input(self, keys):
        """Handle player movement based on input."""
        self.vel_x = 0
        self.vel_y = 0
        
        # ZQSD controls (French AZERTY)
        if keys[pygame.K_z]:  # Up
            self.vel_y = -self.speed
        if keys[pygame.K_s]:  # Down
            self.vel_y = self.speed
        if keys[pygame.K_q]:  # Left
            self.vel_x = -self.speed
        if keys[pygame.K_d]:  # Right
            self.vel_x = self.speed
    
    def update(self, wall_grid):
        """Update player position in world space with wall collisions."""
        self._snap_to_corridor(wall_grid)

        self.rect.x += self.vel_x
        self._resolve_wall_collision('x', wall_grid)

        self.rect.y += self.vel_y
        self._resolve_wall_collision('y', wall_grid)

        self._clamp_bounds()

        if self.invulnerable:
            current_time = pygame.time.get_ticks()
            if current_time - self.invulnerability_timer >= self.invulnerability_duration:
                self.invulnerable = False

        if self.health < self.max_health:
            self.health += 0.05  # Regenerate health slowly
            if self.health > self.max_health:
                self.health = self.max_health

        self.score = self.coin_count * 10 + self.experience * 5 + self.level * 20

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

    def _snap_to_corridor(self, wall_grid):
        center_x = self.rect.centerx
        center_y = self.rect.centery

        col = center_x // TILE_SIZE
        row = center_y // TILE_SIZE

        rows = len(wall_grid)
        cols = len(wall_grid[0])

        if not (0 <= row < rows and 0 <= col < cols):
            return

        tile_center_x = col * TILE_SIZE + TILE_SIZE // 2
        tile_center_y = row * TILE_SIZE + TILE_SIZE // 2

        snap_strength = 2  # try 1 or 2

        # If moving mostly horizontally, help align vertically
        if self.vel_x != 0 and self.vel_y == 0:
            if abs(center_y - tile_center_y) <= TILE_SIZE // 3:
                if center_y < tile_center_y:
                    self.rect.centery += min(snap_strength, tile_center_y - center_y)
                elif center_y > tile_center_y:
                    self.rect.centery -= min(snap_strength, center_y - tile_center_y)

        # If moving mostly vertically, help align horizontally
        elif self.vel_y != 0 and self.vel_x == 0:
            if abs(center_x - tile_center_x) <= TILE_SIZE // 3:
                if center_x < tile_center_x:
                    self.rect.centerx += min(snap_strength, tile_center_x - center_x)
                elif center_x > tile_center_x:
                    self.rect.centerx -= min(snap_strength, center_x - tile_center_x)
    
    def draw(self, surface, camera):
        """Draw player on surface using camera coordinates."""
        screen_rect = camera.apply(self.rect)
        surface.blit(self.image, screen_rect)
        self.draw_health_bar(surface, camera)
        self.draw_experience_bar(surface, camera)
    
    def draw_health_bar(self, surface, camera):
        """Draw the player's health bar above the sprite."""
        screen_rect = camera.apply(self.rect)
        bar_width = self.rect.width
        bar_height = 5
        health_ratio = self.health / self.max_health
        health_bar_width = int(bar_width * health_ratio)

        # Background bar (red)
        pygame.draw.rect(surface, (255, 0, 0), (screen_rect.x, screen_rect.y - bar_height - 2, bar_width, bar_height))
        # Foreground bar (green)
        pygame.draw.rect(surface, (0, 255, 0), (screen_rect.x, screen_rect.y - bar_height - 2, health_bar_width, bar_height))

    def hurt(self, damage):
        """Apply damage to the player, considering defense and invulnerability."""
        if self.invulnerable:
            return
        
        effective_damage = max(0, damage - self.defense)
        self.health -= effective_damage
        if self.health < 0:
            self.health = 0
        
        self.invulnerable = True
        self.invulnerability_timer = pygame.time.get_ticks()
    
    def level_up(self):
        """Increase player level and improve stats."""
        self.level += 1
        self.experience = 0
        self.experience_to_next_level = int(self.experience_to_next_level * 1.5)
        self.max_health += 20
        self.health = self.max_health
        self.attack += 5
        self.defense += 2
        self.speed += 0.5

    def draw_experience_bar(self, surface, camera):
        """Draw the player's experience bar below the health bar."""
        screen_rect = camera.apply(self.rect)
        bar_width = self.rect.width
        bar_height = 5
        experience_ratio = self.experience / self.experience_to_next_level
        experience_bar_width = int(bar_width * experience_ratio)

        level_text = self.font.render(f"Level {self.level}", True, (90, 90, 90, 128))
        surface.blit(level_text, (screen_rect.x, screen_rect.y - level_text.get_height() - 10))

        # Background bar (gray)
        pygame.draw.rect(surface, (100, 100, 100, 128), (screen_rect.x, screen_rect.y + self.rect.height + 2, bar_width, bar_height))
        # Foreground bar (blue)
        pygame.draw.rect(surface, (0, 0, 255), (screen_rect.x, screen_rect.y + self.rect.height + 2, experience_bar_width, bar_height))
    