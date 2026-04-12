from __future__ import annotations

from curses.panel import panel
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import pygame

from GameItem import GameItem
from Hotbar import Hotbar


Color = Tuple[int, int, int]


# @dataclass
# class InventoryItem:
#     item_id: str
#     name: str
#     quantity: int = 1
#     icon_path: Optional[str] = None
#     description: str = ""
#     category: str = "Misc"
#     rarity: str = "Common"
#     value: int = 0
#     stackable: bool = True

#     def add(self, amount: int = 1) -> None:
#         self.quantity = max(0, self.quantity + amount)


class InventoryUI:
    def __init__(self, screen_width: int, screen_height: int, hotbar:Hotbar, scale: float = 1.0, font_path: Optional[str] = None):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.scale = max(0.5, scale)
        self.font_path = font_path
        self.open = False

        self.items: Dict[str, GameItem] = {}
        self.display_order: List[str] = []
        self.image_cache: Dict[str, Optional[pygame.Surface]] = {}

        self.hotbar = hotbar

        self._apply_scale_metrics()

        self.bg_color = (14, 12, 10)
        self.panel_color = (28, 24, 20)
        self.panel_border = (118, 102, 82)
        self.slot_color = {
            "Common": (48, 42, 36), # base color
            "Uncommon": (42, 50, 40), # green
            "Rare": (40, 44, 54), # blue
            "Epic": (48, 40, 56), # purple
            "Legendary": (58, 48, 36) # gold
        }
        self.slot_hover_color = {
            "Common": (70, 60, 50), # base color
            "Uncommon": (58, 70, 54), # green
            "Rare": (54, 62, 76), # blue
            "Epic": (66, 54, 78), # purple
            "Legendary": (82, 68, 48) # gold
        }
        self.slot_border = {
            "Common": (120, 108, 92), # base color
            "Uncommon": (98, 126, 94), # green
            "Rare": (92, 112, 148), # blue
            "Epic": (128, 102, 156), # purple
            "Legendary": (168, 138, 82) # gold
        }
        self.text_color = (236, 228, 218)
        self.item_text_color = {
            "Common": (236, 228, 218), # base color
            "Uncommon": (228, 236, 224), # green
            "Rare": (228, 234, 242), # blue
            "Epic": (236, 228, 242), # purple
            "Legendary": (244, 236, 214) # gold
        }
        self.subtext_color = {
            "Common": (180, 170, 156), # base color
            "Uncommon": (166, 180, 160), # green
            "Rare": (160, 172, 188), # blue
            "Epic": (180, 166, 192), # purple
            "Legendary": (198, 182, 144) # gold
        }
        self.accent_color = (196, 166, 104)
        self.tooltip_bg = {
            "Common": (24, 21, 18), # base color
            "Uncommon": (20, 25, 19), # green
            "Rare": (19, 22, 29), # blue
            "Epic": (24, 20, 30), # purple
            "Legendary": (31, 25, 17) # gold
        }

        self.hovered_item_id: Optional[str] = None
        self.clicked_item_id: Optional[str] = None
        self._slot_rects: List[Tuple[pygame.Rect, str]] = []

        self._build_fonts()
        self._rebuild_layout()
    
    def _scaled(self, value: int, minimum: Optional[int] = None) -> int:
        scaled = int(round(value * self.scale))
        if minimum is not None:
            scaled = max(minimum, scaled)
        return scaled
    
    def _font(self, size: int, bold: bool = False) -> pygame.font.Font:
        if self.font_path:
            return pygame.font.Font(self.font_path, size)
        return pygame.font.SysFont("arial", size, bold=bold)

    def _build_fonts(self) -> None:
        pygame.font.init()
        self.title_font = self._font(self._scaled(28, 18), bold=True)
        self.body_font = self._font(self._scaled(20, 14))
        self.small_font = self._font(self._scaled(16, 12))
        self.min_font = self._font(self._scaled(14, 10))
        self.qty_font = self._font(self._scaled(18, 13), bold=True)

    def _apply_scale_metrics(self) -> None:
        self.scroll_speed = max(1, int(round(self.scale)))
        self.slot_size = self._scaled(72, 44)
        self.slot_gap = self._scaled(12, 8)
        self.padding = self._scaled(24, 14)
        self.header_height = self._scaled(108, 72)
        self.footer_height = 0
        self.corner_radius = self._scaled(14, 8)
        self.border_width = self._scaled(3, 2)
        self.icon_inset = self._scaled(18, 10)
        self.first_row_offset = self._scaled(10, 6)

    def _rebuild_layout(self) -> None:
        horizontal_margin = self._scaled(120, 60)
        vertical_margin = self._scaled(120, 60)

        panel_width = min(
            self._scaled(980, 560),
            max(self._scaled(640, 420), self.screen_width - horizontal_margin)
        )
        panel_height = min(
            self._scaled(720, 380),
            max(self._scaled(420, 260), self.screen_height - vertical_margin)
        )

        x = (self.screen_width - panel_width) // 2
        y = (self.screen_height - panel_height) // 2
        self.panel_rect = pygame.Rect(x, y, panel_width, panel_height)

        usable_width = panel_width - self.padding * 2
        self.columns = max(5, usable_width // (self.slot_size + self.slot_gap))
        self.grid_rect = pygame.Rect(
            self.panel_rect.x + self.padding,
            self.panel_rect.y + self.header_height,
            usable_width,
            panel_height - self.header_height - self.first_row_offset,
        )
    
    def set_ui_scale(self, ui_scale: float, font_path: str | None = None) -> None:
        self.ui_scale = max(0.5, ui_scale)
        if font_path is not None:
            self.font_path = font_path
        self._apply_scale_metrics()
        self._build_fonts()
        self._rebuild_layout()

    def set_screen_size(self, width: int, height: int, ui_scale: float | None = None) -> None:
        self.screen_width = width
        self.screen_height = height
        if ui_scale is not None:
            self.ui_scale = max(0.5, ui_scale)
            self._apply_scale_metrics()
            self._build_fonts()
        self._rebuild_layout()

    def toggle(self) -> None:
        self.open = not self.open

    def close(self) -> None:
        self.open = False

    def clear(self) -> None:
        self.items.clear()
        self.display_order.clear()
        self.scroll_offset = 0
        self.hovered_item_id = None
        self.clicked_item_id = None

    def total_item_types(self) -> int:
        return len(self.items)

    def total_item_count(self) -> int:
        return sum(item.quantity for item in self.items.values())

    def _normalize_item_dict(self, item: dict) -> dict:
        item_id = str(item.get("id")).strip().lower()
        base_id = item_id.split('#')[0] if '#' in item_id else item_id
        return {
            "item_id": item_id,
            "item_base_id": base_id,
            "name": str(item.get("name", base_id.title())),
            "quantity": max(1, int(item.get("quantity", 1))),
            "icon_path": item.get("icon_path"),
            "description": str(item.get("description", "")),
            "category": str(item.get("category", "Misc")),
            "rarity": str(item.get("rarity", "common")),
            "value": int(item.get("value", 0)),
            "stackable": bool(item.get("stackable", True)),
            "attack": int(item.get("attack", 0)),
            "defense": int(item.get("defense", 0)),
            "heal": int(item.get("heal", 0)),
            "equip_slot": item.get("equip_slot")
        }

    def _next_nonstackable_id(self, base_id: str) -> str:
        if base_id not in self.items:
            return base_id
        index = 1
        while f"{base_id}#{index}" in self.items:
            index += 1
        return f"{base_id}#{index}"

    def add_item(self, item: dict, quantity=1) -> GameItem:
        data = self._normalize_item_dict(item)
        base_id = data["item_id"]

        if data["stackable"]:
            if base_id in self.items:
                self.items[base_id].add(quantity)
                return self.items[base_id]
            final_id = base_id
        else:
            if "#" in base_id and base_id not in self.items:
                final_id = base_id
            else:
                final_id = self._next_nonstackable_id(base_id)

        entry = GameItem(
            item_id=final_id,
            item_base_id=base_id,
            name=data["name"],
            category=data["category"],
            description=data["description"],
            quantity=quantity,
            stackable=data["stackable"],
            icon_path=data["icon_path"],
            rarity=data["rarity"],
            value=data["value"],
            attack=data["attack"],
            defense=data["defense"],
            heal=data["heal"],
            equip_slot=data["equip_slot"]
        )
        self.items[final_id] = entry
        self.display_order.append(final_id)
        return entry

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

    def sorted_items(self) -> List[GameItem]:
        return [self.items[iid] for iid in self.display_order if iid in self.items and self.items[iid].quantity > 0]

    def serialize_items(self) -> List[dict]:
        return [
            {
                "item_id": item.item_id,
                "item_base_id": item.item_base_id,
                "name": item.name,
                "quantity": item.quantity,
                "icon_path": item.icon_path,
                "description": item.description,
                "category": item.category,
                "rarity": item.rarity,
                "value": item.value,
                "stackable": item.stackable,
                "attack": item.attack,
                "defense": item.defense,
                "heal": item.heal,
                "equip_slot": item.equip_slot
            }
            for item in self.sorted_items()
        ]

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
        
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.clicked_item_id = None
            for rect, item_id in self._slot_rects:
                if rect.collidepoint(event.pos):
                    self.clicked_item_id = item_id
                    break

        return self.panel_rect.collidepoint(getattr(event, "pos", (-1, -1)))

    def _get_icon(self, icon_path: Optional[str]) -> Optional[pygame.Surface]:
        if not icon_path:
            return None
        if icon_path in self.image_cache:
            return self.image_cache[icon_path]
        try:
            image = pygame.image.load(icon_path).convert_alpha()
        except Exception:
            image = None
        self.image_cache[icon_path] = image
        return image

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
            f"{self.total_item_types()} item types   •   {self.total_item_count()} total items",
            True,
            self.subtext_color["Common"],
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
            tip = self.small_font.render("Collected items will appear here automatically.", True, self.subtext_color["Common"])
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
            slot_rect = pygame.Rect(
                self.grid_rect.x + col * (self.slot_size + self.slot_gap),
                self.grid_rect.y + row * (self.slot_size + self.slot_gap),
                self.slot_size,
                self.slot_size,
            )
            self._slot_rects.append((slot_rect, item.item_id))
            hovered = slot_rect.collidepoint(mouse_pos)
            if hovered:
                self.hovered_item_id = item.item_id
            self._draw_slot(surface, slot_rect, item, hovered)

        self._draw_scrollbar(surface)

    def _draw_slot(self, surface: pygame.Surface, rect: pygame.Rect, item: GameItem, hovered: bool) -> None:
        fill = self.slot_hover_color[item.rarity] if hovered else self.slot_color[item.rarity]
        slot_radius = self._scaled(10, 6)
        slot_border = max(1, self._scaled(2, 1))
        pygame.draw.rect(surface, fill, rect, border_radius=slot_radius)
        pygame.draw.rect(surface, self.slot_border[item.rarity], rect, width=slot_border, border_radius=slot_radius)
        
        icon_rect = rect.inflate(-self.icon_inset, -self.icon_inset)
        icon = self._get_icon(item.icon_path)
        if icon is not None:
            src_w, src_h = icon.get_size()
            scale_ratio = min(icon_rect.width / src_w, icon_rect.height / src_h)
            target_w = max(1, int(round(src_w * scale_ratio)))
            target_h = max(1, int(round(src_h * scale_ratio)))
            scaled = pygame.transform.scale(icon, (target_w, target_h))
            surface.blit(scaled, scaled.get_rect(center=rect.center))
        else:
            fallback = self.body_font.render(item.name[:1].upper(), True, self.text_color)
            surface.blit(fallback, fallback.get_rect(center=rect.center))

        if item.quantity > 1:
            qty_text = self.qty_font.render(str(item.quantity), True, (255, 255, 255))
            qty_bg = qty_text.get_rect(bottomright=(rect.right - 8, rect.bottom - 6)).inflate(14, 8)
            pygame.draw.rect(surface, (15, 15, 15), qty_bg, border_radius=8)
            pygame.draw.rect(surface, self.slot_border["Common"], qty_bg, width=1, border_radius=8)
            surface.blit(qty_text, qty_text.get_rect(center=qty_bg.center))

    def _draw_scrollbar(self, surface: pygame.Surface) -> None:
        total_rows = self._total_rows()
        visible_rows = self._visible_rows()
        if total_rows <= visible_rows:
            return

        track_rect = pygame.Rect(self.grid_rect.right + 8, self.grid_rect.y, 8, self.grid_rect.height)
        pygame.draw.rect(surface, (34, 34, 34), track_rect, border_radius=8)

        handle_height = max(36, int(track_rect.height * (visible_rows / total_rows)))
        max_scroll = max(1, total_rows - visible_rows)
        handle_y = track_rect.y + int((track_rect.height - handle_height) * (self.scroll_offset / max_scroll))
        handle_rect = pygame.Rect(track_rect.x, handle_y, track_rect.width, handle_height)
        pygame.draw.rect(surface, self.accent_color, handle_rect, border_radius=8)

    def _draw_tooltip(self, surface: pygame.Surface) -> None:
        if not self.hovered_item_id or self.hovered_item_id not in self.items:
            return

        item = self.items[self.hovered_item_id]
        lines = [
            self.body_font.render(item.name, True, self.item_text_color[item.rarity]),
            self.small_font.render(f"Attack: ", True, self.subtext_color["Common"]) if item.attack > 0 else None,
            self.small_font.render(f"{item.attack}", True, self.item_text_color[item.rarity]) if item.attack > 0 else None,
            self.small_font.render(f"Defense: ", True, self.subtext_color["Common"]) if item.defense > 0 else None,
            self.small_font.render(f"{item.defense}", True, self.item_text_color[item.rarity]) if item.defense > 0 else None,
            self.small_font.render(f"Heal: ", True, self.subtext_color["Common"]) if item.heal > 0 else None,
            self.small_font.render(f"{item.heal}", True, self.item_text_color[item.rarity]) if item.heal > 0 else None,
            self.min_font.render(f"Value: ", True, self.subtext_color["Common"]),
            self.min_font.render(f"{item.value}", True, self.item_text_color[item.rarity]),
            self.min_font.render(f"Category: ", True, self.subtext_color["Common"]),
            self.min_font.render(f"{item.category}", True, self.item_text_color[item.rarity]),
            self.min_font.render(f"Rarity: ", True, self.subtext_color["Common"]),
            self.min_font.render(f"{item.rarity}", True, self.item_text_color[item.rarity])
        ]
        # if item.description:
        #     lines.append(self.small_font.render(item.description, True, self.subtext_color))

        # width = max(line.get_width() if type(line) == pygame.Surface else 0 for line in lines) + self._scaled(24, 12) 
        # height = sum(line.get_height() if type(line) == pygame.Surface else 0 for line in lines) + self._scaled(20, 10) + (len(lines) - 1) * 4
        width = 0
        height = lines[0].get_height()
        max_width = lines[0].get_width()
        for i in range(1, len(lines)-1, 2):
            if type(lines[i]) == pygame.Surface:
                width = 0
                width += lines[i].get_width() + lines[i+1].get_width()
                height += lines[i].get_height()
                if width > max_width:
                    max_width = width
            else:
                continue
        width = max_width + self._scaled(24, 12)
        height += self._scaled(20, 10) + (len(lines)//2 - 1) * 4
        mx, my = pygame.mouse.get_pos()
        tooltip_rect = pygame.Rect(mx + self._scaled(18, 9), my + self._scaled(18, 9), width, height)
        if tooltip_rect.right > self.screen_width - self._scaled(8, 4):
            tooltip_rect.right = self.screen_width - self._scaled(8, 4)
        if tooltip_rect.bottom > self.screen_height - self._scaled(8, 4):
            tooltip_rect.bottom = self.screen_height - self._scaled(8, 4)

        pygame.draw.rect(surface, (*self.tooltip_bg[item.rarity], 230), tooltip_rect, border_radius=10)
        pygame.draw.rect(surface, self.slot_border[item.rarity], tooltip_rect, width=1, border_radius=10)

        y = tooltip_rect.y + self._scaled(10, 5)
        surface.blit(lines[0], (tooltip_rect.x + self._scaled(12, 6), y))
        y += lines[0].get_height() + self._scaled(4, 2)
        for j in range(1, len(lines) - 1, 2):
            if type(lines[j]) == pygame.Surface:
                surface.blit(lines[j], (tooltip_rect.x + self._scaled(12, 6), y))
                surface.blit(lines[j+1], (tooltip_rect.x + lines[j].get_width() + self._scaled(12, 6), y))
                y += max(lines[j].get_height(), lines[j+1].get_height()) + self._scaled(4, 2)
            else:
                continue
