"""Camera system for following the player."""

import pygame


class Camera:
    """Camera that follows the player and renders world coordinates."""

    def __init__(self, world_width, world_height, viewport_width, viewport_height):
        self.world_width = world_width
        self.world_height = world_height
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.x = 0
        self.y = 0

    def set_viewport_size(self, width, height):
        self.viewport_width = width
        self.viewport_height = height

    def follow_player(self, player):
        """Center camera on player."""
        self.x = player.rect.centerx - self.viewport_width // 2
        self.y = player.rect.centery - self.viewport_height // 2

        self.x = max(0, min(self.x, self.world_width - self.viewport_width))
        self.y = max(0, min(self.y, self.world_height - self.viewport_height))

    def apply(self, rect):
        return rect.move(-self.x, -self.y)

    def get_sprite_screen_pos(self, sprite):
        screen_x = sprite.rect.centerx - self.x
        screen_y = sprite.rect.centery - self.y
        return (screen_x, screen_y)