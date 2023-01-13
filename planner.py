import random
import time
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from house import House

DOORS = {
    'bathroom':         True,
    'outdoor':          True,
    'top_bedroom':      True,
    'bottom_bedroom':   True,
    'kitchen':          True,
}

class Planner:

    def __init__(self, house: House, test_mode=False, debug_mode=False):
        self._house = house
        self._test_mode = test_mode
        self._debug_mode = debug_mode

    def plan_motion(self, start=[0.,0.], end=[0.,0.], step_size=0.5, max_iter=1000):
        """
        Plan the motion of the mobile manipulator with a starting position and a final position.
        @DISCLAIMER: Manually-written motion planning as of the moment.
        """
        MIN_CORNER, MAX_CORNER = self._house._corners

        def assert_coordinates(coord, type):
            assert MIN_CORNER[0] <= coord[0] <= MAX_CORNER[0], f"{type} x-position outside of expected range, got: {MIN_CORNER[0]} <= {start[0]} <= {MAX_CORNER[0]}"
            assert MIN_CORNER[1] <= coord[1] <= MAX_CORNER[1], f"{type} y-position outside of expected range, got: {MIN_CORNER[1]} <= {start[1]} <= {MAX_CORNER[1]}"

        assert_coordinates(start, 'Start')
        assert_coordinates(end, 'End')

        # # Manually-written motion planning per room
        # if not self._test_mode:
        #     self._routes = [
        #         [[-9.25,-3.5], [-9.25,-3.0], [-7.5,-3.0], [-6.5,-1.5]],
        #         [[-5.5,-1.5], [0.0,-1.5], [0.0, -2.5], [3.8, -3.5], [4.2,-4.5], [6.6,-4.2]],
        #         [[6.4,-3.5], [6.0,-1.9]],
        #     ]
        # else:
        #     self._routes = [    # @TEST_MODE
        #         [start, end],
        #     ]

        # Manually-written doors' "openness" (ignore this)
        self._doors = [
            {
                'bathroom':         True,
                'outdoor':          True,
                'top_bedroom':      True,
                'bottom_bedroom':   True,
                'kitchen':          True,
            },
            {
                'bathroom':         False,
                'outdoor':          False,
                'top_bedroom':      False,
                'bottom_bedroom':   True,
                'kitchen':          False,
            },
            {
                'bathroom':         True,
                'outdoor':          False,
                'top_bedroom':      False,
                'bottom_bedroom':   True,
                'kitchen':          False,
            },
        ]

        # Initiation of motion planning
        no_rooms = 1 #len(self._routes) TODO
        self.mp_done = False

        # Coordinates of obstacles
        self._lines, self._points, self._boxes = self._house.generate_plot_obstacles(door_generated=False)
        obstacle_list = []
        for line in self._lines:
            if line['type'] == 'door':
                continue
            obstacle = Obstacle(line['coord'][0], line['coord'][1])
            obstacle_list.append(obstacle)
        for box in self._boxes:
            x1 = box['x']
            y1 = box['y']
            x2 = x1 + box['w']
            y2 = y1 + box['h']
            obstacle_left = Obstacle([x1,y1], [x1,y2])
            obstacle_right = Obstacle([x2,y1], [x2,y2])
            obstacle_up = Obstacle([x1,y1], [x2,y1])
            obstacle_down = Obstacle([x1,y2], [x2,y2])
            obstacle_list.append(obstacle_left)
            obstacle_list.append(obstacle_right)
            obstacle_list.append(obstacle_up)
            obstacle_list.append(obstacle_down)
        
        house_dim = [MIN_CORNER, MAX_CORNER]
        
        if self._debug_mode:
            start_time = time.time()

        self.rrt = RRT(start=start, goal=end, dim=house_dim, obstacle_list=obstacle_list, step_size=step_size, max_iter=max_iter)
        self.path, path_cost = self.rrt.find_path()

        assert self.path is not None, f"There is no optimal path found with RRT* with parameters `step_size` {step_size} and `max_iter` {max_iter}. Please restart the simulation or adjust the parameters."
        
        room_history = []
        self._routes = []
        bifurcation_idx = 0
        room = self._house.get_room(self.path[0][0], self.path[0][1])
        room_history.append(room)
        for vertex_idx, vertex in enumerate(self.path[1:]):
            room = self._house.get_room(vertex[0], vertex[1])
            if room is None:
                continue
            if room == room_history[-1]:
                continue
            route = self.path[bifurcation_idx:vertex_idx+1]
            bifurcation_idx = vertex_idx + 1
            room_history.append(room)
            self._routes.append(route)
        route = self.path[bifurcation_idx:]
        self._routes.append(route)

        if self._debug_mode:
            print(f'RRT: {len(self.path)}') if self.path is not None else print('RRT: 0')
            print(f'Vertices: {len(self.rrt.vertices)}')
            print(f'Cost: {path_cost} m')
            print(f'RRT execution time: {round(time.time() - start_time,3)} s')
            print(f'Room exploration: {room_history}')
            print(f'Routes: {self._routes}')

        return no_rooms

    def generate_waypoints(self, room):
        # assert len(self._routes[room]) > 0, f"There is no route generated. Run planner.plan_motion() before executing this method."
        # assert len(self._doors[room]) > 0, f"There is no door 'openness' generated. Run planner.plan_motion() before executing this method."
        return self.path, self._doors[room]

    def generate_trajectory(self, start, end, type=None):
        # TODO - Linear
        # TODO - Circular
        pass

    def plot_plan_2d(self, route):
        # Obtain the line and boxe coordinates of the walls, doors and furniture.
        # lines, points, boxes = self._house.generate_plot_obstacles()

        # Generate 2D plot of house.
        fig, ax = plt.subplots()

        # Plot the walls and doors as lines.
        for line in self._lines:
            x = np.array(line['coord'])[:,0]
            y = np.array(line['coord'])[:,1]
            if line['type'] == 'wall':  # Color walls as black
                color = 'black'
            else:                       # Color doors as green
                color = 'yellow'
            ax.plot(x,y, color, linewidth=2)

        # Plot the door knobs as points.
        for point in self._points:
            ax.plot(point[0], point[1], color='lime', marker='o', markersize=5)

        # Plot the furniture as boxes.
        for box in self._boxes:
            ax.add_patch(
                Rectangle((box['x'],box['y']),box['w'],box['h'],
                facecolor='blue',
                fill=True,
            ))

        # Plot RRT
        # num_points = int(self.rrt.step_size*self.rrt.max_iter)
        for vertex in self.rrt.vertices:
            ax.plot(vertex[1], vertex[2], color='orange', marker='o', markersize=1)
        
        # Plot the route as red vectors.
        if self.path is not None:
            for i in range(1,len(self.path)):
                x1 = route[i-1]
                x2 = route[i]
                magnitude_x = x2[0] - x1[0]
                magnitude_y = x2[1] - x1[1]
                theta = np.arctan2(magnitude_y, magnitude_x)
                ax.arrow(x1[0], x1[1], magnitude_x-0.05*np.cos(theta), magnitude_y-0.05*np.sin(theta), color='r', head_width=0.05, width=0.01)
                circle = plt.Circle((x1[0], x1[1]), self.rrt.step_size, color='brown', fill=False)
                ax.add_patch(circle)


        # Plot the route as red vectors.
        for routee in self._routes:
            for i in range(1,len(routee)):
                x1 = routee[i-1]
                x2 = routee[i]
                magnitude_x = x2[0] - x1[0]
                magnitude_y = x2[1] - x1[1]
                theta = np.arctan2(magnitude_y, magnitude_x)
                ax.arrow(x1[0], x1[1], magnitude_x-0.25*np.cos(theta), magnitude_y-0.25*np.sin(theta), color='g', head_width=0.2, width=0.05)
        
        plt.show()

