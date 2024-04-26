import queue
import random
from enum import Enum
import copy
import heapq


class Compass(Enum):
    NORTH = (-1, 0)
    SOUTH = (1, 0)
    WEST = (0, -1)
    EAST = (0, 1)


def print_path_on_board(board, path):

    if path == None:
        return

    for y in range(len(board)):
        for x in range(len(board[0])):
            if (x, y) == path[0]:
                print("S", end=" ")  # Start
            elif (x, y) == path[-1]:
                print("E", end=" ")  # End
            elif (x, y) in path:
                print("x", end=" ")  # Path
            elif board[y][x] == 0:
                print(".", end=" ")  # Open space
            else:
                print("#", end=" ")  # Wall
        print()


def get_compass_from_value(value):
    for member in Compass.__members__.values():
        if member.value == value:
            return member
    raise ValueError("Value not found in the enum")


def heuristic(node, current_direction, end, next_direction=None):
    if current_direction is None:
        return abs(node[0] - end[0]) + abs(node[1] - end[1])

    turns = 7 if next_direction != current_direction else 0
    return turns + abs(node[0] - end[0]) + abs(node[1] - end[1])


def a_star_least_turns(grid, start, end):
    # (total_cost, current_node, current_direction, path)
    priority_queue = [(0, start, Compass.SOUTH, [])]
    visited = set()

    width = len(grid[0])
    height = len(grid)

    while len(priority_queue):
        total_cost, current_node, current_direction, path = heapq.heappop(
            priority_queue)

        if current_node == end:
            return path + [current_node]

        if current_node in visited:
            continue

        visited.add(current_node)

        x, y = current_node
        for adjacent_x, adjacent_y in [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]:
            if (
                0 <= adjacent_x < width
                and 0 <= adjacent_y < height
                and grid[adjacent_y][adjacent_x] == 0
                and (adjacent_x, adjacent_y) not in visited
            ):
                new_direction = get_compass_from_value(
                    (y - adjacent_y, x - adjacent_x))  # Calculate new direction
  # Calculate new direction
                new_path = path + [current_node]
                cost = len(new_path)/2 + heuristic((adjacent_x,
                                                    adjacent_y), current_direction, end, new_direction)
                heapq.heappush(
                    priority_queue, (cost, (adjacent_x, adjacent_y), new_direction, new_path))

    return None


def bfs(grid: list, start: tuple, end: tuple):
    bfs_queue = queue.Queue()
    bfs_queue.put([start])
    visited = set([start])
    width = len(grid[0])
    height = len(grid)
    while not bfs_queue.empty():
        path = bfs_queue.get()
        x, y = path[-1]
        if (x, y) == end:  # Path found
            return path
        # Representing coordinates for neighbouring blocks Down,Up,Right,Left respectivly
        for adjacent_x, adjacent_y in [(x+1, y), (x-1, y), (x, y+1), (x, y-1)]:
            # Check if a negihbouring block are within bounds, not a wall and visited
            if 0 <= adjacent_x < width and 0 <= adjacent_y < height and grid[adjacent_y][adjacent_x] == 0 and (adjacent_x, adjacent_y) not in visited:
                # queue neighbour
                bfs_queue.put(path + [(adjacent_x, adjacent_y)])
                # Add neighbour to visisted
                visited.add((adjacent_x, adjacent_y))

    return None


def generate_biased_random_board(rows, cols, bias_factor=0.6):
    board = [[random.choices([0, 1], weights=[bias_factor, 1 - bias_factor])[0]
              for _ in range(cols)] for _ in range(rows)]
    board[0][0] = 0
    board[rows-1][cols-1] = 0
    return board


def path_length_with_turns(heading, path):

    path_copy = copy.copy(path)

    current_heading = heading
    current_coordinate = path[0]

    length = 0

    for i in range(1, len(path)):

        current_y, current_x = current_coordinate

        next_coordinate = path[i]
        next_y, next_x = next_coordinate

        if current_x > next_x:
            next_heading = Compass.WEST
        elif current_x < next_x:
            next_heading = Compass.EAST
        elif current_y < next_y:
            next_heading = Compass.SOUTH
        elif current_y > next_y:
            next_heading = Compass.NORTH

        if next_heading != current_heading:
            length += 1.5

        current_heading = next_heading
        current_coordinate = next_coordinate
        length += 1.125

    return length


def main() -> int:
    '''board = [
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 1, 1, 0, 0, 1, 1, 0, 0, 0],
        [0, 0, 0, 0, 0, 1, 1, 0, 0, 0],
        [0, 0, 0, 1, 0, 1, 1, 0, 0, 0],
        [0, 1, 1, 1, 0, 0, 0, 0, 0, 0],
        [0, 1, 1, 1, 0, 1, 1, 0, 0, 0],
        [0, 0, 0, 0, 0, 1, 1, 0, 0, 0],
        [0, 1, 1, 0, 0, 1, 1, 0, 0, 0],
        [0, 0, 0, 0, 0, 1, 1, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ]'''

    larger_rows = 8
    larger_cols = 8

    heading = Compass.SOUTH
# Generate a biased random board with 0s weighing more
    board = generate_biased_random_board(
        larger_rows, larger_cols, bias_factor=0.8)

    for row in board:
        print(row)

    start = (0, 0)
    end = (larger_rows-1, larger_cols-1)

    bfs_path = bfs(board, start, end)
    print("BFS:")
    print(path_length_with_turns(heading, bfs_path))
    print_path_on_board(board, bfs_path)
    print()

    a_star_path = a_star_least_turns(board, start, end)
    print(path_length_with_turns(heading, a_star_path))
    print("A_STAR:")
    print(a_star_path)
    print_path_on_board(board, a_star_path)

    return 0


if __name__ == '__main__':
    main()
