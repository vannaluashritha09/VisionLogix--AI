import cv2
import time
import pygame
import numpy as np
from collections import deque

# ==================================================
# VISIONLOGIX - SMART WAREHOUSE AUTOMATION
# ==================================================

pygame.init()

CELL = 40
COLS = 20
ROWS = 12
HEADER = 150

WIDTH = COLS * CELL
HEIGHT = ROWS * CELL + HEADER

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption(
    "VisionLogix - Smart Warehouse Automation"
)

font = pygame.font.SysFont("Arial", 20)
small_font = pygame.font.SysFont("Arial", 15)
clock = pygame.time.Clock()

# ==================================================
# WAREHOUSE DATA
# ==================================================

robot = (1, 1)
robot2 = (1, 10)
# Robot 2's independent movement state
robot2_path = []
robot2_target = None
robot2_state = "IDLE"
robot2_carrying_package = None

shelves = {
    (4, 1), (4, 2), (4, 3),
    (7, 4), (8, 4), (9, 4),
    (12, 2), (12, 3), (12, 4),
    (6, 8), (7, 8), (8, 8),
    (14, 7), (14, 8), (14, 9)
}

# Package locations
packages = {
    (3, 5): "P1",
    (9, 2): "P2",
    (11, 6): "P3",
    (5, 10): "P4",
    (16, 5): "P5"
}

red_zone = (18, 2)
green_zone = (18, 9)

target = None
path = []

detected_colour = "No colour detected"
status = "Waiting for colour selection"

carrying_package = None
delivered_count = 0
total_packages = len(packages)
# Performance dashboard statistics
delivery_attempts = 0
failed_deliveries = 0
session_start_time = time.time()

# The robot will use these states:
# IDLE -> TO_PACKAGE -> TO_DESTINATION -> IDLE

robot_state = "IDLE"

# Prevents repeated deliveries while the same colour stays visible.
last_requested_colour = None

# ==================================================
# CAMERA
# ==================================================

camera = cv2.VideoCapture(0,cv2.CAP_DSHOW)

if not camera.isOpened():
    print("ERROR: Camera could not be opened.")
    pygame.quit()
    raise SystemExit


# ==================================================
# PATHFINDING: BREADTH-FIRST SEARCH
# ==================================================

def find_path(start, goal):
    queue = deque([(start, [start])])
    visited = {start}

    while queue:
        current, current_path = queue.popleft()

        if current == goal:
            return current_path

        x, y = current

        neighbours = [
            (x + 1, y),
            (x - 1, y),
            (x, y + 1),
            (x, y - 1)
        ]

        for nx, ny in neighbours:
            next_cell = (nx, ny)

            if (
                0 <= nx < COLS
                and 0 <= ny < ROWS
                and next_cell not in shelves
                and next_cell not in visited
            ):
                visited.add(next_cell)
                queue.append(
                    (next_cell, current_path + [next_cell])
                )

    return []


# ==================================================
# CAMERA COLOUR DETECTION
# ==================================================
def detect_colour():
    print("DEBUG: detect_colour() called")

    success, frame = camera.read()

    print("DEBUG: Camera success:", success)
    print("DEBUG: Frame received:", frame is not None)

    if not success or frame is None:
        return "No colour detected"

    frame = cv2.flip(frame, 1)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Red colour ranges
    lower_red1 = np.array([0, 100, 100])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([160, 100, 100])
    upper_red2 = np.array([180, 255, 255])

    red_mask = (
        cv2.inRange(hsv, lower_red1, upper_red1)
        | cv2.inRange(hsv, lower_red2, upper_red2)
    )

    # Green colour range
    lower_green = np.array([35, 70, 70])
    upper_green = np.array([85, 255, 255])

    green_mask = cv2.inRange(
        hsv, lower_green, upper_green
    )

    # Count matching pixels
    red_pixels = cv2.countNonZero(red_mask)
    green_pixels = cv2.countNonZero(green_mask)

    print("Red pixels:", red_pixels)
    print("Green pixels:", green_pixels)

    # Decide detected colour
    MIN_PIXELS = 500
    DOMINANCE_RATIO = 1.5

    colour = "No colour detected"

    if (
        red_pixels >= MIN_PIXELS
        and red_pixels > green_pixels * DOMINANCE_RATIO
    ):
        colour = "RED"

    elif (
        green_pixels >= MIN_PIXELS
        and green_pixels > red_pixels * DOMINANCE_RATIO
    ):
        colour = "GREEN"

    print("Final detected colour:", colour)

    cv2.putText(
        frame,
        "Detected: " + colour,
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 255, 255),
        2
    )

    cv2.imshow("VisionLogix Camera", frame)
    cv2.waitKey(1)

    return colour

