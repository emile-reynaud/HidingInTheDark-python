"""Main game entry point with menu, save slots, options, and animated preview."""

import json
import os
import random
import sys

import pygame
import pyautogui

from Enemy import Enemy, generate_enemy_grid
from background import create_background
from Camera import Camera
from Coin import Coin, generate_coin_grid
from config import FPS, PLAYER_SIZE, SCREEN_HEIGHT, SCREEN_WIDTH, TILE_SIZE
from Lighting import LightingSystem
from Player import Player
from walls import draw_walls, generate_wall_grid
from Button import Button
from Inventory import InventoryUI


SAVE_DIR = "saves"
SAVE_SLOTS = 3
DEFAULT_LIGHT_RADIUS = 280
DEFAULT_LIGHT_FALLOFF = 100
TITLE = "Hiding in the Dark"

MENU = "menu"
SAVE_SELECT = "save_select"
OPTIONS = "options"
GAME = "game"


class GameApp:
    def __init__(self):
        pygame.init()
        self.fullscreen = False
        self.monitor_width, self.monitor_height = pyautogui.size()

        if self.fullscreen:
            self.window_width, self.window_height = self.monitor_width, self.monitor_height
            self.screen = pygame.display.set_mode(
                (self.window_width, self.window_height),
                pygame.FULLSCREEN | pygame.HWSURFACE | pygame.DOUBLEBUF,
            )
        else:
            self.window_width, self.window_height = SCREEN_WIDTH, SCREEN_HEIGHT
            self.screen = pygame.display.set_mode(
                (self.window_width, self.window_height),
                pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.RESIZABLE,
            )

        self.player = None
        self.scale = 0
        
        self.update_ui_scale()
        
        pygame.display.set_caption(TITLE)

        self.clock = pygame.time.Clock()

        self.running = True
        self.state = MENU
        self.selected_slot = None
        self.message = ""
        self.preview_time = 0.0
        self.preview_camera = None

        self.music_enabled = True
        self.show_fps = True

        self.background = None
        self.world_width = 0
        self.world_height = 0
        self.wall_grid = None
        self.coin_grid = None
        self.enemy_grid = None
        self.tile_grid = None
        self.coins = pygame.sprite.Group()
        self.player = None
        self.camera = None
        self.lighting_system = None
        self.temp_surface = pygame.Surface((self.window_width, self.window_height)).convert()

        self.menu_buttons = []
        self.save_buttons = []
        self.options_buttons = []

        self.inventory = InventoryUI(
            self.window_width,
            self.window_height,
            ui_scale=self.scale,
            font_path="assets/fonts/Kenney Mini.ttf",
        )

        os.makedirs(SAVE_DIR, exist_ok=True)
        self.create_menu_buttons()
        self.create_save_buttons()
        self.create_options_buttons()
        self.build_preview_world(seed=9999)

    def get_inventory_icon(self, item_id, meta=None):
        normalized_id = (item_id or '').strip().lower()
        meta = meta or {}

        icon_path = meta.get("icon_path")
        if not icon_path and normalized_id == "coin":
            icon_path = "assets/textures/coin/coin.png"

        if not icon_path:
            return None

        try:
            return pygame.image.load(icon_path).convert_alpha()
        except Exception:
            return None

    def save_path(self, slot):
        return os.path.join(SAVE_DIR, f"slot_{slot}.json")

    def slot_exists(self, slot):
        return os.path.exists(self.save_path(slot))

    def read_slot(self, slot):
        path = self.save_path(slot)
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            return None

    def write_slot(self, slot):
        if self.player is None:
            return

        coin_positions = []
        for coin in self.coins:
            coin_positions.append([coin.col, coin.row])
        
        enemy_positions = []
        for enemy in self.enemies:
            enemy_positions.append([enemy.rect.centerx, enemy.rect.centery])

        inventory_items = []
        for item in self.inventory.sorted_items():
            inventory_items.append({
                "item_id": item.item_id,
                "name": item.name,
                "quantity": item.quantity,
                "description": item.description,
                "category": item.category,
                "meta": item.meta,
            })

        data = {
            "slot": slot,
            "seed": self.current_seed,
            "player_x": self.player.rect.centerx,
            "player_y": self.player.rect.centery,
            "coin_count": self.player.coin_count,
            "inventory_items": inventory_items,
            "remaining_coins": coin_positions,
            "enemy_positions": enemy_positions,
            "experience": self.player.experience,
            "level": self.player.level,
            "health": self.player.health,
            "max_health": self.player.max_health,
            "score": self.player.score,
            "speed": self.player.speed,
            "attack": self.player.attack,
            "defense": self.player.defense,
            "invulnerable": self.player.invulnerable,
            "invulnerability_timer": self.player.invulnerability_timer,
            "level_up_experience": self.player.experience_to_next_level,
            "tile_grid": self.tile_grid,
        }
        with open(self.save_path(slot), "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def delete_slot(self, slot):
        path = self.save_path(slot)
        if os.path.exists(path):
            os.remove(path)

    def create_menu_buttons(self):
        self.menu_buttons = [
            Button("Play", (0, 0, 320, 76), self.menu_font, self.open_save_select, self.small_font),
            Button("Options", (0, 0, 320, 76), self.menu_font, self.open_options, self.small_font),
            Button("Quit Game", (0, 0, 320, 76), self.menu_font, self.quit_game, self.small_font),
        ]
        self.layout_menu_buttons()

    def create_save_buttons(self):
        self.save_buttons = []
        for slot in range(1, SAVE_SLOTS + 1):
            self.save_buttons.append(
                Button(f"Save Slot {slot}", (0, 0, 360, 110), self.menu_font, lambda s=slot: self.start_slot(s), self.small_font)
            )
        self.layout_save_buttons()

    def create_options_buttons(self):
        self.options_buttons = [
            Button("Fullscreen", (0, 0, 360, 76), self.menu_font, self.toggle_fullscreen, self.small_font),
            Button("FPS Counter", (0, 0, 360, 76), self.menu_font, self.toggle_fps, self.small_font),
            Button("Back", (0, 0, 300, 60), self.menu_font, self.back_to_menu, self.small_font),
        ]
        self.layout_options_buttons()

    def layout_menu_buttons(self):
        btn_w = int(320 * self.scale)
        btn_h = int(76 * self.scale)
        spacing = int(95 * self.scale)

        start_x = self.window_width // 2 - btn_w // 2
        start_y = self.window_height // 2 - btn_h // 2

        for index, button in enumerate(self.menu_buttons):
            button.font = self.menu_font
            button.secondary_font = self.small_font
            button.set_rect((start_x, start_y + index * spacing, btn_w, btn_h))

    def layout_save_buttons(self):
        width = int(360 * self.scale)
        height = int(110 * self.scale)
        gap = int(40 * self.scale)

        total = SAVE_SLOTS * width + (SAVE_SLOTS - 1) * gap
        start_x = max(20, (self.window_width - total) // 2)
        y = self.window_height // 2 - height // 2 + int(30 * self.scale)

        for index, button in enumerate(self.save_buttons):
            button.font = self.menu_font
            button.secondary_font = self.small_font
            button.set_rect((start_x + index * (width + gap), y, width, height))

    def layout_options_buttons(self):
        width = int(360 * self.scale)
        height = int(76 * self.scale)
        spacing = int(150 * self.scale)

        x = self.window_width // 2 - width // 2
        start_y = self.window_height // 2 - height // 2

        for index, button in enumerate(self.options_buttons):
            button.font = self.menu_font
            button.secondary_font = self.small_font
            button.set_rect((x, start_y + index * spacing, width, height))

    def refresh_button_info(self):
        for index, button in enumerate(self.save_buttons, start=1):
            slot_data = self.read_slot(index)
            if slot_data:
                button.set_info(
                    f"Score: {slot_data.get('score', 0)}",
                    f"Seed: {slot_data.get('seed', 'unknown')}",
                )
            else:
                button.set_info("Empty slot", "Start a new run")

        self.options_buttons[0].set_info("On" if self.fullscreen else "Off")
        self.options_buttons[1].set_info("Visible" if self.show_fps else "Hidden")
        self.options_buttons[2].set_info("Return to main menu")

    def build_preview_world(self, seed):
        self.current_seed = seed
        random.seed(seed)
        self.background, self.world_width, self.world_height = create_background()
        self.background = self.background.convert()
        self.wall_grid = generate_wall_grid(self.world_width, self.world_height)
        draw_walls(self.background, self.wall_grid)
        self.coin_grid = generate_coin_grid(self.world_width, self.world_height, self.wall_grid)
        self.coins = self.build_coins_from_grid(self.coin_grid)
        self.enemy_grid = generate_enemy_grid(self.wall_grid, enemy_count=40)
        self.enemies = self.build_enemies_from_grid(self.enemy_grid)
        self.player = Player(self.world_width // 2, self.world_height // 2, self.world_width, self.world_height)
        self.tile_grid = self.create_tile_grid(self.world_width, self.world_height, TILE_SIZE, self.wall_grid, self.coin_grid, self.enemy_grid, (self.player.rect.centerx, self.player.rect.centery))
        self.camera = Camera(self.world_width, self.world_height, self.window_width, self.window_height)
        self.preview_camera = Camera(self.world_width, self.world_height, self.window_width, self.window_height)
        self.lighting_system = LightingSystem(self.window_width, self.window_height, DEFAULT_LIGHT_RADIUS, DEFAULT_LIGHT_FALLOFF)
        self.temp_surface = pygame.Surface((self.window_width, self.window_height)).convert()

    def build_world_for_slot(self, slot_data=None, slot=None):
        if slot_data is None:
            seed = random.randint(1000, 999999)
            self.build_preview_world(seed)
            self.selected_slot = slot
            self.inventory.clear()
            self.inventory.close()
            self.player.coin_count = 0
            self.message = f"Started new game in slot {slot}"
            return

        seed = slot_data.get("seed", random.randint(1000, 999999))
        self.build_preview_world(seed)
        self.selected_slot = slot
        self.player.rect.center = (
            slot_data.get("player_x", self.world_width // 2),
            slot_data.get("player_y", self.world_height // 2),
        )
        self.player.coin_count = slot_data.get("coin_count", 0)
        self.inventory.clear()
        self.inventory.close()

        remaining = slot_data.get("remaining_coins")
        if isinstance(remaining, list):
            self.coins = pygame.sprite.Group()
            for col, row in remaining:
                self.coins.add(Coin(col, row))
        
        enemy_positions = slot_data.get("enemy_positions")
        if isinstance(enemy_positions, list):
            self.enemies = pygame.sprite.Group()
            for x, y in enemy_positions:
                self.enemies.add(Enemy(x, y, self.world_width, self.world_height))
        
        self.player.experience = slot_data.get("experience", 0)
        self.player.level = slot_data.get("level", 1)
        self.player.health = slot_data.get("health", self.player.max_health)
        self.player.max_health = slot_data.get("max_health", self.player.max_health)
        self.player.speed = slot_data.get("speed", self.player.speed)
        self.player.attack = slot_data.get("attack", self.player.attack)
        self.player.defense = slot_data.get("defense", self.player.defense)
        self.player.invulnerable = slot_data.get("invulnerable", False)
        self.player.invulnerability_timer = slot_data.get("invulnerability_timer", 0)
        self.player.experience_to_next_level = slot_data.get("level_up_experience", self.player.experience_to_next_level)

        inventory_items = slot_data.get("inventory_items", [])
        if isinstance(inventory_items, list):
            for item_data in inventory_items:
                quantity = int(item_data.get("quantity", 0))
                if quantity <= 0:
                    continue
                item_id = item_data.get("item_id")
                item_meta = item_data.get("meta", {})
                self.inventory.add_item(
                    item_data.get("name", "Item"),
                    quantity=quantity,
                    item_id=item_id,
                    icon=self.get_inventory_icon(item_id, item_meta),
                    description=item_data.get("description", ""),
                    category=item_data.get("category", "Misc"),
                    meta=item_meta,
                )
        elif self.player.coin_count > 0:
            self.inventory.add_item(
                "Coin",
                quantity=self.player.coin_count,
                item_id="coin",
                icon=self.get_inventory_icon("coin", {"icon_path": "assets/textures/coin/coin.png"}),
                description="A shiny gold coin.",
                category="Currency",
                meta={"icon_path": "assets/textures/coin/coin.png"},
            )

        self.tile_grid = slot_data.get("tile_grid", self.tile_grid)

        self.message = f"Loaded slot {slot}"

    def build_coins_from_grid(self, coin_grid):
        coins = pygame.sprite.Group()
        for row in range(len(coin_grid)):
            for col in range(len(coin_grid[row])):
                if coin_grid[row][col] == 1:
                    coins.add(Coin(col, row))
        return coins
    
    def build_enemies_from_grid(self, enemy_grid):
        enemies = pygame.sprite.Group()
        for row in range(len(enemy_grid)):
            for col in range(len(enemy_grid[row])):
                if enemy_grid[row][col]:
                    x = col * TILE_SIZE + (TILE_SIZE - PLAYER_SIZE) // 2
                    y = row * TILE_SIZE + (TILE_SIZE - PLAYER_SIZE) // 2
                    enemies.add(Enemy(x, y, self.world_width, self.world_height))
        return enemies

    def open_save_select(self):
        self.state = SAVE_SELECT
        self.refresh_button_info()
        self.message = "Choose one of the 3 save slots"

    def open_options(self):
        self.state = OPTIONS
        self.refresh_button_info()
        self.message = "Options menu"

    def back_to_menu(self):
        self.state = MENU
        self.refresh_button_info()
        self.message = "Main menu"

    def start_slot(self, slot):
        slot_data = self.read_slot(slot)
        self.build_world_for_slot(slot_data=slot_data, slot=slot)
        self.state = GAME

    def save_current_game(self):
        if self.selected_slot is not None:
            self.write_slot(self.selected_slot)
            self.message = f"Saved slot {self.selected_slot}"

    def quit_to_menu(self):
        self.inventory.close()
        self.save_current_game()
        preview_seed = 9999 if self.selected_slot is None else self.current_seed
        self.build_preview_world(preview_seed)
        self.state = MENU
        self.refresh_button_info()
        self.message = "Returned to main menu"

    def quit_game(self):
        if self.state == GAME:
            self.save_current_game()
        self.running = False

    def toggle_fps(self):
        self.show_fps = not self.show_fps
        self.refresh_button_info()

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            self.window_width, self.window_height = self.monitor_width, self.monitor_height
            self.screen = pygame.display.set_mode(
                (self.window_width, self.window_height),
                pygame.FULLSCREEN | pygame.HWSURFACE | pygame.DOUBLEBUF,
            )
        else:
            self.window_width, self.window_height = SCREEN_WIDTH, SCREEN_HEIGHT
            self.screen = pygame.display.set_mode(
                (self.window_width, self.window_height),
                pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.RESIZABLE,
            )
        
        self.update_ui_scale()
        self.camera.set_viewport_size(self.window_width, self.window_height)
        self.preview_camera.set_viewport_size(self.window_width, self.window_height)
        self.lighting_system.set_screen_size(self.window_width, self.window_height)
        self.temp_surface = pygame.Surface((self.window_width, self.window_height)).convert()
        self.layout_menu_buttons()
        self.layout_save_buttons()
        self.layout_options_buttons()
        self.inventory.set_screen_size(self.window_width, self.window_height, self.scale)
        self.refresh_button_info()

    def resize_window(self, width, height):
        self.window_width, self.window_height = width, height
        self.screen = pygame.display.set_mode(
            (self.window_width, self.window_height),
            pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.RESIZABLE,
        )

        self.update_ui_scale()
        self.camera.set_viewport_size(self.window_width, self.window_height)
        self.preview_camera.set_viewport_size(self.window_width, self.window_height)
        self.lighting_system.set_screen_size(self.window_width, self.window_height)
        self.temp_surface = pygame.Surface((self.window_width, self.window_height)).convert()
        self.layout_menu_buttons()
        self.layout_save_buttons()
        self.layout_options_buttons()
        self.inventory.set_screen_size(self.window_width, self.window_height, self.scale)

    def handle_global_keys(self, event):
        if event.type != pygame.KEYDOWN:
            return

        if self.state == GAME and event.key == pygame.K_e:
            self.inventory.toggle()
            return

        if event.key == pygame.K_f:
            self.toggle_fullscreen()
            return

        if event.key == pygame.K_ESCAPE:
            if self.state == GAME:
                if self.inventory.open:
                    self.inventory.close()
                else:
                    self.save_current_game()
                    self.quit_to_menu()
            elif self.state in (SAVE_SELECT, OPTIONS):
                self.back_to_menu()
            else:
                self.running = False
            return

        if self.state == GAME and event.key == pygame.K_F5:
            self.save_current_game()

    def handle_events(self):
        active_buttons = []
        if self.state == MENU:
            active_buttons = self.menu_buttons
        elif self.state == SAVE_SELECT:
            active_buttons = self.save_buttons
        elif self.state == OPTIONS:
            active_buttons = self.options_buttons

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit_game()
                continue

            self.handle_global_keys(event)

            if event.type == pygame.VIDEORESIZE and not self.fullscreen:
                self.resize_window(event.w, event.h)
                continue

            if self.state == GAME and self.inventory.handle_event(event):
                continue

            for button in active_buttons:
                if button.handle_event(event):
                    break

    def update_preview(self, dt):
        self.preview_time += dt
        px = int(self.world_width * 0.5 + (self.world_width * 0.22) * pygame.math.Vector2(1, 0).rotate(self.preview_time * 22).x)
        py = int(self.world_height * 0.5 + (self.world_height * 0.18) * pygame.math.Vector2(0, 1).rotate(self.preview_time * 18).y)
        self.preview_camera.x = max(0, min(px - self.window_width // 2, self.world_width - self.window_width))
        self.preview_camera.y = max(0, min(py - self.window_height // 2, self.world_height - self.window_height))

    def update_game(self):
        if self.inventory.open:
            self.player.vel_x = 0
            self.player.vel_y = 0
        else:
            keys = pygame.key.get_pressed()
            self.player.handle_input(keys)
        self.player.update(self.wall_grid)
        self.camera.follow_player(self.player)

        for coin in pygame.sprite.spritecollide(self.player, self.coins, dokill=True):
            self.player.coin_count += 1
            self.inventory.add_item(
                "Coin",
                quantity=1,
                item_id="coin",
                icon=coin.image,
                description="A shiny gold coin.",
                category="Currency",
                meta={"icon_path": "assets/textures/coin/coin.png"},
            )

        for enemy in self.enemies:
            enemy.update(self.player.rect.center, self.wall_grid)
            if enemy._collision_rect().colliderect(self.player._collision_rect()):
                self.player.hurt(enemy.attack)
                enemy.hurt(self.player.attack)
                if self.player.health <= 0:
                    self.message = "You died! Returning to menu..."
                    pygame.time.delay(1500)
                    self.quit_to_menu()
                if enemy.health <= 0:
                    self.enemies.remove(enemy)
                    self.player.experience += enemy.experience
                    if self.player.experience >= self.player.experience_to_next_level:
                        self.player.level_up()
        
        self.update_tile_grid(self.tile_grid, self.coin_grid, self.enemy_grid, (self.player.rect.centerx, self.player.rect.centery))

    def render_world(self, active_camera):
        camera_rect = pygame.Rect(active_camera.x, active_camera.y, self.window_width, self.window_height)
        self.temp_surface.fill((0, 0, 0))
        self.temp_surface.blit(self.background, (0, 0), camera_rect)

    def render_preview(self):
        self.render_world(self.preview_camera)
        self.screen.blit(self.temp_surface, (0, 0))

        shade = pygame.Surface((self.window_width, self.window_height), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 135))
        self.screen.blit(shade, (0, 0))

        title = self.big_font.render(TITLE, True, (240, 240, 240))
        self.screen.blit(title, (self.window_width // 2 - title.get_width() // 2, self.window_height // 2 - title.get_height() - 60))

        for button in self.menu_buttons:
            button.draw(self.screen)

        info = self.small_font.render(self.message, True, (220, 220, 220))
        self.screen.blit(info, (82, self.window_height - 70))

    def render_save_select(self):
        self.render_world(self.preview_camera)
        self.screen.blit(self.temp_surface, (0, 0))

        shade = pygame.Surface((self.window_width, self.window_height), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 135))
        self.screen.blit(shade, (0, 0))

        overlay = pygame.Surface((self.window_width, self.window_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 70))
        self.screen.blit(overlay, (0, 0))

        header = self.menu_font.render("Choose a Save Slot", True, (255, 255, 255))
        self.screen.blit(header, (self.window_width // 2 - header.get_width() // 2, 120))

        hint = self.small_font.render("Click a slot to start or continue", True, (220, 220, 220))
        self.screen.blit(hint, (self.window_width // 2 - hint.get_width() // 2, 200))

        for button in self.save_buttons:
            button.draw(self.screen)

    def render_options(self):
        self.render_world(self.preview_camera)
        self.screen.blit(self.temp_surface, (0, 0))

        shade = pygame.Surface((self.window_width, self.window_height), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 135))
        self.screen.blit(shade, (0, 0))

        overlay = pygame.Surface((self.window_width, self.window_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 90))
        self.screen.blit(overlay, (0, 0))

        header = self.menu_font.render("Options", True, (255, 255, 255))
        self.screen.blit(header, (self.window_width // 2 - header.get_width() // 2, 130))

        for button in self.options_buttons:
            button.draw(self.screen)

    def render_game(self):
        self.render_world(self.camera)
        player_screen_pos = self.camera.get_sprite_screen_pos(self.player)
        self.lighting_system.apply_lighting(self.screen, self.temp_surface, player_screen_pos)

        for coin in self.coins:
            coin_x, coin_y = self.camera.get_sprite_screen_pos(coin)
            if 0 <= coin_x <= self.window_width and 0 <= coin_y <= self.window_height:
                dx = coin_x - player_screen_pos[0]
                dy = coin_y - player_screen_pos[1]
                distance = (dx * dx + dy * dy) ** 0.5
                if distance <= self.lighting_system.light_radius:
                    alpha = 255
                elif distance <= self.lighting_system.total_radius:
                    fade = 1 - ((distance - self.lighting_system.light_radius) / self.lighting_system.light_falloff)
                    alpha = int(255 * fade)
                else:
                    alpha = 0
                if alpha > 0:
                    coin.draw(self.screen, self.camera, alpha)
            
        for enemy in self.enemies:
            enemy_x, enemy_y = self.camera.get_sprite_screen_pos(enemy)
            if 0 <= enemy_x <= self.window_width and 0 <= enemy_y <= self.window_height:
                dx = enemy_x - player_screen_pos[0]
                dy = enemy_y - player_screen_pos[1]
                distance = (dx * dx + dy * dy) ** 0.5
                if distance <= self.lighting_system.light_radius:
                    alpha = 255
                elif distance <= self.lighting_system.total_radius:
                    fade = 1 - ((distance - self.lighting_system.light_radius) / self.lighting_system.light_falloff)
                    alpha = int(255 * fade)
                else:
                    alpha = 0
                if alpha > 0:
                    enemy.draw(self.screen, self.camera, alpha)

        self.player.draw(self.screen, self.camera)

        pad_x = int(15 * self.scale)
        pad_y = int(12 * self.scale)
        line_gap = int(10 * self.scale)

        score_text = self.menu_font.render(f"Score: {self.player.score}", True, (255, 255, 255))
        coin_text = self.menu_font.render(f"Coins: {self.player.coin_count}", True, (255, 255, 255))
        slot_text = self.small_font.render(
            f"Slot {self.selected_slot}   ESC: Menu   F5: Save   F: Fullscreen",
            True,
            (230, 230, 230),
        )

        self.screen.blit(score_text, (pad_x, pad_y))
        self.screen.blit(coin_text, (pad_x, pad_y + score_text.get_height() + line_gap))
        self.screen.blit(slot_text, (pad_x, pad_y + score_text.get_height() + coin_text.get_height() + line_gap * 2))

        if self.show_fps:
            fps = self.small_font.render(f"FPS: {self.clock.get_fps():.0f}", True, (255, 255, 255))
            self.screen.blit(
                fps,
                (pad_x, pad_y + score_text.get_height() + coin_text.get_height() + slot_text.get_height() + line_gap * 3),
            )

        self.inventory.draw(self.screen)

    def run(self):
        self.refresh_button_info()
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            self.handle_events()

            if self.state == GAME:
                self.update_game()
                self.render_game()
            else:
                self.update_preview(dt)
                if self.state == MENU:
                    self.render_preview()
                elif self.state == SAVE_SELECT:
                    self.render_save_select()
                elif self.state == OPTIONS:
                    self.render_options()

            pygame.display.flip()

        pygame.quit()
        sys.exit()

    def create_tile_grid(self, width, height, tile_size, wall_grid, coin_grid, enemy_grid, player_pos):
        cols = width // tile_size
        rows = height // tile_size
        grid = [[0 for _ in range(cols)] for _ in range(rows)]
        for row in range(rows):
            for col in range(cols):
                if wall_grid[row][col] == 1:
                    grid[row][col] = 1
                elif coin_grid[row][col] == 1:
                    grid[row][col] = 2
                elif enemy_grid[row][col] == 1:
                    grid[row][col] = 3
                elif (col * tile_size <= player_pos[0] < (col + 1) * tile_size) and (row * tile_size <= player_pos[1] < (row + 1) * tile_size):
                    grid[row][col] = 4
        # print(grid)
        return grid
    
    def update_tile_grid(self, grid, coin_grid, enemy_grid, player_pos):
        cols = len(grid[0])
        rows = len(grid)
        for row in range(rows):
            for col in range(cols):
                if grid[row][col] == 1:
                    continue
                elif coin_grid[row][col] == 1:
                    grid[row][col] = 2
                elif enemy_grid[row][col] == 1:
                    grid[row][col] = 3
                elif (col * TILE_SIZE <= player_pos[0] < (col + 1) * TILE_SIZE) and (row * TILE_SIZE <= player_pos[1] < (row + 1) * TILE_SIZE):
                    grid[row][col] = 4
                else:
                    grid[row][col] = 0
        
        # print(grid)

    def update_ui_scale(self):
        base_w, base_h = self.monitor_width, self.monitor_height
        self.scale = min(self.window_width / base_w, self.window_height / base_h)

        title_size = max(36, int(76 * self.scale))
        menu_size = max(22, int(42 * self.scale))
        small_size = max(14, int(26 * self.scale))

        self.big_font = pygame.font.Font("assets/fonts/Kenney Mini.ttf", title_size)
        self.menu_font = pygame.font.Font("assets/fonts/Kenney Mini.ttf", menu_size)
        self.small_font = pygame.font.Font("assets/fonts/Kenney Mini.ttf", small_size)

        # Keep player text scaled too
        if self.player is not None:
            self.player.font = pygame.font.Font("assets/fonts/Kenney Mini.ttf", max(10, int(12 * self.scale)))

if __name__ == "__main__":
    GameApp().run()
