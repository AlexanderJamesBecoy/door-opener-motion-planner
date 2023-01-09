import gym
import numpy as np
from model import Model
from house import House
import warnings

R_SCALE = 1.0 #how much to scale the robot's dimensions for collision check

#Dimension of robot base, found in mobilePandaWithGripper.urdf
R_RADIUS = 0.2
R_HEIGHT = 0.3

if __name__ == "__main__":

    show_warnings = False
    warning_flag = "default" if show_warnings else "ignore"
    with warnings.catch_warnings():
        warnings.filterwarnings(warning_flag)

        robot_dim = np.array([R_HEIGHT, R_RADIUS])
        robots = [Model(dim=robot_dim),]
        robots[0]._urdf.center
        env = gym.make(
            "urdf-env-v0",
            dt=0.01, robots=robots, render=True
        )

        action = np.zeros(env.n())
        action[2] = 0.5

        start_pos = robots[0].set_initial_pos(3.0,-2.0)
        ob = env.reset(pos=start_pos) # pos=...
        house = House(env, robot_dim=robot_dim, scale=R_SCALE)
        is_open = {
            'bathroom':         False,
            'outdoor':          False,
            'top_bedroom':      False,
            'bottom_bedroom':   False,
            'kitchen':          False,
        }
        house.generate_walls()
        house.generate_doors(is_open)
        house.generate_furniture()
        print(env.get_obstacles())

        print(f"Length: {len(action)}")
        print(f"Initial observation : {ob}")
        history = []

        # Target position of the robot
        waypoint = np.array([0, -2])        
        waypoints = np.array([[0, -2], [2, -2], [2, 0], [0, 0], [0, 10], [10, 10], [-10, -10]])

        # Follow a path set by waypoints
        robots[0].follow_path(env=env, house=house, waypoints=waypoints)

        env.close()
