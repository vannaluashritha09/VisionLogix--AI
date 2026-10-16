import heapq


def heuristic(a, b):
    """Calculate Manhattan distance between two positions."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def find_path(grid, start, goal):
    """
    Find the shortest route using A*.

    0 = free space
    1 = obstacle

    Positions are represented as (row, column).
    """

    rows = len(grid)

    if rows == 0:
        return None

    cols = len(grid[0])

    if any(len(row) != cols for row in grid):
        raise ValueError("Grid rows must have equal lengths.")

    def valid(position):
        r, c = position
        return 0 <= r < rows and 0 <= c < cols

    if not valid(start) or not valid(goal):
        return None

    if grid[start[0]][start[1]] != 0:
        return None

    if grid[goal[0]][goal[1]] != 0:
        return None

    queue = [(heuristic(start, goal), 0, start)]
    came_from = {start: None}
    cost = {start: 0}

    directions = [
        (-1, 0),
        (1, 0),
        (0, -1),
        (0, 1)
    ]

    while queue:
        _, current_cost, current = heapq.heappop(queue)

        if current_cost != cost.get(current):
            continue

        if current == goal:
            path = []

            while current is not None:
                path.append(current)
                current = came_from[current]

            return path[::-1]

        for dr, dc in directions:
            neighbor = (current[0] + dr, current[1] + dc)

            if not valid(neighbor):
                continue

            r, c = neighbor

            if grid[r][c] == 1:
                continue

            new_cost = current_cost + 1

            if new_cost < cost.get(neighbor, float("inf")):
                cost[neighbor] = new_cost
                came_from[neighbor] = current

                priority = new_cost + heuristic(neighbor, goal)

                heapq.heappush(
                    queue,
                    (priority, new_cost, neighbor)
                )

    return None


if __name__ == "__main__":
    warehouse = [
        [0, 0, 0, 0, 0],
        [0, 1, 1, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 1, 0, 1, 0],
        [0, 0, 0, 0, 0]
    ]

    start = (0, 0)
    goal = (4, 4)

    path = find_path(warehouse, start, goal)

    if path:
        print("Route found!")
        print("Path:", path)
        print("Total moves:", len(path) - 1)
    else:
        print("No valid route found.")