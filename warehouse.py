import pygame
from collections import deque

pygame.init()

# Window settings
CELL = 40
COLS = 20
ROWS = 12
HEADER = 60

WIDTH = COLS * CELL
HEIGHT = ROWS * CELL + HEADER

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("VisionLogix - Smart Warehouse")

clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 24)
title_font = pygame.font.SysFont(None, 28)

# Robot starting position
robot = (1, 1)

# Warehouse shelves
shelves = {
    (4, 1), (4, 2), (4, 3),
    (7, 4), (8, 4), (9, 4),
    (12, 2), (12, 3), (12, 4),
    (6, 8), (7, 8), (8, 8),
    (14, 7), (14, 8), (14, 9)
}

# Shelves act as obstacles
obstacles = shelves

# Packages stored on shelves
packages = {
    (4, 2): "P1",
    (8, 4): "P2",
    (12, 3): "P3",
    (7, 8): "P4",
    (14, 8): "P5"
}

# Destination zones
red_zone = (17, 2)
green_zone = (17, 9)

target = None
path = []
last_move = 0


def find_path(start, destination):
    """Find a path around shelves using BFS."""

    queue = deque([(start, [])])
    visited = {start}

    directions = [
        (1, 0),
        (-1, 0),
        (0, 1),
        (0, -1)
    ]

    while queue:
        current, current_path = queue.popleft()

        if current == destination:
            return current_path

        for dx, dy in directions:
            nxt = (current[0] + dx, current[1] + dy)

            inside = (
                0 <= nxt[0] < COLS
                and 0 <= nxt[1] < ROWS
            )

            if (
                inside
                and nxt not in obstacles
                and nxt not in visited
            ):
                visited.add(nxt)
                queue.append(
                    (nxt, current_path + [nxt])
                )

    return []


def draw_text(text, x, y, color=(20, 20, 20)):
    image = font.render(text, True, color)
    screen.blit(image, (x, y))


running = True

while running:

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_r:
                target = red_zone
                path = find_path(robot, target)

            elif event.key == pygame.K_g:
                target = green_zone
                path = find_path(robot, target)

            elif event.key == pygame.K_ESCAPE:
                running = False

    # Move robot along the calculated path
    now = pygame.time.get_ticks()

    if path and now - last_move > 180:
        robot = path.pop(0)
        last_move = now

    # Draw background
    screen.fill((245, 245, 235))

    # Header
    draw_text(
        "VisionLogix - Smart Warehouse",
        15, 8
    )

    draw_text(
        "Press R: Red Zone | Press G: Green Zone",
        15, 32
    )

    # Draw warehouse grid
    for x in range(COLS):
        for y in range(ROWS):

            rect = pygame.Rect(
                x * CELL,
                HEADER + y * CELL,
                CELL,
                CELL
            )

            pygame.draw.rect(
                screen,
                (210, 210, 210),
                rect,
                1
            )

    # Draw red destination
    pygame.draw.rect(
        screen,
        (235, 75, 75),
        (
            red_zone[0] * CELL,
            HEADER + red_zone[1] * CELL,
            CELL,
            CELL
        )
    )

    draw_text(
        "R",
        red_zone[0] * CELL + 14,
        HEADER + red_zone[1] * CELL + 10,
        (255, 255, 255)
    )

    # Draw green destination
    pygame.draw.rect(
        screen,
        (50, 180, 80),
        (
            green_zone[0] * CELL,
            HEADER + green_zone[1] * CELL,
            CELL,
            CELL
        )
    )

    draw_text(
        "G",
        green_zone[0] * CELL + 14,
        HEADER + green_zone[1] * CELL + 10,
        (255, 255, 255)
    )

    # Draw warehouse shelves
    for x, y in shelves:

        pygame.draw.rect(
            screen,
            (120, 85, 55),
            (
                x * CELL + 2,
                HEADER + y * CELL + 2,
                CELL - 4,
                CELL - 4
            ),
            border_radius=4
        )

    # Draw package labels
    for (x, y), package_name in packages.items():

        label = font.render(
            package_name,
            True,
            (255, 255, 255)
        )

        screen.blit(
            label,
            (
                x * CELL + 4,
                HEADER + y * CELL + 10
            )
        )

    # Draw robot
    robot_rect = pygame.Rect(
        robot[0] * CELL + 5,
        HEADER + robot[1] * CELL + 5,
        CELL - 10,
        CELL - 10
    )

    pygame.draw.rect(
        screen,
        (40, 100, 230),
        robot_rect,
        border_radius=8
    )

    # Status message
    if target is None:
        status = "Robot ready. Select a destination."

    elif robot == target:
        status = "Destination reached!"

    elif not path:
        status = "No route available!"

    else:
        status = "Robot navigating around shelves..."

    draw_text(
        status,
        15,
        HEIGHT - 25
    )

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