# ==================================================
# SELECT AND COLLECT A PACKAGE
# ==================================================

def start_delivery(colour):
    global target, path, status
    global carrying_package, robot_state
    global last_requested_colour
    global delivery_attempts, failed_deliveries

   # Only start a new delivery when the robot is idle.
    if robot_state != "IDLE":
        return

    # Do not count another attempt after all packages are delivered.
    if not packages or delivered_count >= total_packages:
        status = "All packages delivered!"
        return

    delivery_attempts += 1

    destination = red_zone if colour == "RED" else green_zone

    # Find the nearest reachable package.
    nearest_package = None
    shortest_path = None
    shortest_distance = float("inf")

    for package_position in packages:
        candidate_path = find_path(robot, package_position)

        if (
            candidate_path
            and len(candidate_path) < shortest_distance
        ):
            nearest_package = package_position
            shortest_path = candidate_path
            shortest_distance = len(candidate_path)

    if nearest_package is None:
        failed_deliveries +=1
        status = "No reachable packages found"
        return

    carrying_package = None
    target = nearest_package
    path = shortest_path
    robot_state = "TO_PACKAGE"
    last_requested_colour = colour

    status = (
        "Moving to " + packages[nearest_package]
        + " for " + colour + " delivery"
    )


# ==================================================
# ROBOT MOVEMENT AND DELIVERY
# ==================================================

def move_robot():
    global robot, path, robot_state
    global carrying_package, target, status
    global delivered_count
    global failed_deliveries

    if robot_state == "IDLE":
        return

    # Move one cell along the route.
    if len(path) > 1:
        path.pop(0)
        robot = path[0]

    # Arrived at package
    if robot_state == "TO_PACKAGE" and robot == target:

        carrying_package = packages.pop(target)

        status = "Picked up " + carrying_package

        # Select delivery destination from the detected colour.
        if last_requested_colour == "RED":
            target = red_zone
        else:
            target = green_zone

        path = find_path(robot, target)

        if path:
            robot_state = "TO_DESTINATION"
            status = (
                "Carrying " + carrying_package
                + " to " + last_requested_colour + " zone"
            )
        else:
            # Restore the package if delivery is impossible.
            packages[robot] = carrying_package
            carrying_package = None
            robot_state = "IDLE"
            failed_deliveries +=1
            status = "No route to destination"

    # Arrived at delivery destination
    elif (
        robot_state == "TO_DESTINATION"
        and robot == target
    ):
        delivered_count += 1

        status = (
            "Delivered package! Total: "
            + str(delivered_count)
        )

        carrying_package = None
        robot_state = "IDLE"
        path = []
        target = None
def move_robot2():
    global robot2, robot2_path, robot2_target, robot2_state

    if robot2_state != "MOVING":
        return

    if not robot2_path:
        robot2_state = "IDLE"
        robot2_target = None
        return

    # Move one cell along the calculated path
    if len(robot2_path) > 1:
        robot2_path.pop(0)
        robot2 = robot2_path[0]
        print("Robot 2 current position:",robot2)

    

    # Stop after reaching the target
    if robot2 == robot2_target:
        print("Robot 2 reachedd its destination!",robot2)
        robot2_state = "IDLE"
        robot2_path = []
        robot2_target = None
# ==================================================
# DRAW WAREHOUSE
# ==================================================

