"""A* pathfinding implementation for navigating the tile grid."""

import heapq


def heuristic(a, b):
    dx = abs(a[1] - b[1])
    dy = abs(a[0] - b[0])
    return max(dx, dy) + (1.4142 - 1) * min(dx, dy)


def get_neighbors(node, wall_grid):
    row, col = node
    rows = len(wall_grid)
    cols = len(wall_grid[0])
    neighbors = []

    # Straight moves
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nr, nc = row + dr, col + dc
        if 0 <= nr < rows and 0 <= nc < cols and wall_grid[nr][nc] == 0:
            neighbors.append(((nr, nc), 1.0))

    # Diagonal moves
    for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
        nr, nc = row + dr, col + dc

        if not (0 <= nr < rows and 0 <= nc < cols):
            continue
        if wall_grid[nr][nc] == 1:
            continue

        # Prevent corner cutting
        if wall_grid[row + dr][col] == 1:
            continue
        if wall_grid[row][col + dc] == 1:
            continue

        neighbors.append(((nr, nc), 1.4142))

    return neighbors


def reconstruct_path(came_from, current):
    path = [current]
    while current in came_from:
        current = came_from[current]
        path.append(current)
    path.reverse()
    return path


def astar(start, goal, wall_grid):
    if start == goal:
        return [start]

    open_heap = []
    heapq.heappush(open_heap, (0, start))

    came_from = {}
    g_score = {start: 0.0}
    f_score = {start: heuristic(start, goal)}
    open_lookup = {start}

    while open_heap:
        _, current = heapq.heappop(open_heap)
        open_lookup.discard(current)

        if current == goal:
            return reconstruct_path(came_from, current)

        for neighbor, move_cost in get_neighbors(current, wall_grid):
            tentative_g = g_score[current] + move_cost

            if tentative_g < g_score.get(neighbor, float("inf")):
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                f_score[neighbor] = tentative_g + heuristic(neighbor, goal)

                if neighbor not in open_lookup:
                    heapq.heappush(open_heap, (f_score[neighbor], neighbor))
                    open_lookup.add(neighbor)

    return []