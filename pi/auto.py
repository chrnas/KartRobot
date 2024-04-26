import queue

import copy
import heapq

from enum import Enum

WALL_DETECTION_THRESHOLD = 20
START_POS = (8, 8)


class Direction(Enum):
    FORWARD = "forward"
    LEFT = "left"
    RIGHT = "right"


class Compass(Enum):
    NORTH = (-1, 0)
    SOUTH = (1, 0)
    WEST = (0, -1)
    EAST = (0, 1)


class Instruction(Enum):
    ROTATE_WEST = 0
    ROTATE_EAST = 1
    ROTATE_NORTH = 2
    ROTATE_SOUTH = 3
    DRIVE = 4


class Block_type(Enum):
    UNKNOWN = 'unknown'
    EMPTY = 'empty'
    WALL = 'wall'


class Autopilot:
    def __init__(self, motor, server):
        self.motor = motor
        self.server = server
        self.pos = START_POS
        self.stack = []
        self.heading = Compass.NORTH
        self.map = [[Block_type.UNKNOWN for x in range(17)] for y in range(17)]
        self.visited = set()
        self.instr_queue = queue.Queue()
        self.mapping = False
        self.paused = False
        self.verbose = True

    def log(self, msg):
        if self.verbose:
            print("Auto.py: ")
            print(msg)
            print("\n")

    # Get values in Enum compass
    def get_compass_from_value(self, value):
        for member in Compass.__members__.values():
            if member.value == value:
                return member
        raise ValueError("Value not found in the enum")

    # Get next heading with respect to coordinates
    def get_next_heading(self, current_x, next_x, current_y, next_y):
        if current_x > next_x:
            return Compass.WEST
        elif current_x < next_x:
            return Compass.EAST
        elif current_y < next_y:
            return Compass.SOUTH
        elif current_y > next_y:
            return Compass.NORTH

    # Generate list of instructions from path
    def make_instructions_from_path(self, path):

        current_heading = self.heading
        current_coordinate = path.pop(0)

        while len(path):

            current_y, current_x = current_coordinate

            next_coordinate = path.pop(0)
            next_y, next_x = next_coordinate

            next_heading = self.get_next_heading(
                current_x, next_x, current_y, next_y)

            if next_heading != current_heading:
                if next_heading == Compass.NORTH:
                    self.instr_queue.put(Instruction.ROTATE_NORTH)
                elif next_heading == Compass.WEST:
                    self.instr_queue.put(Instruction.ROTATE_WEST)
                elif next_heading == Compass.SOUTH:
                    self.instr_queue.put(Instruction.ROTATE_SOUTH)
                elif next_heading == Compass.EAST:
                    self.instr_queue.put(Instruction.ROTATE_EAST)

            current_heading = next_heading

            self.instr_queue.put(Instruction.DRIVE)
            current_coordinate = next_coordinate

    # Scan neightbours
    def scan_neighbours(self, sensor_data):
        ir_front = sensor_data[0]
        ir_left = sensor_data[1]
        ir_right = sensor_data[2]

        ret = []
        coordinate_front = self.pos[0] + \
            self.heading.value[0], self.pos[1] + self.heading.value[1]
        coordinate_left = self. get_coordinate_left()
        coordinate_right = self.get_coordinate_right()

        # Right
        if ir_right >= WALL_DETECTION_THRESHOLD:
            ret.append(coordinate_right)
            self.map[coordinate_right[1]
                     ][coordinate_right[0]] = Block_type.EMPTY
            self.server.put_empty(coordinate_right)
        else:
            self.map[coordinate_right[1]
                     ][coordinate_right[0]] = Block_type.WALL
            self.server.put_wall(coordinate_right)

        # Left
        if ir_left >= WALL_DETECTION_THRESHOLD:
            ret.append(coordinate_left)
            self.map[coordinate_left[1]][coordinate_left[0]] = Block_type.EMPTY
            self.server.put_empty(coordinate_left)
        else:
            self.map[coordinate_left[1]][coordinate_left[0]] = Block_type.WALL
            self.server.put_wall(coordinate_left)

        # Front. Add last for "Forward first search"
        if ir_front >= WALL_DETECTION_THRESHOLD:
            ret.append(coordinate_front)
            self.map[coordinate_front[1]
                     ][coordinate_front[0]] = Block_type.EMPTY
            self.server.put_empty(coordinate_front)
        else:
            self.map[coordinate_front[1]
                     ][coordinate_front[0]] = Block_type.WALL
            self.server.put_wall(coordinate_front)


        return ret
    # Find fastest path

    def find_path(self, end_pos):

        bfs_path = self.bfs(self.map, self.pos, end_pos)
        # a_star_path = self.a_star_least_turns(self.map,self.pos,end_pos)

        bfs_length = self.path_length_with_turns(bfs_path)
        # a_start_length = self.path_length_with_turns(a_star_path)

        # Compare BFS and A* to get the fastest path (the one with the least amount of turns)
        # if a_start_length <= bfs_length:
        #    return a_star_path

        return bfs_path

    # Heuristic for A* to get least amount of turns
    def heuristic(self, node, end, current_direction, next_direction=None):

        if current_direction is None:
            return abs(node[0] - end[0]) + abs(node[1] - end[1])

        turns = 7 if next_direction != current_direction else 0
        return turns + abs(node[0] - end[0]) + abs(node[1] - end[1])

    def a_star_least_turns(self, grid, start, end):
        priority_queue = [(0, start, self.heading, [])]  # Init prio queue
        visited = set()  # Init visited set

        # Get width and length of grid
        width = len(grid[0])
        height = len(grid)

        while len(priority_queue):
            total_cost, current_node, current_direction, path = heapq.heappop(priority_queue)  # Get most prio elem

            # Check if att end
            if current_node == end:
                return path + [current_node]

            # Check if already visited
            if current_node in visited:
                continue

            # Add to visited
            visited.add(current_node)

            x, y = current_node

            # Loop through neighbours
            for adjacent_x, adjacent_y in [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]:

                # If in grid, is empty and not in visited calculate new direction, new path, cost and add to prio queue
                if (
                    0 <= adjacent_x and adjacent_x < width
                    and 0 <= adjacent_y and adjacent_y < height
                    and grid[adjacent_y][adjacent_x] == Block_type.EMPTY
                    and (adjacent_x, adjacent_y) not in visited
                ):
                    new_direction = self.get_compass_from_value(
                        (y - adjacent_y, x - adjacent_x))
                    new_path = path + [current_node]
                    cost = len(new_path)/2 + self.heuristic((adjacent_x,
                                                             adjacent_y), end, current_direction, new_direction)
                    heapq.heappush(
                        priority_queue, (cost, (adjacent_x, adjacent_y), new_direction, new_path))

        return None

    def bfs(self, grid: list, start: tuple, end: tuple):

        # Init queue
        bfs_queue = queue.Queue()
        bfs_queue.put([start])

        # Init visited set
        visited = set([start])

        # Get width and length of grid
        width = len(grid[0])
        height = len(grid)

        while not bfs_queue.empty():

            # Get first item in queue and last pos of that item
            path = bfs_queue.get()
            x, y = path[-1]

            if (x, y) == end:  # Check if att end
                return path

            # Loop through neighbours to current pos
            for adjacent_x, adjacent_y in [(x+1, y), (x-1, y), (x, y+1), (x, y-1)]:

                # If within grid, empty and not visited and to queue and set visited
                if 0 <= adjacent_x < width and 0 <= adjacent_y < height \
                        and grid[adjacent_y][adjacent_x] == Block_type.EMPTY \
                        and (adjacent_x, adjacent_y) not in visited:
                    bfs_queue.put(path + [(adjacent_x, adjacent_y)])
                    visited.add((adjacent_x, adjacent_y))

    # Calculate the true length of a path with respect to turns

    def path_length_with_turns(self, path):

        current_heading = self.heading
        current_coordinate = path[0]

        length = 0

        for coordinate in path[1:]:

            current_y, current_x = current_coordinate

            next_coordinate = coordinate
            next_y, next_x = next_coordinate

            next_heading = self.get_next_heading(
                current_x, next_x, current_y, next_y)

            # If we have to turn add extra
            if next_heading != current_heading:
                length += 1.5

            current_heading = next_heading
            current_coordinate = next_coordinate
            length += 1.125

        return length

    # Get coordinate to the right of current depending on current heading
    def get_coordinate_right(self):
        return self.pos[0] + self.get_clockwise_heading().value[0], self.pos[1] \
            + self.get_clockwise_heading().value[1]

    # Get coordinate to the left of current depending on current heading
    def get_coordinate_left(self):
        return self.pos[0] + self.get_anticlockwise_heading().value[0], self.pos[1] \
            + self.get_anticlockwise_heading().value[1]

    # Get coordinate in front of current depending on current heading
    def get_coordinate_front(self):
        return self.pos[0] + self.heading.value[0], self.pos[1] + self.heading.value[1]

    # Get coordinate in compass direction of current
    def get_coordinate_compass(self, compass, pos):
        return pos[0] + compass.value[1], pos[1] + compass.value[0]

    # Check if a visit is needed
    def is_visit_needed(self, pos):

        # Get coordinates around a pos
        west_coord = self.get_coordinate_compass(Compass.WEST, pos)
        east_coord = self.get_coordinate_compass(Compass.EAST, pos)
        north_coord = self.get_coordinate_compass(Compass.NORTH, pos)
        south_coord = self.get_coordinate_compass(Compass.SOUTH, pos)

        # If any of the squares around the pos is unknown a visit is needed
        if self.map[west_coord[1]][west_coord[0]] == Block_type.UNKNOWN \
                or self.map[east_coord[1]][east_coord[0]] == Block_type.UNKNOWN \
                or self.map[north_coord[1]][north_coord[0]] == Block_type.UNKNOWN \
                or self.map[south_coord[1]][south_coord[0]] == Block_type.UNKNOWN:
            return True

        # Else it is not needed
        return False

    # Get clockwise heading depending on current heading

    def get_clockwise_heading(self):
        if self.heading == Compass.NORTH:
            return Compass.EAST
        elif self.heading == Compass.EAST:
            return Compass.SOUTH
        elif self.heading == Compass.SOUTH:
            return Compass.WEST
        elif self.heading == Compass.WEST:
            return Compass.NORTH

    # Get anticlockwise heading depending on current heading
    def get_anticlockwise_heading(self):
        if self.heading == Compass.NORTH:
            return Compass.WEST
        elif self.heading == Compass.WEST:
            return Compass.SOUTH
        elif self.heading == Compass.SOUTH:
            return Compass.EAST
        elif self.heading == Compass.EAST:
            return Compass.NORTH

    # Drive forward one square
    def drive(self):
        new_pos = self.get_coordinate_front()
        self.motor.drive_forward(1)
        self.server.put_empty(self.pos)
        self.server.put_robot(new_pos)
        self.pos = new_pos

    # Rotate to north
    def rotate_north(self):
        if self.heading == Compass.WEST:
            self.motor.turn_right(1)
        elif self.heading == Compass.SOUTH:
            self.motor.turn_left(2)
        elif self.heading == Compass.EAST:
            self.motor.turn_left(1)

        self.heading = Compass.NORTH

    # Rotate to west
    def rotate_west(self):
        if self.heading == Compass.SOUTH:
            self.motor.turn_right(1)
        elif self.heading == Compass.EAST:
            self.motor.turn_left(2)
        elif self.heading == Compass.NORTH:
            self.motor.turn_left(1)

        self.heading = Compass.WEST

    # Rotate to south
    def rotate_south(self):
        if self.heading == Compass.EAST:
            self.motor.turn_right(1)
        elif self.heading == Compass.NORTH:
            self.motor.turn_left(2)
        elif self.heading == Compass.WEST:
            self.motor.turn_left(1)

        self.heading = Compass.SOUTH

    # Rotate to east
    def rotate_east(self):
        if self.heading == Compass.NORTH:
            self.motor.turn_right(1)
        elif self.heading == Compass.WEST:
            self.motor.turn_right(2)
        elif self.heading == Compass.SOUTH:
            self.motor.turn_left(1)

        self.heading = Compass.EAST

    # Execute an instruction

    def execute_instr(self, instr):
        if instr == Instruction.DRIVE:
            self.drive()
        elif instr == Instruction.ROTATE_NORTH:
            self.rotate_north()
        elif instr == Instruction.ROTATE_WEST:
            self.rotate_west()
        elif instr == Instruction.ROTATE_SOUTH:
            self.rotate_south()
        elif instr == Instruction.ROTATE_EAST:
            self.rotate_east()

        else:
            self.log("Unknown instruction")

    # Autopilot cycle
    def cycle_autopilot(self, sensor_data):
        self.log("--------------------------")
        self.log("In autopilot cycle")

        # If instruction in queue execute instruction and return
        if not self.instr_queue.empty():
            self.log("Executing instruction")
            self.execute_instr(self.instr_queue.get())
            return

        # Scan neighbours and add open to stack if not visited
        self.log("Scanning neighbours")
        open_neighbours = self.scan_neighbours(sensor_data)

        if self.pos == START_POS and not len(open_neighbours):
            coordinate_south = self.get_coordinate_compass(
                Compass.SOUTH, self.pos)
            if self.map[coordinate_south[0]][coordinate_south[1]] == Block_type.UNKNOWN:
                self.instr_queue.put(Instruction.ROTATE_SOUTH)
            return

        for n in open_neighbours:
            if n not in self.visited:
                self.stack.append(n)

        # Add current pos to visited
        self.visited.add(self.pos)

        # If stack empty, we assuma mapping is done
        self.log("Check stack")
        if not len(self.stack):

            self.log("Mapping done")

            # If not at start return to start
            if self.pos != START_POS:

                self.log("Returning to start")
                path = self.find_path(START_POS)
                self.send_path(path)
                self.make_instructions_from_path(path)

            elif self.heading != Compass.NORTH:

                # Put rotate north to queue after start pos is reached
                # to make sure that start pos is searched (no IR-sensor in back)
                self.instr_queue.put(Instruction.ROTATE_NORTH)

            else:

                self.mapping = False  # Start position has been searched, done!

            return

        self.log("Getting next")

        # If stack not empty handle stack
        while len(self.stack):

            self.log(self.stack)

            # Get next pos
            nextpos = self.stack.pop()

            # If next pos is not visited
            if nextpos not in self.visited:

                # check if a visit is needed
                if self.is_visit_needed(nextpos):

                    # if neeeded find path and make instructions
                    path = self.find_path(nextpos)
                    self.send_path(path)
                    self.make_instructions_from_path(path)

                    # Make sure copies of next pos is removed from the stack
                    if nextpos in self.stack:
                        self.stack.remove(nextpos)

                    # Break from the loop
                    break
                else:
                    # if not needed add to visit instantly
                    self.visited.add(nextpos)

    def get_pos(self):

        return self.pos

    # Send a planned path to external computer
    def send_path(self, path):

        for coord in path[1:]:
            self.server.put_path(coord)

    def is_mapping(self):

        return self.mapping

    def is_paused(self):

        return self.paused

    def pause_mapping(self):

        self.paused = True
        self.server.reset_mapping_paused()

    def unpause_mapping(self):

        self.paused = False
        self.server.reset_mapping_unpaused()

    # Stop mapping process and return to start
    def stop_mapping(self):

        self.mapping = False
        self.paused = False
        self.server.reset_mapping_stopped()

    # Start the mapping process
    def start_mapping(self):

        self.pos = START_POS
        self.stack = []
        self.heading = Compass.NORTH
        self.map = [[Block_type.UNKNOWN for x in range(17)] for y in range(17)]
        self.map[START_POS[1]][START_POS[0]] = Block_type.EMPTY
        self.visited.clear()
        self.instr_queue = queue.Queue()

        self.server.init_map(self.map, self.pos)

        self.mapping = True
        self.server.reset_mapping_started()

    def get_map(self):

        return self.map


if __name__ == "__main__":

    pass
