import pygame

class Button:
    def __init__(self, text, rect, font, callback, secondary_font=None):
        self.text = text
        self.rect = pygame.Rect(rect)
        self.font = font
        self.secondary_font = secondary_font or font
        self.callback = callback
        self.hovered = False
        self.info_lines = []

    def set_rect(self, rect):
        self.rect = pygame.Rect(rect)

    def set_info(self, *lines):
        self.info_lines = [line for line in lines if line]

    def draw(self, surface):
        bg = (20, 20, 20, 210) if self.hovered else (10, 10, 10, 180)
        border = (220, 220, 220) if self.hovered else (130, 130, 130)

        panel = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        radius = max(6, int(min(self.rect.width, self.rect.height) * 0.08))
        pygame.draw.rect(panel, bg, panel.get_rect(), border_radius=radius)
        pygame.draw.rect(panel, border, panel.get_rect(), width=2, border_radius=radius)
        surface.blit(panel, self.rect.topleft)

        # --- TITLE (always centered) ---
        text_surf = self.font.render(self.text, True, (255, 255, 255))
        text_x = self.rect.centerx - text_surf.get_width() // 2
        text_y = self.rect.centery - text_surf.get_height() // 2
        surface.blit(text_surf, (text_x, text_y))

        # --- INFO (always below title) ---
        if self.info_lines:
            gap = max(6, self.rect.height // 12)
            line_y = text_y + self.rect.height + gap // 4

            for line in self.info_lines:
                info_surf = self.secondary_font.render(line, True, (200, 200, 200))
                info_x = self.rect.centerx - info_surf.get_width() // 2
                surface.blit(info_surf, (info_x, line_y))
                line_y += info_surf.get_height() + gap // 2

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.callback()
                return True
        return False