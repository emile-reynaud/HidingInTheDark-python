"""Lighting and shader system for dynamic light effects."""

import pygame


class LightingSystem:
    def __init__(self, screen_width, screen_height, light_radius=220, light_falloff=80):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.light_radius = light_radius
        self.light_falloff = light_falloff
        self.total_radius = light_radius + light_falloff

        self.light_mask = self._create_light_mask()
        self.dark_overlay = self._create_dark_overlay()

    def set_screen_size(self, width, height):
        self.screen_width = width
        self.screen_height = height
        self.dark_overlay = self._create_dark_overlay()

    def _create_dark_overlay(self):
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 245))
        return overlay

    def _create_light_mask(self):
        size = self.total_radius * 2
        surface = pygame.Surface((size, size), pygame.SRCALPHA)
        center = size // 2

        for radius in range(self.total_radius, -1, -1):
            if radius <= self.light_radius:
                alpha = 255
            else:
                alpha = int(255 * ((self.total_radius - radius) / self.light_falloff))
            alpha = max(0, min(255, alpha))
            pygame.draw.circle(surface, (0, 0, 0, alpha), (center, center), radius)

        return surface

    def apply_lighting(self, screen, screen_copy, player_pos):
        screen.blit(screen_copy, (0, 0))

        dark_surface = self.dark_overlay.copy()
        light_rect = self.light_mask.get_rect(center=player_pos)
        dark_surface.blit(self.light_mask, light_rect, special_flags=pygame.BLEND_RGBA_SUB)
        screen.blit(dark_surface, (0, 0))