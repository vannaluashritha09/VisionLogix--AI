import pygame
from pathfinding import find_path

# Initialize Pygame
pygame.init()

# Warehouse layout
# 0 = Free space
# 1 = Obstacle

warehouse = [
    [0, 0, 0, 0, 0],
    [0, 1, 1, 0, 0],
    [0, 0, 0, 0, 0],
    [0, 1, 0, 1, 0],
    [0, 0, 0, 0, 0]
]

# Starting position and destination
start = (0, 0)
goal = (4, 4)

# Calculate the route using your existing A* algorithm
path = find_path(warehouse, start, goal)

# Window settings
CELL_SIZE = 100
ROWS = len(warehouse)
COLS = len(warehouse[0])

WIDTH = COLS * CELL_SIZE
HEIGHT = ROWS * CELL_SIZE

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("VisionLogix-AI Warehouse")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
BLUE = (50, 120, 255)
GREEN = (0, 200, 0)
RED = (230, 50, 50)

clock = pygame.time.Clock()
# Robot movement settings
robot_path = path if path else []
robot_step = 0
robot_speed = 1  # Move one cell at a time
move_delay = 500  # Milliseconds between movements
last_move_time = pygame.time.get_ticks()

# Keep the window open
running = True

while running:

    # Handle window events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # White background
    screen.fill(WHITE)

    # Move the robot along the calculated path
    current_time = pygame.time.get_ticks()

    if (
        robot_path
        and robot_step < len(robot_path) - 1
        and current_time - last_move_time >= move_delay
    ):
        robot_step += robot_speed
        last_move_time = current_time

    # Draw warehouse grid
    for row in range(ROWS):
        for col in range(COLS):

            rect = pygame.Rect(
                col * CELL_SIZE,
                row * CELL_SIZE,
                CELL_SIZE,
                CELL_SIZE
            )

            if warehouse[row][col] == 1:
                pygame.draw.rect(screen, BLACK, rect)
            else:
                pygame.draw.rect(screen, WHITE, rect)

            pygame.draw.rect(screen, GRAY, rect, 2)

    # Draw the A* route
    if path:
        for row, col in path:
            rect = pygame.Rect(
                col * CELL_SIZE + 25,
                row * CELL_SIZE + 25,
                CELL_SIZE - 50,
                CELL_SIZE - 50
            )

            pygame.draw.rect(screen, BLUE, rect)

    # Draw the starting position
    pygame.draw.circle(
        screen,
        GREEN,
        (
            start[1] * CELL_SIZE + CELL_SIZE // 2,
            start[0] * CELL_SIZE + CELL_SIZE // 2
        ),
        20
    )

    # Draw the destination
    pygame.draw.circle(
        screen,
        RED,
        (
            goal[1] * CELL_SIZE + CELL_SIZE // 2,
            goal[0] * CELL_SIZE + CELL_SIZE // 2
        ),
        20
    )

    # Draw the moving delivery robot
    if robot_path:
        robot_position = robot_path[robot_step]

        robot_x = (
            robot_position[1] * CELL_SIZE
            + CELL_SIZE // 2
        )

        robot_y = (
            robot_position[0] * CELL_SIZE
            + CELL_SIZE // 2
        )

        pygame.draw.circle(
            screen,
            (255, 165, 0),
            (robot_x, robot_y),
            15
        )

    # Update the display
    pygame.display.flip()

    # Control frame rate
    clock.tick(30)

pygame.quit()