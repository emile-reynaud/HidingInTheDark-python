"""Main game entry point."""

import pygame
import sys
from coin import Coin, generate_coin_grid
from config import SCREEN_WIDTH, SCREEN_HEIGHT, FPS
from player import Player
from background import create_background
from camera import Camera
from lighting import LightingSystem
from walls import generate_wall_grid, draw_walls
import pyautogui

# Initialize pygame
pygame.init()

fullscreen = False  # Set to True for fullscreen mode

window_width, window_height = SCREEN_WIDTH, SCREEN_HEIGHT
monitor_width, monitor_height = pyautogui.size()
print(f"Monitor size: {monitor_width}x{monitor_height}")

# Create the game window with optimizations
screen = pygame.display.set_mode((window_width, window_height), pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.RESIZABLE)
pygame.display.set_caption("Hiding in the Dark")

# Clock for controlling frame rate
clock = pygame.time.Clock()

# Font for FPS display
font = pygame.font.Font("assets/fonts/Kenney Mini.ttf", 36)

# Create background (returns surface, width, height)
background, world_width, world_height = create_background()
background = background.convert()

# Create walls and draw them onto the background
wall_grid = generate_wall_grid(world_width, world_height)
draw_walls(background, wall_grid)

# Create camera
camera = Camera(world_width, world_height, window_width, window_height)

coins = pygame.sprite.Group()  # Group to hold coin sprites
coin_grid = generate_coin_grid(world_width, world_height, wall_grid)
for row in range(len(coin_grid)):
    for col in range(len(coin_grid[row])):
        if coin_grid[row][col] == 1:
            coin = Coin(col, row)
            coins.add(coin)

# Create player (starting at center of world)
player = Player(world_width // 2, world_height // 2, world_width, world_height)

# Create lighting system
lighting_system = LightingSystem(window_width, window_height, light_radius=280, light_falloff=100)

# Create a temporary surface for scene rendering (avoid repeated full-screen copies)
temp_surface = pygame.Surface((window_width, window_height)).convert()

# Main game loop
running = True
while running:
    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if fullscreen:
                    fullscreen = False
                    window_width, window_height = SCREEN_WIDTH, SCREEN_HEIGHT
                    screen = pygame.display.set_mode((window_width, window_height), pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.RESIZABLE)
                    camera.set_viewport_size(window_width, window_height)
                    lighting_system.set_screen_size(window_width, window_height)
                    temp_surface = pygame.Surface((window_width, window_height)).convert()
            if event.key == pygame.K_f:
                fullscreen = not fullscreen
                if fullscreen:
                    window_width, window_height = monitor_width, monitor_height
                    screen = pygame.display.set_mode((window_width, window_height), pygame.FULLSCREEN | pygame.HWSURFACE | pygame.DOUBLEBUF)
                else:
                    window_width, window_height = SCREEN_WIDTH, SCREEN_HEIGHT
                    screen = pygame.display.set_mode((window_width, window_height), pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.RESIZABLE)
                camera.set_viewport_size(window_width, window_height)
                lighting_system.set_screen_size(window_width, window_height)
                temp_surface = pygame.Surface((window_width, window_height)).convert()

        elif event.type == pygame.VIDEORESIZE and not fullscreen:
            window_width, window_height = event.w, event.h
            screen = pygame.display.set_mode((window_width, window_height), pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.RESIZABLE)
            camera.set_viewport_size(window_width, window_height)
            lighting_system.set_screen_size(window_width, window_height)
            temp_surface = pygame.Surface((window_width, window_height)).convert()
    
    # Get pressed keys
    keys = pygame.key.get_pressed()
    
    # Update player
    player.handle_input(keys)
    player.update(wall_grid)
    
    # Update camera to follow player
    camera.follow_player(player)
    
    # Draw background to temp surface (only visible portion)
    camera_rect = pygame.Rect(camera.x, camera.y, window_width, window_height)
    temp_surface.fill((0, 0, 0))  # Clear temp surface
    temp_surface.blit(background, (0, 0), camera_rect)

    for coin in pygame.sprite.spritecollide(player, coins, dokill=True):
        player.coin_count += 1
        coin_grid[coin.row][coin.col] = 0  # Mark coin as collected in grid
    
    # Get player positions for lighting
    player_screen_pos = camera.get_sprite_screen_pos(player)
    player_world_pos = player.rect.center

    # for coin in coins:
    #     camera_pos = camera.get_sprite_screen_pos(coin)
    #     if 0 <= camera_pos[0] <= SCREEN_WIDTH and 0 <= camera_pos[1] <= SCREEN_HEIGHT:
    #         coin.draw(temp_surface, camera)

    # Apply lighting overlay - player is the light source
    lighting_system.apply_lighting(screen, temp_surface, player_screen_pos)

    for coin in coins:
        coin_x, coin_y = camera.get_sprite_screen_pos(coin)

        if 0 <= coin_x <= window_width and 0 <= coin_y <= window_height:
            dx = coin_x - player_screen_pos[0]
            dy = coin_y - player_screen_pos[1]
            distance = (dx * dx + dy * dy) ** 0.5

            if distance <= lighting_system.light_radius:
                alpha = 255
            elif distance <= lighting_system.total_radius:
                fade = 1 - ((distance - lighting_system.light_radius) / lighting_system.light_falloff)
                alpha = int(255 * fade)
            else:
                alpha = 0

            if alpha > 0:
                coin.draw(screen, camera, alpha)
    
    # Draw player
    player.draw(screen, camera)
    
    # Display FPS counter
    fps = clock.get_fps()
    fps_text = font.render(f"FPS: {fps:.0f}", True, (255, 255, 255))
    coin_counter_text = font.render(f"Coins: {player.coin_count}", True, (255, 255, 255))
    screen.blit(fps_text, (10, 10))
    screen.blit(coin_counter_text, (10, 50))
    
    # Update display
    pygame.display.flip()
    
    # Control frame rate
    clock.tick(FPS)

# Quit
pygame.quit()
sys.exit()
