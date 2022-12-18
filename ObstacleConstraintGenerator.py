# Obstacles are being stored from house.py. If we add dynamic obstacles they need
# constatins too (house walls and doors), so it would be easier if we also do that
# in house.py

import numpy as np

class ObstacleConstraintsGenerator:
    def __init__(self, robot_dim: list, scale: float) -> None:
        self.walls = []
        self.doors = []
        self.robot_dim = robot_dim*scale # to be used to construct constraints later
    
    def generateConstraintsCylinder(self) -> np.ndarray:
        """
            Generate constraints for obstacles with cylindrical collision body.
            robot_dim = [height, radius]

            returns:
                4 ndarrays with points on the left, right, lower, and upper sides of the obstacles, respectively
                The robot should then have these constraints:
                    robot_radius < left_constraints
                    robot_radius < lower_constraints
                    robot_radius > right_constraints
                    robot_radius > upper_constraints
        """
        left_constraints = []
        right_constraints = []
        lower_constraints = []
        upper_constraints = []

        for wall in self.walls:
            # walls were not rotated
            if np.abs(wall['theta']) != np.pi/2:
                left_constraints.append(wall['x'] - wall['width']/2)
                right_constraints.append(wall['x'] + wall['width']/2)
                lower_constraints.append(wall['y'] - wall['length']/2)
                upper_constraints.append(wall['y'] + wall['length']/2)
            else:
                left_constraints.append(wall['x'] - wall['length']/2)
                right_constraints.append(wall['x'] + wall['length']/2)
                lower_constraints.append(wall['y'] - wall['width']/2)
                upper_constraints.append(wall['y'] + wall['width']/2)

            # TODO: add doors and maybe knobs
        
        return np.array(left_constraints), np.array(right_constraints), np.array(lower_constraints), np.array(upper_constraints)