from pathfinding import find_path
from datetime import datetime

# Warehouse layout
# 0 = free space
# 1 = obstacle

warehouse = [
    [0, 0, 0, 0, 0],
    [0, 1, 1, 0, 0],
    [0, 0, 0, 0, 0],
    [0, 1, 0, 1, 0],
    [0, 0, 0, 0, 0]
]

# Example marker-to-destination mapping
DESTINATIONS = {
    1: (0, 4),  # Zone A
    2: (4, 4),  # Zone B
    3: (4, 0)   # Zone C
}

# Delivery task records
tasks = []


def create_delivery_task(marker_id, robot_position=(0, 0)):
    """Create a delivery task for a detected marker."""

    if marker_id not in DESTINATIONS:
        print(f"Unknown marker ID: {marker_id}")
        return None

    destination = DESTINATIONS[marker_id]

    route = find_path(
        warehouse,
        robot_position,
        destination
    )

    if route is None:
        print("No valid route to destination!")
        return None

    task = {
        "package_id": marker_id,
        "destination": destination,
        "route": route,
        "status": "PENDING",
        "created_at": datetime.now().strftime("%H:%M:%S")
    }

    tasks.append(task)

    print("\n===== NEW DELIVERY TASK =====")
    print("Package ID:", task["package_id"])
    print("Destination:", task["destination"])
    print("Route:", task["route"])
    print("Total moves:", len(task["route"]) - 1)
    print("Status:", task["status"])

    return task

def update_task_status(task, new_status):
    """Update the status of a delivery task."""

    allowed_statuses = {
        "PENDING",
        "IN_PROGRESS",
        "DELIVERED"
    }

    if new_status not in allowed_statuses:
        print("Invalid task status!")
        return

    current_status = task["status"]

    valid_transitions = {
        "PENDING": ["IN_PROGRESS"],
        "IN_PROGRESS": ["DELIVERED"],
        "DELIVERED": []
    }

    if new_status not in valid_transitions[current_status]:
        print(
            f"Cannot change status from "
            f"{current_status} to {new_status}"
        )
        return

    task["status"] = new_status

    print(
        f"Package {task['package_id']} status updated: "
        f"{new_status}"
    )


if __name__ == "__main__":
    print("VISIONLOGIX AI - DELIVERY MANAGEMENT")

    # Simulate detection of Marker ID 2
    detected_marker_id = 2

    task = create_delivery_task(detected_marker_id)

    if task:
        update_task_status(task, "IN_PROGRESS")

        # Simulate successful delivery for now
        update_task_status(task, "DELIVERED")

    print("\n===== TASK SUMMARY =====")

    for task in tasks:
        print(
            f"Package {task['package_id']} | "
            f"Destination {task['destination']} | "
            f"Status {task['status']}"
        )