from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import pygame


Color = Tuple[int, int, int]


@dataclass
class InventoryItem:
    item_id: str
    name: str
    quantity: int = 1
    icon: Optional[pygame.Surface] = None
    description: str = ""
    category: str = "Misc"
    meta: Dict = field(default_factory=dict)

    def add(self, amount: int = 1) -> None:
        self.quantity = max(0, self.quantity + amount)


class InventoryUI:
    def __init__(
        self,
        screen_width: int,
        screen_height: int,
        ui_scale: float = 1.0,
        font_path: Optional[str] = None,
    ):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.ui_scale = max(0.5, ui_scale)
        self.font_path = font_path
        self.open = False

        self.items: Dict[str, InventoryItem] = {}
        self.display_order: List[str] = []

        self.scroll_offset = 0
        self.scroll_speed = 1
        self.hovered_item_id: Optional[str] = None
        self._slot_rects: List[Tuple[pygame.Rect, str]] = []

        self.bg_color = (14, 12, 10)
        self.panel_color = (28, 24, 20)
        self.panel_border = (118, 102, 82)
        self.slot_color = (48, 42, 36)
        self.slot_hover_color = (70, 60, 50)
        self.slot_border = (120, 108, 92)
        self.text_color = (236, 228, 218)
        self.subtext_color = (180, 170, 156)
        self.accent_color = (196, 166, 104)
        self.tooltip_bg = (8, 8, 8)

        self._apply_scale_metrics()
        self._build_fonts()
        self._rebuild_layout()

    def _font(self, size: int, bold: bool = False) -> pygame.font.Font:
        if self.font_path:
            return pygame.font.Font(self.font_path, size)
        return pygame.font.SysFont("arial", size, bold=bold)

    def _scaled(self, value: int, minimum: Optional[int] = None) -> int:
        scaled = int(round(value * self.ui_scale))
        if minimum is not None:
            return max(minimum, scaled)
        return scaled

    def _apply_scale_metrics(self) -> None:
        self.scroll_speed = max(1, int(round(self.ui_scale)))
        self.slot_size = self._scaled(72, 44)
        self.slot_gap = self._scaled(12, 8)
        self.padding = self._scaled(24, 14)
        self.header_height = self._scaled(108, 72)
        self.corner_radius = self._scaled(14, 8)
        self.border_width = self._scaled(3, 2)
        self.scrollbar_gap = self._scaled(10, 6)
        self.scrollbar_width = self._scaled(10, 6)
        self.icon_inset = self._scaled(18, 10)
        self.qty_pad_x = self._scaled(12, 8)
        self.qty_pad_y = self._scaled(8, 6)
        self.tooltip_pad = self._scaled(12, 8)
        self.tooltip_offset = self._scaled(18, 12)
        self.first_row_offset = self._scaled(10, 6)

    def _build_fonts(self) -> None:
        pygame.font.init()
        self.title_font = self._font(self._scaled(28, 18), bold=True)
        self.body_font = self._font(self._scaled(20, 14))
        self.small_font = self._font(self._scaled(16, 12))
        self.qty_font = self._font(self._scaled(18, 13), bold=True)

    def set_ui_scale(self, ui_scale: float, font_path: Optional[str] = None) -> None:
        self.ui_scale = max(0.5, ui_scale)
        if font_path is not None:
            self.font_path = font_path
        self._apply_scale_metrics()
        self._build_fonts()
        self._rebuild_layout()

    def set_screen_size(self, width: int, height: int, ui_scale: Optional[float] = None) -> None:
        self.screen_width = width
        self.screen_height = height
        if ui_scale is not None:
            self.ui_scale = max(0.5, ui_scale)
            self._apply_scale_metrics()
            self._build_fonts()
        self._rebuild_layout()

    def _rebuild_layout(self) -> None:
        horizontal_margin = self._scaled(120, 60)
        vertical_margin = self._scaled(120, 60)
        panel_width = min(self._scaled(980, 560), max(self._scaled(640, 420), self.screen_width - horizontal_margin))
        panel_height = min(self._scaled(720, 380), max(self._scaled(420, 260), self.screen_height - vertical_margin))
        x = (self.screen_width - panel_width) // 2
        y = (self.screen_height - panel_height) // 2
        self.panel_rect = pygame.Rect(x, y, panel_width, panel_height)

        usable_width = panel_width - self.padding * 2 - self.scrollbar_width - self.scrollbar_gap
        self.columns = max(4, usable_width // (self.slot_size + self.slot_gap))

        grid_top = self.panel_rect.y + self.header_height + self.first_row_offset
        grid_height = panel_height - (grid_top - self.panel_rect.y) - self.padding
        self.grid_rect = pygame.Rect(
            self.panel_rect.x + self.padding,
            grid_top,
            usable_width,
            max(self.slot_size, grid_height),
        )

    def toggle(self) -> None:
        self.open = not self.open

    def close(self) -> None:
        self.open = False

    def clear(self) -> None:
        self.items.clear()
        self.display_order.clear()
        self.scroll_offset = 0
        self.hovered_item_id = None

    def total_item_types(self) -> int:
        return len(self.items)

    def total_item_count(self) -> int:
        return sum(item.quantity for item in self.items.values())

    def add_item(
        self,
        name: str,
        quantity: int = 1,
        item_id: Optional[str] = None,
        icon: Optional[pygame.Surface] = None,
        description: str = "",
        category: str = "Misc",
        meta: Optional[Dict] = None,
    ) -> InventoryItem:
        normalized_id = (item_id or name.strip().lower()).strip().lower()
        safe_quantity = max(0, int(quantity))

        if normalized_id in self.items:
            self.items[normalized_id].add(safe_quantity)
            if icon is not None:
                self.items[normalized_id].icon = icon
            if description:
                self.items[normalized_id].description = description
            if category:
                self.items[normalized_id].category = category
            if meta is not None:
                self.items[normalized_id].meta = meta
            return self.items[normalized_id]

        item = InventoryItem(
            item_id=normalized_id,
            name=name,
            quantity=safe_quantity,
            icon=icon,
            description=description,
            category=category,
            meta=meta or {},
        )
        self.items[normalized_id] = item
        self.display_order.append(normalized_id)
        return item

    def remove_item(self, item_id: str, quantity: int = 1) -> bool:
        normalized_id = item_id.strip().lower()
        if normalized_id not in self.items:
            return False

        item = self.items[normalized_id]
        item.add(-quantity)
        if item.quantity <= 0:
            del self.items[normalized_id]
            self.display_order = [iid for iid in self.display_order if iid != normalized_id]
        self._clamp_scroll()
        return True

    def get_item(self, item_id: str) -> Optional[InventoryItem]:
        return self.items.get(item_id.strip().lower())

    def sorted_items(self) -> List[InventoryItem]:
        return [self.items[iid] for iid in self.display_order if iid in self.items and self.items[iid].quantity > 0]

    def _visible_rows(self) -> int:
        return max(1, self.grid_rect.height // (self.slot_size + self.slot_gap))

    def _total_rows(self) -> int:
        count = len(self.sorted_items())
        if count == 0:
            return 0
        return (count + self.columns - 1) // self.columns

    def _max_scroll(self) -> int:
        return max(0, self._total_rows() - self._visible_rows())

    def _clamp_scroll(self) -> None:
        self.scroll_offset = max(0, min(self.scroll_offset, self._max_scroll()))

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.KEYDOWN:
            if self.open and event.key == pygame.K_ESCAPE:
                self.close()
                return True
            if self.open and event.key == pygame.K_UP:
                self.scroll_offset -= self.scroll_speed
                self._clamp_scroll()
                return True
            if self.open and event.key == pygame.K_DOWN:
                self.scroll_offset += self.scroll_speed
                self._clamp_scroll()
                return True
            if self.open and event.key == pygame.K_PAGEUP:
                self.scroll_offset -= max(1, self._visible_rows() - 1)
                self._clamp_scroll()
                return True
            if self.open and event.key == pygame.K_PAGEDOWN:
                self.scroll_offset += max(1, self._visible_rows() - 1)
                self._clamp_scroll()
                return True

        if not self.open:
            return False

        if event.type == pygame.MOUSEWHEEL:
            self.scroll_offset -= event.y
            self._clamp_scroll()
            return True

        if event.type == pygame.MOUSEMOTION:
            self.hovered_item_id = None
            for rect, item_id in self._slot_rects:
                if rect.collidepoint(event.pos):
                    self.hovered_item_id = item_id
                    break

        return self.panel_rect.collidepoint(getattr(event, "pos", (-1, -1)))

    def draw(self, surface: pygame.Surface) -> None:
        if not self.open:
            return

        self._rebuild_layout()
        self._slot_rects.clear()
        self.hovered_item_id = None

        shade = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 165))
        surface.blit(shade, (0, 0))

        panel = pygame.Surface(self.panel_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(panel, (*self.panel_color, 245), panel.get_rect(), border_radius=self.corner_radius)
        pygame.draw.rect(panel, self.panel_border, panel.get_rect(), width=self.border_width, border_radius=self.corner_radius)
        surface.blit(panel, self.panel_rect.topleft)

        self._draw_header(surface)
        self._draw_grid(surface)
        self._draw_tooltip(surface)

    def _draw_header(self, surface: pygame.Surface) -> None:
        title = self.title_font.render("Inventory", True, self.text_color)
        subtitle = self.small_font.render(
            f"Unlimited capacity   •   {self.total_item_types()} item types   •   {self.total_item_count()} total items",
            True,
            self.subtext_color,
        )
        hint = self.small_font.render(
            "E: open-close   •   Mouse wheel / arrows: scroll",
            True,
            self.accent_color,
        )

        x = self.panel_rect.x + self.padding
        y = self.panel_rect.y + self._scaled(18, 10)
        surface.blit(title, (x, y))
        surface.blit(subtitle, (x, y + self._scaled(34, 20)))
        surface.blit(hint, (x, y + self._scaled(56, 36)))

    def _draw_grid(self, surface: pygame.Surface) -> None:
        items = self.sorted_items()

        if not items:
            empty = self.body_font.render("Nothing picked up yet.", True, self.text_color)
            tip = self.small_font.render("Collected items will appear here automatically.", True, self.subtext_color)
            cx = self.grid_rect.centerx - empty.get_width() // 2
            cy = self.grid_rect.centery - empty.get_height()
            surface.blit(empty, (cx, cy))
            surface.blit(tip, (self.grid_rect.centerx - tip.get_width() // 2, cy + self._scaled(34, 18)))
            return

        start_index = self.scroll_offset * self.columns
        visible_count = self._visible_rows() * self.columns
        visible_items = items[start_index:start_index + visible_count]

        mouse_pos = pygame.mouse.get_pos()

        for index, item in enumerate(visible_items):
            row = index // self.columns
            col = index % self.columns
            slot_x = self.grid_rect.x + col * (self.slot_size + self.slot_gap)
            slot_y = self.grid_rect.y + row * (self.slot_size + self.slot_gap)
            slot_rect = pygame.Rect(slot_x, slot_y, self.slot_size, self.slot_size)
            self._slot_rects.append((slot_rect, item.item_id))

            hovered = slot_rect.collidepoint(mouse_pos)
            if hovered:
                self.hovered_item_id = item.item_id

            self._draw_slot(surface, slot_rect, item, hovered)

        self._draw_scrollbar(surface)

    def _draw_slot(self, surface: pygame.Surface, rect: pygame.Rect, item: InventoryItem, hovered: bool) -> None:
        fill = self.slot_hover_color if hovered else self.slot_color
        pygame.draw.rect(surface, fill, rect, border_radius=self._scaled(10, 6))
        pygame.draw.rect(surface, self.slot_border, rect, width=max(1, self._scaled(2, 1)), border_radius=self._scaled(10, 6))

        icon_rect = rect.inflate(-self.icon_inset, -self.icon_inset)
        if item.icon is not None:
            source = item.icon
            src_w, src_h = source.get_size()
            if src_w > 0 and src_h > 0:
                scale_ratio = min(icon_rect.width / src_w, icon_rect.height / src_h)
                target_w = max(1, int(round(src_w * scale_ratio)))
                target_h = max(1, int(round(src_h * scale_ratio)))
                # Use nearest-neighbor scaling to keep pixel art crisp.
                icon = pygame.transform.scale(source, (target_w, target_h))
                surface.blit(icon, icon.get_rect(center=rect.center))
        else:
            pygame.draw.rect(surface, (88, 76, 62), icon_rect, border_radius=self._scaled(8, 5))
            letter = self.body_font.render(item.name[:1].upper(), True, self.text_color)
            surface.blit(letter, letter.get_rect(center=rect.center))

        if item.quantity > 1:
            qty = self.qty_font.render(str(item.quantity), True, (255, 255, 255))
            qty_bg = qty.get_rect(bottomright=(rect.right - self._scaled(7, 4), rect.bottom - self._scaled(5, 3))).inflate(self.qty_pad_x, self.qty_pad_y)
            qty_surface = pygame.Surface(qty_bg.size, pygame.SRCALPHA)
            pygame.draw.rect(qty_surface, (0, 0, 0, 170), qty_surface.get_rect(), border_radius=self._scaled(8, 5))
            surface.blit(qty_surface, qty_bg.topleft)
            surface.blit(qty, qty.get_rect(center=qty_bg.center))

    def _draw_scrollbar(self, surface: pygame.Surface) -> None:
        total_rows = self._total_rows()
        visible_rows = self._visible_rows()
        if total_rows <= visible_rows:
            return

        track_rect = pygame.Rect(
            self.grid_rect.right + self.scrollbar_gap,
            self.grid_rect.y,
            self.scrollbar_width,
            self.grid_rect.height,
        )
        pygame.draw.rect(surface, (54, 48, 42), track_rect, border_radius=self._scaled(6, 4))

        thumb_height = max(self._scaled(36, 22), int(track_rect.height * (visible_rows / total_rows)))
        max_scroll = max(1, total_rows - visible_rows)
        travel = track_rect.height - thumb_height
        thumb_y = track_rect.y + int((self.scroll_offset / max_scroll) * travel)
        thumb_rect = pygame.Rect(track_rect.x, thumb_y, track_rect.width, thumb_height)
        pygame.draw.rect(surface, self.accent_color, thumb_rect, border_radius=self._scaled(6, 4))

    def _draw_tooltip(self, surface: pygame.Surface) -> None:
        if not self.hovered_item_id or self.hovered_item_id not in self.items:
            return

        item = self.items[self.hovered_item_id]
        if item.quantity <= 0:
            return

        name_surf = self.body_font.render(item.name, True, self.text_color)
        qty_surf = self.small_font.render(f"Quantity: {item.quantity}", True, self.accent_color)
        cat_surf = self.small_font.render(f"Category: {item.category}", True, self.subtext_color)
        desc_text = item.description or "Collected item"
        desc_surf = self.small_font.render(desc_text, True, self.subtext_color)

        width = max(name_surf.get_width(), qty_surf.get_width(), cat_surf.get_width(), desc_surf.get_width()) + self.tooltip_pad * 2
        height = (
            name_surf.get_height()
            + qty_surf.get_height()
            + cat_surf.get_height()
            + desc_surf.get_height()
            + self.tooltip_pad * 2
            + self._scaled(10, 6)
        )

        mouse_x, mouse_y = pygame.mouse.get_pos()
        x = min(mouse_x + self.tooltip_offset, self.screen_width - width - self._scaled(10, 6))
        y = min(mouse_y + self.tooltip_offset, self.screen_height - height - self._scaled(10, 6))
        tooltip_rect = pygame.Rect(x, y, width, height)

        tip_surface = pygame.Surface(tooltip_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(tip_surface, (*self.tooltip_bg, 235), tip_surface.get_rect(), border_radius=self._scaled(10, 6))
        pygame.draw.rect(tip_surface, self.panel_border, tip_surface.get_rect(), width=max(1, self._scaled(2, 1)), border_radius=self._scaled(10, 6))
        surface.blit(tip_surface, tooltip_rect.topleft)

        line_y = y + self.tooltip_pad
        surface.blit(name_surf, (x + self.tooltip_pad, line_y))
        line_y += name_surf.get_height() + self._scaled(4, 2)
        surface.blit(qty_surf, (x + self.tooltip_pad, line_y))
        line_y += qty_surf.get_height() + self._scaled(2, 2)
        surface.blit(cat_surf, (x + self.tooltip_pad, line_y))
        line_y += cat_surf.get_height() + self._scaled(4, 2)
        surface.blit(desc_surf, (x + self.tooltip_pad, line_y))