def draw_warehouse():
    screen.fill((245, 245, 245))

    title = font.render(
        "VISIONLOGIX - SMART WAREHOUSE",
        True,
        (20, 20, 20)
    )
    screen.blit(title, (10, 10))

    colour_text = small_font.render(
        "Camera: " + detected_colour,
        True,
        (20, 20, 20)
    )
    screen.blit(colour_text, (10, 40))

    status_text = small_font.render(
        "Status: " + status,
        True,
        (20, 20, 20)
    )
    screen.blit(status_text, (10, 60))

    count_text = small_font.render(
        "Delivered: " + str(delivered_count)
        + " / " + str(total_packages),
        True,
        (20, 20, 20)
    )
    screen.blit(count_text, (330, 40))
    # Live warehouse dashboard statistics
    remaining_packages = total_packages - delivered_count

    progress = (
        int(delivered_count / total_packages * 100)
        if total_packages > 0
        else 100
    )

    robot_text = small_font.render(
        "Robot: " + robot_state, True, (20, 20, 20)
    )
    screen.blit(robot_text, (330, 60))

    progress_text = small_font.render(
        f"Progress: {progress}% | Remaining: {remaining_packages}",
        True, (20, 20, 20)
    )
    screen.blit(progress_text, (330, 80))
    # Draw delivery progress bar
    bar_x = 330
    bar_y = 100
    bar_width = 200
    bar_height = 15

    # Background of the progress bar
    pygame.draw.rect(
        screen,
        (50, 50, 50),
        (bar_x, bar_y, bar_width, bar_height),
        1
    )
    # Performance dashboard
    elapsed_minutes = max(
        (time.time() - session_start_time) / 60,
        1 / 60
    )

    completed_jobs = delivered_count + failed_deliveries

    success_rate = (
        delivered_count / completed_jobs * 100
        if completed_jobs > 0
        else 0
    )

    packages_per_minute = delivered_count / elapsed_minutes

    dashboard_line1 = small_font.render(
        f"Attempts: {delivery_attempts} | Failed: {failed_deliveries}",
        True, (20, 20, 20)
    )
    screen.blit(dashboard_line1, (10, 120))

    dashboard_line2 = small_font.render(
        f"Success: {success_rate:.1f}% | Rate: {packages_per_minute:.2f} packages/min",
        True, (20, 20, 20)
    )
    screen.blit(dashboard_line2, (330, 120))


    # Filled section based on delivery percentage
    filled_width = int(bar_width * progress / 100)

    pygame.draw.rect(
        screen,
        (40, 180, 80),
        (bar_x, bar_y, filled_width, bar_height)
    )

    # Border around the progress bar
    pygame.draw.rect(
        screen,
        (50, 50, 50),
        (bar_x, bar_y, bar_width, bar_height),
        1
    )

    route_steps = max(0, len(path) - 1)

    if robot_state == "TO_PACKAGE" and target is not None:
        task_text = "Collect package"
    elif robot_state == "TO_DESTINATION" and target is not None:
        task_text = "Deliver package"
    else:
        task_text = "Waiting for task"

    route_text = small_font.render(
        f"Task: {task_text} | Steps: {route_steps}",
        True, (20, 20, 20)
    )
    screen.blit(route_text, (560, 60))

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
                screen, (210, 210, 210), rect, 1
            )
        

    # Draw shelves
    for x, y in shelves:
        pygame.draw.rect(
            screen,
            (125, 80, 45),
            (
                x * CELL,
                HEADER + y * CELL,
                CELL,
                CELL
            )
        )

    # Draw packages remaining on shelves
    for (x, y), label in packages.items():

        pygame.draw.rect(
            screen,
            (100, 100, 100),
            (
                x * CELL + 4,
                HEADER + y * CELL + 4,
                CELL - 8,
                CELL - 8
            )
        )

        package_text = small_font.render(
            label, True, (255, 255, 255)
        )

        screen.blit(
            package_text,
            (
                x * CELL + 7,
                HEADER + y * CELL + 12
            )
        )

    # Red destination
    pygame.draw.rect(
        screen,
        (230, 50, 50),
        (
            red_zone[0] * CELL,
            HEADER + red_zone[1] * CELL,
            CELL,
            CELL
        )
    )

    # Green destination
    pygame.draw.rect(
        screen,
        (30, 180, 70),
        (
            green_zone[0] * CELL,
            HEADER + green_zone[1] * CELL,
            CELL,
            CELL
        )
    )

    # Draw planned route
    if len(path) > 1:
        points = [
            (
                x * CELL + CELL // 2,
                HEADER + y * CELL + CELL // 2
            )
            for x, y in path
        ]

        pygame.draw.lines(
            screen,
            (255, 165, 0),
            False,
            points,
            4
        )

    # Draw robot
    robot_x = robot[0] * CELL + CELL // 2
    robot_y = HEADER + robot[1] * CELL + CELL // 2

    # Choose robot colour based on its current state
    if robot_state == "IDLE":
        robot_colour = (40, 180, 80)       # Green
    elif robot_state == "TO_PACKAGE":
        robot_colour = (30, 100, 255)     # Blue
    else:
        robot_colour = (255, 145, 30)     # Orange

    # Draw robot
    pygame.draw.circle(
        screen,
        robot_colour,
        (robot_x, robot_y),
        CELL // 3
    )

    pygame.draw.circle(
        screen,
        (255, 255, 255),
        (robot_x, robot_y),
        CELL // 3,
        2
    )

    # Show package on robot when carrying one.
    if carrying_package:
        package_label = small_font.render(
            carrying_package,
            True,
            (0, 0, 0)
        )

        screen.blit(
            package_label,
            (robot_x - 15, robot_y - 30)
        )
        # Draw Robot 2 (stationary for now)
    robot2_x = robot2[0] * CELL + CELL // 2
    robot2_y = HEADER + robot2[1] * CELL + CELL // 2

    pygame.draw.circle(
        screen,
        (160, 70, 200),
        (robot2_x, robot2_y),
        CELL // 3
    )

    pygame.draw.circle(
        screen,
        (255, 255, 255),
        (robot2_x, robot2_y),
        CELL // 3,
        2
    )

    robot2_label = small_font.render(
        "R2", True, (255, 255, 255)
    )
    robot2_position_text = small_font.render(
        f"Robot 2 Position: {robot2}",
        True,
        (20, 20, 20)
    )
    screen.blit(robot2_position_text, (560, 80))

    screen.blit(
        robot2_label,
        (robot2_x - 9, robot2_y - 8)
    )

    # Robot status legend
    legend_y = 115

    pygame.draw.circle(
        screen, (40, 180, 80), (15, legend_y), 6
    )
    screen.blit(
        small_font.render("IDLE", True, (20, 20, 20)),
        (27, legend_y - 8)
    )

    pygame.draw.circle(
        screen, (30, 100, 255), (100, legend_y), 6
    )
    screen.blit(
        small_font.render("TO_PACKAGE", True, (20, 20, 20)),
        (112, legend_y - 8)
    )

    pygame.draw.circle(
        screen, (255, 145, 30), (245, legend_y), 6
    )
    screen.blit(
        small_font.render("TO_DESTINATION", True, (20, 20, 20)),
        (257, legend_y - 8)
    )
    pygame.display.flip()


