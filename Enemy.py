import pygame
import random
from config import PLAYER_SIZE, TILE_SIZE

def generate_enemy_grid(wall_grid, enemy_count):
    enemy_grid = [[0 for _ in range(len(wall_grid[0]))] for _ in range(len(wall_grid))]
    empty_cells = [(row, col) for row in range(len(wall_grid)) for col in range(len(wall_grid[0])) if not wall_grid[row][col]]
    random.shuffle(empty_cells)
    for i in range(min(enemy_count, len(empty_cells))):
        row, col = empty_cells[i]
        enemy_grid[row][col] = 1
    return enemy_grid

class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, world_width, world_height):
        super().__init__()
        self.image = pygame.transform.scale(pygame.image.load('assets/textures/enemy/enemy.png').convert_alpha(), (PLAYER_SIZE, PLAYER_SIZE))
        self.rect = self.image.get_rect(topleft=(x, y))
        self.speed = 1.5
        self.direction = pygame.math.Vector2(0, 0)
        self.world_width = world_width
        self.world_height = world_height
        self.experience = random.randint(20, 70)  # Experience points awarded when defeated
        self.max_health = random.randint(10, 30)  # Health points for the enemy
        self.health = self.max_health
        self.attack = random.randint(1, 15)  # Attack power of the enemy
        self.defense = random.randint(0, 5)  # Defense power of the enemy

    def update(self, player_pos, wall_grid):
        # Move towards the player
        direction_vector = pygame.math.Vector2(player_pos) - pygame.math.Vector2(self.rect.center)
        if direction_vector.length() > 0:
            self.direction = direction_vector.normalize()
        else:
            self.direction = pygame.math.Vector2(0, 0)

        self.rect.x += self.direction.x * self.speed
        self._resolve_wall_collision('x', wall_grid)

        self.rect.y += self.direction.y * self.speed
        self._resolve_wall_collision('y', wall_grid)

        self._clamp_bounds()
    
    def _collision_rect(self):
        margin = 4  # Smaller margin for enemies
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
                            if self.direction.x > 0:
                                self.rect.right = wall_rect.left
                            elif self.direction.x < 0:
                                self.rect.left = wall_rect.right
                        elif direction == 'y':
                            if self.direction.y > 0:
                                self.rect.bottom = wall_rect.top
                            elif self.direction.y < 0:
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
    
    def hurt(self, damage):
        effective_damage = max(0, damage - self.defense)
        self.health -= effective_damage
        return effective_damage  # Return the actual damage dealt after defense is applied
    
    def draw(self, surface, camera):
        screen_rect = camera.apply(self.rect)
        surface.blit(self.image, screen_rect)
        self.draw_health_bar(surface, camera)

    def draw_health_bar(self, surface, camera):
        screen_rect = camera.apply(self.rect)
        bar_width = self.rect.width
        bar_height = 5
        health_ratio = self.health / self.max_health
        health_bar_width = int(bar_width * health_ratio)

        # Background bar (red)
        pygame.draw.rect(surface, (255, 0, 0), (screen_rect.x, screen_rect.y - bar_height - 2, bar_width, bar_height))
        # Foreground bar (green)
        pygame.draw.rect(surface, (0, 255, 0), (screen_rect.x, screen_rect.y - bar_height - 2, health_bar_width, bar_height))