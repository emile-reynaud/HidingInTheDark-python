"""Enemy class with improved AI behaviors and pathfinding."""

import random
import pygame

from config import PLAYER_SIZE, TILE_SIZE
from pathfinding import astar


def generate_enemy_grid(wall_grid, enemy_count):
    enemy_grid = [[0 for _ in range(len(wall_grid[0]))] for _ in range(len(wall_grid))]
    empty_cells = [
        (row, col)
        for row in range(len(wall_grid))
        for col in range(len(wall_grid[0]))
        if not wall_grid[row][col]
    ]
    random.shuffle(empty_cells)

    for i in range(min(enemy_count, len(empty_cells))):
        row, col = empty_cells[i]
        enemy_grid[row][col] = 1

    return enemy_grid


class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, world_width, world_height):
        super().__init__()

        self.image = pygame.transform.scale(
            pygame.image.load("assets/textures/enemy/enemy.png").convert_alpha(),
            (PLAYER_SIZE, PLAYER_SIZE),
        )
        self.rect = self.image.get_rect(topleft=(x, y))

        self.speed = 1.5
        self.direction = pygame.math.Vector2(0, 0)

        self.world_width = world_width
        self.world_height = world_height

        self.experience = random.randint(20, 70)
        self.max_health = random.randint(10, 30)
        self.health = self.max_health
        self.attack = random.randint(1, 15)
        self.defense = random.randint(0, 5)

        # AI state
        self.state = "idle"   # "idle", "wander", "chase"

        # Distance thresholds
        self.close_range = 8 * TILE_SIZE
        self.mid_range = 16 * TILE_SIZE

        # Pathfinding
        self.path = []
        self.repath_timer = 0
        self.repath_delay = 15

        # Wandering
        self.wander_timer = 0
        self.wander_direction = pygame.math.Vector2(0, 0)

    def update(self, player_pos, wall_grid):
        distance_to_player = pygame.math.Vector2(player_pos).distance_to(self.rect.center)

        previous_state = self.state

        if distance_to_player <= self.close_range:
            self.state = "chase"
        elif distance_to_player <= self.mid_range:
            self.state = "wander"
        else:
            self.state = "idle"

        # Reset state-specific data when switching states
        if self.state != previous_state:
            if self.state != "chase":
                self.path = []
                self.repath_timer = 0
            if self.state != "wander":
                self.wander_timer = 0
                self.wander_direction = pygame.math.Vector2(0, 0)

        # Run behavior
        if self.state == "chase":
            self.chase_player(player_pos, wall_grid)
        elif self.state == "wander":
            self.wander(player_pos, wall_grid)
        else:
            self.direction = pygame.math.Vector2(0, 0)
            self._clamp_bounds()

    def _collision_rect(self):
        margin = 4
        return pygame.Rect(
            self.rect.left + margin // 2,
            self.rect.top + margin // 2,
            self.rect.width - margin,
            self.rect.height - margin,
        )

    def _resolve_wall_collision(self, axis, wall_grid):
        collision_rect = self._collision_rect()

        left = max(0, collision_rect.left // TILE_SIZE - 1)
        right = min((self.world_width // TILE_SIZE) - 1, collision_rect.right // TILE_SIZE + 1)
        top = max(0, collision_rect.top // TILE_SIZE - 1)
        bottom = min((self.world_height // TILE_SIZE) - 1, collision_rect.bottom // TILE_SIZE + 1)

        for row in range(top, bottom + 1):
            for col in range(left, right + 1):
                if wall_grid[row][col]:
                    wall_rect = pygame.Rect(
                        col * TILE_SIZE,
                        row * TILE_SIZE,
                        TILE_SIZE,
                        TILE_SIZE,
                    )

                    if collision_rect.colliderect(wall_rect):
                        if axis == "x":
                            if self.direction.x > 0:
                                self.rect.right = wall_rect.left
                            elif self.direction.x < 0:
                                self.rect.left = wall_rect.right
                        elif axis == "y":
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

        snap_strength = 2

        # moving mostly horizontally -> align vertically
        if abs(self.direction.x) > abs(self.direction.y):
            if abs(center_y - tile_center_y) <= TILE_SIZE // 3:
                if center_y < tile_center_y:
                    self.rect.centery += min(snap_strength, tile_center_y - center_y)
                elif center_y > tile_center_y:
                    self.rect.centery -= min(snap_strength, center_y - tile_center_y)

        # moving mostly vertically -> align horizontally
        elif abs(self.direction.y) > abs(self.direction.x):
            if abs(center_x - tile_center_x) <= TILE_SIZE // 3:
                if center_x < tile_center_x:
                    self.rect.centerx += min(snap_strength, tile_center_x - center_x)
                elif center_x > tile_center_x:
                    self.rect.centerx -= min(snap_strength, center_x - tile_center_x)

    def world_to_tile(self, pos):
        x, y = pos
        return (y // TILE_SIZE, x // TILE_SIZE)  # row, col

    def tile_to_world_center(self, tile_pos):
        row, col = tile_pos
        return pygame.math.Vector2(
            col * TILE_SIZE + TILE_SIZE // 2,
            row * TILE_SIZE + TILE_SIZE // 2,
        )

    def choose_wander_direction(self, player_pos=None):
        # 30% chance to bias wandering roughly toward the player
        if player_pos is not None and random.random() < 0.3:
            dx = player_pos[0] - self.rect.centerx
            dy = player_pos[1] - self.rect.centery

            if abs(dx) > abs(dy):
                self.wander_direction = pygame.math.Vector2(1 if dx > 0 else -1, 0)
            else:
                self.wander_direction = pygame.math.Vector2(0, 1 if dy > 0 else -1)
        else:
            self.wander_direction = random.choice([
                pygame.math.Vector2(1, 0),
                pygame.math.Vector2(-1, 0),
                pygame.math.Vector2(0, 1),
                pygame.math.Vector2(0, -1),
                pygame.math.Vector2(0, 0),
            ])

        self.wander_timer = random.randint(20, 70)

    def wander(self, player_pos, wall_grid):
        if self.wander_timer <= 0 or self.wander_direction.length_squared() == 0:
            self.choose_wander_direction(player_pos)

        self.wander_timer -= 1
        self.direction = self.wander_direction
        self._snap_to_corridor(wall_grid)

        old_x = self.rect.x
        self.rect.x += self.direction.x * self.speed
        self._resolve_wall_collision("x", wall_grid)

        if self.rect.x == old_x and self.direction.x != 0:
            self.wander_timer = 0

        old_y = self.rect.y
        self.rect.y += self.direction.y * self.speed
        self._resolve_wall_collision("y", wall_grid)

        if self.rect.y == old_y and self.direction.y != 0:
            self.wander_timer = 0

        self._clamp_bounds()

    def chase_player(self, player_pos, wall_grid):
        self.repath_timer -= 1

        start_tile = self.world_to_tile(self.rect.center)
        goal_tile = self.world_to_tile(player_pos)

        if self.repath_timer <= 0 or not self.path:
            self.path = astar(start_tile, goal_tile, wall_grid)
            self.repath_timer = self.repath_delay

        if len(self.path) > 1:
            next_tile = self.path[1]
            target = self.tile_to_world_center(next_tile)

            to_target = target - pygame.math.Vector2(self.rect.center)

            if to_target.length() <= 16:
                # close enough to consider this step reached
                self.path.pop(0)
                self.direction = pygame.math.Vector2(0, 0)
                self._clamp_bounds()
                return

            self.direction = to_target.normalize()
            self._snap_to_corridor(wall_grid)

            old_pos = pygame.math.Vector2(self.rect.center)

            # Move on x
            self.rect.x += self.direction.x * self.speed
            self._resolve_wall_collision("x", wall_grid)

            # Move on y
            self.rect.y += self.direction.y * self.speed
            self._resolve_wall_collision("y", wall_grid)

            new_pos = pygame.math.Vector2(self.rect.center)
            moved_distance = new_pos.distance_to(old_pos)

            # If we barely moved, we are probably stuck on a corner
            if moved_distance < 0.2:
                self.repath_timer = 0
                self.path = []

        else:
            self.direction = pygame.math.Vector2(0, 0)

        self._clamp_bounds()

    def hurt(self, damage):
        effective_damage = max(0, damage - self.defense)
        self.health -= effective_damage
        return effective_damage

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

        pygame.draw.rect(
            surface,
            (255, 0, 0),
            (screen_rect.x, screen_rect.y - bar_height - 2, bar_width, bar_height),
        )
        pygame.draw.rect(
            surface,
            (0, 255, 0),
            (screen_rect.x, screen_rect.y - bar_height - 2, health_bar_width, bar_height),
        )

    
