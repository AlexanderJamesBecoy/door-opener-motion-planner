import gym
import numpy as np
import matplotlib as mpl
mpl.use('TkAgg')
from model import Model
from house import House
from planner import Planner
import warnings
from MPC import MPController
from free_space import FreeSpace
import matplotlib.pyplot as plt

TEST_MODE = True # Boolean to initialize test mode to test the MPC
R_SCALE = 1.0 #how much to scale the robot's dimensions for collision check
METHOD = ''
TOL = 1e-1

#Dimension of robot base, found in mobilePandaWithGripper.urdf
R_RADIUS = 0.2
R_HEIGHT = 0.3

if __name__ == "__main__":
    show_warnings = False
    warning_flag = "default" if show_warnings else "ignore"
    with warnings.catch_warnings():
        warnings.filterwarnings(warning_flag)

        # Main init
        robot_dim = np.array([R_HEIGHT, R_RADIUS])
        robots = [Model(dim=robot_dim),]
        robots[0]._urdf.center
        env = gym.make("urdf-env-v0", dt=0.01, robots=robots, render=True)
        house = House(env, robot_dim=robot_dim, scale=R_SCALE, test_mode=True)
        ellipsoids = []

        # History
        history = []

        # Set initial and end points
        init_position = [-3, -3, 0.4]
        end_position = [3, 3, 0.4]

        # Generate the environment
        start_pos = robots[0].set_initial_pos(init_position[:2])
        ob = env.reset(pos=start_pos)
        is_open = {
            'bathroom':         True,
            'outdoor':          True,
            'top_bedroom':      True,
            'bottom_bedroom':   True,
            'kitchen':          True,
        }
        house.generate_walls()
        # house.generate_doors()
        house.generate_furniture()
        planner = Planner(house=house, test_mode=True, debug_mode=False)
        no_rooms = planner.plan_motion(init_position[:2], end_position[:2], step_size=1)
        house.draw_walls()
        # house.draw_doors(is_open)
        house.draw_furniture()

        # Initialize MPC controller and FreeSpace for ellipsoid calculations
        MPC = MPController(robots[0])
        goal = np.array([end_position[0], end_position[1], 0, 0, 0, 0, 0])
        action = np.zeros(env.n())
        k = 0
        vertices = np.array(house.Obstacles.getVertices())

        # Combine the routes
        route = []
        for i, points in enumerate(planner._routes):
            if i == 0:
                route = np.array(points)
            elif i < len(planner._routes):
                route = np.concatenate((route, points), axis=0)

        # Add a column of z-offsets
        z_col = np.ones((route.shape[0], 1)) * 0.4
        route = np.hstack((route, z_col))

        # Initial step and observation
        action = np.zeros(env.n())

        for k, waypoint in enumerate(route):
            goal = np.array([waypoint[0], waypoint[1], 0, 0, 0, 0, 0])
            b, A = house.Obstacles.generateConstraintsCylinder(waypoint, vision_range = 1)
            z_col = np.ones((A.shape[0], 1)) * 0.4
            A = np.hstack((A, z_col))
            # MPC.add_obstacle_avoidance_constraints(A, b) 

            while (1):
                ob, _, _, _ = env.step(action)
                state0 = ob['robot_0']['joint_state']['position'][robots[0]._dofs]
                p0 = [state0[0], state0[1], 0.4]
                print("current point")
                print(k, p0, waypoint)
                b, A = house.Obstacles.generateConstraintsCylinder(p0, vision_range = 1)
                z_col = np.ones((A.shape[0], 1)) * 0.4
                A = np.hstack((A, z_col))
                if (np.allclose(p0, waypoint, rtol=TOL, atol=TOL)):
                    print("Point reached")
                    break

                try:
                    actionMPC = MPC.solve_MPC(state0, goal, A, b)
                except:
                    print(MPC.opti.debug.show_infeasibilities())
                    print(house.Obstacles.sides)
                    print(house.Obstacles.normals)
                    house.Obstacles.display()
                    # print(MPC.opti.value(MPC.A_i)@MPC.opti.value(MPC.x[:3, :]))
                    # print(b-0.3)
                    # print(house.Obstacles.sides)
                    # print(house.Obstacles.points)
                    # house.Obstacles.display()
                    
                # actionMPC = MPC.solve_MPC(state0, goal, ellipsoid[0], ellipsoid[1])
                # If current target waypoint is not the last one
                action = np.zeros(env.n())
                for i, j in enumerate(robots[0]._dofs):
                    action[j] = actionMPC[i]
            # TODO:
                # Try adding offsets
                MPC.refresh_MPC()
            # MPC.opti.set_value(MPC.state0, state0)
        print("GOAL REACHED!")
        env.close()