# ==================================================
# MAIN LOOP
# ==================================================

running = True
movement_timer = 0


while running:

    detected_colour = detect_colour()

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            print("KEY EVENT RECIEVED:", event.key)
            print("KEY NAME:",pygame.key.name(event.key))

            if event.key == pygame.K_ESCAPE:
                running = False
            if event.key in (pygame.K_2, pygame.K_KP2):
                print("KEY 2 PRESSED")
                if robot2_state == "IDLE":
                    robot2_target = green_zone
                    robot2_path = find_path(robot2, robot2_target)
                    print("R2 start:", robot2)
                    print("R2 target:", robot2_target)
                    print("R2 path:", robot2_path)
                    if robot2_path and len(robot2_path) > 1:
                        robot2_state = "MOVING"
                    else:
                        robot2_path = []
                        robot2_target = None
                        print("No valid path for Robot 2")

            # Manual testing controls
            if event.key == pygame.K_r:
                start_delivery("RED")

            if event.key == pygame.K_g:
                start_delivery("GREEN")

    # Start a delivery when the camera detects a new colour.
    # Reset the colour trigger only when the robot is idle
    # and no coloured object is visible.
    if robot_state == "IDLE" and detected_colour not in ("RED", "GREEN"):
        last_requested_colour = None

    # Start a delivery when a new colour is detected.
    if (
        detected_colour in ("RED", "GREEN")
        and detected_colour != last_requested_colour
        and robot_state == "IDLE"
    ):
        start_delivery(detected_colour)
    # Allow the robot to move at a visible speed.
    movement_timer += 1

    if movement_timer >= 5:
        move_robot()
        move_robot2()
        movement_timer = 0

    draw_warehouse()

    # Press Q in the camera window to exit.
    if cv2.waitKey(1) & 0xFF == ord("q"):
        running = False

    clock.tick(30)


# ==================================================
# CLEANUP
# ==================================================

camera.release()
cv2.destroyAllWindows()
pygame.quit()
