"""Maze wall generation and drawing utilities."""

import random
import pygame
from config import TILE_SIZE, WALL_COLOR


def generate_wall_grid(world_width, world_height):
    """Generate a maze with rooms placed first and connected by corridors."""
    cols = world_width // TILE_SIZE
    rows = world_height // TILE_SIZE

    # Start with all walls
    grid = [[1 for _ in range(cols)] for _ in range(rows)]

    # Outer border walls stay in place
    for x in range(cols):
        grid[0][x] = 1
        grid[rows - 1][x] = 1
    for y in range(rows):
        grid[y][0] = 1
        grid[y][cols - 1] = 1

    rooms = _place_rooms(grid, cols, rows)
    _generate_maze_around_rooms(grid, cols, rows, rooms)
    _carve_room_entrances(grid, rooms)

    # Clear a small start area around center for the player
    start_x = cols // 2
    start_y = rows // 2
    for dy in range(-2, 3):
        for dx in range(-2, 3):
            if 0 <= start_y + dy < rows and 0 <= start_x + dx < cols:
                grid[start_y + dy][start_x + dx] = 0

    return grid


def _place_rooms(grid, cols, rows, count=7, min_size=7, max_size=11):
    """Place rooms closer together in the center region."""
    rooms = []
    center_x = cols // 2
    center_y = rows // 2
    radius_x = cols // 6
    radius_y = rows // 6

    def overlaps(a, b):
        ax, ay, aw, ah = a
        bx, by, bw, bh = b
        return not (ax + aw + 2 < bx or bx + bw + 2 < ax or ay + ah + 2 < by or by + bh + 2 < ay)

    attempts = 0
    while len(rooms) < count and attempts < count * 30:
        attempts += 1
        width = random.randrange(min_size, max_size + 1, 2)
        height = random.randrange(min_size, max_size + 1, 2)
        x = random.randrange(max(2, center_x - radius_x), min(cols - width - 2, center_x + radius_x) + 1, 2)
        y = random.randrange(max(2, center_y - radius_y), min(rows - height - 2, center_y + radius_y) + 1, 2)

        room = (x, y, width, height)
        if any(overlaps(room, other) for other in rooms):
            continue

        rooms.append(room)
        _carve_room(grid, room)

    return rooms


def _carve_room(grid, room):
    """Carve a room interior while keeping its walls intact."""
    x, y, width, height = room
    for ry in range(y + 1, y + height - 1):
        for rx in range(x + 1, x + width - 1):
            grid[ry][rx] = 0


def _carve_room_entrances(grid, rooms):
    """Carve exactly one entrance in each wall of every room and connect it to the maze."""
    for room in rooms:
        x, y, width, height = room

        # top wall
        door_x = random.randrange(x + 2, x + width - 2)
        grid[y][door_x] = 0
        _open_outside_cell(grid, door_x, y - 1)

        # bottom wall
        door_x = random.randrange(x + 2, x + width - 2)
        grid[y + height - 1][door_x] = 0
        _open_outside_cell(grid, door_x, y + height)

        # left wall
        door_y = random.randrange(y + 2, y + height - 2)
        grid[door_y][x] = 0
        _open_outside_cell(grid, x - 1, door_y)

        # right wall
        door_y = random.randrange(y + 2, y + height - 2)
        grid[door_y][x + width - 1] = 0
        _open_outside_cell(grid, x + width, door_y)


def _open_outside_cell(grid, x, y):
    rows = len(grid)
    cols = len(grid[0])
    if 0 <= x < cols and 0 <= y < rows:
        grid[y][x] = 0


def _generate_maze_around_rooms(grid, cols, rows, rooms):
    """Generate a full maze in all available space outside rooms."""
    def is_room_interior(x, y):
        return any(x > rx and x < rx + rw - 1 and y > ry and y < ry + rh - 1 for rx, ry, rw, rh in rooms)

    def is_maze_cell(x, y):
        return 0 < x < cols - 1 and 0 < y < rows - 1 and x % 2 == 1 and y % 2 == 1 and not is_room_interior(x, y)

    visited = [[False] * cols for _ in range(rows)]
    stack = []

    # Find a starting cell outside rooms
    for y in range(1, rows, 2):
        for x in range(1, cols, 2):
            if is_maze_cell(x, y):
                stack.append((x, y))
                visited[y][x] = True
                grid[y][x] = 0
                break
        if stack:
            break

    if not stack:
        return

    directions = [(2, 0), (-2, 0), (0, 2), (0, -2)]
    while stack:
        cx, cy = stack[-1]
        neighbors = []
        for dx, dy in directions:
            nx = cx + dx
            ny = cy + dy
            between_x = cx + dx // 2
            between_y = cy + dy // 2
            if is_maze_cell(nx, ny) and not visited[ny][nx]:
                neighbors.append((nx, ny, between_x, between_y))

        if not neighbors:
            stack.pop()
            continue

        nx, ny, bx, by = random.choice(neighbors)
        visited[ny][nx] = True
        grid[by][bx] = 0
        grid[ny][nx] = 0
        stack.append((nx, ny))


def draw_walls(surface, wall_grid):
    wall1 = pygame.image.load("assets/textures/wall/wall0.png").convert()
    wall2 = pygame.image.load("assets/textures/wall/wall1.png").convert()

    wall1 = pygame.transform.scale(wall1, (TILE_SIZE, TILE_SIZE))
    wall2 = pygame.transform.scale(wall2, (TILE_SIZE, TILE_SIZE))

    textures = [wall1, wall2]

    for row_index, row in enumerate(wall_grid):
        for col_index, cell in enumerate(row):
            if cell:
                x = col_index * TILE_SIZE
                y = row_index * TILE_SIZE

                texture = random.choices(textures, weights=[0.6, 0.4])[0]  # 🔥 random wall
                surface.blit(texture, (x, y))