class RRT:
    def __init__(self, start, goal, dim, obstacle_list, step_size = 1.0, max_iter = 100):
        self.start = start
        self.goal = goal
        self.dim = dim
        self.obstacle_list = obstacle_list
        self.step_size = step_size
        self.max_iter = max_iter
        self.vertices = []

    def get_distance(self, point_1, point_2):
        """
        Helper function
        """
        return np.linalg.norm(np.array(point_2) - np.array(point_1))
        # return np.sqrt((point_1[0]-point_2[0])**2 + (point_1[1]-point_2[1])**2)

    def get_heuristic(self, point):
        """
        Helper function
        """
        return self.get_distance(point[1:3], self.goal)

    def in_collision(self, point_1, point_2):
        """
        Helper function to check if a line segment between p1 and p2 is in collision
        """
        random.shuffle(self.obstacle_list)
        for obstacle in self.obstacle_list:
            if obstacle.check_collision(point_1, point_2):
                return True
        return False

    def find_nearest(self, point):
        """
        Helper function
        """
        min_dist = float('inf')
        nearest_point = None
        for vertex in self.vertices:
            dist = self.get_distance(point, vertex[1:3])
            if dist < min_dist:
                nearest_point = vertex
                min_dist = dist
        
        return nearest_point
    
    def steer(self, random_point, nearest_point, option='default'):
        """
        Helper function: steer
        """
        if self.in_collision(nearest_point, random_point):
            return None
        if self.get_distance(nearest_point, random_point) > self.step_size:
            if option == 'random':
                theta = np.random.uniform(-np.pi, np.pi)
                # mean = np.arctan2(self.goal[1] - nearest_point[1], self.goal[0] - nearest_point[0])
                # theta = np.random.normal(mean, scale=np.pi)
                random_point = [
                    nearest_point[0] + self.step_size*np.cos(theta),
                    nearest_point[1] + self.step_size*np.sin(theta),
                ]
            else:
                random_point = [
                    nearest_point[0] + self.step_size*(random_point[0]-nearest_point[0])/self.get_distance(nearest_point,random_point),
                    nearest_point[1] + self.step_size*(random_point[1]-nearest_point[1])/self.get_distance(nearest_point,random_point),
                ]
        return random_point

    def find_nearest_cluster(self, new_point):
        """
        Helper function
        """
        nearest_points = []
        for vertex in self.vertices:
            dist = self.get_distance(new_point, vertex[1:3])
            if dist < self.step_size:
                nearest_points.append(vertex[0])
        return nearest_points

    def choose_parent(self, new_point, nearest_point, nearest_points):
        """
        Helper function
        """
        chosen_parent = nearest_point[0]
        min_cost = nearest_point[4] + self.get_distance(new_point, nearest_point[1:3])
        for vertex_idx in nearest_points:
            if vertex_idx == nearest_point[0]:
                continue
            vertex = self.vertices[vertex_idx]
            cost = vertex[4] + self.get_distance(new_point, vertex[1:3])
            if cost < min_cost:
                chosen_parent = vertex[0]
                min_cost = cost
        return chosen_parent, min_cost

    def rewire(self, new_point, nearest_points):
        """
        Helper function
        """
        for vertex_idx in nearest_points:
            vertex = self.vertices[vertex_idx]
            if self.in_collision(vertex[1:3], new_point[1:3]):
                continue
            if vertex[3] is None:
                continue
            cost = new_point[4] + self.get_distance(vertex[1:3], new_point[1:3])
            if cost < vertex[4]:
                self.vertices[vertex_idx][3] = new_point[0]
                self.vertices[vertex_idx][4] = cost

    def find_path(self):
        min_x, min_y = self.dim[0]
        max_x, max_y = self.dim[1]
        self.vertices = [[0, self.start[0], self.start[1], None, 0.0]]
        while len(self.vertices) < self.max_iter:
            rand_point = [np.random.uniform(min_x, max_x), np.random.uniform(min_y, max_y)]
            nearest_point = self.find_nearest(rand_point)
            new_point = self.steer(random_point=rand_point, nearest_point=nearest_point[1:3], option='default')

            print(f'nearest point to point {len(self.vertices)}: {nearest_point}')
            if new_point is None:
                continue
            if self.in_collision(new_point, nearest_point[1:3]):
                continue

            i = len(self.vertices)
            nearest_points_idx = self.find_nearest_cluster(new_point)
            parent, cost = self.choose_parent(new_point, nearest_point, nearest_points_idx)
            new_point = [i, new_point[0], new_point[1], parent, cost]
            print(f'new point {len(self.vertices)-1}: {new_point}')
            self.vertices.append(new_point)
            self.rewire(new_point, nearest_points_idx)
            
            if self.get_heuristic(new_point) <= self.step_size:
                path = [self.goal, new_point[1:3]]
                cur_point = new_point
                while cur_point[1:3] != self.start:
                    dead_end = True
                    for vertex in self.vertices:
                        if vertex[0] == cur_point[3]:
                            print(f'Append vertex to path: {vertex[1:3]}, length: {len(path)}')
                            cur_point = vertex
                            path.append(vertex[1:3])
                            dead_end = False
                            break
                    if dead_end:
                        break
                if cur_point[1:3] == self.start:
                    return path[::-1], new_point[4]
        return None, 0

class Obstacle:
    def __init__(self, v1, v2):
        self.v1 = v1
        self.v2 = v2
        
    def check_collision(self, p1, p2):
        """ Check if the line segment from p1 to p2 intersects with the obstacle"""
        x1, y1 = p1
        x2, y2 = p2
        x3, y3 = self.v1
        x4, y4 = self.v2
        
        denominator = ((x1-x2)*(y3-y4) - (y1-y2)*(x3-x4))
        if denominator == 0:
            return False
        
        t = ((x1-x3)*(y3-y4) - (y1-y3)*(x3-x4)) / denominator
        u = -((x1-x2)*(y1-y3) - (y1-y2)*(x1-x3)) / denominator
        
        if (0 <= t <= 1) and (0 <= u <= 1):
            return True
        return False
